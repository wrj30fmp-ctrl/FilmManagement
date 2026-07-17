"""
首页仪表盘 — 暖色柔和风格
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.services.statistics_service import StatisticsService
from app.constants import get_status_display, FilmStatus
from app.utils.date_utils import days_until_expiry
from app.ui.theme import Colors


class DashboardPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats_service = StatisticsService()
        self._setup_ui()

    def _setup_ui(self):
        c = {k: v for k, v in vars(Colors).items() if not k.startswith("_")}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: transparent; }}")

        content = QWidget()
        content.setStyleSheet(f"background: transparent;")
        self._layout = QVBoxLayout(content)
        self._layout.setSpacing(18)
        self._layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("首页概览")
        title.setFont(QFont("", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['text_primary']}; background: transparent; padding: 0;")
        self._layout.addWidget(title)

        # 库存卡片行
        inv_title = QLabel("📦 胶卷库存")
        inv_title.setStyleSheet(f"color: {c['text_primary']}; font-weight: bold; background: transparent; font-size: 14px;")
        self._layout.addWidget(inv_title)
        self._inventory_grid = QGridLayout()
        self._inventory_grid.setSpacing(12)
        self._layout.addLayout(self._inventory_grid)

        # 拍摄状态行
        shoot_title = QLabel("📷 拍摄状态")
        shoot_title.setStyleSheet(f"color: {c['text_primary']}; font-weight: bold; background: transparent; font-size: 14px;")
        self._layout.addWidget(shoot_title)
        self._shooting_grid = QGridLayout()
        self._shooting_grid.setSpacing(12)
        self._layout.addLayout(self._shooting_grid)

        # 最近活动
        recent_row = QHBoxLayout()
        recent_row.setSpacing(14)

        left = QVBoxLayout()
        recent_inv_title = QLabel("<b>最近添加的库存</b>")
        recent_inv_title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        left.addWidget(recent_inv_title)
        self._recent_inv = QLabel()
        self._recent_inv.setWordWrap(True)
        self._recent_inv.setMinimumHeight(80)
        self._recent_inv.setStyleSheet(
            f"QLabel {{ background: {c['card_bg']}; color: {c['text_primary']}; "
            f"padding: 14px; border-radius: 8px; "
            f"border: 1px solid {c['border']}; }}"
        )
        left.addWidget(self._recent_inv)
        recent_row.addLayout(left)

        right = QVBoxLayout()
        recent_rolls_title = QLabel("<b>最近拍摄记录</b>")
        recent_rolls_title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        right.addWidget(recent_rolls_title)
        self._recent_rolls = QLabel()
        self._recent_rolls.setWordWrap(True)
        self._recent_rolls.setMinimumHeight(80)
        self._recent_rolls.setStyleSheet(
            f"QLabel {{ background: {c['card_bg']}; color: {c['text_primary']}; "
            f"padding: 14px; border-radius: 8px; "
            f"border: 1px solid {c['border']}; }}"
        )
        right.addWidget(self._recent_rolls)
        recent_row.addLayout(right)

        self._layout.addLayout(recent_row)

        # 优先使用推荐 + 库存预测
        rec_row = QHBoxLayout()
        rec_row.setSpacing(14)

        rec_left = QVBoxLayout()
        rec_title = QLabel("🎯 优先使用推荐")
        rec_title.setStyleSheet(f"color: {c['text_primary']}; font-weight: bold; background: transparent; font-size: 14px;")
        rec_left.addWidget(rec_title)
        self._recommend_label = QLabel()
        self._recommend_label.setWordWrap(True)
        self._recommend_label.setMinimumHeight(70)
        self._recommend_label.setStyleSheet(
            f"QLabel {{ background: {c['card_bg']}; color: {c['text_primary']}; "
            f"padding: 12px; border-radius: 8px; border: 1px solid {c['border']}; }}"
        )
        rec_left.addWidget(self._recommend_label)
        rec_row.addLayout(rec_left)

        rec_right = QVBoxLayout()
        pred_title = QLabel("📈 库存预测")
        pred_title.setStyleSheet(f"color: {c['text_primary']}; font-weight: bold; background: transparent; font-size: 14px;")
        rec_right.addWidget(pred_title)
        self._predict_label = QLabel()
        self._predict_label.setWordWrap(True)
        self._predict_label.setMinimumHeight(70)
        self._predict_label.setStyleSheet(
            f"QLabel {{ background: {c['card_bg']}; color: {c['text_primary']}; "
            f"padding: 12px; border-radius: 8px; border: 1px solid {c['border']}; }}"
        )
        rec_right.addWidget(self._predict_label)
        rec_row.addLayout(rec_right)

        self._layout.addLayout(rec_row)

        # 过期提醒
        exp_title = QLabel("⚠ 过期提醒")
        exp_title.setStyleSheet(f"color: {c['text_primary']}; font-weight: bold; background: transparent; font-size: 14px;")
        self._layout.addWidget(exp_title)
        self._expiry_label = QLabel()
        self._expiry_label.setWordWrap(True)
        self._expiry_label.setStyleSheet(
            f"QLabel {{ background: {c['warning_bg']}; color: {c['text_primary']}; "
            f"padding: 14px; border-radius: 8px; "
            f"border-left: 4px solid {c['warning_border']}; }}"
        )
        self._layout.addWidget(self._expiry_label)
        self._layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh_data(self):
        c = {k: v for k, v in vars(Colors).items() if not k.startswith('_')}
        stats = self._stats_service.get_dashboard_stats()
        self._clear_grid(self._inventory_grid)
        self._clear_grid(self._shooting_grid)

        # 库存卡片
        inv_cards = [
            ("未拍库存", str(stats["inventory_total"]), c["accent"]),
            ("135 胶卷", f"{stats['inventory_135']} 卷", c["success"]),
            ("120 胶卷", f"{stats['inventory_120']} 卷", c["warning_border"]),
        ]
        for i, (label, value, color) in enumerate(inv_cards):
            card = self._make_card(value, label, color)
            self._inventory_grid.addWidget(card, 0, i)

        # 拍摄卡片
        shoot_cards = [
            ("拍摄中", stats["shooting_count"], c["danger"]),
            ("待冲洗", stats["shot_waiting_dev"], c["warning_border"]),
            ("待扫描", stats["developed_waiting_scan"], c["accent"]),
            ("待归档", stats["scanned_waiting_archive"], "#8e6ab3"),
            ("已归档", stats["archived_count"], c["success"]),
        ]
        for i, (label, value, color) in enumerate(shoot_cards):
            card = self._make_card(str(value), label, color)
            self._shooting_grid.addWidget(card, 0, i)

        # 最近库存
        inv_text = ""
        for item in stats["recent_inventory"]:
            inv_text += f"• {item.get('brand','')} {item.get('model','')} ({item.get('film_format','')}) x{item.get('quantity_cache',0)}<br>"
        if not inv_text:
            inv_text = f"<span style='color:{c['text_hint']};'>暂无库存记录</span>"
        self._recent_inv.setText(inv_text)

        # 最近拍摄
        roll_text = ""
        for item in stats["recent_rolls"]:
            roll_text += f"• {item.get('roll_number','')} {item.get('model','')} [{get_status_display(item.get('status',''))}]<br>"
        if not roll_text:
            roll_text = f"<span style='color:{c['text_hint']};'>暂无拍摄记录</span>"
        self._recent_rolls.setText(roll_text)

        # 过期提醒
        exp_lines = []
        for item in stats["expired_inventory"]:
            days = days_until_expiry(item.get("expiry_date", ""))
            exp_lines.append(
                f"● <b>{item.get('brand','')} {item.get('model','')}</b> x{item.get('quantity_cache',0)} — "
                f"已过期 {abs(days) if days else '?'} 天"
            )
        for item in stats["expiring_inventory"]:
            days = days_until_expiry(item.get("expiry_date", ""))
            exp_lines.append(
                f"● <b>{item.get('brand','')} {item.get('model','')}</b> x{item.get('quantity_cache',0)} — "
                f"有效期至 {item.get('expiry_date','')}（剩余 {days} 天）"
            )
        if exp_lines:
            self._expiry_label.setText("<br>".join(exp_lines))
        else:
            self._expiry_label.setText("暂无即将过期或已过期的胶卷 ✓")

        # --- 优先使用推荐 ---
        rec_films = self._stats_service.get_recommended_films()
        if rec_films:
            rec_lines = []
            for f in rec_films[:5]:
                days = days_until_expiry(f.get("expiry_date", ""))
                if days is not None and days <= 90:
                    tag = " ⚡" if days > 0 else " ⚠"
                else:
                    tag = ""
                rec_lines.append(
                    f"• <b>{f.get('brand','')} {f.get('model','')}</b> "
                    f"({f.get('film_format','')}) x{f.get('quantity_cache',0)}{tag}"
                )
            self._recommend_label.setText("<br>".join(rec_lines))
        else:
            self._recommend_label.setText("库存中暂无胶卷，快去添加吧！")

        # --- 库存预测 ---
        usage = self._stats_service.get_usage_rate()
        pred_text = (
            f"月均拍摄：<b>{usage['rolls_per_month']} 卷/月</b><br>"
            f"当前库存：<b>{usage['total_inventory']} 卷</b><br>"
        )
        remaining = usage['months_remaining']
        if remaining >= 99:
            pred_text += "暂无足够数据预测"
        elif remaining <= 3:
            pred_text += f"预计耗尽：<b style='color:#b5433a;'>{remaining} 个月</b> ⚠"
        elif remaining <= 6:
            pred_text += f"预计耗尽：<b style='color:#d4853c;'>{remaining} 个月</b>"
        else:
            pred_text += f"预计耗尽：<b style='color:#5d8c4a;'>{remaining} 个月</b>"
        self._predict_label.setText(pred_text)

    def _make_card(self, value: str, label: str, color: str) -> QFrame:
        c = {k: v for k, v in vars(Colors).items() if not k.startswith('_')}
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {c['card_bg']}; border: 1px solid {c['border']}; "
            f"border-radius: 10px; border-left: 4px solid {color}; padding: 16px 18px; }}"
        )
        lay = QVBoxLayout(card)
        lay.setSpacing(4)
        lay.setContentsMargins(0, 0, 0, 0)

        val_lbl = QLabel(value)
        val_lbl.setFont(QFont("", 24, QFont.Weight.Bold))
        val_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent; border: none;")
        lay.addWidget(val_lbl)

        desc_lbl = QLabel(label)
        desc_lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 12px; background: transparent; border: none;")
        lay.addWidget(desc_lbl)

        return card

    def _clear_grid(self, grid: QGridLayout):
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_data()
