"""
主窗口 — 暖色胶片风格 + 可折叠图标侧栏
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLineEdit, QStatusBar, QLabel,
    QSplitter, QFrame, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from app.config import APP_NAME, APP_VERSION
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.inventory_page import InventoryPage
from app.ui.pages.shooting_page import ShootingPage
from app.ui.pages.development_page import DevelopmentPage
from app.ui.pages.scan_page import ScanPage
from app.ui.pages.archive_page import ArchivePage
from app.ui.pages.statistics_page import StatisticsPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.theme import Colors


# 导航项定义：(图标, 文字, 页面key)
NAV_ITEMS = [
    ("🏠", "首页概览", "dashboard"),
    ("📦", "胶卷库存", "inventory"),
    ("📷", "拍摄记录", "shooting"),
    ("🧪", "冲洗管理", "development"),
    ("🖼", "扫描管理", "scan"),
    ("📁", "归档管理", "archive"),
    ("📊", "数据统计", "statistics"),
    ("⚙", "设置", "settings"),
]


class _NavButton(QPushButton):
    """侧栏导航按钮：折叠时只显示图标，展开时图标+文字"""

    def __init__(self, icon: str, text: str, collapsed: bool = False):
        super().__init__()
        self.icon = icon
        self.text_label = text
        self._collapsed = collapsed
        self._update_appearance()

    def _update_appearance(self):
        if self._collapsed:
            self.setText(f"  {self.icon}")
            self.setToolTip(self.text_label)
        else:
            self.setText(f"  {self.icon}  {self.text_label}")
            self.setToolTip("")
        self.setFont(QFont("", 14 if self._collapsed else 12))

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self._update_appearance()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1300, 820)
        self.setMinimumSize(900, 600)
        self._pages = {}
        self._sidebar_collapsed = False
        self._setup_ui()
        self._navigate_to("dashboard")

    def _setup_ui(self):
        # 转为 dict 方便 subscript 访问
        c = {k: v for k, v in vars(Colors).items() if not k.startswith("_")}

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- 顶部栏 ----
        top_bar = QFrame()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet(
            f"QFrame {{ background: {c['card_bg']}; "
            f"border-bottom: 1px solid {c['border']}; }}"
        )
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(14, 0, 14, 0)
        top_layout.setSpacing(14)

        # 侧栏折叠按钮
        self._collapse_btn = QPushButton("☰")
        self._collapse_btn.setFixedSize(32, 32)
        self._collapse_btn.setFont(QFont("", 16))
        self._collapse_btn.setStyleSheet(
            f"QPushButton {{ color: {c['text_secondary']}; background: transparent; "
            f"border: none; border-radius: 6px; }}"
            f"QPushButton:hover {{ background: {c['bg_secondary']}; }}"
        )
        self._collapse_btn.clicked.connect(self._toggle_sidebar)
        top_layout.addWidget(self._collapse_btn)

        # 标题
        app_label = QLabel(f"<b>{APP_NAME}</b>")
        app_label.setFont(QFont("", 13))
        app_label.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        top_layout.addWidget(app_label)

        # 搜索框
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("全局搜索：品牌、型号、编号、相机、镜头…")
        self.global_search.setFixedWidth(360)
        self.global_search.setStyleSheet(
            f"QLineEdit {{ color: {c['text_primary']}; "
            f"background: {c['bg_primary']}; border: 1px solid {c['border']}; "
            f"border-radius: 16px; padding: 6px 14px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border-color: {c['accent']}; }}"
        )
        top_layout.addWidget(self.global_search)
        top_layout.addStretch()

        main_layout.addWidget(top_bar)

        # ---- 主体 ----
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # 左侧折叠导航
        self._sidebar = QFrame()
        self._sidebar.setStyleSheet(
            f"QFrame {{ background: {c['bg_sidebar']}; border: none; }}"
        )
        self._sidebar_layout = QVBoxLayout(self._sidebar)
        self._sidebar_layout.setContentsMargins(0, 6, 0, 6)
        self._sidebar_layout.setSpacing(2)

        # 导航按钮
        self._nav_buttons: list[_NavButton] = []
        for icon, text, key in NAV_ITEMS:
            btn = _NavButton(icon, text, collapsed=False)
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._nav_btn_style(False))
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k))
            self._nav_buttons.append(btn)
            self._sidebar_layout.addWidget(btn)

        self._sidebar_layout.addStretch()

        # 版本标签
        self._version_label = QLabel(f"v{APP_VERSION}")
        self._version_label.setStyleSheet(
            f"color: {c['text_sidebar_dim']}; font-size: 10px; padding: 8px; "
            f"background: transparent;"
        )
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sidebar_layout.addWidget(self._version_label)

        self._sidebar.setFixedWidth(185)
        body.addWidget(self._sidebar)

        # 分隔线
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"QFrame {{ background: {c['border']}; border: none; }}")
        body.addWidget(sep)

        # 右侧页面区
        self.page_stack = QStackedWidget()
        self.page_stack.setStyleSheet(f"background: {c['bg_primary']};")
        body.addWidget(self.page_stack)

        main_layout.addLayout(body, 1)

        # 状态栏
        self.status_bar = QStatusBar()
        self.statusBar().hide()  # 隐藏默认状态栏，用自己设置的
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("")

    def _nav_btn_style(self, selected: bool) -> str:
        c = {k: v for k, v in vars(Colors).items() if not k.startswith("_")}
        if selected:
            return (
                f"QPushButton {{ color: #fffefb; background: {c['bg_sidebar_active']}; "
                f"border: none; border-radius: 6px; margin: 1px 8px; text-align: left; }}"
            )
        else:
            return (
                f"QPushButton {{ color: {c['text_sidebar']}; background: transparent; "
                f"border: none; border-radius: 6px; margin: 1px 8px; text-align: left; }}"
                f"QPushButton:hover {{ background: {c['bg_sidebar_hover']}; }}"
            )

    # ================================================================
    # 侧栏折叠
    # ================================================================

    def _toggle_sidebar(self):
        self._sidebar_collapsed = not self._sidebar_collapsed
        w = 52 if self._sidebar_collapsed else 185
        self._sidebar.setFixedWidth(w)
        for btn in self._nav_buttons:
            btn.set_collapsed(self._sidebar_collapsed)
            btn.setStyleSheet(self._nav_btn_style(False))
        self._version_label.setText("" if self._sidebar_collapsed else f"v{APP_VERSION}")

        # 更新当前选中按钮样式
        for btn in self._nav_buttons:
            btn.setStyleSheet(
                self._nav_btn_style(btn.property("selected") or False)
            )

    # ================================================================
    # 导航
    # ================================================================

    def _navigate_to(self, key: str):
        if key not in self._pages:
            page = self._create_page(key)
            if page is None:
                return
            self._pages[key] = page
            self.page_stack.addWidget(page)

        page = self._pages[key]
        self.page_stack.setCurrentWidget(page)

        if key == "dashboard" and hasattr(page, "refresh_data"):
            page.refresh_data()

        # 高亮当前按钮
        for btn in self._nav_buttons:
            is_selected = btn.text_label == dict(
                (n[2], n[1]) for n in NAV_ITEMS).get(key, "")
            btn.setProperty("selected", is_selected)
            btn.setStyleSheet(self._nav_btn_style(is_selected))

        item_names = {n[2]: n[1] for n in NAV_ITEMS}
        self.status_bar.showMessage(f"  {item_names.get(key, key)}")

    def _create_page(self, key: str) -> QWidget | None:
        pages = {
            "dashboard": DashboardPage,
            "inventory": InventoryPage,
            "shooting": ShootingPage,
            "development": DevelopmentPage,
            "scan": ScanPage,
            "archive": ArchivePage,
            "statistics": StatisticsPage,
            "settings": SettingsPage,
        }
        cls = pages.get(key)
        return cls() if cls else None
