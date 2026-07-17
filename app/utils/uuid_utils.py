"""UUID 生成工具"""

import uuid


def generate_uuid() -> str:
    """生成 UUID v4 字符串，用作数据库主键"""
    return str(uuid.uuid4())


def is_valid_uuid(value: str) -> bool:
    """检查字符串是否为有效 UUID 格式"""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
