"""
颜色定义

不再使用全局样式表，只提供颜色常量。
每个控件显式设置自己的颜色，避免任何覆盖冲突。
"""


class Colors:
    """暖色胶片配色（固定浅色方案，不支持切换）"""

    # 背景
    bg_primary = "#faf6f0"
    bg_secondary = "#f2ece2"
    bg_tertiary = "#ede5d8"
    bg_sidebar = "#3b2818"
    bg_sidebar_hover = "#4d3624"
    bg_sidebar_active = "#5c402a"

    # 文字
    text_primary = "#2c1810"
    text_secondary = "#6b5a4e"
    text_hint = "#9b8a7e"
    text_sidebar = "#e0d5c5"
    text_sidebar_dim = "#a89880"

    # 边框和分隔
    border = "#e0d5c5"
    border_light = "#ede5d8"

    # 强调色
    accent = "#c8783c"
    accent_hover = "#b06830"
    accent_light = "#f0d8b8"

    # 功能色
    danger = "#b5433a"
    success = "#5d8c4a"
    warning_bg = "#faf0e0"
    warning_border = "#d4853c"

    # 组件色
    card_bg = "#fffefb"
    table_alt_row = "#f7f1e8"
    input_bg = "#fffefb"
    input_border = "#d8cdb8"
    header_bg = "#ede5d8"


# 向下兼容：保留旧的 get_theme API，但不做主题切换
class _ColorAccessor:
    """提供 Colors 属性的访问器，兼容旧代码"""
    colors = Colors
    is_dark = lambda self: False
    current = "light"

    def add_listener(self, callback):
        pass

    def remove_listener(self, callback):
        pass


_inst = _ColorAccessor()


def get_theme():
    return _inst
