# src/views/sidebar.py
import streamlit as st
from src.database import export_seed_data
from src.services.members import get_all_members, add_member, delete_member

def show_sidebar():
    with st.sidebar:
        st.title("🏥 家庭药箱助手 Pro")
        st.caption("v0.7")
        
        menu = st.radio("导航", ["🏠 药箱看板", "💊 药品操作", "📖 公共药库", "🤖 AI 药剂师"])
        st.divider()

        # === 👇 新增：家庭成员管理区域 👇 ===
        with st.expander("👨‍👩‍👧‍👦 家庭成员管理"):
            current_members = get_all_members()
            
            # 1. 展示标签
            st.caption("当前成员：")
            st.markdown(" ".join([f"`{m}`" for m in current_members]))
            
            # 2. 添加
            c1, c2 = st.columns([2, 1])
            new_name = c1.text_input("新名字", placeholder="如: 爷爷", label_visibility="collapsed")
            if c2.button("➕添加"):
                ok, msg = add_member(new_name)
                if ok: st.success(msg); st.rerun()
                else: st.error(msg)
            
            # 3. 删除
            st.caption("删除成员：")
            del_name = st.selectbox("选择删除", [""] + current_members, label_visibility="collapsed")
            if del_name and st.button("🗑️ 确认删除"):
                delete_member(del_name)
                st.success(f"已删除 {del_name}")
                st.rerun()
        
        st.divider()
        
        # 维护者模式
        st.markdown("### 👨‍💻 开发者模式")
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