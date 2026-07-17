"""
数据库备份与恢复服务

支持手动备份、启动时自动备份、退出时自动备份。
备份文件以日期时间命名，支持自动清理旧备份。
恢复前自动备份当前数据库。
"""

import shutil
import logging
from datetime import datetime
from pathlib import Path

from app.config import get_database_path, get_backup_dir
from app.utils.date_utils import CHINA_TZ

logger = logging.getLogger(__name__)


class BackupService:
    """数据库备份与恢复服务"""

    def __init__(self, max_backups: int = 20):
        """
        Args:
            max_backups: 保留的最大备份数量
        """
        self.max_backups = max_backups
        self.db_path = get_database_path()
        self.backup_dir = get_backup_dir()

    def create_backup(self) -> Path | None:
        """创建数据库备份

        复制完整的 SQLite 数据库文件到备份目录。
        备份文件命名格式：film_manager_2026-07-17_143025.db

        Returns:
            备份文件路径，失败返回 None
        """
        if not self.db_path.exists():
            logger.warning("数据库文件不存在，跳过备份。")
            return None

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(CHINA_TZ).strftime("%Y-%m-%d_%H%M%S")
        backup_name = f"film_manager_{timestamp}.db"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"数据库备份完成: {backup_path}")
            self._cleanup_old_backups()
            return backup_path
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return None

    def restore_backup(self, backup_path: str | Path) -> bool:
        """从备份文件恢复数据库

        恢复前自动备份当前数据库（即使当前数据库可能有问题），
        然后使用指定的备份文件覆盖当前数据库。

        Args:
            backup_path: 备份文件路径

        Returns:
            是否恢复成功
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            logger.error(f"备份文件不存在: {backup_path}")
            return False

        try:
            # 恢复前先备份当前数据库
            if self.db_path.exists():
                self.create_backup()

            # 复制备份文件到数据库位置
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"数据库已从备份恢复: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            return False

    def list_backups(self) -> list[Path]:
        """列出所有备份文件（按时间降序）"""
        if not self.backup_dir.exists():
            return []
        backups = sorted(
            self.backup_dir.glob("film_manager_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return backups

    def get_last_backup_time(self) -> str | None:
        """获取最近一次备份的时间"""
        backups = self.list_backups()
        if not backups:
            return None
        # 从文件名中提取时间
        name = backups[0].stem  # film_manager_2026-07-17_143025
        try:
            parts = name.split("_", 2)  # ["film", "manager", "2026-07-17_143025"]
            time_str = parts[2] if len(parts) > 2 else ""
            dt = datetime.strptime(time_str, "%Y-%m-%d_%H%M%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, IndexError):
            return str(backups[0].stat().st_mtime)

    def _cleanup_old_backups(self) -> None:
        """自动删除超过保留数量的最旧备份"""
        backups = self.list_backups()
        if len(backups) > self.max_backups:
            for old_backup in backups[self.max_backups:]:
                try:
                    old_backup.unlink()
                    logger.info(f"已删除旧备份: {old_backup}")
                except Exception as e:
                    logger.warning(f"删除旧备份失败: {e}")

    def delete_backup(self, backup_path: str | Path) -> bool:
        """删除指定备份文件"""
        try:
            Path(backup_path).unlink()
            return True
        except Exception:
            return False
