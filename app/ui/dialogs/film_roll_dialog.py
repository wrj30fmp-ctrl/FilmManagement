"""
拍摄记录新增/编辑对话框

支持手动创建拍摄记录和从库存创建拍摄记录。
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QTextEdit, QDialogButtonBox, QVBoxLayout,
    QLabel, QMessageBox, QDateEdit, QHBoxLayout, QPushButton,
)
from PySide6.QtCore import Qt, QDate

from app.constants import (
    FilmStatus, get_status_display, FILM_FORMATS, FILM_TYPES,
)


class FilmRollDialog(QDialog):
    """拍摄记录新增/编辑对话框"""

    def __init__(self, parent=None, record: dict | None = None,
                 inventory_data: dict | None = None):
        """
        Args:
            parent: 父窗口
            record: 编辑时传入已有记录，新增时为 None
            inventory_data: 从库存创建时传入的库存数据
        """
        super().__init__(parent)
        self._record = record
        self._inventory_data = inventory_data
        self._is_edit = record is not None
        self._from_inventory = inventory_data is not None

        if self._is_edit:
            self.setWindowTitle("编辑拍摄记录")
        elif self._from_inventory:
            self.setWindowTitle("从库存开始拍摄")
        else:
            self.setWindowTitle("新增拍摄记录")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._setup_ui()

        if self._from_inventory:
            self._load_inventory_data()
        elif self._is_edit:
            self._load_record()

    def _setup_ui(self):
        """构建表单"""
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # --- 基本信息 ---
        # 胶卷编号
        self.roll_number_input = QLineEdit()
        self.roll_number_input.setPlaceholderText("留空则自动生成，例如 2026-07-001")
        form.addRow("胶卷编号:", self.roll_number_input)

        # 品牌
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("例如 Kodak, Fujifilm")
        form.addRow("品牌:", self.brand_input)

        # 胶卷型号（必填）
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("例如 Portra 400（必填）")
        form.addRow(self._required_label("胶卷型号:"), self.model_input)

        # 画幅（必填）
        self.format_combo = QComboBox()
        self.format_combo.addItem("-- 请选择 --", "")
        for fmt in FILM_FORMATS:
            self.format_combo.addItem(fmt, fmt)
        form.addRow(self._required_label("画幅:"), self.format_combo)

        # 色彩类型
        self.type_combo = QComboBox()
        self.type_combo.addItem("-- 请选择 --", "")
        for ft in FILM_TYPES:
            self.type_combo.addItem(ft, ft)
        form.addRow("色彩类型:", self.type_combo)

        # ISO
        iso_layout = QHBoxLayout()
        self.box_iso_spin = QSpinBox()
        self.box_iso_spin.setRange(0, 51200)
        self.box_iso_spin.setSpecialValueText("--")
        self.box_iso_spin.setPrefix("标称: ")
        iso_layout.addWidget(self.box_iso_spin)

        self.exposure_iso_spin = QSpinBox()
        self.exposure_iso_spin.setRange(0, 51200)
        self.exposure_iso_spin.setSpecialValueText("--")
        self.exposure_iso_spin.setPrefix("实际: ")
        iso_layout.addWidget(self.exposure_iso_spin)
        form.addRow("ISO:", iso_layout)

        # --- 拍摄信息 ---
        # 相机
        self.camera_input = QLineEdit()
        self.camera_input.setPlaceholderText("例如 Canon AE-1")
        form.addRow("相机:", self.camera_input)

        # 镜头
        self.lens_input = QLineEdit()
        self.lens_input.setPlaceholderText("例如 50mm f/1.8")
        form.addRow("镜头:", self.lens_input)

        # EXIF 读取按钮
        exif_layout = QHBoxLayout()
        self.exif_btn = QPushButton("📷 从照片读取 EXIF")
        self.exif_btn.setStyleSheet(
            "QPushButton { background-color: #8e6ab3; color: white; padding: 6px 14px; "
            "border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #7a5a9e; }"
        )
        self.exif_btn.clicked.connect(self._on_read_exif)
        exif_layout.addWidget(self.exif_btn)
        exif_layout.addStretch()
        form.addRow("", exif_layout)

        # 装卷日期
        self.load_date = QDateEdit()
        self.load_date.setCalendarPopup(True)
        self.load_date.setDate(QDate.currentDate())
        form.addRow("装卷日期:", self.load_date)

        # 拍摄完成日期
        self.finish_date = QDateEdit()
        self.finish_date.setCalendarPopup(True)
        self.finish_date.setSpecialValueText("--")
        form.addRow("完成日期:", self.finish_date)

        # 拍摄地点
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("例如 北京、东京")
        form.addRow("拍摄地点:", self.location_input)

        # 拍摄主题
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("例如 街拍、人像、风光")
        form.addRow("拍摄主题:", self.subject_input)

        # 迫冲/拉冲
        self.push_pull_spin = QDoubleSpinBox()
        self.push_pull_spin.setRange(-5.0, 5.0)
        self.push_pull_spin.setSingleStep(0.5)
        self.push_pull_spin.setSpecialValueText("无")
        self.push_pull_spin.setSuffix(" 档")
        form.addRow("迫冲/拉冲:", self.push_pull_spin)

        # --- 照片 ---
        from app.ui.widgets.photo_thumbnail import PhotoThumbnail
        self.photo_thumb = PhotoThumbnail(size=120)
        form.addRow("样片照片:", self.photo_thumb)

        # --- 备注 ---
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("其他备注信息...")
        form.addRow("备注:", self.notes_edit)

        layout.addLayout(form)

        # 必填说明
        hint = QLabel("* 为必填项")
        hint.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _required_label(self, text: str) -> QLabel:
        return QLabel(f"<span style='color: red;'>*</span> {text}")

    def _validate_and_accept(self):
        """验证输入"""
        errors = []
        if not self.model_input.text().strip():
            errors.append("「胶卷型号」为必填项，请填写后重试。")
        if not self.format_combo.currentData():
            errors.append("「画幅」为必填项，请选择后重试。")

        if errors:
            QMessageBox.warning(self, "输入校验失败", "\n".join(errors))
            return
        self.accept()

    def _load_inventory_data(self):
        """从库存数据预填表单"""
        inv = self._inventory_data
        self.brand_input.setText(inv.get("brand", ""))
        self.model_input.setText(inv.get("model", ""))

        idx = self.format_combo.findData(inv.get("film_format", ""))
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)

        idx = self.type_combo.findData(inv.get("film_type", ""))
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        iso = inv.get("box_iso", 0)
        if iso:
            self.box_iso_spin.setValue(iso)

    def _load_record(self):
        """加载已有记录到表单"""
        r = self._record
        self.roll_number_input.setText(r.get("roll_number", ""))
        self.brand_input.setText(r.get("brand", ""))
        self.model_input.setText(r.get("model", ""))

        idx = self.format_combo.findData(r.get("film_format", ""))
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)

        idx = self.type_combo.findData(r.get("film_type", ""))
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        self.box_iso_spin.setValue(r.get("box_iso", 0) or 0)
        self.exposure_iso_spin.setValue(r.get("exposure_iso", 0) or 0)
        self.camera_input.setText(r.get("camera", ""))
        self.lens_input.setText(r.get("lens", ""))

        load_date = r.get("load_date", "")
        if load_date:
            self.load_date.setDate(QDate.fromString(load_date, "yyyy-MM-dd"))

        finish_date = r.get("finish_date", "")
        if finish_date:
            self.finish_date.setDate(QDate.fromString(finish_date, "yyyy-MM-dd"))

        self.location_input.setText(r.get("location", ""))
        self.subject_input.setText(r.get("subject", ""))
        self.push_pull_spin.setValue(r.get("push_pull", 0) or 0)
        self.notes_edit.setText(r.get("notes", ""))
        # 加载照片
        photo = r.get("photo_path", "")
        if photo:
            self.photo_thumb.photo_path = photo

    def get_form_data(self) -> dict:
        """获取表单数据"""
        load_date = self.load_date.date()
        finish_date = self.finish_date.date()

        return {
            "roll_number": self.roll_number_input.text().strip(),
            "brand": self.brand_input.text().strip(),
            "model": self.model_input.text().strip(),
            "film_format": self.format_combo.currentData() or "",
            "film_type": self.type_combo.currentData() or "",
            "box_iso": self.box_iso_spin.value() or 0,
            "exposure_iso": self.exposure_iso_spin.value() or 0,
            "camera": self.camera_input.text().strip(),
            "lens": self.lens_input.text().strip(),
            "load_date": load_date.toString("yyyy-MM-dd") if load_date.isValid() and load_date > QDate(2000, 1, 1) else "",
            "finish_date": finish_date.toString("yyyy-MM-dd") if finish_date.isValid() and finish_date > QDate(2000, 1, 1) else "",
            "location": self.location_input.text().strip(),
            "subject": self.subject_input.text().strip(),
            "push_pull": self.push_pull_spin.value(),
            "notes": self.notes_edit.toPlainText().strip(),
            "photo_path": self.photo_thumb.photo_path,
        }

    def _on_read_exif(self):
        """从照片文件读取 EXIF 信息并自动填充表单"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from app.utils.exif_utils import read_exif
        import os

        # 先尝试从扫描记录获取文件夹路径
        default_dir = ""
        if self._record:
            roll_id = self._record.get("id", "")
            if roll_id:
                from app.services.scan_service import ScanService
                scan_svc = ScanService()
                scan_rec = scan_svc.get_by_roll(roll_id)
                if scan_rec and scan_rec.get("local_path"):
                    default_dir = scan_rec["local_path"]

        path, _ = QFileDialog.getOpenFileName(
            self, "选择照片文件读取 EXIF",
            default_dir if default_dir else os.path.expanduser("~"),
            "图片文件 (*.jpg *.jpeg *.tiff *.tif *.png);;所有文件 (*.*)",
        )
        if not path:
            return

        exif = read_exif(path)
        if not exif or not exif.get("camera"):
            QMessageBox.information(
                self, "无 EXIF 数据",
                "所选文件中未找到 EXIF 拍摄信息。\n\n"
                "这可能是因为：\n"
                "• 文件不是相机直出的 JPEG/TIFF\n"
                "• EXIF 数据已被处理软件移除\n"
                "• 文件格式不支持 EXIF"
            )
            return

        # 自动填充表单
        if exif.get("camera"):
            self.camera_input.setText(exif["camera"])
        if exif.get("lens"):
            self.lens_input.setText(exif["lens"])
        if exif.get("exposure_iso"):
            self.exposure_iso_spin.setValue(exif["exposure_iso"])
        if exif.get("date_taken"):
            from PySide6.QtCore import QDate
            try:
                dt = exif["date_taken"].replace("-", "-")
                self.load_date.setDate(QDate.fromString(dt, "yyyy-MM-dd"))
            except Exception:
                pass

        # 构建反馈信息
        filled = []
        for k, v in exif.items():
            if k in ("camera", "lens", "exposure_iso", "aperture",
                      "shutter_speed", "focal_length", "date_taken") and v:
                label = {
                    "camera": "相机", "lens": "镜头",
                    "exposure_iso": "ISO", "aperture": "光圈",
                    "shutter_speed": "快门", "focal_length": "焦距",
                    "date_taken": "日期",
                }.get(k, k)
                filled.append(f"{label}: {v}")

        QMessageBox.information(
            self, "EXIF 读取成功",
            f"已从照片中读取以下信息并自动填充：\n\n" +
            "\n".join(filled)
        )
