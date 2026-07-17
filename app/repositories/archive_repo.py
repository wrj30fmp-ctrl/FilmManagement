"""归档记录 Repository"""

from app.repositories.base import BaseRepository


class ArchiveRepository(BaseRepository):
    table_name = "archive_records"
    columns = [
        "id", "user_id", "film_roll_id", "negative_location",
        "binder_number", "page_number", "local_path", "cloud_url",
        "storage_type", "cloud_backup", "offsite_backup",
        "archive_date", "notes",
        "created_at", "updated_at", "deleted_at", "version",
        "device_id", "sync_status",
    ]

    def get_by_roll(self, film_roll_id: str) -> dict | None:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM archive_records "
                "WHERE film_roll_id = ? AND deleted_at IS NULL;",
                (film_roll_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
