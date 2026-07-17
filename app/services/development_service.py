"""冲洗记录业务服务"""

import logging
from app.repositories.development_repo import DevelopmentRepository
from app.utils.date_utils import today_date_str

logger = logging.getLogger(__name__)


class DevelopmentService:
    """冲洗记录业务服务"""

    def __init__(self):
        self.repo = DevelopmentRepository()

    def get_by_roll(self, film_roll_id: str) -> dict | None:
        """根据拍摄记录获取冲洗信息"""
        return self.repo.get_by_roll(film_roll_id)

    def list_all(self) -> list[dict]:
        """获取所有冲洗记录"""
        return self.repo.list_all()

    def save(self, film_roll_id: str, data: dict) -> str:
        """创建或更新冲洗记录

        如果该胶卷已有冲洗记录则更新，否则创建新记录。

        Args:
            film_roll_id: 拍摄记录 UUID
            data: 冲洗数据

        Returns:
            记录 UUID
        """
        existing = self.repo.get_by_roll(film_roll_id)
        if existing:
            self.repo.update(existing["id"], data)
            return existing["id"]
        else:
            data["film_roll_id"] = film_roll_id
            if not data.get("completed_date"):
                data["completed_date"] = today_date_str()
            return self.repo.create(data)

    def delete(self, record_id: str) -> bool:
        """软删除冲洗记录"""
        return self.repo.soft_delete(record_id)
