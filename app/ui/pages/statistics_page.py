"""
数据统计页面 — 纵向单列布局，确保所有内容不遮挡
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt

from app.services.statistics_service import StatisticsService
from app.ui.widgets.chart_widget import ChartCanvas


class StatisticsPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats_service = StatisticsService()
        self._charts: list[ChartCanvas] = []
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("color: #2c1810;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 16, 20, 20)

        title = QLabel("<h2>数据统计</h2>")
        title.setStyleSheet("color: #2c1810; background: transparent;")
        layout.addWidget(title)

        # ── 成本明细 + 费用构成 ──
        cost_group = QGroupBox("成本概览")
        cost_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        cost_row = QHBoxLayout(cost_group)
        self._cost_form = QFormLayout()
        cost_row.addLayout(self._cost_form)
        self._cost_pie = ChartCanvas(width=4.5, height=2.8, dpi=90, dark_mode=False)
        self._charts.append(self._cost_pie)
        cost_row.addWidget(self._cost_pie)
        layout.addWidget(cost_group)

        # ── 月度消费趋势 ──
        trend_group = QGroupBox("月度消费趋势")
        trend_lay = QVBoxLayout(trend_group)
        self._cost_trend = ChartCanvas(width=9, height=2.8, dpi=90, dark_mode=False)
        self._charts.append(self._cost_trend)
        trend_lay.addWidget(self._cost_trend)
        layout.addWidget(trend_group)

        # ── 每月拍摄 + 库存预测 ──
        mid_group = QGroupBox("拍摄趋势与库存预测")
        mid_row = QHBoxLayout(mid_group)
        self._monthly = ChartCanvas(width=5.5, height=2.8, dpi=90, dark_mode=False)
        self._charts.append(self._monthly)
        mid_row.addWidget(self._monthly)
        self._pred_form = QFormLayout()
        mid_row.addLayout(self._pred_form)
        layout.addWidget(mid_group)

        # ── 相机使用 ──
        cam_group = QGroupBox("相机使用次数")
        cam_lay = QVBoxLayout(cam_group)
        self._camera = ChartCanvas(width=9, height=2.8, dpi=90, dark_mode=False)
        self._charts.append(self._camera)
        cam_lay.addWidget(self._camera)
        layout.addWidget(cam_group)

        # ── 画幅 + 库存 ──
        bot_group = QGroupBox("画幅分布与库存")
        bot_row = QHBoxLayout(bot_group)
        self._format = ChartCanvas(width=4, height=2.5, dpi=90, dark_mode=False)
        self._charts.append(self._format)
        bot_row.addWidget(self._format)
        self._inv_table = QTableWidget()
        self._inv_table.setColumnCount(5)
        self._inv_table.setHorizontalHeaderLabels(["品牌", "型号", "画幅", "类型", "库存"])
        self._inv_table.horizontalHeader().setStretchLastSection(True)
        self._inv_table.setMinimumHeight(180)
        bot_row.addWidget(self._inv_table)
        layout.addWidget(bot_group)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh_data(self):
        svc = self._stats_service

        # ── 成本明细 ──
        cost = svc.get_total_cost()
        self._clear_form(self._cost_form)
        self._cost_form.addRow("库存购买总成本:",
                               QLabel(f"¥ {cost['inventory_cost']:.2f}"))
        self._cost_form.addRow("冲洗总成本:",
                               QLabel(f"¥ {cost['development_cost']:.2f}"))
        self._cost_form.addRow("扫描总成本:",
                               QLabel(f"¥ {cost['scan_cost']:.2f}"))
        self._cost_form.addRow("",
                               QLabel(f"<b>总成本 ¥ {cost['total_cost']:.2f}</b>"))
        self._cost_form.addRow("已拍摄:", QLabel(f"{cost['total_rolls']} 卷"))
        self._cost_form.addRow("单卷平均:",
                               QLabel(f"<b>¥ {cost['average_cost_per_roll']:.2f}</b>"))

        # ── 费用构成饼图 ──
        cat = svc.get_cost_by_category()
        if cat and sum(v for _, v in cat) > 0:
            self._cost_pie.pie_chart(
                [c[0] for c in cat], [c[1] for c in cat],
                title="费用构成", colors=["#c8783c", "#5d8c4a", "#8e6ab3"]
            )
        else:
            self._cost_pie.clear(); self._cost_pie.draw()

        # ── 月度消费趋势 ──
        trend = svc.get_cost_by_month(12)
        if trend:
            self._cost_trend.line_chart(
                [t[0] for t in trend], [t[1] for t in trend],
                title="月度消费趋势", xlabel="月份", ylabel="估算花费 (¥)",
                color="#c8783c"
            )
        else:
            self._cost_trend.clear(); self._cost_trend.draw()

        # ── 每月拍摄 ──
        monthly = svc.get_roll_count_by_month(12)
        if monthly:
            self._monthly.line_chart(
                [m[0] for m in monthly], [m[1] for m in monthly],
                title="近12个月拍摄趋势", xlabel="月份", ylabel="卷数",
                color="#5d8c4a"
            )
        else:
            self._monthly.clear(); self._monthly.draw()

        # ── 库存预测 ──
        usage = svc.get_usage_rate()
        self._clear_form(self._pred_form)
        self._pred_form.addRow("统计跨度:", QLabel(f"{usage['months_tracked']} 个月"))
        self._pred_form.addRow("已拍摄:", QLabel(f"{usage['total_rolls']} 卷"))
        self._pred_form.addRow("月均速度:",
                               QLabel(f"<b>{usage['rolls_per_month']} 卷/月</b>"))
        self._pred_form.addRow("当前库存:", QLabel(f"{usage['total_inventory']} 卷"))
        r = usage['months_remaining']
        if r >= 99:
            txt, clr = "暂无足够数据", "#9b8a7e"
        elif r <= 3:
            txt, clr = f"⚠ {r} 个月后耗尽，建议补货！", "#b5433a"
        elif r <= 6:
            txt, clr = f"约 {r} 个月后耗尽", "#d4853c"
        else:
            txt, clr = f"约 {r} 个月后耗尽，库存充足", "#5d8c4a"
        self._pred_form.addRow("预计耗尽:",
                               QLabel(f"<b style='color:{clr};'>{txt}</b>"))

        # ── 相机使用 ──
        cam = svc.get_camera_usage()
        if cam:
            self._camera.bar_chart(
                [c[0] if c[0] else "未记录" for c in cam[:10]],
                [c[1] for c in cam[:10]],
                title="相机使用次数 (Top 10)", xlabel="相机", ylabel="次数",
                color="#8e6ab3"
            )
        else:
            self._camera.clear(); self._camera.draw()

        # ── 画幅分布 ──
        fmt_data = svc.get_roll_count_by_format()
        if fmt_data:
            self._format.pie_chart(
                [f[0] if f[0] else "未知" for f in fmt_data],
                [f[1] for f in fmt_data], title="画幅分布"
            )
        else:
            self._format.clear(); self._format.draw()

        # ── 库存汇总 ──
        inv = svc.get_inventory_summary()
        self._inv_table.setRowCount(len(inv))
        for i, row in enumerate(inv):
            self._inv_table.setItem(i, 0, QTableWidgetItem(row.get("brand", "")))
            self._inv_table.setItem(i, 1, QTableWidgetItem(row.get("model", "")))
            self._inv_table.setItem(i, 2, QTableWidgetItem(row.get("film_format", "")))
            self._inv_table.setItem(i, 3, QTableWidgetItem(row.get("film_type", "")))
            self._inv_table.setItem(i, 4, QTableWidgetItem(str(row.get("total_qty", 0))))
        self._inv_table.resizeColumnsToContents()

    def _clear_form(self, form: QFormLayout):
        while form.count():
            item = form.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_data()
