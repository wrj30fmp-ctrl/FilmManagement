# 胶片管理器 (Film Manager)

胶卷库存、拍摄、冲洗、扫描和归档管理工具。为胶片摄影爱好者打造的 Windows 本地桌面应用。

## 功能特性

- 📦 **库存管理** — 记录胶卷品牌、型号、ISO、有效期、存放位置，支持筛选和过期提醒
- 📷 **拍摄记录** — 从库存取出胶卷开始拍摄，记录相机、镜头、地点、主题
- 🧪 **冲洗 & 扫描** — 记录冲洗方式、扫描参数、文件夹路径
- 📁 **归档管理** — 底片存放位置、备份状态追踪
- 📊 **数据统计** — 费用构成、拍摄趋势、相机使用频率图表
- 🏷 **标签打印** — 生成可打印的胶卷标签（HTML 格式）
- 📸 **EXIF 读取** — 从照片中自动读取相机、镜头、ISO 等参数
- 💾 **数据安全** — SQLite 本地存储，自动备份，CSV/Excel 导出

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3 |
| GUI | PySide6 |
| 数据库 | SQLite |
| 图表 | Matplotlib |
| 导出 | openpyxl (Excel) |
| 打包 | PyInstaller |

## 安装与运行

### 方法一：源码运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行
python main.py
```

### 方法二：直接使用打包好的 exe

下载 `dist/FilmManager/FilmManager.exe`，双击运行。

## 打包为 Windows 可执行程序

```bash
python -m PyInstaller --windowed --name "FilmManager" --add-data "app;app" --hidden-import matplotlib --hidden-import openpyxl --clean --noconfirm main.py
```

打包结果在 `dist/FilmManager/` 目录下。

## 数据存储

所有数据存储在 `C:\Users\<用户名>\Documents\FilmManager\` 目录：
- `film_manager.db` — SQLite 数据库
- `backups/` — 自动备份（默认保留 20 份）
- `exports/` — 导出的 CSV/Excel 文件

## 项目结构

```
film_manager/
├── main.py              # 程序入口
├── requirements.txt     # Python 依赖
├── app/
│   ├── config.py        # 配置管理
│   ├── constants.py     # 常量定义
│   ├── database/        # 数据库连接、Schema、迁移
│   ├── models/          # 数据模型（dataclass）
│   ├── repositories/    # 数据访问层（Repository 模式）
│   ├── services/        # 业务逻辑层
│   ├── ui/              # 用户界面
│   │   ├── main_window.py  # 主窗口
│   │   ├── pages/       # 各功能页面
│   │   ├── dialogs/     # 表单对话框
│   │   └── widgets/     # 可复用组件
│   └── utils/           # 工具函数
└── resources/           # 资源文件
```

## 架构设计

- **UI 层** — PySide6 界面，不包含任何 SQL 语句
- **Service 层** — 业务逻辑，状态机，事务管理
- **Repository 层** — 参数化 SQL，数据访问抽象
- **Database 层** — SQLite + WAL 模式，版本迁移

## License

MIT
