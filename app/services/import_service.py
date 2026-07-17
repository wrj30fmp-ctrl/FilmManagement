"""
CSV 数据导入服务

支持从 CSV 文件导入库存记录。
- 自动识别列头映射
- 缺失必填字段时报告具体错误
- 导入过程使用事务，失败全部回滚
- 缺少 UUID 时自动生成，缺少 user_id 时设为 local-user
"""

import csv
import logging
from pathlib import Path

from app.database.connection import get_db
from app.utils.uuid_utils import generate_uuid, is_valid_uuid
from app.utils.date_utils import utc_now_iso
from app.constants import TransactionType

logger = logging.getLogger(__name__)

# 库存表必填字段
REQUIRED_FIELDS = ["model", "film_format"]

# 库存表所有合法字段
INVENTORY_FIELDS = [
    "brand", "model", "film_format", "film_type", "box_iso",
    "quantity_cache", "batch_number", "expiry_date", "purchase_date",
    "purchase_source", "unit_price", "currency", "storage_location",
    "storage_method", "notes",
]

# CSV 列名 → 数据库字段名 的常见映射（处理中英文列名）
COLUMN_ALIASES = {
    "品牌": "brand",
    "型号": "model",
    "胶卷型号": "model",
    "画幅": "film_format",
    "色彩类型": "film_type",
    "胶卷类型": "film_type",
    "ISO": "box_iso",
    "标称ISO": "box_iso",
    "标称 ISO": "box_iso",
    "数量": "quantity_cache",
    "库存数量": "quantity_cache",
    "批次": "batch_number",
    "乳剂批次": "batch_number",
    "有效期": "expiry_date",
    "过期日期": "expiry_date",
    "购买日期": "purchase_date",
    "购买渠道": "purchase_source",
    "单价": "unit_price",
    "单卷价格": "unit_price",
    "货币": "currency",
    "存放位置": "storage_location",
    "保存方式": "storage_method",
    "备注": "notes",
}


class ImportResult:
    """导入结果"""

    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.errors: list[str] = []

    @property
    def total(self) -> int:
        return self.success_count + self.error_count

    @property
    def all_success(self) -> bool:
        return self.error_count == 0


def _normalize_header(header: str) -> str:
    """将 CSV 列名映射为数据库字段名"""
    h = header.strip()
    # 先检查别名
    if h in COLUMN_ALIASES:
        return COLUMN_ALIASES[h]
    # 再检查是否是合法字段名本身
    if h in INVENTORY_FIELDS or h in ["id", "user_id", "created_at", "updated_at",
                                        "deleted_at", "version", "device_id", "sync_status"]:
        return h
    # 尝试去掉 BOM 前缀
    if h.startswith("﻿"):
        clean = h[1:]
        if clean in COLUMN_ALIASES:
            return COLUMN_ALIASES[clean]
        if clean in INVENTORY_FIELDS:
            return clean
    return h


def _validate_row(row: dict, row_num: int) -> list[str]:
    """验证一行数据，返回错误列表"""
    errors = []

    # 必填字段检查
    for field in REQUIRED_FIELDS:
        if not row.get(field, "").strip():
            errors.append(f"第 {row_num} 行：缺少必填字段「{field}」")

    # ISO 值检查
    iso_str = row.get("box_iso", "").strip()
    if iso_str:
        try:
            iso_val = int(iso_str)
            if iso_val <= 0:
                errors.append(f"第 {row_num} 行：ISO 值必须为正整数，当前值：{iso_val}")
        except ValueError:
            errors.append(f"第 {row_num} 行：ISO 值格式错误「{iso_str}」，应为整数")

    # 数量检查
    qty_str = row.get("quantity_cache", "").strip()
    if qty_str:
        try:
            qty_val = int(qty_str)
            if qty_val < 0:
                errors.append(f"第 {row_num} 行：库存数量不能为负数，当前值：{qty_val}")
        except ValueError:
            errors.append(f"第 {row_num} 行：库存数量格式错误「{qty_str}」，应为整数")

    # 价格检查
    price_str = row.get("unit_price", "").strip()
    if price_str:
        try:
            float(price_str)
        except ValueError:
            errors.append(f"第 {row_num} 行：价格格式错误「{price_str}」，应为数字")

    return errors


def _clean_value(value: str) -> str:
    """清理 CSV 单元格值"""
    return value.strip() if value else ""


def preview_csv(file_path: str | Path) -> tuple[list[str], list[dict], list[str]]:
    """预览 CSV 文件内容

    Args:
        file_path: CSV 文件路径

    Returns:
        (列名列表, 前5行数据, 警告列表)
    """
    file_path = Path(file_path)
    columns = []
    rows = []
    warnings = []

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                columns = [_normalize_header(h) for h in reader.fieldnames]
                # 检查是否有无法映射的列
                unknown = set(columns) - set(INVENTORY_FIELDS) - {
                    "id", "user_id", "created_at", "updated_at",
                    "deleted_at", "version", "device_id", "sync_status"
                }
                if unknown:
                    warnings.append(f"以下列无法识别，将被忽略：{', '.join(unknown)}")

            for i, row in enumerate(reader):
                if i >= 5:
                    break
                cleaned = {}
                for k, v in row.items():
                    field = _normalize_header(k)
                    cleaned[field] = _clean_value(v)
                rows.append(cleaned)
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(file_path, "r", encoding="gbk") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    columns = [_normalize_header(h) for h in reader.fieldnames]
                for i, row in enumerate(reader):
                    if i >= 5:
                        break
                    cleaned = {}
                    for k, v in row.items():
                        field = _normalize_header(k)
                        cleaned[field] = _clean_value(v)
                    rows.append(cleaned)
        except Exception as e:
            warnings.append(f"读取文件失败：{e}")

    return columns, rows, warnings


