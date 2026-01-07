# src/services.py
import pandas as pd
from datetime import date, datetime, timedelta
from src.database import get_connection

# --- 1. 增 (Create) ---
def add_medicine(name, brand, effect, expiry_date, quantity, location, tags=""):
    """
    将新药品插入数据库
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        sql = """
        INSERT INTO inventory (name, brand, effect_text, expiry_date, quantity, location, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (name, brand, effect, expiry_date, quantity, location, tags))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 入库失败: {e}")
        return False
    finally:
        conn.close()

# --- 2. 查 (Read) ---
def load_data():
    """
    读取所有数据，返回一个 Pandas DataFrame
    (Streamlit 最喜欢 DataFrame，可以直接展示为漂亮表格)
    """
    conn = get_connection()
    try:
        # 直接用 pandas 读取 SQL，一步到位
        df = pd.read_sql_query("SELECT * FROM inventory ORDER BY expiry_date ASC", conn)
        return df
    finally:
        conn.close()

def get_dashboard_metrics():
    """
    计算看板顶部的统计数据：过期数、临期数、总数
    """
    df = load_data()
    if df.empty:
        return 0, 0, 0
    
    # 转换日期列格式 (str -> date)
    df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
    today = date.today()
    
    # 计算指标
    total_count = len(df)
    expired_count = len(df[df['expiry_date'] < today])
    
    # 临期定义：未来 90 天内过期，且没过期的
    warning_date = today + timedelta(days=90)
    expiring_soon_count = len(df[(df['expiry_date'] >= today) & (df['expiry_date'] <= warning_date)])
    
    return total_count, expired_count, expiring_soon_count

# --- 3. 改 (Update) ---
def update_quantity(med_id, new_quantity):
    """
    更新剩余数量（比如吃了一次药）
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_quantity, med_id))
        conn.commit()
    finally:
        conn.close()

# --- 4. 删 (Delete) ---
def delete_medicine(med_id):
    """
    根据 ID 删除药品
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM inventory WHERE id = ?", (med_id,))
        conn.commit()
    finally:
        conn.close()

# --- 5. AI 专用接口 ---
def get_inventory_str_for_ai():
    """
    获取现有库存的文本摘要，专门喂给 AI 做 Prompt
    只提取：ID, 名称, 功效, 位置, 过期日
    过滤掉：已过期的
    """
    df = load_data()
    if df.empty:
        return "库存为空。"
    
    # 数据预处理
    df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
    today = date.today()
    
    # 1. 过滤掉已过期的药 (AI 不应该推荐过期药)
    valid_df = df[df['expiry_date'] >= today]
    
    if valid_df.empty:
        return "库存为空（所有药物均已过期）。"

    # 2. 拼接成字符串
    inventory_list = []
    for _, row in valid_df.iterrows():
        item = (
            f"- ID: {row['id']} | 药名: {row['name']} | "
            f"功效: {row['effect_text']} | "
            f"位置: {row['location']} | "
            f"状态: {row['quantity']}"
        )
        inventory_list.append(item)
    
    return "\n".join(inventory_list)