"""
胶卷库存 Repository

提供库存记录的数据库访问操作，继承自 BaseRepository。
支持按品牌、画幅、ISO、过期状态等条件筛选。
"""

from typing import Any

from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository):
    """胶卷库存数据访问层"""

    table_name = "film_inventory"
    columns = [
        "id", "user_id", "brand", "model", "film_format", "film_type",
        "box_iso", "quantity_cache", "batch_number", "expiry_date",
        "purchase_date", "purchase_source", "unit_price", "currency",
        "storage_location", "storage_method", "photo_path", "notes",
        "created_at", "updated_at", "deleted_at", "version",
        "device_id", "sync_status",
    ]

    def list_with_filters(
        self,
        brand: str = "",
        film_format: str = "",
        film_type: str = "",
        box_iso: int | None = None,
        expired: str = "",            # "expired" / "expiring_soon" / ""
        keyword: str = "",
        order_by: str = "created_at",
        order_desc: bool = True,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict]:
        """带筛选条件的库存列表查询

        Args:
            brand: 品牌筛选（模糊匹配）
            film_format: 画幅
            film_type: 色彩类型
            box_iso: ISO
            expired: 过期状态 "expired" / "expiring_soon" / ""
            keyword: 关键词搜索（匹配品牌、型号、批次、备注）
            order_by: 排序字段
            order_desc: 是否降序
            limit: 限制条数
            offset: 偏移量
        """
        conditions = ["deleted_at IS NULL"]
        params: list = []

        if brand:
            conditions.append("brand LIKE ?")
            params.append(f"%{brand}%")

        if film_format:
            conditions.append("film_format = ?")
            params.append(film_format)

        if film_type:
            conditions.append("film_type = ?")
            params.append(film_type)

        if box_iso is not None:
            conditions.append("box_iso = ?")
            params.append(box_iso)

        if expired == "expired":
            conditions.append("expiry_date IS NOT NULL AND expiry_date < date('now', 'localtime')")
        elif expired == "expiring_soon":
            conditions.append(
                "expiry_date IS NOT NULL AND expiry_date >= date('now', 'localtime') "
                "AND expiry_date <= date('now', 'localtime', '+90 days')"
            )

        if keyword:
            conditions.append(
                "(brand LIKE ? OR model LIKE ? OR batch_number LIKE ? OR notes LIKE ?)"
            )
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw, kw])

        where_clause = " AND ".join(conditions)
        order_dir = "DESC" if order_desc else "ASC"
        sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY {order_by} {order_dir}"

        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def count_with_filters(
        self,
        brand: str = "",
        film_format: str = "",
        film_type: str = "",
        box_iso: int | None = None,
        expired: str = "",
        keyword: str = "",
    ) -> int:
        """获取筛选条件下的记录总数"""
        conditions = ["deleted_at IS NULL"]
        params: list = []

        if brand:
            conditions.append("brand LIKE ?")
            params.append(f"%{brand}%")
        if film_format:
            conditions.append("film_format = ?")
            params.append(film_format)
        if film_type:
            conditions.append("film_type = ?")
            params.append(film_type)
        if box_iso is not None:
            conditions.append("box_iso = ?")
            params.append(box_iso)
        if expired == "expired":
            conditions.append("expiry_date IS NOT NULL AND expiry_date < date('now', 'localtime')")
        elif expired == "expiring_soon":
            conditions.append(
                "expiry_date IS NOT NULL AND expiry_date >= date('now', 'localtime') "
                "AND expiry_date <= date('now', 'localtime', '+90 days')"
            )
        if keyword:
            conditions.append(
                "(brand LIKE ? OR model LIKE ? OR batch_number LIKE ? OR notes LIKE ?)"
            )
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw, kw])

        where_clause = " AND ".join(conditions)
        sql = f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()[0]

    def update_quantity(self, inventory_id: str, new_quantity: int) -> bool:
        """更新库存缓存数量

        Args:
            inventory_id: 库存记录 UUID
            new_quantity: 新的库存数量（必须 >= 0）

        Returns:
            是否成功
        """
        with self.db.get_connection() as conn:
            try:
                from app.utils.date_utils import utc_now_iso
                cursor = conn.execute(
                    "UPDATE film_inventory SET quantity_cache = ?, updated_at = ?, "
                    "version = version + 1 WHERE id = ? AND deleted_at IS NULL;",
                    (new_quantity, utc_now_iso(), inventory_id),
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception:
                conn.rollback()
                raise

    def get_brands(self) -> list[str]:
        """获取所有不重复的品牌列表"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT brand FROM film_inventory "
                "WHERE deleted_at IS NULL AND brand IS NOT NULL AND brand != '' "
                "ORDER BY brand;"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_isos(self) -> list[int]:
        """获取所有不重复的 ISO 列表"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT box_iso FROM film_inventory "
                "WHERE deleted_at IS NULL AND box_iso IS NOT NULL AND box_iso > 0 "
                "ORDER BY box_iso;"
            )
            return [row[0] for row in cursor.fetchall()]
