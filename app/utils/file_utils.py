"""文件操作工具"""

import os
import subprocess
import sys
from pathlib import Path


def open_folder(path: str | Path) -> bool:
    """在资源管理器中打开指定文件夹

    Args:
        path: 文件夹路径

    Returns:
        是否成功打开
    """
    path = Path(path)
    if not path.exists():
        return False
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
        return True
    except Exception:
        return False


def ensure_dir(path: str | Path) -> Path:
    """确保目录存在，不存在则创建

    Returns:
        Path 对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_path_accessible(path: str | Path) -> bool:
    """检查路径是否可访问"""
    return Path(path).exists()
