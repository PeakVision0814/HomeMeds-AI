# src/views/sidebar.py
import streamlit as st
from src.database import export_seed_data

def show_sidebar():
    with st.sidebar:
        st.title("🏥 家庭药箱助手 Pro")
        st.caption("v0.6 模块化重构版")
        
        menu = st.radio("导航", ["🏠 药箱看板", "💊 药品操作", "📖 公共药库", "🤖 AI 药剂师"])
        st.divider()
        
        # 维护者模式
        st.markdown("### 👨‍💻 维护者模式")
        dev_mode = st.checkbox("我是维护者/作者")
        if dev_mode:
            st.success("🔓 开发者模式已激活")
            if st.button("📤 导出官方种子文件"):
                try:
                    c = export_seed_data()
                    st.toast(f"✅ 导出 {c} 条数据")
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("🔒 用户模式：官方数据只读")
            
        st.divider()
        with st.expander("⚙️ AI 设置"):
            st.session_state['api_base'] = st.text_input("API Base", value="https://api.deepseek.com")
            key = st.text_input("API Key", type="password")
            if key: st.session_state['api_key'] = key
            
        return menu, dev_mode