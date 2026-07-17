"""
胶卷状态历史 Repository
"""

from app.repositories.base import BaseRepository


class StatusHistoryRepository(BaseRepository):
    """状态历史数据访问层"""

    table_name = "film_roll_status_history"
    columns = [
        "id", "user_id", "film_roll_id", "from_status",
        "to_status", "changed_at", "notes",
        "created_at", "updated_at", "deleted_at", "version",
        "device_id", "sync_status",
    ]

    def get_by_roll(self, film_roll_id: str) -> list[dict]:
        """获取指定胶卷的所有状态历史（按时间倒序）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM film_roll_status_history "
                "WHERE film_roll_id = ? AND deleted_at IS NULL "
                "ORDER BY changed_at DESC;",
                (film_roll_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
