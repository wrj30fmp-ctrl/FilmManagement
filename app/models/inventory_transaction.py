"""库存流水数据模型"""

from dataclasses import dataclass


@dataclass
class InventoryTransaction:
    """库存流水记录"""

    inventory_id: str                    # 关联库存记录 UUID
    change_amount: int                   # 库存变化数量（正数入库，负数出库）
    transaction_type: str                # 流水类型：purchase / start_shooting 等
    id: str = ""
    user_id: str = "local-user"
    related_roll_id: str = ""            # 关联的拍摄记录 UUID
    reason: str = ""                     # 变动原因
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""
    version: int = 1
    device_id: str = ""
    sync_status: str = "local"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "inventory_id": self.inventory_id,
            "change_amount": self.change_amount,
            "transaction_type": self.transaction_type,
            "related_roll_id": self.related_roll_id,
            "reason": self.reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
            "version": self.version,
            "device_id": self.device_id,
            "sync_status": self.sync_status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryTransaction":
        return cls(
            id=data.get("id", ""),
            user_id=data.get("user_id", "local-user"),
            inventory_id=data.get("inventory_id", ""),
            change_amount=data.get("change_amount", 0),
            transaction_type=data.get("transaction_type", ""),
            related_roll_id=data.get("related_roll_id", ""),
            reason=data.get("reason", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            deleted_at=data.get("deleted_at", ""),
            version=data.get("version", 1),
            device_id=data.get("device_id", ""),
            sync_status=data.get("sync_status", "local"),
        )
