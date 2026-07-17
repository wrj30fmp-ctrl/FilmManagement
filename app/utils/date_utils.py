"""日期时间工具

所有数据库时间字段统一使用 ISO 8601 格式（UTC）。
界面显示时转换为用户本地时间。
单纯日期字段使用 YYYY-MM-DD 格式。
"""

from datetime import datetime, date, timezone, timedelta


# 中国时区（UTC+8）
CHINA_TZ = timezone(timedelta(hours=8))


def utc_now_iso() -> str:
    """获取当前 UTC 时间的 ISO 8601 格式字符串，例如 2026-07-17T06:30:00Z"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_datetime() -> datetime:
    """获取当前 UTC 时间的 datetime 对象"""
    return datetime.now(timezone.utc)


def today_date_str() -> str:
    """获取今天的日期字符串 YYYY-MM-DD（本地日期）"""
    return datetime.now(CHINA_TZ).strftime("%Y-%m-%d")


def format_iso_to_local(iso_string: str) -> str:
    """将 ISO 8601 UTC 时间字符串转换为本地时间显示

    Args:
        iso_string: 如 "2026-07-17T06:30:00Z"

    Returns:
        如 "2026-07-17 14:30:00"
    """
    if not iso_string:
        return ""
    try:
        # 解析 ISO 8601 格式
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        # 转换为中国时区
        local_dt = dt.astimezone(CHINA_TZ)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_string


def format_iso_to_date(iso_string: str) -> str:
    """将 ISO 8601 UTC 时间字符串转换为本地日期显示

    Args:
        iso_string: 如 "2026-07-17T06:30:00Z"

    Returns:
        如 "2026-07-17"
    """
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        local_dt = dt.astimezone(CHINA_TZ)
        return local_dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return iso_string


def parse_date_string(date_str: str) -> str | None:
    """解析用户输入的日期字符串，返回标准 YYYY-MM-DD 格式

    支持格式：YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
    如果输入为空或无效，返回 None
    """
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip()
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def days_until_expiry(expiry_date_str: str) -> int | None:
    """计算距离有效期还有多少天

    Args:
        expiry_date_str: YYYY-MM-DD 格式的有效期

    Returns:
        剩余天数（正数表示未过期，负数表示已过期），如果日期无效返回 None
    """
    if not expiry_date_str:
        return None
    try:
        expiry = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        today = datetime.now(CHINA_TZ).date()
        delta = (expiry - today).days
        return delta
    except (ValueError, TypeError):
        return None
