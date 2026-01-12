# app.py
import streamlit as st
from src.views.sidebar import show_sidebar
from src.views.dashboard import show_dashboard
from src.views.operations import show_operations
from src.views.catalog import show_catalog
from src.views.ai_doctor import show_ai_doctor

st.set_page_config(page_title="HomeMeds Pro", page_icon="💊", layout="wide")

# 1. 加载侧边栏，获取当前页面选择和开发者状态
menu, dev_mode = show_sidebar()

# 2. 路由分发
if menu == "🏠 药箱看板":
    show_dashboard()
elif menu == "💊 药品操作":
    show_operations(dev_mode)  # 传入开发者模式状态
elif menu == "📖 公共药库":
    show_catalog()
elif menu == "🤖 AI 药剂师":
    show_ai_doctor()