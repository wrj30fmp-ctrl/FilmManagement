"""
应用常量定义
定义胶卷状态码、画幅、冲洗工艺等枚举值。
数据库中保存英文代码，界面显示中文标签。
"""

# ============================================================
# 胶卷状态代码（数据库存储值）
# ============================================================
class FilmStatus:
    """胶卷状态枚举，数据库存储英文代码"""
    IN_STOCK = "IN_STOCK"                       # 未拍库存
    LOADED = "LOADED"                           # 已装卷
    SHOOTING = "SHOOTING"                       # 拍摄中
    SHOT = "SHOT"                               # 已拍摄，待冲洗
    SENT_FOR_DEVELOPMENT = "SENT_FOR_DEVELOPMENT"  # 已送冲
    DEVELOPED = "DEVELOPED"                     # 已冲洗
    WAITING_FOR_SCAN = "WAITING_FOR_SCAN"       # 待扫描
    SCANNING = "SCANNING"                       # 扫描中
    SCANNED = "SCANNED"                         # 已扫描
    ARCHIVED = "ARCHIVED"                       # 已归档

    # 所有状态列表
    ALL_STATUSES = [
        IN_STOCK, LOADED, SHOOTING, SHOT,
        SENT_FOR_DEVELOPMENT, DEVELOPED,
        WAITING_FOR_SCAN, SCANNING, SCANNED, ARCHIVED,
    ]

    # 拍摄相关状态（在 film_rolls 表中使用的状态）
    ROLL_STATUSES = [
        LOADED, SHOOTING, SHOT,
        SENT_FOR_DEVELOPMENT, DEVELOPED,
        WAITING_FOR_SCAN, SCANNING, SCANNED, ARCHIVED,
    ]


# 状态代码 → 中文显示名 映射
STATUS_DISPLAY_MAP = {
    FilmStatus.IN_STOCK: "未拍库存",
    FilmStatus.LOADED: "已装卷",
    FilmStatus.SHOOTING: "拍摄中",
    FilmStatus.SHOT: "已拍摄，待冲洗",
    FilmStatus.SENT_FOR_DEVELOPMENT: "已送冲",
    FilmStatus.DEVELOPED: "已冲洗",
    FilmStatus.WAITING_FOR_SCAN: "待扫描",
    FilmStatus.SCANNING: "扫描中",
    FilmStatus.SCANNED: "已扫描",
    FilmStatus.ARCHIVED: "已归档",
}


def get_status_display(status_code: str) -> str:
    """将状态代码转换为中文显示名"""
    return STATUS_DISPLAY_MAP.get(status_code, status_code)


# ============================================================
# 画幅
# ============================================================
FILM_FORMATS = ["135", "120", "其他"]

# ============================================================
# 胶卷类型（色彩类型）
# ============================================================
FILM_TYPES = ["彩色负片", "黑白负片", "反转片", "电影卷", "其他"]

# ============================================================
# 保存方式
# ============================================================
STORAGE_METHODS = ["常温", "冷藏", "冷冻", "其他"]

# ============================================================
# 冲洗方式
# ============================================================
DEVELOPMENT_METHODS = [
    "自行冲洗",
    "本地冲洗店",
    "邮寄冲洗",
    "学校暗房",
    "其他",
]

# ============================================================
# 冲洗工艺
# ============================================================
PROCESS_TYPES = ["C-41", "黑白", "E-6", "ECN-2", "其他"]

# ============================================================
# 扫描方式
# ============================================================
SCAN_METHODS = [
    "自行扫描",
    "冲洗店扫描",
    "邮寄扫描",
    "学校设备",
    "其他",
]

# ============================================================
# 文件格式
# ============================================================
FILE_FORMATS = ["JPEG", "TIFF", "DNG", "RAW", "其他"]

# ============================================================
# 货币代码
# ============================================================
CURRENCIES = ["CNY", "USD", "CAD", "JPY", "EUR"]

# ============================================================
# 库存流水类型
# ============================================================
class TransactionType:
    """库存流水类型"""
    PURCHASE = "purchase"                       # 购买入库
    START_SHOOTING = "start_shooting"           # 开始拍摄（出库）
    RETURN_TO_INVENTORY = "return_to_inventory" # 取消拍摄退回
    MANUAL_ADJUSTMENT = "manual_adjustment"     # 手工盘点调整
    EXPIRED_DISCARD = "expired_discard"         # 过期丢弃
    LOST = "lost"                               # 丢失
    IMPORT = "import"                           # 数据导入
    OTHER = "other"                             # 其他

    ALL_TYPES = [
        PURCHASE, START_SHOOTING, RETURN_TO_INVENTORY,
        MANUAL_ADJUSTMENT, EXPIRED_DISCARD, LOST, IMPORT, OTHER,
    ]


# ============================================================
# 同步状态
# ============================================================
class SyncStatus:
    """同步状态"""
    LOCAL = "local"
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


# ============================================================
# 品牌预设列表
# ============================================================
BRANDS = [
    "Kodak",
    "Fujifilm",
    "Ilford",
    "Kentmere",
    "Foma",
    "Lomography",
    "Cinestill",
    "AGFA",
    "Rollei",
    "Arista",
    "Bergger",
    "Adox",
    "Silberra",
    "ORWO",
    "其他",
]
