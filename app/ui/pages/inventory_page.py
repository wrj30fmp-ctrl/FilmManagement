"""
库存管理页面

显示库存列表，提供筛选、新增、编辑、删除功能。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QLabel,
)
from PySide6.QtCore import Qt

from app.services.inventory_service import InventoryService
from app.ui.widgets.film_table import FilmTable
from app.ui.widgets.filter_bar import FilterBar
from app.ui.dialogs.inventory_dialog import InventoryDialog
from app.constants import FILM_FORMATS, FILM_TYPES, STORAGE_METHODS
from app.utils.date_utils import days_until_expiry, format_iso_to_date


class InventoryPage(QWidget):
    """库存管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = InventoryService()
        self._setup_ui()
        self._connect_signals()
        self.refresh_data()

    def _setup_ui(self):
        """构建页面布局"""
        self.setStyleSheet("color: #2c1810;")
        layout = QVBoxLayout(self)

        # --- 标题栏 ---
        title_layout = QHBoxLayout()
        title = QLabel("<h2>胶卷库存</h2>")
        title.setStyleSheet("color: #2c1810; background: transparent;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 新增按钮
        self.add_btn = QPushButton("+ 新增库存")
        self.add_btn.setStyleSheet(
            "QPushButton { background-color: #5d8c4a; color: white; padding: 6px 16px; "
            "border-radius: 6px; font-weight: bold; border: none; }"
            "QPushButton:hover { background-color: #4a7038; }"
        )
        self.add_btn.clicked.connect(self._on_add)
        title_layout.addWidget(self.add_btn)

        layout.addLayout(title_layout)

        # --- 筛选栏 ---
        self.filter_bar = FilterBar()
        self.filter_bar.set_keyword_placeholder("搜索品牌、型号、批次...")
        self.filter_bar.add_combo_filter(
            "film_format", "画幅",
            [("", "全部")] + [(f, f) for f in FILM_FORMATS]
        )
        self.filter_bar.add_combo_filter(
            "expired", "过期状态",
            [
                ("", "全部"),
                ("expiring_soon", "即将过期（90天内）"),
                ("expired", "已过期"),
            ]
        )
        layout.addWidget(self.filter_bar)

        # --- 数据表格 ---
        self.table = FilmTable()
        self.table.set_columns([
            ("brand", "品牌"),
            ("model", "型号"),
            ("film_format", "画幅"),
            ("film_type", "色彩类型"),
            ("box_iso", "ISO"),
            ("quantity_cache", "库存数量"),
            ("expiry_date", "有效期"),
            ("purchase_date", "购买日期"),
            ("storage_method", "保存方式"),
            ("storage_location", "存放位置"),
        ])
        layout.addWidget(self.table)

        # --- 底部操作栏 ---
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("编辑选中记录")
        self.edit_btn.clicked.connect(self._on_edit)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除选中记录")
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { color: #b5433a; }")
        btn_layout.addWidget(self.delete_btn)

        self.label_btn = QPushButton("🏷 生成标签")
        self.label_btn.clicked.connect(self._on_generate_label)
        self.label_btn.setEnabled(False)
        btn_layout.addWidget(self.label_btn)

        btn_layout.addStretch()

        # 库存统计
        self.stats_label = QLabel()
        btn_layout.addWidget(self.stats_label)

        layout.addLayout(btn_layout)

    def _connect_signals(self):
        """连接信号和槽"""
        self.filter_bar.filter_changed.connect(self.refresh_data)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.row_double_clicked.connect(self._on_row_double_click)
        self.table.edit_requested.connect(self._on_edit_row)
        self.table.delete_requested.connect(self._on_delete_row)

    # ================================================================
    # 数据刷新
    # ================================================================

    def refresh_data(self):
        """刷新表格数据"""
        filters = self.filter_bar.get_filter_values()
        data = self._service.list_inventory(
            brand=filters.get("brand", ""),
            film_format=filters.get("film_format", ""),
            expired=filters.get("expired", ""),
            keyword=filters.get("keyword", ""),
        )

        # 格式化表格显示
        for row in data:
            row["expiry_date"] = self._format_expiry_display(row)
            row["purchase_date"] = row.get("purchase_date", "")
            row["box_iso"] = f"{row.get('box_iso', '')}" if row.get("box_iso") else ""

        self.table.load_data(data)

        # 更新统计信息
        total_qty = sum(r.get("quantity_cache", 0) for r in data)
        self.stats_label.setText(
            f"共 {len(data)} 种胶卷  |  总库存 {total_qty} 卷"
        )

    def _format_expiry_display(self, row: dict) -> str:
        """格式化有效期显示，附加过期状态信息"""
        expiry = row.get("expiry_date", "")
        if not expiry:
            return ""

        days = days_until_expiry(expiry)
        if days is None:
            return expiry
        if days < 0:
            return f"{expiry} ⚠ 已过期 {abs(days)} 天"
        if days <= 90:
            return f"{expiry} ⚡ 剩余 {days} 天"
        return expiry

    # ================================================================
    # 操作处理
    # ================================================================

    def _on_selection_changed(self):
        """表格选中状态变更"""
        has_selection = self.table.get_selected_row() is not None
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.label_btn.setEnabled(has_selection)

    def _on_add(self):
        """新增库存"""
        dialog = InventoryDialog(self)
        if dialog.exec() == InventoryDialog.DialogCode.Accepted:
            try:
                form_data = dialog.get_form_data()
                self._service.create_inventory(form_data)
                self.refresh_data()
            except ValueError as e:
                QMessageBox.warning(self, "保存失败", str(e))
            except Exception as e:
                QMessageBox.critical(
                    self, "保存失败",
                    f"保存库存记录时发生错误：{e}\n\n请检查数据后重试。"
                )

    def _on_edit(self):
        """编辑选中记录"""
        result = self.table.get_selected_row()
        if result is None:
            return
        row_idx, row_data = result
        self._edit_record(row_data)

    def _on_row_double_click(self, row: int, row_data: dict):
        """双击编辑"""
        self._edit_record(row_data)

    def _on_edit_row(self, row: int, row_data: dict):
        """右键菜单编辑"""
        self._edit_record(row_data)

    def _edit_record(self, row_data: dict):
        """打开编辑对话框"""
        record_id = row_data["id"]
        # 获取完整的数据库记录
        full_record = self._service.get_inventory(record_id)
        if not full_record:
            QMessageBox.warning(self, "记录不存在", "该库存记录已被删除。")
            self.refresh_data()
            return

        dialog = InventoryDialog(self, record=full_record)
        if dialog.exec() == InventoryDialog.DialogCode.Accepted:
            try:
                form_data = dialog.get_form_data()
                self._service.update_inventory(record_id, form_data)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(
                    self, "保存失败",
                    f"更新库存记录时发生错误：{e}\n\n请检查数据后重试。"
                )

    def _on_delete(self):
        """删除选中记录"""
        result = self.table.get_selected_row()
        if result is None:
            return
        self._delete_record(result[1])

    def _on_delete_row(self, row: int, row_data: dict):
        """右键菜单删除"""
        self._delete_record(row_data)

    def _on_generate_label(self):
        """为选中库存记录生成标签"""
        result = self.table.get_selected_row()
        if result is None:
            return
        row_data = result[1]
        try:
            from app.services.label_service import generate_inventory_label
            import webbrowser
            path = generate_inventory_label(row_data["id"])
            if path:
                webbrowser.open(str(path))
        except Exception as e:
            QMessageBox.critical(self, "标签生成失败", f"无法生成标签：{e}")

    def _delete_record(self, row_data: dict):
        """二次确认后软删除记录"""
        model_name = row_data.get("model", "未知型号")
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除库存记录「{model_name}」吗？\n\n"
            "删除后可在数据库回收站中恢复（未来功能）。\n"
            "此操作不会删除已关联的拍摄记录。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._service.delete_inventory(row_data["id"])
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(
                    self, "删除失败",
                    f"删除库存记录时发生错误：{e}\n\n请稍后重试。"
                )
