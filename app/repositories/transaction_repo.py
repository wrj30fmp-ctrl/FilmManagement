"""
库存流水 Repository

管理 inventory_transactions 表的读写操作。
"""

from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository):
    """库存流水数据访问层"""

    table_name = "inventory_transactions"
    columns = [
        "id", "user_id", "inventory_id", "change_amount",
        "transaction_type", "related_roll_id", "reason",
        "created_at", "updated_at", "deleted_at", "version",
        "device_id", "sync_status",
    ]

    def get_by_inventory(self, inventory_id: str) -> list[dict]:
        """获取指定库存记录的所有流水"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM inventory_transactions "
                "WHERE inventory_id = ? AND deleted_at IS NULL "
                "ORDER BY created_at DESC;",
                (inventory_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_total_quantity(self, inventory_id: str) -> int:
        """通过流水求和获得当前库存数量（用于校验 quantity_cache）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COALESCE(SUM(change_amount), 0) FROM inventory_transactions "
                "WHERE inventory_id = ? AND deleted_at IS NULL;",
                (inventory_id,),
            )
            return cursor.fetchone()[0]
