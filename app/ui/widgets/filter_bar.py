"""
通用筛选栏组件

提供组合筛选控件：下拉框筛选 + 关键词搜索 + 清除按钮
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel,
)
from PySide6.QtCore import Signal


class FilterBar(QWidget):
    """通用筛选栏"""

    # 信号：筛选条件变更
    filter_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filters: list[dict] = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # 关键词搜索框
        self._layout.addWidget(QLabel("搜索:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入关键词搜索...")
        self.keyword_input.setMaximumWidth(250)
        self.keyword_input.textChanged.connect(self._on_filter_changed)
        self._layout.addWidget(self.keyword_input)

        self._layout.addSpacing(10)

        # 下拉筛选框容器
        self.combos: dict[str, QComboBox] = {}

        # 清除筛选按钮
        self.clear_btn = QPushButton("清除筛选")
        self.clear_btn.clicked.connect(self.clear_filters)
        self._layout.addWidget(self.clear_btn)

        self._layout.addStretch()

    def add_combo_filter(self, field: str, label: str, options: list[tuple[str, str]]):
        """添加下拉筛选框

        Args:
            field: 字段名
            label: 显示标签
            options: [(值, 显示文本), ...] 列表，第一项通常为 ("", "全部")
        """
        lbl = QLabel(f"{label}:")
        combo = QComboBox()
        for value, text in options:
            combo.addItem(text, value)

        combo.currentIndexChanged.connect(self._on_filter_changed)

        self._layout.insertWidget(self._layout.count() - 2, lbl)
        self._layout.insertWidget(self._layout.count() - 2, combo)
        self.combos[field] = combo

    def get_filter_values(self) -> dict:
        """获取当前所有筛选条件的值"""
        values = {"keyword": self.keyword_input.text().strip()}
        for field, combo in self.combos.items():
            values[field] = combo.currentData()
        return values

    def clear_filters(self):
        """清除所有筛选条件"""
        self.keyword_input.clear()
        for combo in self.combos.values():
            combo.setCurrentIndex(0)

    def _on_filter_changed(self, *_args):
        """筛选条件变更时发出信号"""
        self.filter_changed.emit()

    def set_keyword_placeholder(self, text: str):
        """设置搜索框提示文本"""
        self.keyword_input.setPlaceholderText(text)
