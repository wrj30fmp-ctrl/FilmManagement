"""胶卷状态历史数据模型"""

from dataclasses import dataclass


@dataclass
class FilmRollStatusHistory:
    """胶卷状态变更历史"""

    film_roll_id: str                      # 关联的拍摄记录 UUID
    to_status: str                         # 变更后状态代码
    changed_at: str                        # 变更时间
    id: str = ""
    user_id: str = "local-user"
    from_status: str = ""                  # 变更前状态代码
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
            "film_roll_id": self.film_roll_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "changed_at": self.changed_at,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
            "version": self.version,
            "device_id": self.device_id,
            "sync_status": self.sync_status,
        }
