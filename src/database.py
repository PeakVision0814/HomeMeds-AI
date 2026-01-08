# src/database.py
import sqlite3
import os

# --- 路径配置 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "medicines.db")

def get_connection():
    """获取数据库连接 (开启外键支持)"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """标准初始化：创建双表结构 (v0.3)"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"📁 已创建数据目录: {DATA_DIR}")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 表1: Catalog (公共库)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_catalog (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            brand TEXT,
            spec TEXT,
            form TEXT,
            unit TEXT,
            effect_text TEXT,
            std_usage TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 表2: Inventory (库存表)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL,
            expiry_date DATE NOT NULL,
            quantity_val REAL NOT NULL,
            location TEXT NOT NULL,
            owner TEXT,
            my_dosage TEXT,
            is_opened BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (barcode) REFERENCES medicine_catalog(barcode)
        );
        """)

        conn.commit()
        print(f"✅ 数据库检查完成！双表结构已就绪。")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()