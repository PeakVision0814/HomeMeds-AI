# src/services/members.py
import sqlite3
from src.database import get_connection

def get_all_members():
    """获取所有成员名单 (列表)"""
    conn = get_connection()
    try:
        # 按 ID 排序，保证顺序稳定
        rows = conn.execute("SELECT name FROM family_members ORDER BY id").fetchall()
        return [r['name'] for r in rows]
    finally:
        conn.close()

def add_member(name):
    """添加新成员"""
    conn = get_connection()
    try:
        name = name.strip()
        if not name: return False, "名字不能为空"
        conn.execute("INSERT INTO family_members (name) VALUES (?)", (name,))
        conn.commit()
        return True, "添加成功"
    except sqlite3.IntegrityError:
        return False, "该成员已存在"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_member(name):
    """删除成员"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM family_members WHERE name = ?", (name,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()