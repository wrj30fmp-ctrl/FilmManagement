"""
应用配置管理
负责管理数据目录、数据库路径、备份路径等配置。
程序首次运行时自动在用户文档目录下创建所需目录。
"""

import os
import sys
from pathlib import Path


def get_data_dir() -> Path:
    """获取数据根目录：~/Documents/FilmManager/"""
    if sys.platform == "win32":
        # Windows: C:\Users\用户名\Documents\FilmManager
        documents = Path.home() / "Documents"
    else:
        documents = Path.home()
    data_dir = documents / "FilmManager"
    return data_dir


def get_database_path() -> Path:
    """获取数据库文件完整路径"""
    return get_data_dir() / "film_manager.db"


def get_backup_dir() -> Path:
    """获取备份目录路径"""
    return get_data_dir() / "backups"


def get_export_dir() -> Path:
    """获取导出目录路径"""
    return get_data_dir() / "exports"


def ensure_directories() -> None:
    """确保所有必需目录都存在，不存在则自动创建"""
    dirs_to_create = [
        get_data_dir(),
        get_backup_dir(),
        get_export_dir(),
    ]
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)


# 应用基本信息
APP_NAME = "胶片管理器"
APP_VERSION = "1.0.0"
DB_VERSION = 2  # 数据库 schema 版本号

# 默认设置
DEFAULT_CURRENCY = "CNY"
DEFAULT_BACKUP_COUNT = 20
DEFAULT_AUTO_BACKUP_ON_START = True
DEFAULT_AUTO_BACKUP_ON_EXIT = True

# roll_number 编号规则设置
# 格式: "YYYY-MM" 或 "YYYY-MM-Camera-Model" 形式，流水号自动追加
ROLL_NUMBER_SEPARATOR = "-"
