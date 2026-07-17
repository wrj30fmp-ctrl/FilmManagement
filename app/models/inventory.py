"""库存记录数据模型"""

from dataclasses import dataclass, field


@dataclass
class FilmInventory:
    """胶卷库存记录"""

    model: str                           # 胶卷型号（必填）
    film_format: str                     # 画幅：135 / 120 / 其他（必填）
    id: str = ""                         # UUID
    user_id: str = "local-user"
    brand: str = ""                      # 品牌
    film_type: str = ""                  # 色彩类型
    box_iso: int = 0                     # 标称 ISO
    quantity_cache: int = 0              # 库存缓存数量
    batch_number: str = ""               # 乳剂批次
    expiry_date: str = ""                # 有效期 YYYY-MM-DD
    purchase_date: str = ""              # 购买日期 YYYY-MM-DD
    purchase_source: str = ""            # 购买渠道
    unit_price: float = 0.0              # 单卷价格
    currency: str = "CNY"                # 货币代码
    storage_location: str = ""           # 存放位置
    storage_method: str = ""             # 保存方式：常温/冷藏/冷冻
    notes: str = ""                      # 备注
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""
    version: int = 1
    device_id: str = ""
    sync_status: str = "local"

    def to_dict(self) -> dict:
        """转换为字典，用于写入数据库"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "brand": self.brand,
            "model": self.model,
            "film_format": self.film_format,
            "film_type": self.film_type,
            "box_iso": self.box_iso,
            "quantity_cache": self.quantity_cache,
            "batch_number": self.batch_number,
            "expiry_date": self.expiry_date,
            "purchase_date": self.purchase_date,
            "purchase_source": self.purchase_source,
            "unit_price": self.unit_price,
            "currency": self.currency,
            "storage_location": self.storage_location,
            "storage_method": self.storage_method,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
            "version": self.version,
            "device_id": self.device_id,
            "sync_status": self.sync_status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FilmInventory":
        """从数据库查询结果字典创建实例"""
        return cls(
            id=data.get("id", ""),
            user_id=data.get("user_id", "local-user"),
            brand=data.get("brand", ""),
            model=data.get("model", ""),
            film_format=data.get("film_format", ""),
            film_type=data.get("film_type", ""),
            box_iso=data.get("box_iso", 0),
            quantity_cache=data.get("quantity_cache", 0),
            batch_number=data.get("batch_number", ""),
            expiry_date=data.get("expiry_date", ""),
            purchase_date=data.get("purchase_date", ""),
            purchase_source=data.get("purchase_source", ""),
            unit_price=data.get("unit_price", 0.0),
            currency=data.get("currency", "CNY"),
            storage_location=data.get("storage_location", ""),
            storage_method=data.get("storage_method", ""),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            deleted_at=data.get("deleted_at", ""),
            version=data.get("version", 1),
            device_id=data.get("device_id", ""),
            sync_status=data.get("sync_status", "local"),
        )
