import streamlit as st
import pandas as pd
from datetime import date
from src.services import (
    add_medicine, 
    load_data, 
    get_dashboard_metrics, 
    update_quantity, 
    delete_medicine,
    get_inventory_str_for_ai
)
# 这里的 src.services 之所以在 app.py 能跑通，是因为 app.py 在根目录

# --- 页面配置 ---
st.set_page_config(page_title="HomeMeds AI", page_icon="💊", layout="wide")

# --- 侧边栏逻辑 ---
with st.sidebar:
    st.title("🏥 家庭药箱助手")
    
    # 导航菜单
    menu = st.radio("导航", ["🏠 药箱看板", "💊 药品操作", "🤖 AI 药剂师"])
    
    st.divider()
    
    # API 设置区
    with st.expander("⚙️ 系统设置 (AI配置)"):
        api_base = st.text_input("API Base URL", value="https://api.deepseek.com")
        api_key = st.text_input("API Key", type="password", help="在此输入你的 DeepSeek 或 OpenAI Key")
        
        if api_key:
            st.session_state['api_key'] = api_key
            st.session_state['api_base'] = api_base
            st.success("API Key 已暂存")

# --- 页面 1: 药箱看板 ---
def show_dashboard():
    st.header("📊 药箱实时看板")
    
    # 1. 指标卡片
    total, expired, soon = get_dashboard_metrics()
    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 总库存", f"{total} 种")
    col2.metric("🟡 临期预警 (90天内)", f"{soon} 种")
    col3.metric("🔴 已过期", f"{expired} 种", delta_color="inverse")
    
    st.divider()
    
    # 2. 搜索与筛选
    search_term = st.text_input("🔍 搜索药品 (支持名称或标签)", placeholder="例如：感冒, 布洛芬...")
    
    # 3. 数据表格展示
    df = load_data()
    
    if not df.empty:
        # 数据处理：计算是否过期，用于高亮
        today = pd.to_datetime("today").normalize()
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        
        # 搜索过滤逻辑
        if search_term:
            df = df[
                df['name'].str.contains(search_term, case=False) | 
                df['tags'].str.contains(search_term, case=False)
            ]

        # 样式函数：过期的标红
        def highlight_expired(row):
            if row['expiry_date'] < today:
                return ['background-color: #ffcccc'] * len(row)
            elif row['expiry_date'] < today + pd.Timedelta(days=90):
                return ['background-color: #ffffe0'] * len(row)
            return [''] * len(row)

        # 展示表格 (只展示关键列)
        display_cols = ['id', 'name', 'quantity', 'expiry_date', 'location', 'tags', 'effect_text']
        st.dataframe(
            df[display_cols].style.apply(highlight_expired, axis=1), 
            use_container_width=True,
            column_config={
                "expiry_date": st.column_config.DateColumn("过期日期", format="YYYY-MM-DD"),
                "effect_text": st.column_config.TextColumn("功效", width="medium"),
            }
        )
    else:
        st.info("药箱是空的，快去「药品操作」里添加吧！")

