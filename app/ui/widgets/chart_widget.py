"""
Matplotlib 图表组件

将 matplotlib 图表嵌入 PySide6 界面。
支持柱状图、饼图、折线图。
自动适配深色/浅色主题。
"""

import matplotlib
matplotlib.use("QtAgg")  # PySide6 后端

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import font_manager
import matplotlib.pyplot as plt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

# ============================================================
# 中文字体配置
# ============================================================
# 尝试设置中文字体，优先使用 Windows 自带字体
_CN_FONTS = [
    "Microsoft YaHei",    # 微软雅黑
    "SimHei",             # 黑体
    "SimSun",             # 宋体
    "KaiTi",              # 楷体
    "FangSong",           # 仿宋
]

for _font_name in _CN_FONTS:
    try:
        font_manager.findfont(_font_name, fallback_to_default=False)
        plt.rcParams["font.family"] = _font_name
        break
    except Exception:
        continue

# 解决负号显示问题
plt.rcParams["axes.unicode_minus"] = False


class ChartCanvas(FigureCanvas):
    """Matplotlib 图表画布，可嵌入 PySide6 界面"""

    def __init__(self, parent=None, width=6, height=4, dpi=100, dark_mode=False):
        self._dark_mode = dark_mode
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.set_tight_layout(True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _apply_theme(self, ax):
        """应用深色/浅色主题到坐标轴"""
        if self._dark_mode:
            ax.set_facecolor("#1e1e1e")
            self.fig.set_facecolor("#1e1e1e")
            ax.tick_params(colors="#cccccc")
            ax.xaxis.label.set_color("#cccccc")
            ax.yaxis.label.set_color("#cccccc")
            ax.title.set_color("#eeeeee")
            ax.spines["bottom"].set_color("#555555")
            ax.spines["top"].set_color("#555555")
            ax.spines["left"].set_color("#555555")
            ax.spines["right"].set_color("#555555")
        else:
            ax.set_facecolor("#ffffff")
            self.fig.set_facecolor("#ffffff")
            ax.tick_params(colors="#333333")
            ax.xaxis.label.set_color("#333333")
            ax.yaxis.label.set_color("#333333")
            ax.title.set_color("#222222")
            ax.spines["bottom"].set_color("#cccccc")
            ax.spines["top"].set_color("#cccccc")
            ax.spines["left"].set_color("#cccccc")
            ax.spines["right"].set_color("#cccccc")

    def set_dark_mode(self, dark: bool):
        """切换深色/浅色模式"""
        self._dark_mode = dark
        self.fig.clear()
        self.draw()

    def clear(self):
        """清空图表"""
        self.fig.clear()

    # ================================================================
    # 柱状图
    # ================================================================
    def bar_chart(self, labels: list[str], values: list[int | float],
                  title: str = "", xlabel: str = "", ylabel: str = "",
                  color: str = "#3498db", text_color: str | None = None):
        """绘制柱状图"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self._apply_theme(ax)

        bars = ax.bar(labels, values, color=color, edgecolor="white", linewidth=0.5)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        # 在柱子上方显示数值
        for bar, val in zip(bars, values):
            if val > 0:
                c = text_color or ("#cccccc" if self._dark_mode else "#333333")
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                        str(val), ha="center", va="bottom", fontsize=9, color=c)

        ax.tick_params(axis="x", rotation=30)
        self.fig.tight_layout()
        self.draw()

    # ================================================================
    # 饼图
    # ================================================================
    def pie_chart(self, labels: list[str], values: list[int | float],
                  title: str = "", colors: list[str] | None = None):
        """绘制饼图"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self._apply_theme(ax)

        default_colors = colors or ["#3498db", "#e74c3c", "#2ecc71", "#f39c12",
                                     "#9b59b6", "#1abc9c", "#e67e22", "#34495e"]
        text_color = "#cccccc" if self._dark_mode else "#333333"

        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct="%1.1f%%",
            colors=default_colors[:len(labels)],
            startangle=90, pctdistance=0.75,
        )

        for t in texts:
            t.set_color(text_color)
            t.set_fontsize(9)
        for at in autotexts:
            at.set_color("white")
            at.set_fontsize(8)
            at.set_fontweight("bold")

        ax.set_title(title, fontsize=13, fontweight="bold")
        self.fig.tight_layout()
        self.draw()

    # ================================================================
    # 折线图
    # ================================================================
    def line_chart(self, labels: list[str], values: list[int | float],
                   title: str = "", xlabel: str = "", ylabel: str = "",
                   color: str = "#3498db"):
        """绘制折线图"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self._apply_theme(ax)

        ax.plot(labels, values, marker="o", color=color, linewidth=2,
                markersize=6, markerfacecolor=color)

        # 填充区域
        ax.fill_between(range(len(labels)), values, alpha=0.15, color=color)

        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=30)

        # 在每个点上标注数值
        for i, val in enumerate(values):
            if val > 0:
                c = "#cccccc" if self._dark_mode else "#333333"
                ax.text(i, val + max(values) * 0.02, str(val),
                        ha="center", fontsize=8, color=c)

        self.fig.tight_layout()
        self.draw()
