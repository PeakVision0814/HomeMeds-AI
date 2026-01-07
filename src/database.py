import sqlite3
import os
from datetime import datetime

# --- 配置部分 ---
# 自动定位到项目根目录下的 data 文件夹
# 逻辑：当前文件在 src/，上一级是根目录，根目录下的 data/ 是目标
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "medicines.db")

def get_connection():
    """获取数据库连接的工具函数"""
    conn = sqlite3.connect(DB_PATH)
    # 让查询结果像字典一样可以通过列名访问 (row['name'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库：创建文件夹和表结构"""
    # 1. 确保 data 文件夹存在
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"📁 已创建数据目录: {DATA_DIR}")

    # 2. 连接数据库 (如果文件不存在，sqlite会自动创建它)
    conn = get_connection()
    cursor = conn.cursor()

    # 3. 执行建表 SQL 语句 (按照 v0.2 设计文档)
    # 使用 IF NOT EXISTS 防止重复创建报错
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,              -- 药品通用名
        brand TEXT,                      -- 品牌
        barcode TEXT,                    -- 条形码 (预留)
        effect_text TEXT,                -- 功效说明 (AI 核心依赖)
        tags TEXT,                       -- 快速标签
        expiry_date DATE NOT NULL,       -- 过期日期 (YYYY-MM-DD)
        quantity TEXT NOT NULL,          -- 剩余状态 (满/少量/空)
        location TEXT NOT NULL,          -- 存放位置
        is_opened BOOLEAN DEFAULT 0,     -- 是否开封 (0=否, 1=是)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"✅ 数据库表 'inventory' 检查/创建成功！")
        print(f"📍 数据库文件路径: {DB_PATH}")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    finally:
        conn.close()

# 当直接运行这个文件时，执行初始化
if __name__ == "__main__":
    init_db()