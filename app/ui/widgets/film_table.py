"""
通用数据表格组件

基于 QTableWidget 封装，提供：
- 自动列宽调整
- 行选择
- 双击编辑回调
- 右键菜单预留
- 排序指示
"""

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction


class FilmTable(QTableWidget):
    """通用数据表格组件"""

    # 信号：双击某一行时发出，携带行数据字典
    row_double_clicked = Signal(int, dict)
    # 信号：右键菜单操作
    edit_requested = Signal(int, dict)
    delete_requested = Signal(int, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = []        # 保存完整的行数据
        self._columns: list[str] = []      # 列名列表
        self._headers: list[str] = []      # 列标题列表
        self._setup_ui()

    def _setup_ui(self):
        """初始化表格样式和交互"""
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(False)

        # 显式设置表格颜色（QTableWidgetItem 不受全局样式表控制）
        self.setStyleSheet(
            "QTableWidget { color: #1a1a1a; background: white; }"
            "QHeaderView::section { color: #1a1a1a; background: #eaeaea; }"
        )

        # 表头设置
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionsClickable(True)

        # 垂直表头隐藏
        self.verticalHeader().setVisible(False)

        # 双击事件
        self.cellDoubleClicked.connect(self._on_double_click)

        # 右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_columns(self, columns: list[tuple[str, str]]):
        """设置列定义

        Args:
            columns: [(字段名, 显示标题), ...] 的列表
                     例如 [("roll_number", "胶卷编号"), ("brand", "品牌")]
        """
        self._columns = [col[0] for col in columns]
        self._headers = [col[1] for col in columns]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(self._headers)

    def load_data(self, data: list[dict]):
        """加载数据到表格

        Args:
            data: 字典列表，每个字典是一行数据，键对应 set_columns 中定义的字段名
        """
        self._data = data
        self.setRowCount(len(data))

        for row_idx, row_data in enumerate(data):
            for col_idx, col_name in enumerate(self._columns):
                value = row_data.get(col_name, "")
                # 某些值需要特殊格式化
                if value is None:
                    value = ""
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, row_data)  # 存储完整行数据
                self.setItem(row_idx, col_idx, item)

        # 自动调整列宽
        self.resizeColumnsToContents()

    def get_selected_row(self) -> tuple[int, dict] | None:
        """获取当前选中的行（单选时使用）

        Returns:
            (行索引, 行数据字典) 或 None
        """
        current = self.currentRow()
        if current < 0 or current >= len(self._data):
            return None
        return current, self._data[current]

    def get_selected_rows(self) -> list[tuple[int, dict]]:
        """获取所有选中的行（多选时使用）

        Returns:
            [(行索引, 行数据字典), ...] 列表
        """
        rows = set()
        for item in self.selectedItems():
            row = item.row()
            if 0 <= row < len(self._data):
                rows.add(row)
        return [(r, self._data[r]) for r in sorted(rows)]

    def clear_table(self):
        """清空表格"""
        self._data = []
        self.setRowCount(0)

    def _on_double_click(self, row: int, col: int):
        """双击行事件"""
        if 0 <= row < len(self._data):
            self.row_double_clicked.emit(row, self._data[row])

    def _show_context_menu(self, pos):
        """右键菜单"""
        row = self.rowAt(pos.y())
        if row < 0 or row >= len(self._data):
            return

        menu = QMenu(self)
        edit_action = QAction("编辑", self)
        delete_action = QAction("删除", self)

        edit_action.triggered.connect(lambda: self.edit_requested.emit(row, self._data[row]))
        delete_action.triggered.connect(lambda: self.delete_requested.emit(row, self._data[row]))

        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self.viewport().mapToGlobal(pos))
