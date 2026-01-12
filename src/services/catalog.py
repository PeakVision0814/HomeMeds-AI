# src/services/catalog.py
import pandas as pd
from src.database import get_connection

def get_catalog_info(query):
    conn = get_connection()
    try:
        sql = """
        SELECT * FROM medicine_catalog 
        WHERE barcode = ? OR name LIKE ? LIMIT 1
        """
        df = pd.read_sql_query(sql, conn, params=(query, f"%{query}%"))
        if not df.empty:
            return df.iloc[0].fillna("").to_dict()
        return None
    finally:
        conn.close()

def upsert_catalog_item(barcode, name, manufacturer, spec, form, unit, 
                       indications, std_usage, adverse_reactions, 
                       contraindications, precautions, 
                       pregnancy_lactation_use, child_use, elderly_use,
                       is_standard=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO medicine_catalog (
            barcode, name, manufacturer, spec, form, unit, indications, std_usage, 
            adverse_reactions, contraindications, precautions, pregnancy_lactation_use, child_use, elderly_use, is_standard
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(barcode) DO UPDATE SET
            name=excluded.name, manufacturer=excluded.manufacturer, spec=excluded.spec,
            form=excluded.form, unit=excluded.unit, indications=excluded.indications,
            std_usage=excluded.std_usage, adverse_reactions=excluded.adverse_reactions,
            contraindications=excluded.contraindications, precautions=excluded.precautions,
            pregnancy_lactation_use=excluded.pregnancy_lactation_use, child_use=excluded.child_use,
            elderly_use=excluded.elderly_use, is_standard=excluded.is_standard;
        """
        cursor.execute(sql, (
            barcode, name, manufacturer, spec, form, unit, indications, std_usage, 
            adverse_reactions, contraindications, precautions, pregnancy_lactation_use, child_use, elderly_use, is_standard
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False
    finally:
        conn.close()

def load_catalog_data():
    conn = get_connection()
    try:
        return pd.read_sql_query("SELECT * FROM medicine_catalog ORDER BY is_standard DESC, created_at DESC", conn)
    finally:
        conn.close()