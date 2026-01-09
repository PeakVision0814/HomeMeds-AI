# src/database.py
import sqlite3
import os
import sys
import json

# --- 1. 路径配置 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "medicines.db")
SEED_FILE = os.path.join(DATA_DIR, "catalog_seed.json")

# --- 2. 基础连接 ---

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

# --- 3. 核心功能：初始化与重置 ---

def init_db():
    """初始化数据库表结构，并自动加载种子数据"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("🏗️ 正在检查数据库表结构 (v0.5)...")

        # 表1: Catalog (基础库) - 增加 is_standard 字段
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_catalog (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            manufacturer TEXT,
            spec TEXT,
            form TEXT,
            unit TEXT,
            indications TEXT,
            std_usage TEXT,
            adverse_reactions TEXT,
            contraindications TEXT,
            precautions TEXT,
            pregnancy_lactation_use TEXT,
            child_use TEXT,
            elderly_use TEXT,
            is_standard BOOLEAN DEFAULT 0,  -- 0=用户私有, 1=官方标准
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 表2: Inventory (库存库)
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
        print(f"✅ 数据库结构就绪。")
        
        # 尝试加载种子数据
        import_seed_data(conn)

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    finally:
        conn.close()

def reset_db():
    """暴力重置：删表 -> 建表 -> 自动导回数据"""
    print(f"🔧 正在连接数据库: {DB_PATH}")
    if input("⚠️ 警告：这将清空所有库存！但会保留 JSON 中的公共库。确认？(y/n): ").lower() != 'y':
        return

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS inventory;")
        cursor.execute("DROP TABLE IF EXISTS medicine_catalog;")
        conn.commit()
        print("💥 旧表已清除。")
        conn.close()
        
        init_db() # 重新初始化
        print("🎉 重置成功！")
    except Exception as e:
        print(f"❌ 重置失败: {e}")

# --- 4. 种子数据管理 (Seed Data) ---

def export_seed_data():
    """
    [维护者专用] 将数据库中标记为 '官方(is_standard=1)' 的数据导出为 JSON
    这样 Git 里永远只保存官方清洗过的数据，不包含用户的私人测试数据。
    """
    conn = get_connection()
    try:
        # 只导出 is_standard = 1 的数据
        rows = conn.execute("SELECT * FROM medicine_catalog WHERE is_standard = 1").fetchall()
        data = [dict(row) for row in rows]
        
        with open(SEED_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"💾 已导出 {len(data)} 条【官方标准数据】到: {SEED_FILE}")
        return len(data)
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        raise e
    finally:
        conn.close()

def import_seed_data(conn):
    """
    [自动调用] 从 JSON 文件加载数据
    强制策略：JSON 里的数据就是权威数据，强制覆盖本地，并标记为 is_standard=1
    """
    if not os.path.exists(SEED_FILE):
        return

    try:
        with open(SEED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"🌱 正在加载 {len(data)} 条官方种子数据...")
        cursor = conn.cursor()
        
        # 使用 INSERT OR REPLACE 确保官方数据覆盖用户的同名数据
        sql = """
        INSERT OR REPLACE INTO medicine_catalog (
            barcode, name, manufacturer, spec, form, unit, 
            indications, std_usage, adverse_reactions, 
            contraindications, precautions, 
            pregnancy_lactation_use, child_use, elderly_use,
            is_standard
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """
        
        for item in data:
            cursor.execute(sql, (
                item.get('barcode'), item.get('name'), item.get('manufacturer'), 
                item.get('spec'), item.get('form'), item.get('unit'),
                item.get('indications'), item.get('std_usage'), 
                item.get('adverse_reactions'), item.get('contraindications'), 
                item.get('precautions'), item.get('pregnancy_lactation_use'), 
                item.get('child_use'), item.get('elderly_use')
            ))
            
        conn.commit()
        print("✅ 官方数据同步完成。")
        
    except Exception as e:
        print(f"⚠️ 种子加载失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--reset": reset_db()
        elif cmd == "--export": export_seed_data()
    else:
        init_db()