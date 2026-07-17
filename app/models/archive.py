"""归档记录数据模型"""

from dataclasses import dataclass


@dataclass
class ArchiveRecord:
    """归档记录"""

    film_roll_id: str
    id: str = ""
    user_id: str = "local-user"
    negative_location: str = ""
    binder_number: str = ""
    page_number: str = ""
    local_path: str = ""
    cloud_url: str = ""
    storage_type: str = "local"
    cloud_backup: bool = False
    offsite_backup: bool = False
    archive_date: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""
    version: int = 1
    device_id: str = ""
    sync_status: str = "local"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}
