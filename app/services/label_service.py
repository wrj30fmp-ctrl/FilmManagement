"""
胶卷标签生成服务

生成可打印的胶卷标签（HTML 格式），包含：
- 品牌、型号、画幅、ISO
- 有效期、存放位置
- 可选：胶卷编号、底片册位置
"""

import logging
from pathlib import Path
from datetime import datetime

from app.database.connection import get_db
from app.config import get_export_dir
from app.utils.date_utils import CHINA_TZ, days_until_expiry

logger = logging.getLogger(__name__)


def _escape_html(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_inventory_label(inventory_id: str) -> Path | None:
    """为指定库存记录生成标签 HTML 文件

    Args:
        inventory_id: 库存记录 UUID

    Returns:
        生成的 HTML 文件路径
    """
    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM film_inventory WHERE id = ? AND deleted_at IS NULL;",
            (inventory_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        data = dict(row)

    return _render_labels([data], "inventory")


def generate_roll_label(roll_id: str) -> Path | None:
    """为指定拍摄记录生成标签"""
    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM film_rolls WHERE id = ? AND deleted_at IS NULL;",
            (roll_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        roll = dict(row)

        # 获取关联的归档信息
        cursor = conn.execute(
            "SELECT * FROM archive_records WHERE film_roll_id = ? AND deleted_at IS NULL;",
            (roll_id,),
        )
        arch = cursor.fetchone()
        archive = dict(arch) if arch else {}

    return _render_labels([roll], "roll", archive=archive)


def generate_batch_labels(
    label_type: str,  # "inventory" or "roll"
    record_ids: list[str] | None = None,
) -> Path | None:
    """批量生成标签（一页多个标签）

    Args:
        label_type: "inventory" 或 "roll"
        record_ids: 指定记录 UUID 列表，None 则包含所有未过期且库存 > 0 的库存

    Returns:
        HTML 文件路径
    """
    db = get_db()

    if record_ids:
        placeholders = ",".join(["?"] * len(record_ids))
        if label_type == "inventory":
            sql = f"SELECT * FROM film_inventory WHERE id IN ({placeholders}) AND deleted_at IS NULL;"
        else:
            sql = f"SELECT * FROM film_rolls WHERE id IN ({placeholders}) AND deleted_at IS NULL;"
        with db.get_connection() as conn:
            cursor = conn.execute(sql, record_ids)
            records = [dict(row) for row in cursor.fetchall()]
    else:
        if label_type == "inventory":
            with db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM film_inventory WHERE deleted_at IS NULL "
                    "AND quantity_cache > 0 ORDER BY expiry_date ASC;"
                )
                records = [dict(row) for row in cursor.fetchall()]
        else:
            return None

    if not records:
        return None

    return _render_labels(records, label_type)


def _render_labels(
    records: list[dict],
    label_type: str,
    archive: dict | None = None,
) -> Path:
    """渲染标签 HTML 并保存到文件"""
    export_dir = get_export_dir()
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(CHINA_TZ).strftime("%Y%m%d_%H%M%S")
    filename = f"胶片标签_{label_type}_{timestamp}.html"
    filepath = export_dir / filename

    # 构建 HTML
    labels_html = ""
    for rec in records:
        brand = _escape_html(rec.get("brand", ""))
        model = _escape_html(rec.get("model", ""))
        fmt = _escape_html(rec.get("film_format", ""))
        iso_val = rec.get("box_iso", "") or ""
        expiry = rec.get("expiry_date", "") or ""
        storage = _escape_html(rec.get("storage_method", ""))
        location = _escape_html(rec.get("storage_location", ""))
        qty = rec.get("quantity_cache", 0)
        batch = _escape_html(rec.get("batch_number", ""))

        if label_type == "roll":
            roll_num = _escape_html(rec.get("roll_number", ""))
            camera = _escape_html(rec.get("camera", ""))
            status = rec.get("status", "")
            from app.constants import get_status_display
            status_cn = get_status_display(status)

        # 过期状态标签
        expiry_badge = ""
        if expiry:
            days = days_until_expiry(expiry)
            if days is not None:
                if days < 0:
                    expiry_badge = f'<span class="badge expired">已过期 {abs(days)} 天</span>'
                elif days <= 90:
                    expiry_badge = f'<span class="badge warning">{days} 天后过期</span>'
                else:
                    expiry_badge = f'<span class="badge ok">有效期至 {expiry}</span>'

        labels_html += f"""
        <div class="label">
            <div class="label-header">
                <span class="brand">{brand}</span>
                <span class="format">{fmt}</span>
            </div>
            <div class="model">{model}</div>
            <div class="info">
                <div class="info-row"><span>ISO</span><strong>{iso_val}</strong></div>
                <div class="info-row"><span>数量</span><strong>×{qty}</strong></div>
                <div class="info-row"><span>保存</span><strong>{storage}</strong></div>
                <div class="info-row"><span>位置</span><strong>{location}</strong></div>
            </div>
            {f'<div class="batch">批次: {batch}</div>' if batch else ''}
            <div class="expiry">{expiry_badge or expiry}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>胶片标签 - {label_type}</title>
<style>
    @page {{ size: A4; margin: 10mm; }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
        display: flex; flex-wrap: wrap; gap: 8mm;
        padding: 8mm; justify-content: flex-start;
        background: #f5f0e8;
    }}
    .label {{
        width: 64mm; min-height: 50mm;
        background: #fffefb;
        border: 1.5px solid #d8cdb8;
        border-radius: 4mm;
        padding: 5mm;
        page-break-inside: avoid;
        display: flex; flex-direction: column;
        gap: 2mm;
    }}
    .label-header {{
        display: flex; justify-content: space-between;
        align-items: baseline;
    }}
    .brand {{
        font-size: 12pt; font-weight: bold; color: #2c1810;
    }}
    .format {{
        font-size: 10pt; color: #fffefb;
        background: #c8783c; padding: 1mm 3mm;
        border-radius: 2mm; font-weight: bold;
    }}
    .model {{
        font-size: 14pt; font-weight: bold; color: #2c1810;
        border-bottom: 1px solid #e0d5c5; padding-bottom: 2mm;
    }}
    .info {{ display: flex; flex-wrap: wrap; gap: 2mm; }}
    .info-row {{
        flex: 1 1 40%; font-size: 9pt;
        display: flex; justify-content: space-between;
    }}
    .info-row span {{ color: #9b8a7e; }}
    .info-row strong {{ color: #2c1810; }}
    .batch {{ font-size: 8pt; color: #9b8a7e; }}
    .expiry {{ margin-top: auto; font-size: 9pt; }}
    .badge {{
        display: inline-block; padding: 1mm 3mm;
        border-radius: 2mm; font-size: 8pt; font-weight: bold;
    }}
    .badge.expired {{ background: #fce4e4; color: #b5433a; }}
    .badge.warning {{ background: #faf0e0; color: #d4853c; }}
    .badge.ok {{ background: #e8f0e0; color: #5d8c4a; }}
    @media print {{
        body {{ background: white; }}
        .label {{ box-shadow: none; }}
    }}
</style>
</head>
<body>
{labels_html}
</body>
</html>"""

    filepath.write_text(html, encoding="utf-8")
    logger.info(f"标签已生成: {filepath}")
    return filepath
