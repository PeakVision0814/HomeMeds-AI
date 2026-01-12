# src/services/ai_service.py
import pandas as pd
from src.database import get_connection

def get_inventory_str_for_ai():
    conn = get_connection()
    try:
        sql = """
        SELECT i.id, c.name, c.manufacturer, i.quantity_val, c.unit, i.owner, 
               c.indications, c.contraindications, c.child_use, i.my_dosage, c.is_standard
        FROM inventory i LEFT JOIN medicine_catalog c ON i.barcode = c.barcode
        WHERE i.expiry_date >= DATE('now')
        """
        df = pd.read_sql_query(sql, conn)
        if df.empty: return "库存为空。"
        
        lines = []
        for _, r in df.iterrows():
            tag = "[官方]" if r['is_standard'] else "[用户]"
            lines.append(f"- {r['name']}{tag} | 剩:{r['quantity_val']}{r['unit']} | 属:{r['owner']} | 禁:{str(r['contraindications'])[:20]} | 儿:{str(r['child_use'])[:20]}")
        return "\n".join(lines)
    finally:
        conn.close()