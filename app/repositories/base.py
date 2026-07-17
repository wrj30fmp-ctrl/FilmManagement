"""
Repository 基类

提供通用的 CRUD 操作，所有数据访问类应继承此类。
- 自动处理 UUID 生成、时间戳、软删除
- 所有查询使用参数化 SQL
- 默认过滤已软删除的记录
"""

import logging
from typing import Any

from app.database.connection import get_db
from app.utils.uuid_utils import generate_uuid
from app.utils.date_utils import utc_now_iso

logger = logging.getLogger(__name__)

# 默认 user_id（第一阶段单用户模式）
DEFAULT_USER_ID = "local-user"


class BaseRepository:
    """通用 Repository 基类

    子类需要设置 table_name 和 columns 属性。

    使用示例:
        class InventoryRepository(BaseRepository):
            table_name = "film_inventory"
            columns = ["brand", "model", "film_format", ...]
    """

    table_name: str = ""
    columns: list[str] = []

    def __init__(self):
        if not self.table_name:
            raise ValueError(f"{self.__class__.__name__} 必须设置 table_name 属性")
        self.db = get_db()

    # ================================================================
    # 通用查询方法
    # ================================================================

    def get_by_id(self, record_id: str) -> dict | None:
        """根据 UUID 获取单条记录（排除已删除）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ? AND deleted_at IS NULL;",
                (record_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_id_include_deleted(self, record_id: str) -> dict | None:
        """根据 UUID 获取单条记录（包含已删除）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?;",
                (record_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_all(
        self,
        order_by: str = "created_at",
        order_desc: bool = True,
        limit: int | None = None,
    ) -> list[dict]:
        """获取所有未删除的记录

        Args:
            order_by: 排序字段
            order_desc: 是否降序
            limit: 限制返回数量
        """
        order_dir = "DESC" if order_desc else "ASC"
        sql = f"SELECT * FROM {self.table_name} WHERE deleted_at IS NULL ORDER BY {order_by} {order_dir}"
        params: list = []
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def count_all(self) -> int:
        """获取未删除记录总数"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE deleted_at IS NULL;"
            )
            return cursor.fetchone()[0]

    # ================================================================
    # 通用写入方法
    # ================================================================

    def create(self, data: dict) -> str:
        """创建新记录

        Args:
            data: 记录数据字典（不需要包含 id, created_at, updated_at）

        Returns:
            新创建的记录 UUID
        """
        now = utc_now_iso()
        record_id = generate_uuid()

        # 自动填充通用字段
        data["id"] = record_id
        data["user_id"] = data.get("user_id", DEFAULT_USER_ID)
        data["created_at"] = now
        data["updated_at"] = now
        data["sync_status"] = data.get("sync_status", "local")

        # 筛选有效的列，并将空字符串转为 None（NULL），避免外键约束失败
        insert_data = {}
        for k, v in data.items():
            if k in self.columns or k == "id":
                insert_data[k] = v if v != "" else None
        # 添加通用字段
        for field in ["id", "user_id", "created_at", "updated_at", "sync_status"]:
            if field not in insert_data:
                insert_data[field] = data.get(field)

        columns_str = ", ".join(insert_data.keys())
        placeholders = ", ".join(["?"] * len(insert_data))
        values = list(insert_data.values())

        sql = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders});"

        with self.db.get_connection() as conn:
            try:
                conn.execute(sql, values)
                conn.commit()
                logger.debug(f"创建记录: {self.table_name} id={record_id}")
                return record_id
            except Exception:
                conn.rollback()
                raise

    def update(self, record_id: str, data: dict) -> bool:
        """更新记录

        Args:
            record_id: 记录 UUID
            data: 要更新的字段字典

        Returns:
            是否成功更新
        """
        if not data:
            return False

        now = utc_now_iso()
        data["updated_at"] = now

        # 只更新合法列，排除 id, created_at 等不可修改字段
        updatable = ["id", "created_at", "user_id", "deleted_at", "sync_status"]
        update_data = {k: v for k, v in data.items() if k not in updatable}

        if not update_data:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [record_id]

        # 增加版本号
        sql = (
            f"UPDATE {self.table_name} SET {set_clause}, version = version + 1 "
            f"WHERE id = ? AND deleted_at IS NULL;"
        )

        with self.db.get_connection() as conn:
            try:
                cursor = conn.execute(sql, values)
                conn.commit()
                updated = cursor.rowcount > 0
                if updated:
                    logger.debug(f"更新记录: {self.table_name} id={record_id}")
                return updated
            except Exception:
                conn.rollback()
                raise

    def soft_delete(self, record_id: str) -> bool:
        """软删除记录（设置 deleted_at 时间戳）

        Args:
            record_id: 记录 UUID

        Returns:
            是否成功删除
        """
        now = utc_now_iso()
        with self.db.get_connection() as conn:
            try:
                cursor = conn.execute(
                    f"UPDATE {self.table_name} SET deleted_at = ?, updated_at = ?, "
                    f"version = version + 1 WHERE id = ? AND deleted_at IS NULL;",
                    (now, now, record_id),
                )
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.debug(f"软删除记录: {self.table_name} id={record_id}")
                return deleted
            except Exception:
                conn.rollback()
                raise

    def restore(self, record_id: str) -> bool:
        """恢复已软删除的记录

        Args:
            record_id: 记录 UUID

        Returns:
            是否成功恢复
        """
        now = utc_now_iso()
        with self.db.get_connection() as conn:
            try:
                cursor = conn.execute(
                    f"UPDATE {self.table_name} SET deleted_at = NULL, updated_at = ?, "
                    f"version = version + 1 WHERE id = ? AND deleted_at IS NOT NULL;",
                    (now, record_id),
                )
                conn.commit()
                restored = cursor.rowcount > 0
                if restored:
                    logger.debug(f"恢复记录: {self.table_name} id={record_id}")
                return restored
            except Exception:
                conn.rollback()
                raise

    def hard_delete(self, record_id: str) -> bool:
        """永久删除记录（物理删除，不可恢复）

        谨慎使用！通常应优先使用 soft_delete。

        Args:
            record_id: 记录 UUID

        Returns:
            是否成功删除
        """
        with self.db.get_connection() as conn:
            try:
                cursor = conn.execute(
                    f"DELETE FROM {self.table_name} WHERE id = ?;",
                    (record_id,),
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception:
                conn.rollback()
                raise

    # ================================================================
    # 辅助方法
    # ================================================================

    def exists(self, record_id: str) -> bool:
        """检查记录是否存在且未被删除"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT 1 FROM {self.table_name} WHERE id = ? AND deleted_at IS NULL;",
                (record_id,),
            )
            return cursor.fetchone() is not None

    def search_by_field(self, field: str, value: Any) -> list[dict]:
        """按指定字段搜索（精确匹配，排除已删除）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE {field} = ? AND deleted_at IS NULL;",
                (value,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_changed_since(self, since: str) -> list[dict]:
        """获取指定时间之后变更的记录（用于同步）

        Args:
            since: ISO 8601 时间字符串

        Returns:
            变更记录列表
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE updated_at > ?;",
                (since,),
            )
            return [dict(row) for row in cursor.fetchall()]
