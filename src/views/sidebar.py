# src/views/sidebar.py
import streamlit as st
from src.database import export_seed_data
from src.services.members import get_all_members, add_member, delete_member

def show_sidebar():
    with st.sidebar:
        st.title("🏥 家庭药箱助手 Pro")
        st.caption("v0.9 站内过期提醒")
        
        menu = st.radio("导航", ["🏠 药箱看板", "💊 药品操作", "📖 公共药库", "🤖 AI 药剂师"])
        st.divider()
        
        # === 👨‍👩‍👧‍👦 家庭成员管理 (优化版) ===
        with st.expander("👨‍👩‍👧‍👦 家庭成员管理"):
            # 获取最新列表
            current_members = get_all_members()
            
            # 1. 展示列表
            st.caption("当前成员列表：")
            if current_members:
                # 使用 pills 或 markdown code 样式，紧凑展示
                st.markdown(" ".join([f"`{m}`" for m in current_members]))
            else:
                st.caption("暂无成员")
            
            # 🗑️ 去掉了 st.divider()，减少间距
            st.write("") # 仅添加一个微小的空行

            # 2. 添加成员 (带自动清空逻辑)
            st.caption("➕ 添加新成员")
            
            # 定义回调函数：处理添加 + 清空
            def on_add_click():
                # 从 session_state 获取输入框的值
                new_name = st.session_state.get("add_mem_input", "").strip()
                if new_name:
                    ok, msg = add_member(new_name)
                    if ok:
                        st.toast(f"✅ {msg}") # 使用 toast 提示，不打断流程
                        st.session_state["add_mem_input"] = "" # 🧹 关键：清空输入框绑定的变量
                    else:
                        st.toast(f"❌ {msg}")
                else:
                    st.toast("❌ 名字不能为空")

            # 输入框绑定 key
            st.text_input("新名字", placeholder="输入名字 (如: 爷爷)", label_visibility="collapsed", key="add_mem_input")
            
            # 按钮绑定 on_click 回调
            st.button("确认添加", type="secondary", use_container_width=True, on_click=on_add_click)
            
            st.write("") # 微小空行

            # 3. 删除成员
            st.caption("🗑️ 删除成员")
            
            # 定义删除回调
            def on_del_click():
                name_to_del = st.session_state.get("del_mem_select")
                if name_to_del and name_to_del != "请选择...":
                    delete_member(name_to_del)
                    st.toast(f"✅ 已删除成员: {name_to_del}")
            
            st.selectbox("选择要删除的成员", ["请选择..."] + current_members, label_visibility="collapsed", key="del_mem_select")
            
            st.button("执行删除", type="primary", use_container_width=True, on_click=on_del_click)
        
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