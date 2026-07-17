"""
拍摄记录管理页面

显示拍摄记录列表，提供筛选、新增、编辑、删除、状态推进功能。
支持从库存开始拍摄。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QLabel, QComboBox, QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from app.services.film_roll_service import FilmRollService
from app.services.inventory_service import InventoryService
from app.ui.widgets.film_table import FilmTable
from app.ui.widgets.filter_bar import FilterBar
from app.ui.dialogs.film_roll_dialog import FilmRollDialog
from app.constants import (
    FilmStatus, get_status_display, FILM_FORMATS,
)


class ShootingPage(QWidget):
    """拍摄记录管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._roll_service = FilmRollService()
        self._inventory_service = InventoryService()
        self._setup_ui()
        self._connect_signals()
        self.refresh_data()

    def _setup_ui(self):
        """构建页面布局"""
        self.setStyleSheet("color: #2c1810;")
        layout = QVBoxLayout(self)

        # --- 标题栏 ---
        title_layout = QHBoxLayout()
        title = QLabel("<h2>拍摄记录</h2>")
        title.setStyleSheet("color: #2c1810; background: transparent;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 从库存开始拍摄按钮
        self.start_from_inventory_btn = QPushButton("从库存开始拍摄")
        self.start_from_inventory_btn.setStyleSheet(
            "QPushButton { background-color: #c8783c; color: white; padding: 6px 16px; "
            "border-radius: 6px; font-weight: bold; border: none; }"
            "QPushButton:hover { background-color: #b06830; }"
        )
        self.start_from_inventory_btn.clicked.connect(self._on_start_from_inventory)
        title_layout.addWidget(self.start_from_inventory_btn)

        # 手动新增按钮
        self.add_btn = QPushButton("+ 新增记录")
        self.add_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 6px 16px; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.add_btn.clicked.connect(self._on_add)
        title_layout.addWidget(self.add_btn)

        layout.addLayout(title_layout)

        # --- 筛选栏 ---
        self.filter_bar = FilterBar()
        self.filter_bar.set_keyword_placeholder("搜索编号、品牌、型号、相机、镜头...")
        self.filter_bar.add_combo_filter(
            "film_format", "画幅",
            [("", "全部")] + [(f, f) for f in FILM_FORMATS]
        )
        self.filter_bar.add_combo_filter(
            "status", "状态",
            [("", "全部状态")] + [
                (s, get_status_display(s)) for s in FilmStatus.ROLL_STATUSES
            ]
        )
        layout.addWidget(self.filter_bar)

        # --- 数据表格 ---
        self.table = FilmTable()
        self.table.set_columns([
            ("roll_number", "胶卷编号"),
            ("brand", "品牌"),
            ("model", "型号"),
            ("film_format", "画幅"),
            ("box_iso", "ISO"),
            ("camera", "相机"),
            ("lens", "镜头"),
            ("load_date", "装卷日期"),
            ("status", "状态"),
            ("location", "拍摄地"),
        ])
        layout.addWidget(self.table)

        # --- 底部操作栏 ---
        btn_layout = QHBoxLayout()

        # 状态推进按钮
        self.advance_btn = QPushButton("▶ 推进状态")
        self.advance_btn.clicked.connect(self._on_advance_status)
        self.advance_btn.setEnabled(False)
        self.advance_btn.setStyleSheet(
            "QPushButton { background-color: #c8783c; color: white; padding: 6px 12px; "
            "border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #b06830; }"
        )
        btn_layout.addWidget(self.advance_btn)

        self.revert_btn = QPushButton("◀ 退回状态")
        self.revert_btn.clicked.connect(self._on_revert_status)
        self.revert_btn.setEnabled(False)
        btn_layout.addWidget(self.revert_btn)

        self.batch_advance_btn = QPushButton("批量推进状态")
        self.batch_advance_btn.clicked.connect(self._on_batch_advance)
        self.batch_advance_btn.setEnabled(False)
        self.batch_advance_btn.setStyleSheet(
            "QPushButton { background-color: #5d8c4a; color: white; padding: 6px 12px; "
            "border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #4a7038; }"
        )
        btn_layout.addWidget(self.batch_advance_btn)

        btn_layout.addSpacing(10)

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._on_edit)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { color: #d32f2f; }")
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.stats_label = QLabel()
        btn_layout.addWidget(self.stats_label)

        layout.addLayout(btn_layout)

    def _connect_signals(self):
        """连接信号"""
        self.filter_bar.filter_changed.connect(self.refresh_data)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.row_double_clicked.connect(self._on_row_double_click)
        self.table.edit_requested.connect(self._on_edit_row)
        self.table.delete_requested.connect(self._on_delete_row)

    # ================================================================
    # 数据刷新
    # ================================================================

    def refresh_data(self):
        """刷新表格"""
        filters = self.filter_bar.get_filter_values()
        data = self._roll_service.list_rolls(
            status=filters.get("status", ""),
            film_format=filters.get("film_format", ""),
            keyword=filters.get("keyword", ""),
        )

        # 格式化显示
        for row in data:
            row["status"] = get_status_display(row.get("status", ""))
            row["box_iso"] = f"{row.get('box_iso', '')}" if row.get("box_iso") else ""

        self.table.load_data(data)
        self.stats_label.setText(f"共 {len(data)} 条记录")

    # ================================================================
    # 操作处理
    # ================================================================

    def _on_selection_changed(self):
        """选中状态变更"""
        has_selection = self.table.get_selected_row() is not None
        has_multi = len(self.table.get_selected_rows()) >= 2
        self.advance_btn.setEnabled(has_selection)
        self.revert_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.batch_advance_btn.setEnabled(has_multi)

    def _on_add(self):
        """手动新增拍摄记录"""
        dialog = FilmRollDialog(self)
        if dialog.exec() == FilmRollDialog.DialogCode.Accepted:
            try:
                self._roll_service.create_roll(dialog.get_form_data())
                self.refresh_data()
            except ValueError as e:
                QMessageBox.warning(self, "保存失败", str(e))
            except Exception as e:
                QMessageBox.critical(self, "保存失败",
                    f"创建拍摄记录时发生错误：{e}")

    def _on_start_from_inventory(self):
        """从库存开始拍摄"""
        # 获取有库存的记录
        inventory_list = self._inventory_service.list_inventory()
        available = [inv for inv in inventory_list if inv["quantity_cache"] > 0]

        if not available:
            QMessageBox.information(
                self, "库存不足",
                "当前没有可用的库存胶卷。\n请先在「库存」页面添加库存记录。"
            )
            return

        # 弹出库存选择对话框
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, \
            QDialogButtonBox, QLabel

        select_dialog = QDialog(self)
        select_dialog.setWindowTitle("选择库存胶卷")
        select_dialog.setMinimumWidth(450)
        sel_layout = QVBoxLayout(select_dialog)

        sel_lbl = QLabel("请选择要使用的库存胶卷：")
        sel_lbl.setStyleSheet("color: #2c1810; background: transparent;")
        sel_layout.addWidget(sel_lbl)
        list_widget = QListWidget()
        for inv in available:
            brand = inv.get("brand", "")
            model = inv.get("model", "")
            fmt = inv.get("film_format", "")
            qty = inv.get("quantity_cache", 0)
            list_widget.addItem(f"{brand} {model} ({fmt}) - 库存 {qty} 卷")
            list_widget.item(list_widget.count() - 1).setData(
                Qt.ItemDataRole.UserRole, inv)

        sel_layout.addWidget(list_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(select_dialog.accept)
        buttons.rejected.connect(select_dialog.reject)
        sel_layout.addWidget(buttons)

        if select_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_item = list_widget.currentItem()
        if not selected_item:
            return
        inventory = selected_item.data(Qt.ItemDataRole.UserRole)

        # 打开拍摄记录对话框（带预填数据）
        dialog = FilmRollDialog(self, inventory_data=inventory)
        if dialog.exec() == FilmRollDialog.DialogCode.Accepted:
            try:
                extra_data = dialog.get_form_data()
                self._roll_service.start_shooting_from_inventory(
                    inventory["id"], extra_data=extra_data
                )
                self.refresh_data()
            except ValueError as e:
                QMessageBox.warning(self, "操作失败", str(e))
            except Exception as e:
                QMessageBox.critical(self, "操作失败",
                    f"从库存开始拍摄时发生错误：{e}")

    def _on_edit(self):
        """编辑选中记录"""
        result = self.table.get_selected_row()
        if result is None:
            return
        self._edit_record(result[1])

    def _on_row_double_click(self, row: int, row_data: dict):
        self._edit_record(row_data)

    def _on_edit_row(self, row: int, row_data: dict):
        self._edit_record(row_data)

    def _edit_record(self, row_data: dict):
        """打开编辑对话框"""
        roll_id = row_data["id"]
        full_record = self._roll_service.get_roll(roll_id)
        if not full_record:
            QMessageBox.warning(self, "记录不存在", "该拍摄记录已被删除。")
            self.refresh_data()
            return

        dialog = FilmRollDialog(self, record=full_record)
        if dialog.exec() == FilmRollDialog.DialogCode.Accepted:
            try:
                self._roll_service.update_roll(roll_id, dialog.get_form_data())
                self.refresh_data()
            except ValueError as e:
                QMessageBox.warning(self, "保存失败", str(e))
            except Exception as e:
                QMessageBox.critical(self, "保存失败",
                    f"更新拍摄记录时发生错误：{e}")

    def _on_delete(self):
        """删除选中记录"""
        result = self.table.get_selected_row()
        if result is None:
            return
        self._delete_record(result[1])

    def _on_delete_row(self, row: int, row_data: dict):
        self._delete_record(row_data)

    def _delete_record(self, row_data: dict):
        """二次确认后删除"""
        roll_number = row_data.get("roll_number", "未知")
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除拍摄记录「{roll_number}」吗？\n\n"
            "此操作为软删除，未来可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._roll_service.delete_roll(row_data["id"])
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "删除失败",
                    f"删除拍摄记录时发生错误：{e}")

    def _on_advance_status(self):
        """推进状态"""
        result = self.table.get_selected_row()
        if result is None:
            return
        row_data = result[1]
        roll_id = row_data["id"]
        try:
            self._roll_service.advance_status(roll_id)
            self.refresh_data()
        except ValueError as e:
            QMessageBox.warning(self, "无法推进状态", str(e))

    def _on_revert_status(self):
        """退回状态"""
        result = self.table.get_selected_row()
        if result is None:
            return
        row_data = result[1]
        roll_id = row_data["id"]
        try:
            self._roll_service.revert_status(roll_id)
            self.refresh_data()
        except ValueError as e:
            QMessageBox.warning(self, "无法退回状态", str(e))

    def _on_batch_advance(self):
        """批量推进状态"""
        selected = self.table.get_selected_rows()
        if len(selected) < 2:
            return

        reply = QMessageBox.question(
            self, "批量推进状态",
            f"确定要将选中的 {len(selected)} 条记录全部推进到下一个状态吗？\n\n"
            "此操作将逐条推进每条记录的状态。\n"
            "部分记录可能因状态限制无法推进（会被跳过）。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        success = 0
        skipped = 0
        for _, row_data in selected:
            try:
                self._roll_service.advance_status(row_data["id"])
                success += 1
            except ValueError:
                skipped += 1

        self.refresh_data()
        QMessageBox.information(
            self, "批量推进完成",
            f"成功推进 {success} 条记录。\n跳过 {skipped} 条（已达到最终状态）。"
        )
