"""
冲洗管理页面

显示已拍摄胶卷列表，支持记录冲洗信息。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QLabel, QDialog, QFormLayout, QComboBox, QDoubleSpinBox,
    QLineEdit, QTextEdit, QDialogButtonBox, QDateEdit,
)
from PySide6.QtCore import Qt, QDate

from app.services.film_roll_service import FilmRollService
from app.services.development_service import DevelopmentService
from app.ui.widgets.film_table import FilmTable
from app.constants import (
    FilmStatus, get_status_display, DEVELOPMENT_METHODS, PROCESS_TYPES,
    CURRENCIES,
)


class DevelopmentPage(QWidget):
    """冲洗管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._roll_service = FilmRollService()
        self._dev_service = DevelopmentService()
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        self.setStyleSheet("color: #2c1810;")
        layout = QVBoxLayout(self)

        # 标题
        title_layout = QHBoxLayout()
        dev_title = QLabel("<h2>冲洗管理</h2>")
        dev_title.setStyleSheet("color: #2c1810; background: transparent;")
        title_layout.addWidget(dev_title)
        title_layout.addStretch()

        # 筛选：只看待冲洗/已冲洗
        self._status_filter = QComboBox()
        self._status_filter.addItem("待冲洗和已冲洗", "")
        self._status_filter.addItem(
            get_status_display(FilmStatus.SHOT), FilmStatus.SHOT)
        self._status_filter.addItem(
            get_status_display(FilmStatus.SENT_FOR_DEVELOPMENT), FilmStatus.SENT_FOR_DEVELOPMENT)
        self._status_filter.addItem(
            get_status_display(FilmStatus.DEVELOPED), FilmStatus.DEVELOPED)
        self._status_filter.currentIndexChanged.connect(self.refresh_data)
        filter_lbl = QLabel("筛选:")
        filter_lbl.setStyleSheet("color: #2c1810; background: transparent;")
        title_layout.addWidget(filter_lbl)
        title_layout.addWidget(self._status_filter)

        layout.addLayout(title_layout)

        # 表格
        self.table = FilmTable()
        self.table.set_columns([
            ("roll_number", "胶卷编号"),
            ("brand", "品牌"),
            ("model", "型号"),
            ("film_format", "画幅"),
            ("box_iso", "ISO"),
            ("camera", "相机"),
            ("status", "状态"),
            ("finish_date", "完成日期"),
        ])
        self.table.row_double_clicked.connect(self._on_open_dev_dialog)
        layout.addWidget(self.table)

        # 底部
        btn_layout = QHBoxLayout()
        self.dev_btn = QPushButton("填写 / 编辑冲洗信息")
        self.dev_btn.clicked.connect(self._on_edit_dev)
        self.dev_btn.setEnabled(False)
        btn_layout.addWidget(self.dev_btn)
        btn_layout.addStretch()
        self.stats_label = QLabel()
        btn_layout.addWidget(self.stats_label)
        layout.addLayout(btn_layout)

        self.table.itemSelectionChanged.connect(
            lambda: self.dev_btn.setEnabled(self.table.get_selected_row() is not None))

    def refresh_data(self):
        """刷新数据：显示已拍摄待冲洗和已冲洗的胶卷"""
        status = self._status_filter.currentData()
        if status:
            data = self._roll_service.list_rolls(status=status)
        else:
            # 显示 SHOT, SENT_FOR_DEVELOPMENT, DEVELOPED 状态的
            from app.database.connection import get_db
            db = get_db()
            with db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM film_rolls WHERE status IN (?, ?, ?) "
                    "AND deleted_at IS NULL ORDER BY updated_at DESC;",
                    (FilmStatus.SHOT, FilmStatus.SENT_FOR_DEVELOPMENT, FilmStatus.DEVELOPED),
                )
                data = [dict(row) for row in cursor.fetchall()]

        for row in data:
            row["status"] = get_status_display(row.get("status", ""))
            row["box_iso"] = f"{row.get('box_iso', '')}" if row.get("box_iso") else ""

        self.table.load_data(data)
        self.stats_label.setText(f"共 {len(data)} 条记录")

    def _on_open_dev_dialog(self, row: int, row_data: dict):
        self._open_dev_dialog(row_data)

    def _on_edit_dev(self):
        result = self.table.get_selected_row()
        if result is None:
            return
        self._open_dev_dialog(result[1])

    def _open_dev_dialog(self, row_data: dict):
        """打开冲洗信息对话框"""
        roll_id = row_data["id"]
        roll_number = row_data.get("roll_number", "")

        # 获取已有的冲洗记录
        existing = self._dev_service.get_by_roll(roll_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"冲洗信息 - {roll_number}")
        dialog.setMinimumWidth(450)
        dialog.setModal(True)

        dlg_layout = QVBoxLayout(dialog)
        form = QFormLayout()

        method_combo = QComboBox()
        method_combo.addItem("-- 请选择 --", "")
        for m in DEVELOPMENT_METHODS:
            method_combo.addItem(m, m)
        form.addRow("冲洗方式:", method_combo)

        process_combo = QComboBox()
        process_combo.addItem("-- 请选择 --", "")
        for p in PROCESS_TYPES:
            process_combo.addItem(p, p)
        form.addRow("冲洗工艺:", process_combo)

        lab_input = QLineEdit()
        lab_input.setPlaceholderText("冲洗店名称或实验室")
        form.addRow("冲洗地点:", lab_input)

        sent_date = QDateEdit()
        sent_date.setCalendarPopup(True)
        sent_date.setDate(QDate.currentDate())
        form.addRow("送冲日期:", sent_date)

        completed_date = QDateEdit()
        completed_date.setCalendarPopup(True)
        completed_date.setDate(QDate.currentDate())
        form.addRow("完成日期:", completed_date)

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
        form.addRow("冲洗费用:", cost_layout)

        push_spin = QDoubleSpinBox()
        push_spin.setRange(-5, 5)
        push_spin.setSingleStep(0.5)
        push_spin.setSpecialValueText("无")
        push_spin.setSuffix(" 档")
        form.addRow("迫冲/拉冲:", push_spin)

        chem_input = QLineEdit()
        chem_input.setPlaceholderText("例如 D-76 1:1")
        form.addRow("药水/配方:", chem_input)

        notes_edit = QTextEdit()
        notes_edit.setMaximumHeight(60)
        form.addRow("备注:", notes_edit)

        dlg_layout.addLayout(form)

        # 加载已有数据
        if existing:
            idx = method_combo.findData(existing.get("development_method", ""))
            if idx >= 0:
                method_combo.setCurrentIndex(idx)
            idx = process_combo.findData(existing.get("process_type", ""))
            if idx >= 0:
                process_combo.setCurrentIndex(idx)
            lab_input.setText(existing.get("lab_name", ""))
            cost_spin.setValue(existing.get("cost", 0) or 0)
            idx = currency_combo.findData(existing.get("currency", "CNY"))
            if idx >= 0:
                currency_combo.setCurrentIndex(idx)
            push_spin.setValue(existing.get("push_pull_stops", 0) or 0)
            chem_input.setText(existing.get("chemistry", ""))
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

        # 保存数据
        dev_data = {
            "development_method": method_combo.currentData() or "",
            "process_type": process_combo.currentData() or "",
            "lab_name": lab_input.text().strip(),
            "sent_date": sent_date.date().toString("yyyy-MM-dd"),
            "completed_date": completed_date.date().toString("yyyy-MM-dd"),
            "cost": cost_spin.value(),
            "currency": currency_combo.currentData() or "CNY",
            "push_pull_stops": push_spin.value(),
            "chemistry": chem_input.text().strip(),
            "notes": notes_edit.toPlainText().strip(),
        }

        try:
            self._dev_service.save(roll_id, dev_data)
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存冲洗信息时发生错误：{e}")
