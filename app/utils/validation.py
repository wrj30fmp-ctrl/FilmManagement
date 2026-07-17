"""输入验证工具

提供常用的输入验证函数，用于表单输入校验。
所有验证函数返回 (is_valid: bool, error_message: str) 元组。
"""


def validate_required(value: str, field_name: str) -> tuple[bool, str]:
    """验证必填字段不为空"""
    if not value or not str(value).strip():
        return False, f"「{field_name}」为必填项，请填写后重试。"
    return True, ""


def validate_number(value: str, field_name: str) -> tuple[bool, str]:
    """验证输入为合法数字（可为小数）"""
    if not value or not str(value).strip():
        return True, ""  # 非必填字段，空值不报错
    try:
        float(str(value).strip())
        return True, ""
    except ValueError:
        return False, f"「{field_name}」必须为合法数字，例如 39.90。"


def validate_integer(value: str, field_name: str, min_value: int = 0) -> tuple[bool, str]:
    """验证输入为合法整数，且不小于 min_value"""
    if not value or not str(value).strip():
        return True, ""  # 非必填
    try:
        num = int(str(value).strip())
        if num < min_value:
            return False, f"「{field_name}」不能小于 {min_value}。"
        return True, ""
    except ValueError:
        return False, f"「{field_name}」必须为合法整数。"


def validate_positive_integer(value: str, field_name: str) -> tuple[bool, str]:
    """验证输入为正整数（>0）"""
    if not value or not str(value).strip():
        return False, f"「{field_name}」必须填写，请输入大于 0 的整数。"
    return validate_integer(value, field_name, min_value=1)


def validate_non_negative_integer(value: str | int, field_name: str) -> tuple[bool, str]:
    """验证库存数量为大于或等于 0 的整数"""
    try:
        num = int(value)
    except (ValueError, TypeError):
        return False, f"「{field_name}」必须为整数，请输入 0 或正整数。"
    if num < 0:
        return False, f"「{field_name}」不能为负数。"
    return True, ""


def validate_iso(value: str | int, field_name: str) -> tuple[bool, str]:
    """验证 ISO 值为合理的正整数（常见范围 25-25600）"""
    if not value or str(value).strip() == "":
        return True, ""  # 非必填
    try:
        num = int(value)
        if num <= 0:
            return False, f"「{field_name}」必须为正整数。"
        return True, ""
    except (ValueError, TypeError):
        return False, f"「{field_name}」必须为合法的 ISO 数值，例如 400。"
