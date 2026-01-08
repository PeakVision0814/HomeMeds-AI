# src/reset_db.py

import sqlite3
import os

# 1. 路径配置
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "medicines.db")

def reset_db():
    print(f"🔧 正在连接数据库: {DB_PATH}")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 2. 暴力删除旧表 (Drop Tables)
        print("💥 正在删除旧表结构...")
        cursor.execute("DROP TABLE IF EXISTS inventory;")
        cursor.execute("DROP TABLE IF EXISTS medicine_catalog;")
        conn.commit()
        print("✅ 旧表已清除。")

        # 3. 重新创建新表 (Create Tables)
        print("🏗️ 正在创建新表结构 (v0.3)...")
        
        # 表1: Catalog
        cursor.execute("""
        CREATE TABLE medicine_catalog (
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

        # 表2: Inventory
        cursor.execute("""
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL,
            expiry_date DATE NOT NULL,
            quantity_val REAL NOT NULL,      -- 这就是之前报错缺失的列
            location TEXT NOT NULL,
            owner TEXT,
            my_dosage TEXT,
            is_opened BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (barcode) REFERENCES medicine_catalog(barcode)
        );
        """)
        
        conn.commit()
        print("🎉 数据库重置成功！所有表结构已更新为最新版。")

    except Exception as e:
        print(f"❌ 重置失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_db()