def import_inventory_from_csv(file_path: str | Path) -> ImportResult:
    """从 CSV 文件导入库存记录

    导入规则：
    - 使用事务，全部成功或全部失败
    - 缺少 UUID 的自动生成
    - 缺少 user_id 的设为 local-user
    - 缺少 created_at / updated_at 的自动填充
    - 跳过空行
    - 必填字段（model, film_format）缺失时报错

    Args:
        file_path: CSV 文件路径

    Returns:
        ImportResult 包含成功数、失败数和错误详情
    """
    result = ImportResult()
    file_path = Path(file_path)

    if not file_path.exists():
        result.errors.append("文件不存在。")
        return result

    db = get_db()

    # 先读取并验证所有行
    all_rows = []
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                result.errors.append("CSV 文件没有列头行，无法导入。")
                return result

            for i, row in enumerate(reader, start=2):  # 第1行是列头，数据从第2行开始
                cleaned = {}
                for k, v in row.items():
                    field = _normalize_header(k)
                    cleaned[field] = _clean_value(v)

                # 跳过完全空行
                if not any(cleaned.values()):
                    continue

                errors = _validate_row(cleaned, i)
                if errors:
                    result.errors.extend(errors)
                    result.error_count += 1
                else:
                    all_rows.append(cleaned)
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, start=2):
                    cleaned = {}
                    for k, v in row.items():
                        field = _normalize_header(k)
                        cleaned[field] = _clean_value(v)
                    if not any(cleaned.values()):
                        continue
                    errors = _validate_row(cleaned, i)
                    if errors:
                        result.errors.extend(errors)
                        result.error_count += 1
                    else:
                        all_rows.append(cleaned)
        except Exception as e:
            result.errors.append(f"读取文件失败：{e}")
            return result
    except Exception as e:
        result.errors.append(f"读取文件失败：{e}")
        return result

    if not all_rows:
        if result.error_count == 0:
            result.errors.append("文件中没有有效数据。")
        return result

    # 在事务中批量插入
    try:
        with db.transaction() as conn:
            for row in all_rows:
                now = utc_now_iso()
                record_id = row.get("id", "").strip()

                # UUID 校验和生成
                if not record_id or not is_valid_uuid(record_id):
                    record_id = generate_uuid()

                # 筛选 inventory 字段
                insert_data = {"id": record_id}
                for field in INVENTORY_FIELDS:
                    if field in row and row[field]:
                        insert_data[field] = row[field]

                # 填充必填和通用字段
                insert_data["user_id"] = row.get("user_id", "").strip() or "local-user"
                insert_data["created_at"] = row.get("created_at", "").strip() or now
                insert_data["updated_at"] = row.get("updated_at", "").strip() or now
                insert_data["sync_status"] = "local"

                # 数值字段处理
                if "box_iso" in insert_data:
                    try:
                        insert_data["box_iso"] = int(insert_data["box_iso"])
                    except (ValueError, TypeError):
                        insert_data["box_iso"] = 0
                if "quantity_cache" in insert_data:
                    try:
                        insert_data["quantity_cache"] = int(insert_data["quantity_cache"])
                    except (ValueError, TypeError):
                        insert_data["quantity_cache"] = 0
                if "unit_price" in insert_data:
                    try:
                        insert_data["unit_price"] = float(insert_data["unit_price"])
                    except (ValueError, TypeError):
                        insert_data["unit_price"] = 0.0

                # 构建 INSERT
                columns_str = ", ".join(insert_data.keys())
                placeholders = ", ".join(["?"] * len(insert_data))
                values = list(insert_data.values())

                conn.execute(
                    f"INSERT INTO film_inventory ({columns_str}) VALUES ({placeholders});",
                    values,
                )

                # 为有数量的记录创建库存流水
                qty = insert_data.get("quantity_cache", 0)
                if qty > 0:
                    from app.utils.uuid_utils import generate_uuid as gen_id
                    trans_id = gen_id()
                    conn.execute(
                        "INSERT INTO inventory_transactions "
                        "(id, user_id, inventory_id, change_amount, transaction_type, "
                        "reason, created_at, updated_at, sync_status) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                        (trans_id, insert_data["user_id"], record_id, qty,
                         TransactionType.IMPORT, "CSV 导入", now, now, "local"),
                    )

                result.success_count += 1

        logger.info(f"CSV 导入完成：成功 {result.success_count} 条，失败 {result.error_count} 条")
    except Exception as e:
        result.errors.append(f"数据库写入失败，已回滚全部数据：{e}")
        result.success_count = 0
        logger.error(f"CSV 导入失败，已回滚：{e}")

    return result
