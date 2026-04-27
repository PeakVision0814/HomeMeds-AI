# src/services/queries.py
import pandas as pd
from datetime import date
from src.database import get_connection


EXPIRY_WARNING_DAYS = 90


def enrich_expiry_status(df, today=None, warning_days=EXPIRY_WARNING_DAYS):
    if df.empty:
        return df

    today = today or date.today()
    result = df.copy()
    expiry_dates = pd.to_datetime(result["expiry_date"]).dt.date
    result["days_until_expiry"] = expiry_dates.apply(lambda expiry: (expiry - today).days)

    def classify(days_left):
        if days_left < 0:
            return "expired"
        if days_left <= warning_days:
            return "expiring"
        return "normal"

    result["expiry_status"] = result["days_until_expiry"].apply(classify)
    return result


def filter_by_expiry_status(df, status):
    if df.empty or status == "all":
        return df
    if status == "attention":
        return df[df["expiry_status"].isin(["expired", "expiring"])]
    return df[df["expiry_status"] == status]

def load_data():
    conn = get_connection()
    try:
        # 👇 修改 SQL：增加了 c.tags
        sql = """
        SELECT 
            i.id, i.barcode,
            c.name, c.manufacturer, c.spec, c.form, c.unit, c.tags, 
            i.quantity_val, i.expiry_date, i.owner,
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
            df = enrich_expiry_status(df)
        return df
    finally:
        conn.close()

def get_dashboard_metrics():
    df = load_data()
    if df.empty: return 0, 0, 0
    return (
        len(df),
        len(df[df["expiry_status"] == "expired"]),
        len(df[df["expiry_status"] == "expiring"]),
    )


def get_expiry_alerts(limit=None):
    df = load_data()
    if df.empty:
        return df

    attention = filter_by_expiry_status(df, "attention")
    attention = attention.sort_values(["expiry_status", "days_until_expiry"])
    if limit is None:
        return attention
    return attention.head(limit)
