"""照片缩略图组件"""

from pathlib import Path
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame, QPushButton, QFileDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap


class PhotoThumbnail(QFrame):
    """可点击的照片缩略图组件

    显示缩略图预览，点击可更换照片。
    图片不存入数据库，只保存文件路径。
    """

    photo_changed = Signal(str)  # 照片路径变更时发出

    def __init__(self, photo_path: str = "", size: int = 140, parent=None):
        super().__init__(parent)
        self._photo_path = photo_path
        self._size = size
        self._setup_ui()
        if photo_path:
            self._load_photo(photo_path)

    def _setup_ui(self):
        self.setFixedSize(self._size + 16, self._size + 40)
        self.setStyleSheet(
            "QFrame { background: #faf6f0; border: 2px dashed #e0d5c5; "
            "border-radius: 10px; }"
            "QFrame:hover { border-color: #c8783c; }"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._image_label = QLabel()
        self._image_label.setFixedSize(self._size, self._size)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet(
            "QLabel { background: #fffefb; border-radius: 6px; border: none; }"
        )

        if not self._photo_path:
            self._image_label.setText("📷\n点击添加照片")

        layout.addWidget(self._image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._path_label = QLabel()
        self._path_label.setMaximumWidth(self._size)
        self._path_label.setStyleSheet(
            "QLabel { color: #9b8a7e; font-size: 10px; border: none; "
            "background: transparent; }"
        )
        self._path_label.setWordWrap(False)
        self._path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._path_label)

        self.mousePressEvent = self._on_click

    def _on_click(self, event):
        """点击选择照片"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择照片",
            str(Path(self._photo_path).parent) if self._photo_path else "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif);;所有文件 (*.*)",
        )
        if path:
            self._load_photo(path)
            self.photo_changed.emit(path)

    def _load_photo(self, path: str):
        """加载并显示照片缩略图"""
        if not path or not Path(path).exists():
            self._image_label.setText("📷\n文件不存在")
            self._photo_path = ""
            self._path_label.setText("")
            return

        self._photo_path = path
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._image_label.setText("⚠\n无法读取图片")
            self._path_label.setText(Path(path).name)
            return

        scaled = pixmap.scaled(
            self._size, self._size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._path_label.setText(Path(path).name)

    @property
    def photo_path(self) -> str:
        return self._photo_path

    @photo_path.setter
    def photo_path(self, path: str):
        self._load_photo(path)
