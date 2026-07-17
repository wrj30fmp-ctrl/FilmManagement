"""
库存新增/编辑对话框

提供库存记录的表单输入界面。
必填字段有红色星号标记，输入不合法时在保存前提示。
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QTextEdit, QDialogButtonBox, QVBoxLayout,
    QLabel, QMessageBox, QDateEdit, QHBoxLayout,
)
from PySide6.QtCore import Qt, QDate

from app.constants import (
    FILM_FORMATS, FILM_TYPES, STORAGE_METHODS, CURRENCIES, BRANDS,
)
from app.utils.validation import (
    validate_required, validate_number,
    validate_non_negative_integer, validate_iso,
)


class InventoryDialog(QDialog):
    """库存新增/编辑对话框"""

    def __init__(self, parent=None, record: dict | None = None):
        """
        Args:
            parent: 父窗口
            record: 编辑时传入已有记录，新增时为 None
        """
        super().__init__(parent)
        self._record = record
        self._is_edit = record is not None
        self.setWindowTitle("编辑库存记录" if self._is_edit else "新增库存记录")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        if self._is_edit:
            self._load_record()

    def _setup_ui(self):
        """构建表单界面"""
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # --- 必填字段 ---
        # 品牌（可编辑下拉框）
        self.brand_combo = QComboBox()
        self.brand_combo.setEditable(True)
        self.brand_combo.addItem("", "")
        for brand in BRANDS:
            self.brand_combo.addItem(brand, brand)
        form.addRow("品牌:", self.brand_combo)

        # 胶卷型号（必填）
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("例如 Portra 400, HP5 Plus（必填）")
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

        # 标称 ISO
        self.iso_spin = QSpinBox()
        self.iso_spin.setRange(0, 51200)
        self.iso_spin.setSpecialValueText("--")
        self.iso_spin.setSuffix(" ISO")
        form.addRow("标称 ISO:", self.iso_spin)

        # --- 数量和价格 ---
        # 库存数量（必填）
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 9999)
        self.quantity_spin.setValue(1)
        form.addRow(self._required_label("库存数量:"), self.quantity_spin)

        # 价格行：价格 + 货币
        price_layout = QHBoxLayout()
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("¥ ")
        price_layout.addWidget(self.price_spin)

        self.currency_combo = QComboBox()
        for curr in CURRENCIES:
            self.currency_combo.addItem(curr, curr)
        self.currency_combo.setCurrentText("CNY")
        price_layout.addWidget(self.currency_combo)
        form.addRow("单卷价格:", price_layout)

        # --- 批次和日期 ---
        # 乳剂批次
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("例如 0123-004")
        form.addRow("乳剂批次:", self.batch_input)

        # 有效期
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setSpecialValueText("--")
        self.expiry_date.setDate(QDate.currentDate().addYears(2))
        form.addRow("有效期:", self.expiry_date)

        # 购买日期
        self.purchase_date = QDateEdit()
        self.purchase_date.setCalendarPopup(True)
        self.purchase_date.setSpecialValueText("--")
        self.purchase_date.setDate(QDate.currentDate())
        form.addRow("购买日期:", self.purchase_date)

        # 购买渠道
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("例如 淘宝、线下店")
        form.addRow("购买渠道:", self.source_input)

        # --- 存放信息 ---
        # 存放位置
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("例如 书桌抽屉、冰箱")
        form.addRow("存放位置:", self.location_input)

        # 保存方式
        self.storage_combo = QComboBox()
        self.storage_combo.addItem("-- 请选择 --", "")
        for sm in STORAGE_METHODS:
            self.storage_combo.addItem(sm, sm)
        form.addRow("保存方式:", self.storage_combo)

        # --- 照片 ---
        from app.ui.widgets.photo_thumbnail import PhotoThumbnail
        self.photo_thumb = PhotoThumbnail(size=120)
        form.addRow("胶卷盒照片:", self.photo_thumb)

        # --- 备注 ---
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("其他备注信息...")
        form.addRow("备注:", self.notes_edit)

        layout.addLayout(form)

        # --- 必填说明 ---
        hint = QLabel("* 为必填项")
        hint.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(hint)

        # --- 按钮 ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _required_label(self, text: str) -> QLabel:
        """创建带红色星号的必填标签"""
        label = QLabel(f"<span style='color: red;'>*</span> {text}")
        return label

    def _validate_and_accept(self):
        """验证输入并保存"""
        errors = []

        # 必填校验
        model = self.model_input.text().strip()
        valid, msg = validate_required(model, "胶卷型号")
        if not valid:
            errors.append(msg)

        film_format = self.format_combo.currentData()
        valid, msg = validate_required(film_format or "", "画幅")
        if not valid:
            errors.append(msg)

        # 数量校验
        quantity = self.quantity_spin.value()
        valid, msg = validate_non_negative_integer(quantity, "库存数量")
        if not valid:
            errors.append(msg)

        # 价格校验（非必填，但如果填了必须是数字）
        price = self.price_spin.value()
        valid, msg = validate_number(str(price) if price > 0 else "", "单卷价格")
        if not valid:
            errors.append(msg)

        # ISO 校验
        iso = self.iso_spin.value()
        valid, msg = validate_iso(iso if iso > 0 else "", "标称 ISO")
        if not valid:
            errors.append(msg)

        if errors:
            QMessageBox.warning(self, "输入校验失败", "\n".join(errors))
            return

        self.accept()

    def _load_record(self):
        """加载已有记录到表单"""
        r = self._record
        # 品牌
        brand = r.get("brand", "")
        idx = self.brand_combo.findData(brand)
        if idx >= 0:
            self.brand_combo.setCurrentIndex(idx)
        else:
            self.brand_combo.setCurrentText(brand)

        self.model_input.setText(r.get("model", ""))

        idx = self.format_combo.findData(r.get("film_format", ""))
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)

        idx = self.type_combo.findData(r.get("film_type", ""))
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        iso = r.get("box_iso", 0)
        self.iso_spin.setValue(iso if iso else 0)

        self.quantity_spin.setValue(r.get("quantity_cache", 0))

        price = r.get("unit_price", 0)
        self.price_spin.setValue(price if price else 0)
        idx = self.currency_combo.findData(r.get("currency", "CNY"))
        if idx >= 0:
            self.currency_combo.setCurrentIndex(idx)

        self.batch_input.setText(r.get("batch_number", ""))

        expiry = r.get("expiry_date", "")
        if expiry:
            self.expiry_date.setDate(QDate.fromString(expiry, "yyyy-MM-dd"))

        purchase = r.get("purchase_date", "")
        if purchase:
            self.purchase_date.setDate(QDate.fromString(purchase, "yyyy-MM-dd"))

        self.source_input.setText(r.get("purchase_source", ""))
        self.location_input.setText(r.get("storage_location", ""))

        idx = self.storage_combo.findData(r.get("storage_method", ""))
        if idx >= 0:
            self.storage_combo.setCurrentIndex(idx)

        self.notes_edit.setText(r.get("notes", ""))
        # 加载照片
        photo = r.get("photo_path", "")
        if photo:
            self.photo_thumb.photo_path = photo

    def get_form_data(self) -> dict:
        """获取表单数据字典

        Returns:
            可直接传给 InventoryService 的数据字典
        """
        expiry = self.expiry_date.date()
        purchase = self.purchase_date.date()

        return {
            "brand": self.brand_combo.currentText().strip(),
            "model": self.model_input.text().strip(),
            "film_format": self.format_combo.currentData() or "",
            "film_type": self.type_combo.currentData() or "",
            "box_iso": self.iso_spin.value() or 0,
            "quantity_cache": self.quantity_spin.value(),
            "batch_number": self.batch_input.text().strip(),
            "expiry_date": expiry.toString("yyyy-MM-dd") if expiry.isValid() and expiry > QDate(2000, 1, 1) else "",
            "purchase_date": purchase.toString("yyyy-MM-dd") if purchase.isValid() and purchase > QDate(2000, 1, 1) else "",
            "purchase_source": self.source_input.text().strip(),
            "unit_price": self.price_spin.value(),
            "currency": self.currency_combo.currentData() or "CNY",
            "storage_location": self.location_input.text().strip(),
            "storage_method": self.storage_combo.currentData() or "",
            "notes": self.notes_edit.toPlainText().strip(),
            "photo_path": self.photo_thumb.photo_path,
        }
