"""冲洗记录 Repository"""

from app.repositories.base import BaseRepository


class DevelopmentRepository(BaseRepository):
    table_name = "development_records"
    columns = [
        "id", "user_id", "film_roll_id", "development_method",
        "process_type", "lab_name", "sent_date", "completed_date",
        "cost", "currency", "push_pull_stops", "chemistry", "notes",
        "created_at", "updated_at", "deleted_at", "version",
        "device_id", "sync_status",
    ]

    def get_by_roll(self, film_roll_id: str) -> dict | None:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM development_records "
                "WHERE film_roll_id = ? AND deleted_at IS NULL;",
                (film_roll_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
