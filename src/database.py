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
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    标准初始化：创建双表结构 (v0.4 Pro版)
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"📁 已创建数据目录: {DATA_DIR}")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("🏗️ 正在检查数据库表结构...")

        # 表1: Catalog (公共库) - 升级为专业版字段
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_catalog (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,           -- 通用名
            manufacturer TEXT,            -- 生产企业 (原品牌)
            spec TEXT,                    -- 规格
            form TEXT,                    -- 剂型
            unit TEXT,                    -- 单位
            indications TEXT,             -- 适应症 (原功能主治)
            std_usage TEXT,               -- 说明书用法
            adverse_reactions TEXT,       -- 不良反应
            contraindications TEXT,       -- 禁忌
            precautions TEXT,             -- 注意事项
            pregnancy_lactation_use TEXT, -- 孕妇及哺乳期妇女用药
            child_use TEXT,               -- 儿童用药
            elderly_use TEXT,             -- 老年用药
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 表2: Inventory (库存表) - 保持不变
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
    """
    print(f"🔧 正在连接数据库: {DB_PATH}")
    
    confirm = input("⚠️ 警告：这将清空所有库存数据并升级表结构！确认重置吗？(输入 'y' 确认): ")
    if confirm.lower() != 'y':
        print("已取消操作。")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("💥 正在删除旧表结构...")
        cursor.execute("DROP TABLE IF EXISTS inventory;")
        cursor.execute("DROP TABLE IF EXISTS medicine_catalog;")
        conn.commit()
        print("✅ 旧表已清除。")
        
        conn.close()
        init_db() 
        
        print("🎉 数据库重置成功！已升级到 Pro 版结构。")

    except Exception as e:
        print(f"❌ 重置失败: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_db()
    else:
        init_db()