"""扫描记录业务服务"""

import logging
from app.repositories.scan_repo import ScanRepository
from app.utils.date_utils import today_date_str

logger = logging.getLogger(__name__)


class ScanService:
    """扫描记录业务服务"""

    def __init__(self):
        self.repo = ScanRepository()

    def get_by_roll(self, film_roll_id: str) -> dict | None:
        """根据拍摄记录获取扫描信息"""
        return self.repo.get_by_roll(film_roll_id)

    def list_all(self) -> list[dict]:
        """获取所有扫描记录"""
        return self.repo.list_all()

    def save(self, film_roll_id: str, data: dict) -> str:
        """创建或更新扫描记录"""
        existing = self.repo.get_by_roll(film_roll_id)
        if existing:
            self.repo.update(existing["id"], data)
            return existing["id"]
        else:
            data["film_roll_id"] = film_roll_id
            if not data.get("scan_date"):
                data["scan_date"] = today_date_str()
            return self.repo.create(data)

    def delete(self, record_id: str) -> bool:
        """软删除扫描记录"""
        return self.repo.soft_delete(record_id)
