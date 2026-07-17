"""
设置页面

提供数据库路径、备份设置、导出等功能。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QSpinBox, QLineEdit, QGroupBox, QMessageBox, QFileDialog,
    QCheckBox, QComboBox, QScrollArea,
)
from PySide6.QtCore import Qt

from app.config import get_database_path, get_backup_dir, get_export_dir
from app.services.backup_service import BackupService
from app.services.export_service import ExportService
from app.utils.file_utils import open_folder
from app.constants import CURRENCIES


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._backup_service = BackupService()
        self._export_service = ExportService()
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("color: #2c1810;")

        # 用滚动区域包裹所有内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)

        title = QLabel("<h2>设置</h2>")
        title.setStyleSheet("color: #2c1810; background: transparent;")
        layout.addWidget(title)

        # 辅助函数：创建带标准间距的 GroupBox
        def _make_group(title_text: str) -> tuple[QGroupBox, QFormLayout]:
            gb = QGroupBox(title_text)
            fl = QFormLayout(gb)
            fl.setSpacing(10)
            fl.setContentsMargins(16, 20, 16, 12)
            fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            return gb, fl

        # --- 数据路径组 ---
        path_group, path_form = _make_group("数据路径")

        # 数据库路径
        db_layout = QHBoxLayout()
        self.db_path_label = QLabel(str(get_database_path()))
        self.db_path_label.setStyleSheet("font-family: monospace;")
        db_layout.addWidget(self.db_path_label)
        db_layout.addStretch()
        db_open_btn = QPushButton("打开数据目录")
        db_open_btn.clicked.connect(lambda: open_folder(get_database_path().parent))
        db_layout.addWidget(db_open_btn)
        path_form.addRow("数据库文件:", db_layout)

        # 备份目录
        backup_layout = QHBoxLayout()
        backup_label = QLabel(str(get_backup_dir()))
        backup_label.setStyleSheet("font-family: monospace;")
        backup_layout.addWidget(backup_label)
        backup_layout.addStretch()
        backup_open_btn = QPushButton("打开备份目录")
        backup_open_btn.clicked.connect(lambda: open_folder(get_backup_dir()))
        backup_layout.addWidget(backup_open_btn)
        path_form.addRow("备份目录:", backup_layout)

        # 导出目录
        export_layout = QHBoxLayout()
        export_label = QLabel(str(get_export_dir()))
        export_label.setStyleSheet("font-family: monospace;")
        export_layout.addWidget(export_label)
        export_layout.addStretch()
        export_open_btn = QPushButton("打开导出目录")
        export_open_btn.clicked.connect(lambda: open_folder(get_export_dir()))
        export_layout.addWidget(export_open_btn)
        path_form.addRow("导出目录:", export_layout)

        layout.addWidget(path_group)

        # --- 备份设置组 ---
        backup_group, backup_form = _make_group("备份设置")

        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 100)
        self.backup_count_spin.setValue(20)
        self.backup_count_spin.setSuffix(" 份")
        backup_form.addRow("保留备份数量:", self.backup_count_spin)

        self.auto_backup_start = QCheckBox("程序启动时自动备份")
        self.auto_backup_start.setChecked(True)
        backup_form.addRow(self.auto_backup_start)

        self.auto_backup_exit = QCheckBox("程序退出时自动备份")
        self.auto_backup_exit.setChecked(True)
        backup_form.addRow(self.auto_backup_exit)

        # 手动备份按钮
        backup_btn_layout = QHBoxLayout()
        self.backup_now_btn = QPushButton("立即备份")
        self.backup_now_btn.setStyleSheet(
            "QPushButton { background-color: #c8783c; color: white; padding: 8px 16px; "
            "border-radius: 6px; font-weight: bold; border: none; }"
            "QPushButton:hover { background-color: #b06830; }"
        )
        self.backup_now_btn.clicked.connect(self._on_backup_now)
        backup_btn_layout.addWidget(self.backup_now_btn)

        self.restore_btn = QPushButton("恢复备份...")
        self.restore_btn.clicked.connect(self._on_restore_backup)
        backup_btn_layout.addWidget(self.restore_btn)

        backup_btn_layout.addStretch()
        backup_form.addRow(backup_btn_layout)

        # 最近备份时间
        self.last_backup_label = QLabel()
        self._update_backup_status()
        backup_form.addRow("最近备份:", self.last_backup_label)

        layout.addWidget(backup_group)

        # --- 默认设置组 ---
        pref_group, pref_form = _make_group("偏好设置")

        self.currency_combo = QComboBox()
        for curr in CURRENCIES:
            self.currency_combo.addItem(curr, curr)
        self.currency_combo.setCurrentText("CNY")
        pref_form.addRow("默认货币:", self.currency_combo)


        layout.addWidget(pref_group)

        # --- 数据导出组 ---
        export_group, export_form = _make_group("数据导出")

        export_btn_layout = QHBoxLayout()
        export_csv_btn = QPushButton("导出 CSV（所有表）")
        export_csv_btn.clicked.connect(self._on_export_csv)
        export_btn_layout.addWidget(export_csv_btn)

        export_excel_btn = QPushButton("导出 Excel")
        export_excel_btn.clicked.connect(self._on_export_excel)
        export_btn_layout.addWidget(export_excel_btn)

        export_btn_layout.addStretch()
        export_form.addRow(export_btn_layout)

        layout.addWidget(export_group)

        # --- 标签打印组 ---
        label_group, label_form = _make_group("标签打印")

        label_btn_layout = QHBoxLayout()
        batch_label_btn = QPushButton("🏷 批量生成库存标签")
        batch_label_btn.clicked.connect(self._on_batch_labels)
        label_btn_layout.addWidget(batch_label_btn)
        label_btn_layout.addStretch()
        label_form.addRow(label_btn_layout)

        label_hint = QLabel(
            "为所有库存 > 0 的胶卷生成打印标签（HTML 格式）。<br>"
            "标签包含品牌、型号、ISO、有效期、存放位置等信息。<br>"
            "在浏览器中打开后可直接打印到标签纸上。"
        )
        label_hint.setStyleSheet("font-size: 12px;")
        label_form.addRow(label_hint)

        layout.addWidget(label_group)

        # --- 数据导入组 ---
        import_group, import_form = _make_group("数据导入")

        import_btn_layout = QHBoxLayout()
        import_csv_btn = QPushButton("从 CSV 导入库存...")
        import_csv_btn.clicked.connect(self._on_import_csv)
        import_csv_btn.setStyleSheet(
            "QPushButton { background-color: #c8783c; color: white; padding: 8px 16px; "
            "border-radius: 6px; font-weight: bold; border: none; }"
            "QPushButton:hover { background-color: #b06830; }"
        )
        import_btn_layout.addWidget(import_csv_btn)

        download_template_btn = QPushButton("下载 CSV 模板")
        download_template_btn.clicked.connect(self._on_download_template)
        import_btn_layout.addWidget(download_template_btn)

        import_btn_layout.addStretch()
        import_form.addRow(import_btn_layout)

        import_hint = QLabel(
            "支持 CSV 和 UTF-8 编码文件。<br>"
            "列名支持中英文，必填字段：型号、画幅。<br>"
            "导入使用事务保护，失败自动回滚，不会破坏现有数据。"
        )
        import_hint.setStyleSheet("font-size: 12px;")
        import_form.addRow(import_hint)

        layout.addWidget(import_group)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _update_backup_status(self):
        """更新最近备份时间显示"""
        last_time = self._backup_service.get_last_backup_time()
        if last_time:
            self.last_backup_label.setText(last_time)
        else:
            self.last_backup_label.setText("尚未创建备份")

    def _on_backup_now(self):
        """手动备份"""
        result = self._backup_service.create_backup()
        if result:
            QMessageBox.information(self, "备份成功",
                f"数据库备份已保存到：\n{result}")
            self._update_backup_status()
        else:
            QMessageBox.warning(self, "备份失败",
                "无法创建数据库备份。\n请确认数据库文件存在且备份目录可写。")

    def _on_restore_backup(self):
        """从备份恢复"""
        backup_dir = get_backup_dir()
        backup_dir.mkdir(parents=True, exist_ok=True)

        path, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件",
            str(backup_dir),
            "SQLite 数据库 (*.db);;所有文件 (*.*)",
        )
        if not path:
            return

        reply = QMessageBox.warning(
            self, "确认恢复",
            f"确定要从以下备份恢复数据库吗？\n\n{path}\n\n"
            "恢复前会自动备份当前数据库。\n"
            "恢复后程序数据将被替换为备份时的状态。\n"
            "此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._backup_service.restore_backup(path):
            QMessageBox.information(self, "恢复成功",
                "数据库已从备份恢复。\n请重新启动程序以加载恢复的数据。")
        else:
            QMessageBox.critical(self, "恢复失败",
                "数据库恢复失败。\n请检查备份文件是否完整。")

    def _on_export_csv(self):
        """导出所有表为 CSV"""
        try:
            results = self._export_service.export_all_to_csv()
            success_count = sum(1 for p in results.values() if p is not None)
            QMessageBox.information(self, "CSV 导出完成",
                f"成功导出 {success_count}/{len(results)} 个文件。\n\n"
                f"导出目录：{get_export_dir()}\n\n"
                "CSV 文件使用 UTF-8 编码，可在 Excel 中直接打开。")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"CSV 导出时发生错误：{e}")

    def _on_export_excel(self):
        """导出 Excel"""
        try:
            result = self._export_service.export_to_excel()
            if result:
                QMessageBox.information(self, "Excel 导出完成",
                    f"数据已导出到：\n{result}")
            else:
                QMessageBox.critical(self, "导出失败",
                    "Excel 导出失败。\n请确认已安装 openpyxl 库。")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"Excel 导出时发生错误：{e}")

    # ============================================================
    # CSV 导入
    # ============================================================

    def _on_import_csv(self):
        """从 CSV 文件导入库存"""
        from app.services.import_service import preview_csv, import_inventory_from_csv
        from app.config import get_export_dir

        # 选择文件
        path, _ = QFileDialog.getOpenFileName(
            self, "选择要导入的 CSV 文件",
            str(get_export_dir()),
            "CSV 文件 (*.csv);;所有文件 (*.*)",
        )
        if not path:
            return

        # 预览 CSV 内容
        columns, preview_rows, warnings = preview_csv(path)

        # 构建预览信息
        preview_text = f"<b>文件：</b>{path}<br><br>"
        preview_text += f"<b>识别到的列：</b>{', '.join(columns[:10])}"
        if len(columns) > 10:
            preview_text += f" ... 等 {len(columns)} 列"
        preview_text += "<br><br>"

        if warnings:
            preview_text += f"<b>⚠ 警告：</b><br>" + "<br>".join(warnings) + "<br><br>"

        if preview_rows:
            preview_text += "<b>前 5 行预览：</b><br>"
            for i, row in enumerate(preview_rows, 1):
                model = row.get("model", "")
                fmt = row.get("film_format", "")
                brand = row.get("brand", "")
                qty = row.get("quantity_cache", "0")
                preview_text += f"  {i}. {brand} {model} ({fmt}) x{qty}<br>"
        else:
            preview_text += "<span style='color:red;'>文件中没有有效数据。</span>"

        # 确认导入
        reply = QMessageBox.question(
            self, "确认导入",
            preview_text + "<br><br>确定要导入此文件吗？<br>"
            "导入过程使用事务保护，失败会自动回滚。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # 执行导入
        try:
            result = import_inventory_from_csv(path)
            if result.all_success:
                QMessageBox.information(
                    self, "导入成功",
                    f"成功导入 {result.success_count} 条库存记录。\n\n"
                    "请前往「胶卷库存」页面查看。"
                )
            else:
                msg = f"成功导入 {result.success_count} 条，{result.error_count} 条失败。\n\n"
                if result.errors:
                    msg += "错误详情（最多显示前10条）：\n" + "\n".join(result.errors[:10])
                    if len(result.errors) > 10:
                        msg += f"\n... 还有 {len(result.errors) - 10} 条错误"
                QMessageBox.warning(self, "导入完成（有错误）", msg)
        except Exception as e:
            QMessageBox.critical(self, "导入失败",
                f"导入过程中发生错误：{e}\n\n数据已回滚，现有数据未受影响。")

    def _on_batch_labels(self):
        """批量生成库存标签"""
        try:
            from app.services.label_service import generate_batch_labels
            import webbrowser
            path = generate_batch_labels("inventory")
            if path:
                webbrowser.open(str(path))
                QMessageBox.information(self, "标签已生成",
                    f"标签文件已在浏览器中打开。\n\n文件位置：{path}")
            else:
                QMessageBox.information(self, "无库存", "当前没有库存 > 0 的胶卷可生成标签。")
        except Exception as e:
            QMessageBox.critical(self, "标签生成失败", f"无法生成标签：{e}")

    def _on_download_template(self):
        """生成并导出 CSV 模板"""
        import csv
        from app.config import get_export_dir

        get_export_dir().mkdir(parents=True, exist_ok=True)
        template_path = get_export_dir() / "库存导入模板.csv"

        # 模板列头（中英文对照）
        headers = [
            "品牌(brand)", "型号(model)*", "画幅(film_format)*", "色彩类型(film_type)",
            "标称ISO(box_iso)", "库存数量(quantity_cache)", "乳剂批次(batch_number)",
            "有效期(expiry_date)", "购买日期(purchase_date)", "购买渠道(purchase_source)",
            "单卷价格(unit_price)", "货币(currency)", "存放位置(storage_location)",
            "保存方式(storage_method)", "备注(notes)",
        ]

        try:
            with open(template_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                # 写入示例行
                writer.writerow([
                    "Kodak", "Portra 400", "135", "彩色负片",
                    "400", "5", "", "2027-06-30", "2026-07-01",
                    "淘宝", "65.00", "CNY", "冰箱", "冷藏", "示例数据，导入后可删除"
                ])

            QMessageBox.information(
                self, "模板已生成",
                f"CSV 导入模板已保存到：\n{template_path}\n\n"
                "模板包含：\n"
                "• 第一行：列头（中英文标注，* 为必填）\n"
                "• 第二行：示例数据\n\n"
                "修改后即可使用「从 CSV 导入库存」功能导入。\n"
                "列头支持中文或英文，必填字段为「型号」和「画幅」。"
            )
        except Exception as e:
            QMessageBox.critical(self, "生成失败", f"无法生成模板：{e}")

