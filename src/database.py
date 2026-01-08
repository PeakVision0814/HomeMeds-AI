# src/database.py
import sqlite3
import os
import sys

# --- 1. 路径配置 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "medicines.db")

# --- 2. 核心功能 ---

def get_connection():
    """获取数据库连接 (开启外键支持)"""
    conn = sqlite3.connect(DB_PATH)
    # 关键：SQLite默认不开启外键约束，必须手动开启
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    标准初始化：创建双表结构 (v0.3)
    如果表不存在则创建，如果存在则跳过
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"📁 已创建数据目录: {DATA_DIR}")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("🏗️ 正在检查数据库表结构...")

        # 表1: Catalog (公共库) - 存储药品基础信息
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

        # 表2: Inventory (库存表) - 存储具体库存
        # 注意：这里包含了 quantity_val 字段
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
        print(f"✅ 数据库初始化完成 (Path: {DB_PATH})")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    finally:
        conn.close()

def reset_db():
    """
    [危险操作] 数据库重置工具
    暴力删除旧表，然后重新调用 init_db 创建新表
    """
    print(f"🔧 正在连接数据库: {DB_PATH}")
    
    # 二次确认防止误删
    confirm = input("⚠️ 警告：这将清空所有库存数据！确认重置吗？(输入 'y' 确认): ")
    if confirm.lower() != 'y':
        print("已取消操作。")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. 暴力删除旧表 (Drop Tables)
        print("💥 正在删除旧表结构...")
        cursor.execute("DROP TABLE IF EXISTS inventory;")
        cursor.execute("DROP TABLE IF EXISTS medicine_catalog;")
        conn.commit()
        print("✅ 旧表已清除。")
        
        # 2. 复用 init_db 重建
        conn.close() # 先断开连接
        init_db()    # 调用初始化函数
        
        print("🎉 数据库重置成功！焕然一新。")

    except Exception as e:
        print(f"❌ 重置失败: {e}")
        if conn:
            conn.close()

# --- 3. 命令行入口 ---

if __name__ == "__main__":
    # 如果运行 python src/database.py --reset 则执行重置
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_db()
    else:
        # 默认执行初始化
        init_db()