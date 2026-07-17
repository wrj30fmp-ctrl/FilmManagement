"""
统计服务

提供首页仪表盘所需的各类聚合统计数据。
所有统计从数据库查询，不依赖界面表格内容。
"""

from app.database.connection import get_db
from app.constants import FilmStatus


class StatisticsService:
    """统计查询服务"""

    def __init__(self):
        self.db = get_db()

    def get_dashboard_stats(self) -> dict:
        """获取首页仪表盘所有统计数据

        Returns:
            包含所有统计指标的字典
        """
        return {
            "inventory_total": self._get_inventory_total(),
            "inventory_135": self._get_inventory_by_format("135"),
            "inventory_120": self._get_inventory_by_format("120"),
            "shooting_count": self._get_roll_count_by_status(FilmStatus.SHOOTING),
            "shot_waiting_dev": self._get_roll_count_by_status(FilmStatus.SHOT),
            "developed_waiting_scan": self._get_roll_count_by_status(FilmStatus.DEVELOPED),
            "scanned_waiting_archive": self._get_roll_count_by_status(FilmStatus.SCANNED),
            "archived_count": self._get_roll_count_by_status(FilmStatus.ARCHIVED),
            "recent_inventory": self._get_recent_inventory(5),
            "recent_rolls": self._get_recent_rolls(5),
            "expiring_inventory": self._get_expiring_inventory(),
            "expired_inventory": self._get_expired_inventory(),
        }

    def _get_inventory_total(self) -> int:
        """未拍胶卷库存总数（按卷数求和）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COALESCE(SUM(quantity_cache), 0) FROM film_inventory "
                "WHERE deleted_at IS NULL;"
            )
            return cursor.fetchone()[0]

    def _get_inventory_by_format(self, film_format: str) -> int:
        """指定画幅的库存卷数"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COALESCE(SUM(quantity_cache), 0) FROM film_inventory "
                "WHERE film_format = ? AND deleted_at IS NULL;",
                (film_format,),
            )
            return cursor.fetchone()[0]

    def _get_roll_count_by_status(self, status: str) -> int:
        """指定状态的拍摄记录数量"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM film_rolls "
                "WHERE status = ? AND deleted_at IS NULL;",
                (status,),
            )
            return cursor.fetchone()[0]

    def _get_recent_inventory(self, limit: int = 5) -> list[dict]:
        """最近添加的库存记录"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT brand, model, film_format, box_iso, quantity_cache, "
                "expiry_date, created_at "
                "FROM film_inventory WHERE deleted_at IS NULL "
                "ORDER BY created_at DESC LIMIT ?;",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _get_recent_rolls(self, limit: int = 5) -> list[dict]:
        """最近完成拍摄的胶卷"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT roll_number, brand, model, film_format, camera, "
                "status, finish_date "
                "FROM film_rolls WHERE deleted_at IS NULL "
                "ORDER BY updated_at DESC LIMIT ?;",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _get_expiring_inventory(self) -> list[dict]:
        """即将过期的库存（90天内）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT brand, model, film_format, quantity_cache, expiry_date "
                "FROM film_inventory "
                "WHERE deleted_at IS NULL AND expiry_date IS NOT NULL "
                "AND quantity_cache > 0 "
                "AND expiry_date >= date('now', 'localtime') "
                "AND expiry_date <= date('now', 'localtime', '+90 days') "
                "ORDER BY expiry_date;"
            )
            return [dict(row) for row in cursor.fetchall()]

    def _get_expired_inventory(self) -> list[dict]:
        """已过期的库存"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT brand, model, film_format, quantity_cache, expiry_date "
                "FROM film_inventory "
                "WHERE deleted_at IS NULL AND expiry_date IS NOT NULL "
                "AND quantity_cache > 0 "
                "AND expiry_date < date('now', 'localtime') "
                "ORDER BY expiry_date;"
            )
            return [dict(row) for row in cursor.fetchall()]

    # ================================================================
    # 统计页面用
    # ================================================================

    def get_roll_count_by_format(self) -> list[tuple[str, int]]:
        """各画幅拍摄数量"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT film_format, COUNT(*) FROM film_rolls "
                "WHERE deleted_at IS NULL GROUP BY film_format;"
            )
            return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_roll_count_by_month(self, months: int = 12) -> list[tuple[str, int]]:
        """每月拍摄数量（最近N个月）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT substr(load_date, 1, 7) AS month, COUNT(*) "
                "FROM film_rolls WHERE deleted_at IS NULL "
                "AND load_date IS NOT NULL "
                "GROUP BY month ORDER BY month DESC LIMIT ?;",
                (months,),
            )
            return [(row[0], row[1]) for row in cursor.fetchall()][::-1]

    def get_camera_usage(self) -> list[tuple[str, int]]:
        """各相机使用次数"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT camera, COUNT(*) FROM film_rolls "
                "WHERE deleted_at IS NULL AND camera IS NOT NULL AND camera != '' "
                "GROUP BY camera ORDER BY COUNT(*) DESC;"
            )
            return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_total_cost(self) -> dict:
        """获取总成本统计"""
        with self.db.get_connection() as conn:
            # 库存购买总成本
            cursor = conn.execute(
                "SELECT COALESCE(SUM(unit_price * quantity_cache), 0) FROM film_inventory "
                "WHERE deleted_at IS NULL;"
            )
            inventory_cost = cursor.fetchone()[0]

            # 冲洗总成本
            cursor = conn.execute(
                "SELECT COALESCE(SUM(cost), 0) FROM development_records "
                "WHERE deleted_at IS NULL;"
            )
            dev_cost = cursor.fetchone()[0]

            # 扫描总成本
            cursor = conn.execute(
                "SELECT COALESCE(SUM(cost), 0) FROM scan_records "
                "WHERE deleted_at IS NULL;"
            )
            scan_cost = cursor.fetchone()[0]

        total_cost = inventory_cost + dev_cost + scan_cost

        # 总拍摄卷数
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM film_rolls WHERE deleted_at IS NULL;"
            )
            total_rolls = cursor.fetchone()[0]

        avg_cost = total_cost / total_rolls if total_rolls > 0 else 0

        return {
            "inventory_cost": inventory_cost,
            "development_cost": dev_cost,
            "scan_cost": scan_cost,
            "total_cost": total_cost,
            "total_rolls": total_rolls,
            "average_cost_per_roll": avg_cost,
        }

    def get_inventory_summary(self) -> list[dict]:
        """各胶卷型号库存数量"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT brand, model, film_format, film_type, "
                "SUM(quantity_cache) AS total_qty "
                "FROM film_inventory WHERE deleted_at IS NULL "
                "GROUP BY brand, model, film_format "
                "ORDER BY total_qty DESC;"
            )
            return [dict(row) for row in cursor.fetchall()]

    # ================================================================
    # 第三阶段：成本分析 + 消耗预测 + 过期推荐
    # ================================================================

    def get_cost_by_format(self) -> list[tuple[str, float]]:
        """各画幅的拍摄 + 冲扫总成本"""
        with self.db.get_connection() as conn:
            results = []
            for fmt in ["135", "120"]:
                # 库存成本（按拍摄卷数估算）
                cursor = conn.execute(
                    "SELECT COALESCE(SUM(fi.unit_price), 0) FROM film_rolls fr "
                    "LEFT JOIN film_inventory fi ON fr.inventory_id = fi.id "
                    "WHERE fr.film_format = ? AND fr.deleted_at IS NULL;",
                    (fmt,),
                )
                film_cost = cursor.fetchone()[0]
                # 冲洗成本
                cursor = conn.execute(
                    "SELECT COALESCE(SUM(dr.cost), 0) FROM development_records dr "
                    "JOIN film_rolls fr ON dr.film_roll_id = fr.id "
                    "WHERE fr.film_format = ? AND dr.deleted_at IS NULL;",
                    (fmt,),
                )
                dev_cost = cursor.fetchone()[0]
                # 扫描成本
                cursor = conn.execute(
                    "SELECT COALESCE(SUM(sr.cost), 0) FROM scan_records sr "
                    "JOIN film_rolls fr ON sr.film_roll_id = fr.id "
                    "WHERE fr.film_format = ? AND sr.deleted_at IS NULL;",
                    (fmt,),
                )
                scan_cost = cursor.fetchone()[0]
                results.append((fmt, film_cost + dev_cost + scan_cost))
            return results

    def get_cost_by_month(self, months: int = 12) -> list[tuple[str, float]]:
        """每月总花费趋势（胶卷 + 冲洗 + 扫描）"""
        with self.db.get_connection() as conn:
            # 按月统计拍摄胶卷数量，估算月度消费
            cursor = conn.execute(
                "SELECT substr(fr.load_date, 1, 7) AS month, COUNT(*) AS cnt "
                "FROM film_rolls fr WHERE fr.deleted_at IS NULL "
                "AND fr.load_date IS NOT NULL "
                "GROUP BY month ORDER BY month DESC LIMIT ?;",
                (months,),
            )
            monthly_rolls = [(row[0], row[1]) for row in cursor.fetchall()]

        # 计算每卷平均成本
        total_cost = self.get_total_cost()
        avg_per_roll = total_cost["average_cost_per_roll"]

        return [(m, cnt * avg_per_roll) for m, cnt in reversed(monthly_rolls)]

    def get_usage_rate(self) -> dict:
        """拍摄频率统计和库存消耗预测"""
        with self.db.get_connection() as conn:
            # 总拍摄卷数和时间跨度
            cursor = conn.execute(
                "SELECT COUNT(*), MIN(load_date), MAX(load_date) "
                "FROM film_rolls WHERE deleted_at IS NULL AND load_date IS NOT NULL;"
            )
            row = cursor.fetchone()
            total_rolls = row[0] or 0
            first_date = row[1] or ""
            last_date = row[2] or ""

            # 当前库存总量
            cursor = conn.execute(
                "SELECT COALESCE(SUM(quantity_cache), 0) FROM film_inventory "
                "WHERE deleted_at IS NULL;"
            )
            total_inventory = cursor.fetchone()[0]

        # 计算月均拍摄量
        months = 1
        if first_date and last_date and first_date != last_date:
            from datetime import datetime
            try:
                first = datetime.strptime(first_date[:10], "%Y-%m-%d")
                last = datetime.strptime(last_date[:10], "%Y-%m-%d")
                months = max(1, (last - first).days / 30.44)
            except ValueError:
                pass

        rolls_per_month = total_rolls / months if months > 0 else 0
        months_remaining = total_inventory / rolls_per_month if rolls_per_month > 0 else 99

        return {
            "total_rolls": total_rolls,
            "months_tracked": round(months, 1),
            "rolls_per_month": round(rolls_per_month, 1),
            "total_inventory": total_inventory,
            "months_remaining": round(months_remaining, 1),
        }

    def get_recommended_films(self) -> list[dict]:
        """按有效期推荐优先使用的胶卷（快过期的排前面）"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT brand, model, film_format, box_iso, quantity_cache, "
                "expiry_date, storage_method "
                "FROM film_inventory WHERE deleted_at IS NULL "
                "AND quantity_cache > 0 AND expiry_date IS NOT NULL "
                "ORDER BY expiry_date ASC LIMIT 15;"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_cost_by_category(self) -> list[tuple[str, float]]:
        """总成本分类：胶卷购买 vs 冲洗 vs 扫描"""
        cost = self.get_total_cost()
        return [
            ("胶卷购买", cost["inventory_cost"]),
            ("冲洗费用", cost["development_cost"]),
            ("扫描费用", cost["scan_cost"]),
        ]
