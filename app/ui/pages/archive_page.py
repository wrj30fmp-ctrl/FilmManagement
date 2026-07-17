"""
归档管理页面

显示已扫描胶卷列表，支持记录归档信息。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QLabel, QDialog, QFormLayout, QLineEdit, QCheckBox,
    QTextEdit, QDialogButtonBox, QDateEdit, QFileDialog,
)
from PySide6.QtCore import Qt, QDate

from app.services.film_roll_service import FilmRollService
from app.services.archive_service import ArchiveService
from app.ui.widgets.film_table import FilmTable
from app.constants import FilmStatus, get_status_display
from app.utils.file_utils import open_folder


class ArchivePage(QWidget):
    """归档管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._roll_service = FilmRollService()
        self._archive_service = ArchiveService()
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        self.setStyleSheet("color: #2c1810;")
        layout = QVBoxLayout(self)
        title = QLabel("<h2>归档管理</h2>")
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
        self.table.row_double_clicked.connect(self._on_open_archive_dialog)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.archive_btn = QPushButton("填写 / 编辑归档信息")
        self.archive_btn.clicked.connect(self._on_edit_archive)
        btn_layout.addWidget(self.archive_btn)
        btn_layout.addStretch()
        self.stats_label = QLabel()
        btn_layout.addWidget(self.stats_label)
        layout.addLayout(btn_layout)

    def refresh_data(self):
        """显示已扫描和已归档的胶卷"""
        from app.database.connection import get_db
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM film_rolls WHERE status IN (?, ?) "
                "AND deleted_at IS NULL ORDER BY updated_at DESC;",
                (FilmStatus.SCANNED, FilmStatus.ARCHIVED),
            )
            data = [dict(row) for row in cursor.fetchall()]

        for row in data:
            row["status"] = get_status_display(row.get("status", ""))
        self.table.load_data(data)
        self.stats_label.setText(f"共 {len(data)} 条记录")

    def _on_open_archive_dialog(self, row: int, row_data: dict):
        self._open_archive_dialog(row_data)

    def _on_edit_archive(self):
        result = self.table.get_selected_row()
        if result is None:
            QMessageBox.information(self, "提示",
                "请先在「拍摄记录」页面添加记录，并将状态推进到「已扫描」或之后。\n\n"
                "归档管理页面只显示已完成扫描的胶卷。")
            return
        self._open_archive_dialog(result[1])

    def _open_archive_dialog(self, row_data: dict):
        roll_id = row_data["id"]
        roll_number = row_data.get("roll_number", "")
        existing = self._archive_service.get_by_roll(roll_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"归档信息 - {roll_number}")
        dialog.setMinimumWidth(450)
        dialog.setModal(True)
        dlg_layout = QVBoxLayout(dialog)
        form = QFormLayout()

        neg_location = QLineEdit()
        neg_location.setPlaceholderText("例如 底片册A、冷藏箱")
        form.addRow("底片存放位置:", neg_location)

        binder_input = QLineEdit()
        binder_input.setPlaceholderText("例如 A")
        form.addRow("底片册编号:", binder_input)

        page_input = QLineEdit()
        page_input.setPlaceholderText("例如 12")
        form.addRow("底片页编号:", page_input)

        # 文件夹路径
        path_layout = QHBoxLayout()
        folder_input = QLineEdit()
        folder_input.setPlaceholderText("归档文件夹路径")
        path_layout.addWidget(folder_input)
        browse_btn = QPushButton("选择...")
        browse_btn.clicked.connect(
            lambda: folder_input.setText(
                QFileDialog.getExistingDirectory(dialog, "选择归档文件夹")))
        path_layout.addWidget(browse_btn)
        form.addRow("文件夹路径:", path_layout)

        cloud_check = QCheckBox("已完成云端备份")
        form.addRow("", cloud_check)

        offsite_check = QCheckBox("已完成异地备份")
        form.addRow("", offsite_check)

        archive_date = QDateEdit()
        archive_date.setCalendarPopup(True)
        archive_date.setDate(QDate.currentDate())
        form.addRow("归档日期:", archive_date)

        notes_edit = QTextEdit()
        notes_edit.setMaximumHeight(60)
        form.addRow("归档备注:", notes_edit)

        dlg_layout.addLayout(form)

        # 加载已有数据
        if existing:
            neg_location.setText(existing.get("negative_location", ""))
            binder_input.setText(existing.get("binder_number", ""))
            page_input.setText(existing.get("page_number", ""))
            folder_input.setText(existing.get("local_path", ""))
            cloud_check.setChecked(bool(existing.get("cloud_backup", 0)))
            offsite_check.setChecked(bool(existing.get("offsite_backup", 0)))
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

        archive_data = {
            "negative_location": neg_location.text().strip(),
            "binder_number": binder_input.text().strip(),
            "page_number": page_input.text().strip(),
            "local_path": folder_input.text().strip(),
            "cloud_backup": cloud_check.isChecked(),
            "offsite_backup": offsite_check.isChecked(),
            "archive_date": archive_date.date().toString("yyyy-MM-dd"),
            "notes": notes_edit.toPlainText().strip(),
        }

        try:
            self._archive_service.save(roll_id, archive_data)
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存归档信息时发生错误：{e}")
