# src/services.py

import pandas as pd
from datetime import date, datetime, timedelta
from src.database import get_connection
import sqlite3

# ==========================================
# A. 公共目录服务 (Catalog Services)
# ==========================================

def get_catalog_info(barcode):
    """
    根据条形码查询公共药品库
    用于前端：输入条形码后，自动回填药名、用法等信息
    """
    conn = get_connection()
    try:
        # 使用 pandas 读取，方便转字典
        df = pd.read_sql_query("SELECT * FROM medicine_catalog WHERE barcode = ?", conn, params=(barcode,))
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    finally:
        conn.close()

def upsert_catalog_item(barcode, name, brand, spec, form, unit, effect, std_usage, tags):
    """
    插入或更新公共药品目录
    (如果条形码已存在，则更新信息；如果不存在，则插入)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO medicine_catalog (barcode, name, brand, spec, form, unit, effect_text, std_usage, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(barcode) DO UPDATE SET
            name=excluded.name,
            brand=excluded.brand,
            spec=excluded.spec,
            form=excluded.form,
            unit=excluded.unit,
            effect_text=excluded.effect_text,
            std_usage=excluded.std_usage,
            tags=excluded.tags;
        """
        cursor.execute(sql, (barcode, name, brand, spec, form, unit, effect, std_usage, tags))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 目录更新失败: {e}")
        return False
    finally:
        conn.close()

# ==========================================
# B. 家庭库存服务 (Inventory Services)
# ==========================================

def add_inventory_item(barcode, expiry_date, quantity_val, location, owner, my_dosage):
    """
    添加具体的库存记录 (关联到 Barcode)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 这里不需要存药名，只需要存 barcode 作为关联
        sql = """
        INSERT INTO inventory (barcode, expiry_date, quantity_val, location, owner, my_dosage)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (barcode, expiry_date, quantity_val, location, owner, my_dosage))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"❌ 入库失败: 条形码 {barcode} 在目录表中不存在，请先添加到目录表。")
        return False
    except Exception as e:
        print(f"❌ 库存添加失败: {e}")
        return False
    finally:
        conn.close()

def quick_add_medicine(full_info_dict):
    """
    [复合功能] 一键入库：同时处理 Catalog 和 Inventory
    前端表单提交时调用此函数
    """
    # 1. 先存/更新目录
    upsert_catalog_item(
        barcode=full_info_dict['barcode'],
        name=full_info_dict['name'],
        brand=full_info_dict.get('brand', ''),
        spec=full_info_dict.get('spec', ''),
        form=full_info_dict.get('form', ''),
        unit=full_info_dict.get('unit', ''),
        effect=full_info_dict.get('effect_text', ''),
        std_usage=full_info_dict.get('std_usage', ''),
        tags=full_info_dict.get('tags', '')
    )
    
    # 2. 再存库存
    return add_inventory_item(
        barcode=full_info_dict['barcode'],
        expiry_date=full_info_dict['expiry_date'],
        quantity_val=full_info_dict['quantity_val'],
        location=full_info_dict['location'],
        owner=full_info_dict.get('owner', '家庭公用'),
        my_dosage=full_info_dict.get('my_dosage', '')
    )

# ==========================================
# C. 查询与展示 (Read & View)
# ==========================================

def load_data():
    """
    读取所有库存数据 (执行 JOIN 操作)
    将 inventory 表和 medicine_catalog 表合并，让前端看起来像一张大表
    """
    conn = get_connection()
    try:
        # 核心 SQL：联表查询
        sql = """
        SELECT 
            i.id, 
            i.barcode,
            c.name, 
            c.brand, 
            c.spec,
            c.form,
            c.unit,
            i.quantity_val, 
            i.expiry_date, 
            i.location, 
            i.owner,
            c.tags,
            c.effect_text,
            i.my_dosage
        FROM inventory i
        LEFT JOIN medicine_catalog c ON i.barcode = c.barcode
        ORDER BY i.expiry_date ASC
        """
        df = pd.read_sql_query(sql, conn)
        
        # 为了前端展示好看，我们在这里把 数量+单位 拼成一个字符串
        # 例如: 12 + 粒 -> "12.0 粒"
        if not df.empty:
            df['quantity_display'] = df['quantity_val'].astype(str) + " " + df['unit'].fillna('')
            
        return df
    finally:
        conn.close()

def get_dashboard_metrics():
    """
    计算看板指标 (逻辑保持不变，只需调用新的 load_data)
    """
    df = load_data()
    if df.empty:
        return 0, 0, 0
    
    df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
    today = date.today()
    
    total = len(df)
    expired = len(df[df['expiry_date'] < today])
    warning_date = today + timedelta(days=90)
    soon = len(df[(df['expiry_date'] >= today) & (df['expiry_date'] <= warning_date)])
    
    return total, expired, soon

# ==========================================
# D. 更新与删除 (Update & Delete)
# ==========================================

def update_quantity(med_id, new_quantity_val):
    """
    更新库存数量 (只更新 inventory 表的 quantity_val)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE inventory SET quantity_val = ? WHERE id = ?", (new_quantity_val, med_id))
        conn.commit()
    finally:
        conn.close()

def delete_medicine(med_id):
    """
    删除单条库存 (不删除 Catalog 里的信息，方便下次再买)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM inventory WHERE id = ?", (med_id,))
        conn.commit()
    finally:
        conn.close()

# ==========================================
# E. AI 专用接口 (RAG Context)
# ==========================================

def get_inventory_str_for_ai():
    """
    生成 AI 提示词所需的库存清单
    [升级版] 增加了：所属人、剂型、单位、医嘱
    """
    df = load_data()
    if df.empty:
        return "库存为空。"
    
    # 预处理
    df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
    today = date.today()
    valid_df = df[df['expiry_date'] >= today]
    
    if valid_df.empty:
        return "库存为空（所有药物均已过期）。"

    inventory_list = []
    for _, row in valid_df.iterrows():
        # 构建更详细的描述字符串
        item = (
            f"- ID: {row['id']} | "
            f"药名: {row['name']} ({row['brand'] or '无品牌'}) | "
            f"剩余: {row['quantity_val']}{row['unit']} | "
            f"位置: {row['location']} | "
            f"归属人: {row['owner'] or '公用'} | "
            f"功效: {row['effect_text'][:50]}... | " # 截断一下防止太长
            f"备注医嘱: {row['my_dosage'] or '无'}"
        )
        inventory_list.append(item)
    
    return "\n".join(inventory_list)

# --- 在 src/services.py 中新增以下函数 ---

def load_catalog_data():
    """
    读取公共药品目录的所有数据
    """
    conn = get_connection()
    try:
        # 简单粗暴，查全表
        df = pd.read_sql_query("SELECT * FROM medicine_catalog ORDER BY name", conn)
        return df
    finally:
        conn.close()