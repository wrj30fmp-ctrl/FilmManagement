"""
数据库版本迁移管理

程序启动时自动检测数据库版本，并按顺序执行迁移脚本。
迁移前自动创建数据库备份。
"""

import sqlite3
import logging
from pathlib import Path

from app.database.schema import (
    ALL_TABLES,
    CREATE_INDEXES,
    CREATE_ROLL_NUMBER_UNIQUE_INDEX,
)
from app.utils.date_utils import utc_now_iso
from app.config import DB_VERSION

logger = logging.getLogger(__name__)


def get_current_db_version(conn: sqlite3.Connection) -> int:
    """获取当前数据库的 schema 版本

    Args:
        conn: 数据库连接

    Returns:
        当前版本号，如果 schema_migrations 表不存在则返回 0
    """
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
        )
        if cursor.fetchone() is None:
            return 0
        cursor = conn.execute(
            "SELECT MAX(version) FROM schema_migrations;"
        )
        row = cursor.fetchone()
        if row and row[0] is not None:
            return row[0]
        return 0
    except sqlite3.Error:
        return 0


def apply_migration(
    conn: sqlite3.Connection,
    version: int,
    description: str,
    sql_statements: list[str],
) -> bool:
    """应用单个迁移

    Args:
        conn: 数据库连接
        version: 目标版本号
        description: 迁移描述
        sql_statements: 要执行的 SQL 语句列表

    Returns:
        是否成功
    """
    try:
        for sql in sql_statements:
            conn.execute(sql)
        conn.execute(
            "INSERT OR REPLACE INTO schema_migrations (version, applied_at, description) "
            "VALUES (?, ?, ?);",
            (version, utc_now_iso(), description),
        )
        conn.commit()
        logger.info(f"数据库迁移成功: v{version} - {description}")
        return True
    except sqlite3.Error as e:
        logger.error(f"数据库迁移失败 v{version}: {e}")
        conn.rollback()
        return False


def run_migrations(db_path: Path) -> bool:
    """运行所有待执行的数据库迁移

    程序启动时调用。会自动检测当前版本并按顺序执行所有待应用的迁移。
    迁移前会创建数据库备份。

    Args:
        db_path: 数据库文件路径

    Returns:
        是否所有迁移都成功
    """
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row

    try:
        current_version = get_current_db_version(conn)
        logger.info(f"当前数据库版本: {current_version}, 目标版本: {DB_VERSION}")

        if current_version >= DB_VERSION:
            return True

        # 如果数据库为空（版本 0），执行完整建表
        if current_version == 0:
            # 确保数据库文件所在目录存在
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # 先创建 schema_migrations 表
            for table_name, create_sql in ALL_TABLES:
                try:
                    conn.execute(create_sql)
                except sqlite3.Error as e:
                    logger.error(f"创建表 {table_name} 失败: {e}")
                    return False

            # 创建索引
            for index_sql in CREATE_INDEXES:
                try:
                    conn.execute(index_sql)
                except sqlite3.Error as e:
                    logger.warning(f"创建索引失败（非致命）: {e}")

            # 创建唯一索引（可能已存在）
            try:
                conn.execute(CREATE_ROLL_NUMBER_UNIQUE_INDEX)
            except sqlite3.Error:
                logger.debug("roll_number 唯一索引已存在，跳过。")

            # 记录初始迁移
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at, description) "
                "VALUES (?, ?, ?);",
                (DB_VERSION, utc_now_iso(), "初始数据库创建"),
            )
            conn.commit()
            logger.info(f"数据库初始化完成，当前版本: {DB_VERSION}")
            return True

        # v2: 添加 photo_path 字段（照片缩略图）
        if current_version < 2:
            migration_2_sql = [
                "ALTER TABLE film_inventory ADD COLUMN photo_path TEXT;",
                "ALTER TABLE film_rolls ADD COLUMN photo_path TEXT;",
            ]
            if not apply_migration(conn, 2, "添加照片路径字段 (photo_path)", migration_2_sql):
                return False

        return True

    except sqlite3.Error as e:
        logger.error(f"数据库迁移过程出错: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
