"""
扫描管理页面

显示已冲洗胶卷列表，支持记录扫描信息。
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QLabel, QDialog, QFormLayout, QComboBox, QDoubleSpinBox,
    QLineEdit, QTextEdit, QDialogButtonBox, QDateEdit, QFileDialog,
)
from PySide6.QtCore import Qt, QDate

from app.services.film_roll_service import FilmRollService
from app.services.scan_service import ScanService
from app.ui.widgets.film_table import FilmTable
from app.constants import (
    FilmStatus, get_status_display, SCAN_METHODS, FILE_FORMATS, CURRENCIES,
)
from app.utils.file_utils import open_folder


class ScanPage(QWidget):
    """扫描管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._roll_service = FilmRollService()
        self._scan_service = ScanService()
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        self.setStyleSheet("color: #2c1810;")
        layout = QVBoxLayout(self)
        title = QLabel("<h2>扫描管理</h2>")
        title.setStyleSheet("color: #2c1810; background: transparent;")
        layout.addWidget(title)

        self.table = FilmTable()
        self.table.set_columns([
            ("roll_number", "胶卷编号"),
            ("brand", "品牌"),
            ("model", "型号"),
            ("film_format", "画幅"),
            ("camera", "相机"),
            ("status", "状态"),
            ("finish_date", "完成日期"),
        ])
        self.table.row_double_clicked.connect(self._on_open_scan_dialog)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton("填写 / 编辑扫描信息")
        self.scan_btn.clicked.connect(self._on_edit_scan)
        btn_layout.addWidget(self.scan_btn)

        self.open_folder_btn = QPushButton("📂 打开扫描文件夹")
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        self.open_folder_btn.setStyleSheet(
            "QPushButton { color: #1565C0; }"
        )
        btn_layout.addWidget(self.open_folder_btn)

        btn_layout.addStretch()
        self.stats_label = QLabel()
        btn_layout.addWidget(self.stats_label)
        layout.addLayout(btn_layout)

    def refresh_data(self):
        """显示等待扫描和已扫描的胶卷"""
        from app.database.connection import get_db
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM film_rolls WHERE status IN (?, ?, ?, ?) "
                "AND deleted_at IS NULL ORDER BY updated_at DESC;",
                (FilmStatus.DEVELOPED, FilmStatus.WAITING_FOR_SCAN,
                 FilmStatus.SCANNING, FilmStatus.SCANNED),
            )
            data = [dict(row) for row in cursor.fetchall()]

        for row in data:
            row["status"] = get_status_display(row.get("status", ""))
        self.table.load_data(data)
        self.stats_label.setText(f"共 {len(data)} 条记录")

    def _on_open_folder(self):
        """打开选中记录的扫描文件夹

        如果没有扫描记录或文件夹路径，引导用户创建。
        打开失败时给出明确提示。
        """
        import os, sys, subprocess
        result = self.table.get_selected_row()
        if result is None:
            return
        row_data = result[1]
        roll_id = row_data["id"]
        roll_number = row_data.get("roll_number", "")
        scan_record = self._scan_service.get_by_roll(roll_id)

        # 没有扫描记录 → 弹出编辑对话框让用户填写
        if not scan_record:
            reply = QMessageBox.question(
                self, "暂无扫描记录",
                f"胶卷「{roll_number}」尚未填写扫描信息。\n\n是否现在填写？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_scan_dialog(row_data)
            return

        folder_path = scan_record.get("local_path", "").strip()

        # 有扫描记录但没有文件夹路径 → 弹出编辑对话框
        if not folder_path:
            reply = QMessageBox.question(
                self, "缺少文件夹路径",
                f"胶卷「{roll_number}」的扫描记录中未设置文件夹路径。\n\n是否现在设置？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_scan_dialog(row_data)
            return

        # 路径存在 → 直接打开
        from pathlib import Path
        path = Path(folder_path)
        if path.exists():
            try:
                if sys.platform == "win32":
                    os.startfile(str(path))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(path)], check=False)
                else:
                    subprocess.run(["xdg-open", str(path)], check=False)
                # 不需要弹窗，直接打开文件夹就是最好的反馈
            except Exception as e:
                QMessageBox.warning(
                    self, "打开失败",
                    f"无法打开文件夹：\n{folder_path}\n\n错误：{e}"
                )
        else:
            # 路径失效 → 提示并让用户重新选择
            reply = QMessageBox.warning(
                self, "路径不可访问",
                f"扫描文件夹路径已失效：\n{folder_path}\n\n"
                "文件夹可能已被移动、重命名或删除。\n\n是否重新选择文件夹？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_scan_dialog(row_data)

    def _on_open_scan_dialog(self, row: int, row_data: dict):
        self._open_scan_dialog(row_data)

    def _on_edit_scan(self):
        result = self.table.get_selected_row()
        if result is None:
            QMessageBox.information(self, "提示",
                "请先在「拍摄记录」页面添加记录，并将状态推进到「已冲洗」或之后。\n\n"
                "扫描管理页面只显示已完成冲洗的胶卷。")
            return
        self._open_scan_dialog(result[1])

    def _open_scan_dialog(self, row_data: dict):
        roll_id = row_data["id"]
        roll_number = row_data.get("roll_number", "")
        existing = self._scan_service.get_by_roll(roll_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"扫描信息 - {roll_number}")
        dialog.setMinimumWidth(450)
        dialog.setModal(True)
        dlg_layout = QVBoxLayout(dialog)
        form = QFormLayout()

        method_combo = QComboBox()
        method_combo.addItem("-- 请选择 --", "")
        for m in SCAN_METHODS:
            method_combo.addItem(m, m)
        form.addRow("扫描方式:", method_combo)

        scanner_input = QLineEdit()
        scanner_input.setPlaceholderText("例如 Epson V600")
        form.addRow("扫描设备:", scanner_input)

        software_input = QLineEdit()
        software_input.setPlaceholderText("例如 SilverFast")
        form.addRow("扫描软件:", software_input)

        scan_date = QDateEdit()
        scan_date.setCalendarPopup(True)
        scan_date.setDate(QDate.currentDate())
        form.addRow("扫描日期:", scan_date)

        resolution_input = QLineEdit()
        resolution_input.setPlaceholderText("例如 2400 dpi")
        form.addRow("扫描分辨率:", resolution_input)

        format_combo = QComboBox()
        format_combo.addItem("-- 请选择 --", "")
        for f in FILE_FORMATS:
            format_combo.addItem(f, f)
        form.addRow("文件格式:", format_combo)

        # 文件夹路径选择
        path_layout = QHBoxLayout()
        folder_input = QLineEdit()
        folder_input.setPlaceholderText("扫描文件所在文件夹")
        path_layout.addWidget(folder_input)
        browse_btn = QPushButton("选择...")
        browse_btn.clicked.connect(
            lambda: folder_input.setText(
                QFileDialog.getExistingDirectory(dialog, "选择扫描文件夹")))
        path_layout.addWidget(browse_btn)
        form.addRow("文件夹路径:", path_layout)

        cost_layout = QHBoxLayout()
        cost_spin = QDoubleSpinBox()
        cost_spin.setRange(0, 99999.99)
        cost_spin.setDecimals(2)
        cost_layout.addWidget(cost_spin)
        currency_combo = QComboBox()
        for c in CURRENCIES:
            currency_combo.addItem(c, c)
        currency_combo.setCurrentText("CNY")
        cost_layout.addWidget(currency_combo)
        form.addRow("扫描费用:", cost_layout)

        notes_edit = QTextEdit()
        notes_edit.setMaximumHeight(60)
        form.addRow("备注:", notes_edit)

        dlg_layout.addLayout(form)

        # 加载已有数据
        if existing:
            idx = method_combo.findData(existing.get("scan_method", ""))
            if idx >= 0:
                method_combo.setCurrentIndex(idx)
            scanner_input.setText(existing.get("scanner", ""))
            software_input.setText(existing.get("software", ""))
            resolution_input.setText(existing.get("resolution", ""))
            idx = format_combo.findData(existing.get("file_format", ""))
            if idx >= 0:
                format_combo.setCurrentIndex(idx)
            folder_input.setText(existing.get("local_path", ""))
            cost_spin.setValue(existing.get("cost", 0) or 0)
            idx = currency_combo.findData(existing.get("currency", "CNY"))
            if idx >= 0:
                currency_combo.setCurrentIndex(idx)
            notes_edit.setText(existing.get("notes", ""))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlg_layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        scan_data = {
            "scan_method": method_combo.currentData() or "",
            "scanner": scanner_input.text().strip(),
            "software": software_input.text().strip(),
            "scan_date": scan_date.date().toString("yyyy-MM-dd"),
            "resolution": resolution_input.text().strip(),
            "file_format": format_combo.currentData() or "",
            "local_path": folder_input.text().strip(),
            "cost": cost_spin.value(),
            "currency": currency_combo.currentData() or "CNY",
            "notes": notes_edit.toPlainText().strip(),
        }

        try:
            self._scan_service.save(roll_id, scan_data)
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存扫描信息时发生错误：{e}")
