"""
胶片管理器 - 主入口

胶卷库存、拍摄、冲洗、扫描和归档管理工具。
Windows 本地运行，数据存储在 SQLite 数据库中。
"""

import sys
import logging
import traceback
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import ensure_directories, get_database_path, APP_NAME
from app.database.connection import initialize_database
from app.database.migrations import run_migrations
from app.services.backup_service import BackupService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def init_app() -> bool:
    """初始化应用程序

    1. 创建数据目录
    2. 初始化数据库连接
    3. 运行数据库迁移
    4. 启动时自动备份（如果数据库已存在）

    Returns:
        是否初始化成功
    """
    try:
        # 确保数据目录存在
        ensure_directories()
        logger.info(f"数据目录已就绪: {get_database_path().parent}")

        # 启动时自动备份（仅在数据库已存在时）
        db_path = get_database_path()
        if db_path.exists():
            try:
                backup = BackupService()
                backup.create_backup()
            except Exception as e:
                logger.warning(f"启动时自动备份失败（非致命）: {e}")

        # 初始化数据库连接
        initialize_database(db_path)
        logger.info(f"数据库连接已建立: {db_path}")

        # 运行迁移
        if not run_migrations(db_path):
            logger.error("数据库迁移失败！")
            return False

        logger.info("应用程序初始化完成")
        return True
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        return False


def global_exception_hook(exc_type, exc_value, exc_tb):
    """全局异常处理钩子：捕获未处理的异常，显示错误提示而非直接崩溃"""
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(f"未捕获的异常:\n{error_msg}")

    # 尝试显示错误对话框
    try:
        QMessageBox.critical(
            None,
            "程序错误",
            f"程序遇到了意外错误：\n\n{str(exc_value)}\n\n"
            "程序将尝试继续运行。如果问题持续出现，\n"
            "请检查数据目录中的日志或尝试恢复备份。\n\n"
            f"数据目录：{get_database_path().parent}"
        )
    except Exception:
        pass

    # 调用默认处理
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main():
    """主函数"""
    # 设置全局异常处理
    sys.excepthook = global_exception_hook

    # 初始化
    if not init_app():
        print("应用程序初始化失败，请检查日志后重试。")
        sys.exit(1)

    # 启动 PySide6 应用
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Fusion 引擎 + 现代化暖色样式
    app.setStyle("Fusion")
    app.setStyleSheet("""
        /* ====== 全局文字 ====== */
        QLabel { color: #2c1810; }

        /* ====== 输入框 — 圆润浮动风格 ====== */
        QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
            color: #2c1810;
            background-color: #fffefb;
            border: 2px solid #e0d5c5;
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 13px;
            selection-background-color: #f0d8b8;
        }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
            border-color: #c8783c;
            background-color: #fffaf5;
        }
        QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover {
            border-color: #d4c0a0;
        }

        /* ====== 下拉框 — 圆润 ====== */
        QComboBox {
            color: #2c1810;
            background-color: #fffefb;
            border: 2px solid #e0d5c5;
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 13px;
        }
        QComboBox:focus { border-color: #c8783c; }
        QComboBox:hover { border-color: #d4c0a0; }
        QComboBox::drop-down {
            border: none;
            padding-right: 8px;
        }
        QComboBox QAbstractItemView {
            color: #2c1810;
            background-color: #fffefb;
            border: 1px solid #e0d5c5;
            border-radius: 6px;
            padding: 4px;
            selection-background-color: #f0d8b8;
        }

        /* ====== 文本编辑区 ====== */
        QTextEdit, QPlainTextEdit {
            color: #2c1810;
            background-color: #fffefb;
            border: 2px solid #e0d5c5;
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 13px;
        }
        QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #c8783c;
            background-color: #fffaf5;
        }

        /* ====== 按钮 — 微阴影悬浮感 ====== */
        QPushButton {
            color: #2c1810;
            background-color: #f2ece2;
            border: 1px solid #e0d5c5;
            border-radius: 8px;
            padding: 6px 16px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #ede5d8;
            border-color: #c8783c;
        }
        QPushButton:pressed {
            background-color: #f0d8b8;
        }

        /* ====== 表格 — 柔和圆角 ====== */
        QTableWidget {
            color: #2c1810;
            background-color: #fffefb;
            gridline-color: #ede5d8;
            border: 1px solid #e0d5c5;
            border-radius: 8px;
        }
        QHeaderView::section {
            color: #6b5a4e;
            background-color: #f2ece2;
            padding: 8px 12px;
            border: none;
            border-bottom: 2px solid #e0d5c5;
            font-weight: bold;
            font-size: 12px;
        }

        /* ====== 复选框/单选框 ====== */
        QCheckBox { color: #2c1810; spacing: 8px; }

        /* ====== 滚动条 — 细窄隐藏式 ====== */
        QScrollBar:vertical {
            background: transparent;
            width: 8px;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background: #d8cdb8;
            border-radius: 4px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover { background: #c0b098; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal {
            background: transparent;
            height: 8px;
        }
        QScrollBar::handle:horizontal {
            background: #d8cdb8;
            border-radius: 4px;
            min-width: 30px;
        }
        QScrollBar::handle:horizontal:hover { background: #c0b098; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

        /* ====== 分组框 ====== */
        QGroupBox {
            color: #2c1810;
            font-weight: bold;
            border: 1px solid #e0d5c5;
            border-radius: 10px;
            margin-top: 14px;
            padding: 22px 14px 14px 14px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: #6b5a4e;
        }

        /* ====== 状态栏 ====== */
        QStatusBar {
            color: #6b5a4e;
            background-color: #f2ece2;
            border-top: 1px solid #e0d5c5;
            font-size: 12px;
        }

        /* ====== 提示框 ====== */
        QToolTip {
            color: #2c1810;
            background-color: #fffefb;
            border: 1px solid #e0d5c5;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }
    """)

    # 设置应用级别异常处理（Qt 事件循环中的异常）
    def qt_exception_hook(exc_type, exc_value, exc_tb):
        global_exception_hook(exc_type, exc_value, exc_tb)

    # 使用完整的主窗口
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    # 运行应用
    exit_code = app.exec()

    # 退出时自动备份
    try:
        backup = BackupService()
        backup.create_backup()
        logger.info("退出时自动备份完成。")
    except Exception as e:
        logger.warning(f"退出时自动备份失败（非致命）: {e}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
