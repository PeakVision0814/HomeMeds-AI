# src/views/dashboard.py
import streamlit as st
import pandas as pd
from src.services.queries import load_data, get_dashboard_metrics

def show_dashboard():
    st.header("📊 药箱实时看板")
    total, expired, soon = get_dashboard_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 总库存", total)
    c2.metric("🟡 临期预警", soon)
    c3.metric("🔴 已过期", expired, delta_color="inverse")
    
    st.divider()
    
    col_s, col_f = st.columns([3, 1])
    search = col_s.text_input("🔍 搜索库存", placeholder="药名/适应症...")
    owner = col_f.selectbox("归属人", ["全部", "公用", "爸爸", "妈妈", "宝宝", "老人"])
    
    df = load_data()
    if not df.empty:
        if search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            df = df[mask]
        if owner != "全部":
            df = df[df['owner'] == owner]
            
        today = pd.to_datetime("today").normalize()
        def style_rows(row):
            exp = pd.to_datetime(row['expiry_date'])
            
            # 🔴 已过期
            if exp < today: 
                # 修复：增加 color: black，强制文字变黑，防止在暗色模式下由白字变成不可见
                return ['background-color: #ffcccc; color: black'] * len(row)
            
            # 🟡 临期预警
            if exp < today + pd.Timedelta(days=90): 
                # 修复：增加 color: black
                return ['background-color: #ffffe0; color: black'] * len(row)
            
            # ⚪ 正常状态 (使用默认样式，暗色模式下就是黑底白字)
            return [''] * len(row)

        st.dataframe(
            df.style.apply(style_rows, axis=1),
            use_container_width=True, hide_index=True,
            column_order=["name", "quantity_display", "expiry_date", "owner", "indications", "is_standard"],
            column_config={
                "name": "药品 (厂商)", "quantity_display": "剩余", 
                "expiry_date": st.column_config.DateColumn("效期", format="YYYY-MM-DD"),
                "is_standard": st.column_config.CheckboxColumn("官方", width="small")
            }
        )
    else:
        st.info("暂无库存")