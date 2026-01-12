# src/views/catalog.py
import streamlit as st
from src.services.catalog import load_catalog_data

def show_catalog():
    st.header("📖 药品知识库")
    df = load_catalog_data()
    if not df.empty:
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={
                "is_standard": st.column_config.CheckboxColumn("官方", width="small"),
                "name": "通用名", "manufacturer": "厂商", "indications": "适应症"
            }
        )
    else:
        st.info("库是空的")