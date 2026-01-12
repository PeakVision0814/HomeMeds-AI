# src/services/queries.py
import pandas as pd
from datetime import date, timedelta
from src.database import get_connection

def load_data():
    conn = get_connection()
    try:
        sql = """
        SELECT 
            i.id, i.barcode, c.name, c.manufacturer, c.spec, c.form, c.unit,
            i.quantity_val, i.expiry_date, i.owner, c.indications, c.child_use, 
            c.contraindications, c.is_standard, i.my_dosage
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
    return len(df), len(dates[dates < today]), len(dates[(dates >= today) & (dates <= (today + timedelta(days=90)))])