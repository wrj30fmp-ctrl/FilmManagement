"""扫描记录数据模型"""

from dataclasses import dataclass


@dataclass
class ScanRecord:
    """扫描记录"""

    film_roll_id: str
    id: str = ""
    user_id: str = "local-user"
    scan_method: str = ""
    scanner: str = ""
    software: str = ""
    scan_date: str = ""
    resolution: str = ""
    file_format: str = ""
    local_path: str = ""
    cloud_url: str = ""
    file_hash: str = ""
    storage_type: str = "local"
    cost: float = 0.0
    currency: str = "CNY"
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""
    version: int = 1
    device_id: str = ""
    sync_status: str = "local"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}
