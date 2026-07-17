"""
拍摄记录 Repository

提供 film_rolls 表和 film_roll_status_history 表的数据访问。
"""

from app.repositories.base import BaseRepository


class FilmRollRepository(BaseRepository):
    """拍摄记录数据访问层"""

    table_name = "film_rolls"
    columns = [
        "id", "user_id", "roll_number", "inventory_id",
        "brand", "model", "film_format", "film_type",
        "box_iso", "exposure_iso", "camera", "lens",
        "load_date", "finish_date", "location", "subject",
        "status", "push_pull", "photo_path", "notes",
        "created_at", "updated_at", "deleted_at", "version",
        "device_id", "sync_status",
    ]

    def list_with_filters(
        self,
        status: str = "",
        film_format: str = "",
        brand: str = "",
        camera: str = "",
        year: str = "",
        keyword: str = "",
        order_by: str = "created_at",
        order_desc: bool = True,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict]:
        """带筛选条件的拍摄记录列表"""
        conditions = ["deleted_at IS NULL"]
        params: list = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if film_format:
            conditions.append("film_format = ?")
            params.append(film_format)

        if brand:
            conditions.append("brand LIKE ?")
            params.append(f"%{brand}%")

        if camera:
            conditions.append("camera LIKE ?")
            params.append(f"%{camera}%")

        if year:
            conditions.append("load_date LIKE ? OR finish_date LIKE ?")
            params.extend([f"{year}%", f"{year}%"])

        if keyword:
            conditions.append(
                "(roll_number LIKE ? OR brand LIKE ? OR model LIKE ? "
                "OR camera LIKE ? OR lens LIKE ? OR location LIKE ? OR notes LIKE ?)"
            )
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw, kw, kw, kw, kw])

        where_clause = " AND ".join(conditions)
        order_dir = "DESC" if order_desc else "ASC"
        sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY {order_by} {order_dir}"

        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def count_with_filters(
        self,
        status: str = "",
        film_format: str = "",
        keyword: str = "",
    ) -> int:
        """获取筛选条件下的记录总数"""
        conditions = ["deleted_at IS NULL"]
        params: list = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if film_format:
            conditions.append("film_format = ?")
            params.append(film_format)
        if keyword:
            conditions.append(
                "(roll_number LIKE ? OR brand LIKE ? OR model LIKE ? "
                "OR camera LIKE ? OR lens LIKE ? OR location LIKE ? OR notes LIKE ?)"
            )
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw, kw, kw, kw, kw])

        where_clause = " AND ".join(conditions)
        sql = f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()[0]

    def get_by_roll_number(self, roll_number: str) -> dict | None:
        """根据胶卷编号获取记录"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM film_rolls WHERE roll_number = ? AND deleted_at IS NULL;",
                (roll_number,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def is_roll_number_taken(self, roll_number: str, exclude_id: str = "") -> bool:
        """检查胶卷编号是否已被占用

        Args:
            roll_number: 要检查的编号
            exclude_id: 排除的记录 UUID（编辑时排除自身）

        Returns:
            True 表示已被占用
        """
        with self.db.get_connection() as conn:
            if exclude_id:
                cursor = conn.execute(
                    "SELECT 1 FROM film_rolls WHERE roll_number = ? "
                    "AND id != ? AND deleted_at IS NULL;",
                    (roll_number, exclude_id),
                )
            else:
                cursor = conn.execute(
                    "SELECT 1 FROM film_rolls WHERE roll_number = ? AND deleted_at IS NULL;",
                    (roll_number,),
                )
            return cursor.fetchone() is not None

    def update_status(self, roll_id: str, new_status: str) -> bool:
        """更新胶卷状态"""
        from app.utils.date_utils import utc_now_iso
        now = utc_now_iso()
        with self.db.get_connection() as conn:
            try:
                cursor = conn.execute(
                    "UPDATE film_rolls SET status = ?, updated_at = ?, "
                    "version = version + 1 WHERE id = ? AND deleted_at IS NULL;",
                    (new_status, now, roll_id),
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception:
                conn.rollback()
                raise

    def get_cameras(self) -> list[str]:
        """获取所有不重复的相机列表"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT camera FROM film_rolls "
                "WHERE deleted_at IS NULL AND camera IS NOT NULL AND camera != '' "
                "ORDER BY camera;"
            )
            return [row[0] for row in cursor.fetchall()]
