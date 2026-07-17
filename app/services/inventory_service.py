"""
库存管理业务服务

处理库存的新增、编辑、删除、筛选等业务逻辑。
涉及库存数量变更时，必须同时写入库存流水表，并在同一事务中完成。
"""

import logging
from typing import Any

from app.database.connection import get_db
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.transaction_repo import TransactionRepository
from app.constants import TransactionType
from app.utils.uuid_utils import generate_uuid
from app.utils.date_utils import utc_now_iso, days_until_expiry

logger = logging.getLogger(__name__)


class InventoryService:
    """库存业务服务"""

    def __init__(self):
        self.repo = InventoryRepository()
        self.trans_repo = TransactionRepository()
        self.db = get_db()

    # ================================================================
    # 查询
    # ================================================================

    def get_inventory(self, inventory_id: str) -> dict | None:
        """获取单条库存记录"""
        return self.repo.get_by_id(inventory_id)

    def list_inventory(
        self,
        brand: str = "",
        film_format: str = "",
        film_type: str = "",
        box_iso: int | None = None,
        expired: str = "",
        keyword: str = "",
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> list[dict]:
        """获取库存列表（支持筛选和排序）"""
        return self.repo.list_with_filters(
            brand=brand,
            film_format=film_format,
            film_type=film_type,
            box_iso=box_iso,
            expired=expired,
            keyword=keyword,
            order_by=order_by,
            order_desc=order_desc,
        )

    def count_inventory(
        self,
        brand: str = "",
        film_format: str = "",
        expired: str = "",
        keyword: str = "",
    ) -> int:
        """获取库存数量"""
        return self.repo.count_with_filters(
            brand=brand,
            film_format=film_format,
            expired=expired,
            keyword=keyword,
        )

    def get_filter_options(self) -> dict:
        """获取筛选选项：现有品牌列表和 ISO 列表"""
        return {
            "brands": self.repo.get_brands(),
            "isos": self.repo.get_isos(),
        }

    # ================================================================
    # 新增库存（含初始库存流水）
    # ================================================================

    def create_inventory(self, data: dict) -> str:
        """新增库存记录

        新增库存时，同时创建一条 purchase 类型的库存流水。
        两个操作在同一事务中完成。

        Args:
            data: 库存数据字典，必须包含 model, film_format, quantity_cache

        Returns:
            新创建的库存记录 UUID

        Raises:
            ValueError: 数据校验不通过
        """
        # 必填字段校验
        if not data.get("model", "").strip():
            raise ValueError("胶卷型号为必填项。")
        if not data.get("film_format", "").strip():
            raise ValueError("画幅为必填项。")

        quantity = data.get("quantity_cache", 0)
        if quantity < 0:
            raise ValueError("库存数量不能为负数。")

        with self.db.transaction() as conn:
            # 1. 创建库存记录
            record_id = self.repo.create(data)

            # 2. 如果数量 > 0，创建 purchase 类型的库存流水
            if quantity > 0:
                trans_data = {
                    "inventory_id": record_id,
                    "change_amount": quantity,
                    "transaction_type": TransactionType.PURCHASE,
                    "reason": "初始库存入库",
                }
                self.trans_repo.create(trans_data)

            logger.info(f"新增库存: id={record_id}, model={data.get('model')}, qty={quantity}")
            return record_id

    # ================================================================
    # 编辑库存
    # ================================================================

    def update_inventory(self, inventory_id: str, data: dict) -> bool:
        """编辑库存记录（不修改数量）

        如需修改数量，请使用 adjust_quantity 方法以产生库存流水。

        Args:
            inventory_id: 库存 UUID
            data: 要更新的字段

        Returns:
            是否成功
        """
        # 不允许直接修改数量，必须通过 adjust_quantity
        data.pop("quantity_cache", None)

        if not data:
            return False

        return self.repo.update(inventory_id, data)

    # ================================================================
    # 库存数量调整（产生流水）
    # ================================================================

    def adjust_quantity(
        self,
        inventory_id: str,
        change_amount: int,
        transaction_type: str,
        reason: str = "",
        related_roll_id: str = "",
    ) -> bool:
        """调整库存数量（在同一事务中更新缓存和写入流水）

        Args:
            inventory_id: 库存 UUID
            change_amount: 变化量（正数入库，负数出库）
            transaction_type: 流水类型
            reason: 变动原因
            related_roll_id: 关联的拍摄记录 UUID

        Returns:
            是否成功

        Raises:
            ValueError: 库存不足
        """
        inventory = self.repo.get_by_id(inventory_id)
        if not inventory:
            raise ValueError(f"库存记录不存在: {inventory_id}")

        current_qty = inventory["quantity_cache"]
        new_qty = current_qty + change_amount

        if new_qty < 0:
            raise ValueError(
                f"库存不足。当前库存 {current_qty}，尝试出库 {abs(change_amount)} 卷。"
            )

        with self.db.transaction() as conn:
            # 1. 更新库存缓存
            self.repo.update_quantity(inventory_id, new_qty)

            # 2. 写入库存流水
            trans_data = {
                "inventory_id": inventory_id,
                "change_amount": change_amount,
                "transaction_type": transaction_type,
                "related_roll_id": related_roll_id,
                "reason": reason,
            }
            self.trans_repo.create(trans_data)

            logger.info(
                f"库存调整: inventory={inventory_id}, "
                f"change={change_amount}, new_qty={new_qty}, type={transaction_type}"
            )
            return True

    # ================================================================
    # 删除
    # ================================================================

    def delete_inventory(self, inventory_id: str) -> bool:
        """软删除库存记录"""
        return self.repo.soft_delete(inventory_id)

    # ================================================================
    # 过期检查
    # ================================================================

    def get_expiry_status(self, expiry_date: str) -> str:
        """获取过期状态

        Returns:
            "expired" / "expiring_soon" / "normal" / "unknown"
        """
        if not expiry_date:
            return "unknown"
        days = days_until_expiry(expiry_date)
        if days is None:
            return "unknown"
        if days < 0:
            return "expired"
        if days <= 90:
            return "expiring_soon"
        return "normal"

    def get_expiring_inventory(self) -> list[dict]:
        """获取即将过期（90天内）和已过期的库存"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM film_inventory "
                "WHERE deleted_at IS NULL AND expiry_date IS NOT NULL "
                "AND quantity_cache > 0 "
                "ORDER BY expiry_date;"
            )
            return [dict(row) for row in cursor.fetchall()]
