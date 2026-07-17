"""冲洗记录数据模型"""

from dataclasses import dataclass


@dataclass
class DevelopmentRecord:
    """冲洗记录"""

    film_roll_id: str
    id: str = ""
    user_id: str = "local-user"
    development_method: str = ""
    process_type: str = ""
    lab_name: str = ""
    sent_date: str = ""
    completed_date: str = ""
    cost: float = 0.0
    currency: str = "CNY"
    push_pull_stops: float = 0.0
    chemistry: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""
    version: int = 1
    device_id: str = ""
    sync_status: str = "local"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}
