"""归档记录业务服务"""

import logging
from app.repositories.archive_repo import ArchiveRepository
from app.utils.date_utils import today_date_str

logger = logging.getLogger(__name__)


class ArchiveService:
    """归档记录业务服务"""

    def __init__(self):
        self.repo = ArchiveRepository()

    def get_by_roll(self, film_roll_id: str) -> dict | None:
        """根据拍摄记录获取归档信息"""
        return self.repo.get_by_roll(film_roll_id)

    def list_all(self) -> list[dict]:
        """获取所有归档记录"""
        return self.repo.list_all()

    def save(self, film_roll_id: str, data: dict) -> str:
        """创建或更新归档记录"""
        existing = self.repo.get_by_roll(film_roll_id)
        if existing:
            self.repo.update(existing["id"], data)
            return existing["id"]
        else:
            data["film_roll_id"] = film_roll_id
            if not data.get("archive_date"):
                data["archive_date"] = today_date_str()
            # 布尔值转为整数
            data["cloud_backup"] = 1 if data.get("cloud_backup") else 0
            data["offsite_backup"] = 1 if data.get("offsite_backup") else 0
            return self.repo.create(data)

    def delete(self, record_id: str) -> bool:
        """软删除归档记录"""
        return self.repo.soft_delete(record_id)
