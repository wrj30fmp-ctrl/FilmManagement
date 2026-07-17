"""
SQLite 数据库连接管理

提供线程安全的数据库连接获取和上下文管理器。
使用 WAL 模式提升并发性能，启用外键约束。
"""

import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager


class DatabaseConnection:
    """SQLite 数据库连接管理器

    使用线程本地存储（threading.local）确保每个线程有独立的连接。
    启用 WAL 模式以支持更好的并发读取。
    """

    def __init__(self, db_path: str | Path):
        """
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._local = threading.local()

    def _get_conn(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接，若不存在则创建"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._create_connection()
        return self._local.conn

    def _create_connection(self) -> sqlite3.Connection:
        """创建新的数据库连接并配置"""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        # 启用 WAL 模式：允许同时读写，提升并发性能
        conn.execute("PRAGMA journal_mode=WAL;")
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys=ON;")
        # 使用 str 作为默认的 row_factory，方便后续转换
        conn.row_factory = sqlite3.Row
        return conn

    def close(self) -> None:
        """关闭当前线程的数据库连接"""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    def close_all(self) -> None:
        """关闭所有连接（程序退出时调用）"""
        self.close()

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器

        使用方式：
            with db.get_connection() as conn:
                cursor = conn.execute("SELECT ...")
        """
        conn = self._get_conn()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise

    @contextmanager
    def transaction(self):
        """数据库事务上下文管理器

        自动提交或回滚事务。使用方式：
            with db.transaction() as conn:
                conn.execute("INSERT ...")
                conn.execute("UPDATE ...")
                # 自动提交；若发生异常则自动回滚
        """
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def commit(self) -> None:
        """手动提交当前事务"""
        conn = self._get_conn()
        conn.commit()

    def rollback(self) -> None:
        """手动回滚当前事务"""
        conn = self._get_conn()
        conn.rollback()


# 全局数据库连接实例（由 main.py 初始化）
_db_instance: DatabaseConnection | None = None


def get_db() -> DatabaseConnection:
    """获取全局数据库连接实例"""
    global _db_instance
    if _db_instance is None:
        raise RuntimeError("数据库尚未初始化，请先调用 initialize_database()。")
    return _db_instance


def initialize_database(db_path: str | Path) -> DatabaseConnection:
    """初始化全局数据库连接

    Args:
        db_path: 数据库文件路径

    Returns:
        DatabaseConnection 实例
    """
    global _db_instance
    _db_instance = DatabaseConnection(db_path)
    return _db_instance
