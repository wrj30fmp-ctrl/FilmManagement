"""拍摄胶卷记录数据模型"""

from dataclasses import dataclass


@dataclass
class FilmRoll:
    """拍摄胶卷记录"""

    roll_number: str                       # 用户可见编号，如 2026-07-001
    model: str                             # 胶卷型号（必填）
    film_format: str                       # 画幅（必填）
    status: str                            # 状态代码（英文）
    id: str = ""
    user_id: str = "local-user"
    inventory_id: str = ""                 # 来源库存 UUID
    brand: str = ""
    film_type: str = ""
    box_iso: int = 0
    exposure_iso: int = 0                  # 实际拍摄 ISO
    camera: str = ""
    lens: str = ""
    load_date: str = ""                    # 装卷日期
    finish_date: str = ""                  # 拍摄完成日期
    location: str = ""                     # 拍摄地点
    subject: str = ""                      # 拍摄主题
    push_pull: float = 0.0                 # 迫冲/拉冲档数
    notes: str = ""
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
            "roll_number": self.roll_number,
            "inventory_id": self.inventory_id,
            "brand": self.brand,
            "model": self.model,
            "film_format": self.film_format,
            "film_type": self.film_type,
            "box_iso": self.box_iso,
            "exposure_iso": self.exposure_iso,
            "camera": self.camera,
            "lens": self.lens,
            "load_date": self.load_date,
            "finish_date": self.finish_date,
            "location": self.location,
            "subject": self.subject,
            "status": self.status,
            "push_pull": self.push_pull,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
            "version": self.version,
            "device_id": self.device_id,
            "sync_status": self.sync_status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FilmRoll":
        return cls(
            id=data.get("id", ""),
            user_id=data.get("user_id", "local-user"),
            roll_number=data.get("roll_number", ""),
            inventory_id=data.get("inventory_id", ""),
            brand=data.get("brand", ""),
            model=data.get("model", ""),
            film_format=data.get("film_format", ""),
            film_type=data.get("film_type", ""),
            box_iso=data.get("box_iso", 0),
            exposure_iso=data.get("exposure_iso", 0),
            camera=data.get("camera", ""),
            lens=data.get("lens", ""),
            load_date=data.get("load_date", ""),
            finish_date=data.get("finish_date", ""),
            location=data.get("location", ""),
            subject=data.get("subject", ""),
            status=data.get("status", ""),
            push_pull=data.get("push_pull", 0.0),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            deleted_at=data.get("deleted_at", ""),
            version=data.get("version", 1),
            device_id=data.get("device_id", ""),
            sync_status=data.get("sync_status", "local"),
        )
