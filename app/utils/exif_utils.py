"""
EXIF 信息读取工具

从 JPEG/TIFF 等文件中提取拍摄参数：
- 相机型号、镜头型号
- 拍摄日期、ISO、光圈、快门速度
- 焦距
"""

from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, IFD
import logging

logger = logging.getLogger(__name__)

# 常见 EXIF 标签 → 字段名映射
EXIF_FIELD_MAP = {
    "Make": "camera_make",
    "Model": "camera_model",
    "LensModel": "lens_model",
    "DateTimeOriginal": "date_taken",
    "ISOSpeedRatings": "iso",
    "FNumber": "aperture",
    "ExposureTime": "shutter_speed",
    "FocalLength": "focal_length",
    "ExposureBiasValue": "exposure_bias",
}

# 需要格式化的字段
APERTURE_VALUES = {
    1.0: "f/1.0", 1.4: "f/1.4", 2.0: "f/2.0", 2.8: "f/2.8",
    4.0: "f/4.0", 5.6: "f/5.6", 8.0: "f/8.0", 11.0: "f/11",
    16.0: "f/16", 22.0: "f/22",
}


def _get_decimal_from_rational(rational) -> float:
    """将 IFDRational 转为浮点数"""
    try:
        return float(rational)
    except (TypeError, ValueError):
        return 0.0


def _format_exif_value(tag_name: str, value) -> str:
    """格式化 EXIF 值为可读字符串"""
    if value is None:
        return ""

    if tag_name == "FNumber":
        num = _get_decimal_from_rational(value)
        if num > 0:
            return f"f/{num:.1f}".rstrip("0").rstrip(".")
        return ""

    if tag_name == "ExposureTime":
        num = _get_decimal_from_rational(value)
        if num >= 1:
            return f"{num:.0f}s"
        else:
            denom = round(1 / num) if num > 0 else 0
            return f"1/{denom}s" if denom > 0 else ""

    if tag_name == "ISOSpeedRatings":
        try:
            return str(int(value))
        except (ValueError, TypeError):
            # ISO 可能是元组
            if isinstance(value, tuple):
                return str(value[0])
            return str(value)

    if tag_name == "FocalLength":
        num = _get_decimal_from_rational(value)
        return f"{num:.0f}mm" if num > 0 else ""

    if tag_name == "ExposureBiasValue":
        num = _get_decimal_from_rational(value)
        if num >= 0:
            return f"+{num:.1f} EV"
        else:
            return f"{num:.1f} EV"

    return str(value).strip()


def read_exif(file_path: str | Path) -> dict:
    """从图片文件读取 EXIF 信息

    Args:
        file_path: 图片文件路径

    Returns:
        包含拍摄参数的字典：
        {
            "camera": "相机品牌 + 型号",
            "lens": "镜头型号",
            "date_taken": "拍摄日期 YYYY-MM-DD",
            "exposure_iso": ISO 数值 int,
            "aperture": "光圈值如 f/2.8",
            "shutter_speed": "快门速度如 1/125s",
            "focal_length": "焦距如 50mm",
            "exif_raw": {原始 EXIF 标签字典}
        }
        如果读取失败或没有 EXIF 数据，返回空 dict
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return {}

    # 检查扩展名
    ext = file_path.suffix.lower()
    if ext not in (".jpg", ".jpeg", ".tiff", ".tif", ".dng", ".png"):
        logger.debug(f"不支持的文件格式: {ext}")
        return {}

    try:
        img = Image.open(file_path)
        exif_data = img._getexif()
        if not exif_data:
            logger.debug(f"图片无 EXIF 数据: {file_path}")
            return {}

        # 将数字标签转为可读标签名
        exif_tags = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, str(tag_id))
            exif_tags[tag_name] = value

        # 提取有用字段
        result = {"exif_raw": {}}

        make = str(exif_tags.get("Make", "")).strip()
        model = str(exif_tags.get("Model", "")).strip()

        # 组合相机名称
        if make and model:
            if model.startswith(make):
                result["camera"] = model
            else:
                result["camera"] = f"{make} {model}"
        elif model:
            result["camera"] = model
        elif make:
            result["camera"] = make

        # 镜头
        lens = str(exif_tags.get("LensModel", "")).strip()
        if lens:
            result["lens"] = lens

        # 拍摄日期
        date_str = str(exif_tags.get("DateTimeOriginal", "")).strip()
        if date_str:
            # EXIF 日期格式: "2026:07:15 14:30:00"
            try:
                dt = date_str.replace(":", "-", 2).split(" ")[0]
                result["date_taken"] = dt
            except Exception:
                result["date_taken"] = date_str

        # ISO
        iso_val = exif_tags.get("ISOSpeedRatings")
        if iso_val is not None:
            try:
                result["exposure_iso"] = int(iso_val)
            except (ValueError, TypeError):
                if isinstance(iso_val, tuple):
                    result["exposure_iso"] = int(iso_val[0])

        # 光圈
        aperture = exif_tags.get("FNumber")
        if aperture is not None:
            f_val = _get_decimal_from_rational(aperture)
            if f_val > 0:
                result["aperture"] = f"f/{f_val:.1f}".rstrip("0").rstrip(".")

        # 快门
        shutter = exif_tags.get("ExposureTime")
        if shutter is not None:
            result["shutter_speed"] = _format_exif_value("ExposureTime", shutter)

        # 焦距
        focal = exif_tags.get("FocalLength")
        if focal is not None:
            f = _get_decimal_from_rational(focal)
            if f > 0:
                result["focal_length"] = f"{f:.0f}mm"

        # 保存原始数据用于调试
        for k, v in exif_tags.items():
            try:
                result["exif_raw"][k] = str(v)
            except Exception:
                pass

        img.close()
        return result

    except Exception as e:
        logger.warning(f"读取 EXIF 失败 ({file_path}): {e}")
        return {}
