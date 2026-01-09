# src/services.py

import pandas as pd
from datetime import date, datetime, timedelta
import sqlite3
from src.database import get_connection

# ==========================================
# A. 公共目录服务
# ==========================================

def get_catalog_info(barcode):
    """查询公共药品库，返回包含 is_standard 的字典"""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM medicine_catalog WHERE barcode = ?", conn, params=(barcode,))
        if not df.empty:
            return df.iloc[0].fillna("").to_dict()
        return None
    finally:
        conn.close()

def upsert_catalog_item(barcode, name, manufacturer, spec, form, unit, 
                       indications, std_usage, adverse_reactions, 
                       contraindications, precautions, 
                       pregnancy_lactation_use, child_use, elderly_use,
                       is_standard=0): # 默认为0(用户数据)
    """
    插入或更新公共药品目录
    参数 is_standard: 决定这条数据是“官方认证”还是“用户录入”
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO medicine_catalog (
            barcode, name, manufacturer, spec, form, unit, 
            indications, std_usage, 
            adverse_reactions, contraindications, precautions,
            pregnancy_lactation_use, child_use, elderly_use,
            is_standard
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(barcode) DO UPDATE SET
            name=excluded.name,
            manufacturer=excluded.manufacturer,
            spec=excluded.spec,
            form=excluded.form,
            unit=excluded.unit,
            indications=excluded.indications,
            std_usage=excluded.std_usage,
            adverse_reactions=excluded.adverse_reactions,
            contraindications=excluded.contraindications,
            precautions=excluded.precautions,
            pregnancy_lactation_use=excluded.pregnancy_lactation_use,
            child_use=excluded.child_use,
            elderly_use=excluded.elderly_use,
            is_standard=excluded.is_standard;
        """
        cursor.execute(sql, (
            barcode, name, manufacturer, spec, form, unit, 
            indications, std_usage, adverse_reactions, 
            contraindications, precautions, 
            pregnancy_lactation_use, child_use, elderly_use,
            is_standard
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False
    finally:
        conn.close()

def load_catalog_data():
    """读取公共库数据"""
    conn = get_connection()
    try:
        # 优先展示官方数据 (is_standard DESC)
        df = pd.read_sql_query("SELECT * FROM medicine_catalog ORDER BY is_standard DESC, created_at DESC", conn)
        return df
    finally:
        conn.close()

# ==========================================
# B. 家庭库存服务 (基本无变化)
# ==========================================

def add_inventory_item(barcode, expiry_date, quantity_val, location, owner, my_dosage):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO inventory (barcode, expiry_date, quantity_val, location, owner, my_dosage)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (barcode, expiry_date, quantity_val, location, owner, my_dosage))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"❌ 入库失败: 条形码 {barcode} 未录入基础库")
        return False
    except Exception as e:
        print(f"❌ 库存添加失败: {e}")
        return False
    finally:
        conn.close()

# ==========================================
# C. 查询与展示
# ==========================================

def load_data():
    conn = get_connection()
    try:
        sql = """
        SELECT 
            i.id, i.barcode,
            c.name, c.manufacturer, c.spec, c.form, c.unit,
            i.quantity_val, i.expiry_date, i.location, i.owner,
            c.indications, c.child_use, c.contraindications, c.is_standard,
            i.my_dosage
        FROM inventory i
        LEFT JOIN medicine_catalog c ON i.barcode = c.barcode
        ORDER BY i.expiry_date ASC
        """
        df = pd.read_sql_query(sql, conn)
        if not df.empty:
            df['quantity_display'] = df['quantity_val'].astype(str) + " " + df['unit'].fillna('')
            df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        return df
    finally:
        conn.close()

def get_dashboard_metrics():
    df = load_data()
    if df.empty: return 0, 0, 0
    dates = pd.to_datetime(df['expiry_date']).dt.date
    today = date.today()
    total = len(df)
    expired = len(dates[dates < today])
    soon = len(dates[(dates >= today) & (dates <= (today + timedelta(days=90)))])
    return total, expired, soon

# ==========================================
# D. 更新与删除
# ==========================================

def update_quantity(med_id, new_quantity_val):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE inventory SET quantity_val = ? WHERE id = ?", (new_quantity_val, med_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 更新数量失败: {e}")
        return False
    finally:
        conn.close()

def delete_medicine(med_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM inventory WHERE id = ?", (med_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        return False
    finally:
        conn.close()

# ==========================================
# E. AI 专用接口
# ==========================================

def get_inventory_str_for_ai():
    conn = get_connection()
    try:
        sql = """
        SELECT 
            i.id, c.name, c.manufacturer, i.quantity_val, c.unit, i.location, i.owner, i.expiry_date,
            c.indications, c.contraindications, c.child_use, c.pregnancy_lactation_use, i.my_dosage, c.is_standard
        FROM inventory i
        LEFT JOIN medicine_catalog c ON i.barcode = c.barcode
        WHERE i.expiry_date >= DATE('now')
        """
        df = pd.read_sql_query(sql, conn)
        if df.empty: return "库存为空。"

        inventory_list = []
        for _, row in df.iterrows():
            # 增加一个标记告诉AI这是官方数据
            source_tag = "[官方数据]" if row['is_standard'] else "[用户录入]"
            item = (
                f"- ID:{row['id']} {source_tag} | {row['name']} | "
                f"剩:{row['quantity_val']}{row['unit']} | {row['location']} | "
                f"禁忌:{str(row['contraindications'])[:30]} | "
                f"儿童:{str(row['child_use'])[:30]} | "
                f"医嘱:{row['my_dosage']}"
            )
            inventory_list.append(item)
        return "\n".join(inventory_list)
    finally:
        conn.close()