# src/services/inventory.py
import sqlite3
from src.database import get_connection

def add_inventory_item(barcode, expiry_date, quantity_val, owner, my_dosage):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO inventory (barcode, expiry_date, quantity_val, owner, my_dosage) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(sql, (barcode, expiry_date, quantity_val, owner, my_dosage))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"❌ 库存添加失败: {e}")
        return False
    finally:
        conn.close()

def update_quantity(med_id, new_quantity_val):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE inventory SET quantity_val = ? WHERE id = ?", (new_quantity_val, med_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def decrease_quantity(med_id, decrease_amount):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT quantity_val FROM inventory WHERE id = ?", (med_id,))
        row = cursor.fetchone()
        if not row: return False, "找不到记录"
        
        new_qty = max(0, row['quantity_val'] - decrease_amount)
        cursor.execute("UPDATE inventory SET quantity_val = ? WHERE id = ?", (new_qty, med_id))
        conn.commit()
        return True, new_qty
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_medicine(med_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM inventory WHERE id = ?", (med_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()