# --- 页面 2: 药品操作 ---
def show_operations():
    st.header("💊 药品管理")
    tab1, tab2, tab3 = st.tabs(["🥣 我要吃药/更新", "➕ 新药入库", "🗑️ 删库/清理"])
    
    # --- Tab 1: 更新库存 ---
    with tab1:
        st.subheader("更新药品状态")
        df = load_data()
        if df.empty:
            st.warning("暂无数据")
        else:
            # 制作一个下拉选项： "ID - 药名 (位置)"
            med_options = {f"{row['id']} - {row['name']} ({row['location']})": row['id'] for _, row in df.iterrows()}
            selected_label = st.selectbox("选择药品", list(med_options.keys()))
            selected_id = med_options[selected_label]
            
            # 获取当前选中药品的详情
            current_med = df[df['id'] == selected_id].iloc[0]
            st.info(f"当前状态: {current_med['quantity']}")
            
            new_qty = st.select_slider("更新后剩余量:", options=["满盒/未拆", "剩余大半", "剩余一半", "少量", "已空"], value=current_med['quantity'])
            
            if st.button("更新状态"):
                if new_qty == "已空":
                    delete_medicine(selected_id)
                    st.success(f"{current_med['name']} 已用完，已从数据库移除！")
                    st.rerun()
                else:
                    update_quantity(selected_id, new_qty)
                    st.success("状态已更新！")
                    st.rerun()

    # --- Tab 2: 新增入库 ---
    with tab2:
        st.subheader("录入新药")
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("药品通用名", placeholder="如: 布洛芬缓释胶囊")
            brand = c2.text_input("品牌", placeholder="如: 芬必得")
            
            c3, c4 = st.columns(2)
            loc = c3.selectbox("存放位置", ["客厅电视柜", "餐边柜", "主卧抽屉", "冰箱冷藏", "随身包", "其他"])
            qty = c4.select_slider("初始状态", options=["满盒/未拆", "剩余大半", "剩余一半", "少量"])
            
            exp_date = st.date_input("过期日期")
            tags = st.text_input("快速标签 (逗号分隔)", placeholder="如: #发烧, #止痛")
            effect = st.text_area("功能主治 (非常重要，用于AI识别)", placeholder="请抄写说明书上的适应症，例如：用于缓解轻至中度疼痛如头痛...")
            
            submitted = st.form_submit_button("📥 确认入库", type="primary")
            if submitted:
                if name and effect:
                    add_medicine(name, brand, effect, exp_date, qty, loc, tags)
                    st.toast(f"✅ {name} 入库成功！")
                else:
                    st.error("药名和功能主治不能为空！")

    # --- Tab 3: 删除 ---
    with tab3:
        st.subheader("批量清理")
        df = load_data()
        if not df.empty:
            # 多选框
            to_delete_labels = st.multiselect("选择要删除的药品", options=[f"{row['id']} - {row['name']}" for _, row in df.iterrows()])
            if st.button("🗑️ 确认删除", type="primary"):
                for label in to_delete_labels:
                    med_id = int(label.split(" - ")[0])
                    delete_medicine(med_id)
                st.success("删除成功！")
                st.rerun()

# --- 页面 3: AI 药剂师 ---
def show_ai_doctor():
    st.header("🤖 私人 AI 药剂师")
    
    if 'api_key' not in st.session_state:
        st.warning("⚠️ 请先在左侧侧边栏设置 API Key 才能使用 AI 功能。")
        return

    # 初始化聊天历史
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 展示历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 处理用户输入
    if prompt := st.chat_input("请描述您的症状 (例如: 嗓子疼，有点流鼻涕)..."):
        # 1. 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. 准备 AI 上下文 (RAG 核心步骤)
        inventory_context = get_inventory_str_for_ai()
        
        system_prompt = f"""
        你是一个专业的家庭全科医生。
        以下是用户家里的【现有库存药品清单】（已自动过滤过期药）：
        {inventory_context}
        
        用户正在咨询症状。请遵循以下规则：
        1. **优先推荐**：只能推荐清单里有的药。
        2. **位置指引**：必须告诉用户药在哪里（清单里有 location）。
        3. **安全第一**：如果清单里没有对症的药，请直接建议就医或去药店购买，不要瞎编。
        4. **简洁回复**：直接给出建议方案。
        """

        # 3. 调用 API (使用 OpenAI 兼容格式，适配 DeepSeek)
        from openai import OpenAI
        
        client = OpenAI(api_key=st.session_state['api_key'], base_url=st.session_state['api_base'])
        
        with st.chat_message("assistant"):
            try:
                stream = client.chat.completions.create(
                    model="deepseek-chat", # 如果是用 OpenAI 改成 gpt-3.5-turbo
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"AI 调用失败: {e}")

# --- 主路由 ---
if menu == "🏠 药箱看板":
    show_dashboard()
elif menu == "💊 药品操作":
    show_operations()
elif menu == "🤖 AI 药剂师":
    show_ai_doctor()