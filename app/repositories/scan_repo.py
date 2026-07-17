"""扫描记录 Repository"""

from app.repositories.base import BaseRepository


class ScanRepository(BaseRepository):
    table_name = "scan_records"
    columns = [
        "id", "user_id", "film_roll_id", "scan_method", "scanner",
        "software", "scan_date", "resolution", "file_format",
        "local_path", "cloud_url", "file_hash", "storage_type",
        "cost", "currency", "notes",
        "created_at", "updated_at", "deleted_at", "version",
        "device_id", "sync_status",
    ]

    def get_by_roll(self, film_roll_id: str) -> dict | None:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM scan_records "
                "WHERE film_roll_id = ? AND deleted_at IS NULL;",
                (film_roll_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
