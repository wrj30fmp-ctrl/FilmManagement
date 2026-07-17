"""
数据库 Schema 定义

包含所有数据表和索引的 DDL 建表语句。
所有核心表使用 UUID 主键、通用同步字段和软删除支持。

数据库版本: 1
"""

# ============================================================
# 设置表（存储程序配置）
# ============================================================
CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# ============================================================
# Schema 迁移记录表
# ============================================================
CREATE_SCHEMA_MIGRATIONS = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL,
    description TEXT
);
"""

# ============================================================
# 胶卷库存表
# ============================================================
CREATE_FILM_INVENTORY = """
CREATE TABLE IF NOT EXISTS film_inventory (
    id               TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL DEFAULT 'local-user',
    brand            TEXT,
    model            TEXT NOT NULL,
    film_format      TEXT NOT NULL,
    film_type        TEXT,
    box_iso          INTEGER,
    quantity_cache   INTEGER NOT NULL DEFAULT 0,
    batch_number     TEXT,
    expiry_date      TEXT,
    purchase_date    TEXT,
    purchase_source  TEXT,
    unit_price       REAL,
    currency         TEXT DEFAULT 'CNY',
    storage_location TEXT,
    storage_method   TEXT,
    photo_path       TEXT,
    notes            TEXT,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    deleted_at       TEXT,
    version          INTEGER NOT NULL DEFAULT 1,
    device_id        TEXT,
    sync_status      TEXT NOT NULL DEFAULT 'local'
);
"""

# ============================================================
# 胶卷拍摄记录表
# ============================================================
CREATE_FILM_ROLLS = """
CREATE TABLE IF NOT EXISTS film_rolls (
    id               TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL DEFAULT 'local-user',
    roll_number      TEXT NOT NULL,
    inventory_id     TEXT,
    brand            TEXT,
    model            TEXT NOT NULL,
    film_format      TEXT NOT NULL,
    film_type        TEXT,
    box_iso          INTEGER,
    exposure_iso     INTEGER,
    camera           TEXT,
    lens             TEXT,
    load_date        TEXT,
    finish_date      TEXT,
    location         TEXT,
    subject          TEXT,
    status           TEXT NOT NULL,
    push_pull        REAL,
    photo_path       TEXT,
    notes            TEXT,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    deleted_at       TEXT,
    version          INTEGER NOT NULL DEFAULT 1,
    device_id        TEXT,
    sync_status      TEXT NOT NULL DEFAULT 'local',
    FOREIGN KEY (inventory_id) REFERENCES film_inventory(id)
);
"""

# ============================================================
# 冲洗记录表
# ============================================================
CREATE_DEVELOPMENT_RECORDS = """
CREATE TABLE IF NOT EXISTS development_records (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL DEFAULT 'local-user',
    film_roll_id        TEXT NOT NULL,
    development_method  TEXT,
    process_type        TEXT,
    lab_name            TEXT,
    sent_date           TEXT,
    completed_date      TEXT,
    cost                REAL,
    currency            TEXT DEFAULT 'CNY',
    push_pull_stops     REAL,
    chemistry           TEXT,
    notes               TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    deleted_at          TEXT,
    version             INTEGER NOT NULL DEFAULT 1,
    device_id           TEXT,
    sync_status         TEXT NOT NULL DEFAULT 'local',
    FOREIGN KEY (film_roll_id) REFERENCES film_rolls(id)
);
"""

# ============================================================
# 扫描记录表
# ============================================================
CREATE_SCAN_RECORDS = """
CREATE TABLE IF NOT EXISTS scan_records (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL DEFAULT 'local-user',
    film_roll_id    TEXT NOT NULL,
    scan_method     TEXT,
    scanner         TEXT,
    software        TEXT,
    scan_date       TEXT,
    resolution      TEXT,
    file_format     TEXT,
    local_path      TEXT,
    cloud_url       TEXT,
    file_hash       TEXT,
    storage_type    TEXT DEFAULT 'local',
    cost            REAL,
    currency        TEXT DEFAULT 'CNY',
    notes           TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    deleted_at      TEXT,
    version         INTEGER NOT NULL DEFAULT 1,
    device_id       TEXT,
    sync_status     TEXT NOT NULL DEFAULT 'local',
    FOREIGN KEY (film_roll_id) REFERENCES film_rolls(id)
);
"""

# ============================================================
# 归档记录表
# ============================================================
CREATE_ARCHIVE_RECORDS = """
CREATE TABLE IF NOT EXISTS archive_records (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL DEFAULT 'local-user',
    film_roll_id      TEXT NOT NULL,
    negative_location TEXT,
    binder_number     TEXT,
    page_number       TEXT,
    local_path        TEXT,
    cloud_url         TEXT,
    storage_type      TEXT DEFAULT 'local',
    cloud_backup      INTEGER NOT NULL DEFAULT 0,
    offsite_backup    INTEGER NOT NULL DEFAULT 0,
    archive_date      TEXT,
    notes             TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    deleted_at        TEXT,
    version           INTEGER NOT NULL DEFAULT 1,
    device_id         TEXT,
    sync_status       TEXT NOT NULL DEFAULT 'local',
    FOREIGN KEY (film_roll_id) REFERENCES film_rolls(id)
);
"""

# ============================================================
# 库存流水表
# ============================================================
CREATE_INVENTORY_TRANSACTIONS = """
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id               TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL DEFAULT 'local-user',
    inventory_id     TEXT NOT NULL,
    change_amount    INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    related_roll_id  TEXT,
    reason           TEXT,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    deleted_at       TEXT,
    version          INTEGER NOT NULL DEFAULT 1,
    device_id        TEXT,
    sync_status      TEXT NOT NULL DEFAULT 'local',
    FOREIGN KEY (inventory_id) REFERENCES film_inventory(id),
    FOREIGN KEY (related_roll_id) REFERENCES film_rolls(id)
);
"""

# ============================================================
# 胶卷状态历史表
# ============================================================
CREATE_FILM_ROLL_STATUS_HISTORY = """
CREATE TABLE IF NOT EXISTS film_roll_status_history (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL DEFAULT 'local-user',
    film_roll_id  TEXT NOT NULL,
    from_status   TEXT,
    to_status     TEXT NOT NULL,
    changed_at    TEXT NOT NULL,
    notes         TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    deleted_at    TEXT,
    version       INTEGER NOT NULL DEFAULT 1,
    device_id     TEXT,
    sync_status   TEXT NOT NULL DEFAULT 'local',
    FOREIGN KEY (film_roll_id) REFERENCES film_rolls(id)
);
"""

# ============================================================
# 变更日志表（轻量级审计日志）
# ============================================================
CREATE_CHANGE_LOG = """
CREATE TABLE IF NOT EXISTS change_log (
    id           TEXT PRIMARY KEY,
    table_name   TEXT NOT NULL,
    record_id    TEXT NOT NULL,
    operation    TEXT NOT NULL,
    changed_at   TEXT NOT NULL,
    device_id    TEXT,
    sync_status  TEXT NOT NULL DEFAULT 'local'
);
"""

# ============================================================
# 所有建表语句列表（按依赖顺序排列）
# ============================================================
ALL_TABLES = [
    ("settings", CREATE_SETTINGS),
    ("schema_migrations", CREATE_SCHEMA_MIGRATIONS),
    ("film_inventory", CREATE_FILM_INVENTORY),
    ("film_rolls", CREATE_FILM_ROLLS),
    ("development_records", CREATE_DEVELOPMENT_RECORDS),
    ("scan_records", CREATE_SCAN_RECORDS),
    ("archive_records", CREATE_ARCHIVE_RECORDS),
    ("inventory_transactions", CREATE_INVENTORY_TRANSACTIONS),
    ("film_roll_status_history", CREATE_FILM_ROLL_STATUS_HISTORY),
    ("change_log", CREATE_CHANGE_LOG),
]

# ============================================================
# 索引创建语句
# ============================================================
CREATE_INDEXES = [
    # 库存表索引
    "CREATE INDEX IF NOT EXISTS idx_inventory_user ON film_inventory(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_inventory_brand ON film_inventory(brand);",
    "CREATE INDEX IF NOT EXISTS idx_inventory_format ON film_inventory(film_format);",
    "CREATE INDEX IF NOT EXISTS idx_inventory_expiry ON film_inventory(expiry_date);",
    "CREATE INDEX IF NOT EXISTS idx_inventory_deleted ON film_inventory(deleted_at);",

    # 拍摄记录表索引
    "CREATE INDEX IF NOT EXISTS idx_rolls_user ON film_rolls(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_rolls_number ON film_rolls(roll_number);",
    "CREATE INDEX IF NOT EXISTS idx_rolls_status ON film_rolls(status);",
    "CREATE INDEX IF NOT EXISTS idx_rolls_inventory ON film_rolls(inventory_id);",
    "CREATE INDEX IF NOT EXISTS idx_rolls_deleted ON film_rolls(deleted_at);",

    # 冲洗记录索引
    "CREATE INDEX IF NOT EXISTS idx_dev_roll ON development_records(film_roll_id);",
    "CREATE INDEX IF NOT EXISTS idx_dev_deleted ON development_records(deleted_at);",

    # 扫描记录索引
    "CREATE INDEX IF NOT EXISTS idx_scan_roll ON scan_records(film_roll_id);",
    "CREATE INDEX IF NOT EXISTS idx_scan_deleted ON scan_records(deleted_at);",

    # 归档记录索引
    "CREATE INDEX IF NOT EXISTS idx_archive_roll ON archive_records(film_roll_id);",
    "CREATE INDEX IF NOT EXISTS idx_archive_deleted ON archive_records(deleted_at);",

    # 库存流水索引
    "CREATE INDEX IF NOT EXISTS idx_trans_inventory ON inventory_transactions(inventory_id);",
    "CREATE INDEX IF NOT EXISTS idx_trans_type ON inventory_transactions(transaction_type);",
    "CREATE INDEX IF NOT EXISTS idx_trans_deleted ON inventory_transactions(deleted_at);",

    # 状态历史索引
    "CREATE INDEX IF NOT EXISTS idx_history_roll ON film_roll_status_history(film_roll_id);",
    "CREATE INDEX IF NOT EXISTS idx_history_deleted ON film_roll_status_history(deleted_at);",
]

# ============================================================
# 唯一索引
# ============================================================
"""
胶卷编号在同一用户范围内唯一。
SQLite 不支持 CREATE UNIQUE INDEX IF NOT EXISTS，因此此处用 CREATE UNIQUE INDEX，
但在 migrations 中会捕获已存在时的错误。
"""
CREATE_ROLL_NUMBER_UNIQUE_INDEX = (
    "CREATE UNIQUE INDEX idx_rolls_user_number ON film_rolls(user_id, roll_number);"
)
