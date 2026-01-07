import streamlit as st
import pandas as pd
from datetime import date
from src.services import (
    load_data, 
    get_dashboard_metrics, 
    update_quantity, 
    delete_medicine,
    get_inventory_str_for_ai,
    get_catalog_info,
    quick_add_medicine,
    load_catalog_data  # <--- 新增引入这个!
)

# --- 页面配置 ---
st.set_page_config(page_title="HomeMeds AI", page_icon="💊", layout="wide")

# --- 侧边栏逻辑 ---
with st.sidebar:
    st.title("🏥 家庭药箱助手")
    st.caption("v0.3 双表架构版")
    
    # 导航菜单
    menu = st.radio("导航", ["🏠 药箱看板", "💊 药品操作", "📖 公共药库", "🤖 AI 药剂师"])
    
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
    col1.metric("🟢 总库存", f"{total} 个")
    col2.metric("🟡 临期预警 (90天内)", f"{soon} 个")
    col3.metric("🔴 已过期", f"{expired} 个", delta_color="inverse")
    
    st.divider()
    
    # 2. 搜索与筛选
    c1, c2 = st.columns([3, 1])
    with c1:
        search_term = st.text_input("🔍 搜索 (支持药名、品牌、症状、归属人)", placeholder="例如：感冒, 宝宝...")
    with c2:
        filter_owner = st.selectbox("按归属人筛选", ["全部", "公用", "爸爸", "妈妈", "宝宝", "老人"])
    
    # 3. 数据表格展示
    df = load_data()
    
    if not df.empty:
        # 数据预处理
        today = pd.to_datetime("today").normalize()
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        
        # 筛选逻辑
        if search_term:
            # 这里的字段名要和 load_data 返回的一致
            mask = (
                df['name'].str.contains(search_term, case=False) | 
                df['tags'].str.contains(search_term, case=False) |
                df['brand'].str.contains(search_term, case=False) |
                df['effect_text'].str.contains(search_term, case=False)
            )
            df = df[mask]
        
        if filter_owner != "全部":
            df = df[df['owner'] == filter_owner]

        # 样式函数：过期的标红
        def highlight_expired(row):
            if row['expiry_date'] < today:
                return ['background-color: #ffcccc'] * len(row)
            elif row['expiry_date'] < today + pd.Timedelta(days=90):
                return ['background-color: #ffffe0'] * len(row)
            return [''] * len(row)

        # 核心展示配置 (适配新字段)
        st.dataframe(
            df.style.apply(highlight_expired, axis=1), 
            use_container_width=True,
            hide_index=True,
            column_order=["id", "name", "brand", "quantity_display", "expiry_date", "location", "owner", "my_dosage", "effect_text"], 
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "name": st.column_config.TextColumn("药品名称", width="medium"),
                "brand": st.column_config.TextColumn("品牌", width="small"),
                "quantity_display": st.column_config.TextColumn("剩余量", width="small"), # 12.0 粒
                "expiry_date": st.column_config.DateColumn("过期日期", format="YYYY-MM-DD"),
                "location": st.column_config.TextColumn("位置", width="small"),
                "owner": st.column_config.TextColumn("归属", width="small"),
                "my_dosage": st.column_config.TextColumn("医嘱/备注", width="medium"),
                "effect_text": st.column_config.TextColumn("功效 (AI)", width="large"),
            }
        )
    else:
        st.info("药箱空空如也，请去「药品操作」入库吧！")

# --- 页面 2: 药品操作 ---
def show_operations():
    st.header("💊 药品管理")
    tab1, tab2, tab3 = st.tabs(["🥣 我要吃药/更新", "➕ 新药入库 (扫码版)", "🗑️ 删库/清理"])
    
    # --- Tab 1: 更新库存 ---
    with tab1:
        st.subheader("更新剩余数量")
        df = load_data()
        if df.empty:
            st.warning("暂无数据")
        else:
            # 下拉选项展示更多信息: ID - 药名 (归属人)
            med_options = {f"{row['id']} - {row['name']} ({row['owner']})": row['id'] for _, row in df.iterrows()}
            selected_label = st.selectbox("选择要操作的药品", list(med_options.keys()))
            selected_id = med_options[selected_label]
            
            # 获取当前选中药品的详情
            current_med = df[df['id'] == selected_id].iloc[0]
            
            # 展示当前信息
            st.info(f"当前库存: **{current_med['quantity_val']} {current_med['unit']}** | 位置: {current_med['location']}")
            
            # 数字输入框 (步长根据单位智能调整，如果是ml则0.1，如果是粒则1)
            step = 0.5 if current_med['unit'] in ['ml', 'g', '瓶'] else 1.0
            new_val = st.number_input("修正后的剩余数值", value=float(current_med['quantity_val']), step=step, min_value=0.0)
            
            if st.button("更新状态"):
                if new_val == 0:
                    delete_medicine(selected_id)
                    st.success(f"{current_med['name']} 已用完，已自动移除！")
                    st.rerun()
                else:
                    update_quantity(selected_id, new_val)
                    st.success(f"已更新为 {new_val} {current_med['unit']}")
                    st.rerun()

    # --- Tab 2: 新增入库 (核心升级) ---
    with tab2:
        st.subheader("智能入库流程")
        
        # Step 1: 扫码/输码区
        col_scan, col_tip = st.columns([2, 1])
        with col_scan:
            # 这是一个独立于 Form 的输入框，输入完回车会自动刷新页面
            barcode_input = st.text_input("📸 第一步: 扫码或输入条形码 (按回车查询)", placeholder="例如: 69xxxx...", key="barcode_input")
        with col_tip:
            st.caption("ℹ️ 如果是库里已有的药，下方会自动填好信息。如果是新药，请手动补全，下次就记住了。")

        # 状态管理：初始化默认值
        default_vals = {
            "name": "", "brand": "", "spec": "", "form": "胶囊", 
            "unit": "粒", "effect": "", "usage": "", "tags": ""
        }
        
        # 如果用户输入了条码，去 Catalog 查一下
        if barcode_input:
            catalog_data = get_catalog_info(barcode_input)
            if catalog_data:
                st.toast(f"🎉 发现已收录药品: {catalog_data['name']}")
                # 覆盖默认值
                default_vals.update({
                    "name": catalog_data['name'],
                    "brand": catalog_data['brand'],
                    "spec": catalog_data['spec'],
                    "form": catalog_data['form'],
                    "unit": catalog_data['unit'],
                    "effect": catalog_data['effect_text'],
                    "usage": catalog_data['std_usage'],
                    "tags": catalog_data['tags']
                })
            else:
                st.info("🆕 这是一个新条码，请录入一次公共信息。")

        st.divider()

        # Step 2: 填写详细表单
        with st.form("add_full_form", clear_on_submit=True):
            st.markdown("#### 1️⃣ 公共信息 (Catalog)")
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("药品通用名 *", value=default_vals['name'])
            brand = c2.text_input("品牌", value=default_vals['brand'])
            spec = c3.text_input("规格", value=default_vals['spec'], placeholder="0.3g*24粒")
            
            c4, c5 = st.columns(2)
            form = c4.selectbox("剂型", ["胶囊", "片剂", "颗粒/冲剂", "口服液", "软膏/外用", "喷雾", "其他"], index=["胶囊", "片剂", "颗粒/冲剂", "口服液", "软膏/外用", "喷雾", "其他"].index(default_vals['form']) if default_vals['form'] in ["胶囊", "片剂", "颗粒/冲剂", "口服液", "软膏/外用", "喷雾", "其他"] else 0)
            unit = c5.selectbox("最小计量单位", ["粒", "片", "包/袋", "ml", "瓶/支", "g", "盒"], index=["粒", "片", "包/袋", "ml", "瓶/支", "g", "盒"].index(default_vals['unit']) if default_vals['unit'] in ["粒", "片", "包/袋", "ml", "瓶/支", "g", "盒"] else 0)
            
            effect = st.text_area("功能主治 (AI核心) *", value=default_vals['effect'], height=80)
            std_usage = st.text_input("说明书用法", value=default_vals['usage'])
            tags = st.text_input("标签 (逗号分隔)", value=default_vals['tags'])

            st.markdown("#### 2️⃣ 本次库存 (Inventory)")
            i1, i2, i3 = st.columns(3)
            # 注意：如果不输条码，这里会拦截
            final_barcode = i1.text_input("确认条形码 *", value=barcode_input, disabled=True) 
            qty_val = i2.number_input("剩余数量", min_value=0.1, value=1.0, step=1.0)
            exp_date = i3.date_input("过期日期 *")
            
            i4, i5, i6 = st.columns(3)
            loc = i4.selectbox("存放位置", ["客厅电视柜", "餐边柜", "主卧抽屉", "冰箱", "急救包"])
            owner = i5.selectbox("归属人", ["公用", "爸爸", "妈妈", "宝宝", "老人"])
            my_dosage = i6.text_input("个人医嘱/备注", placeholder="如: 发烧38.5才吃")

            submitted = st.form_submit_button("📥 确认入库", type="primary")
            
            if submitted:
                if not barcode_input:
                    st.error("❌ 必须输入条形码才能入库！")
                elif not name or not effect:
                    st.error("❌ 药名和功能主治不能为空！")
                else:
                    # 组装大字典
                    full_data = {
                        "barcode": barcode_input,
                        "name": name, "brand": brand, "spec": spec,
                        "form": form, "unit": unit,
                        "effect_text": effect, "std_usage": std_usage, "tags": tags,
                        "expiry_date": exp_date,
                        "quantity_val": qty_val,
                        "location": loc, "owner": owner, "my_dosage": my_dosage
                    }
                    
                    if quick_add_medicine(full_data):
                        st.success(f"✅ {name} 入库成功！")
                    else:
                        st.error("入库失败，请检查日志")

    # --- Tab 3: 删除 ---
    with tab3:
        st.subheader("批量清理")
        df = load_data()
        if not df.empty:
            to_delete_labels = st.multiselect("选择要删除的库存记录", options=[f"{row['id']} - {row['name']}" for _, row in df.iterrows()])
            if st.button("🗑️ 确认删除", type="primary"):
                for label in to_delete_labels:
                    med_id = int(label.split(" - ")[0])
                    delete_medicine(med_id)
                st.success("删除成功！")
                st.rerun()


# --- 页面 4: 公共药库 (新增) ---
def show_catalog_viewer():
    st.header("📖 公共药品基础库")
    st.caption("这里存放了所有只要录入过的药品信息（即使库存吃完了，这里还在）。")
    
    df = load_catalog_data()
    
    if not df.empty:
        # 搜索框
        search = st.text_input("🔍 搜索基础库", placeholder="药名、条码、功效...")
        if search:
            mask = (
                df['name'].str.contains(search, case=False) | 
                df['barcode'].str.contains(search, case=False) |
                df['effect_text'].str.contains(search, case=False)
            )
            df = df[mask]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "barcode": st.column_config.TextColumn("条形码", width="medium"),
                "name": st.column_config.TextColumn("通用名", width="medium"),
                "brand": st.column_config.TextColumn("品牌", width="small"),
                "effect_text": st.column_config.TextColumn("功效", width="large"),
                "created_at": st.column_config.DatetimeColumn("首次收录时间", format="YYYY-MM-DD HH:mm"),
            }
        )
    else:
        st.info("基础库还是空的，快去「药品操作」里扫码录入吧！")


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
    if prompt := st.chat_input("请描述您的症状 (例如: 宝宝半夜发烧39度，体重15kg)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 准备 AI 上下文 (已包含 Dosage 和 Owner)
        inventory_context = get_inventory_str_for_ai()
        
        system_prompt = f"""
        你是一个专业的家庭全科医生。
        以下是用户家里的【现有库存药品清单】（已自动过滤过期药）：
        {inventory_context}
        
        用户正在咨询症状。请严格遵循以下步骤进行推理：
        1. **分析患者身份**：从用户描述中判断是成人还是儿童（如提到“宝宝”、“体重”）。
        2. **匹配药物**：
           - 只能推荐清单里有的药。
           - **关键检查**：检查药物的【归属人】字段。如果用户是给宝宝问药，严禁推荐归属为“成人”或明显不适合儿童的药。
           - **剂型检查**：注意查看剩余量和剂型（如“剩0.5瓶”），如果库存不足要提示。
        3. **输出建议**：
           - 明确告知药物名称、存放位置。
           - 结合清单里的【备注医嘱】和【说明书用法】给出建议用量。
        4. **安全警告**：如果清单里没有对症药物，直接建议就医。
        """

        from openai import OpenAI
        client = OpenAI(api_key=st.session_state['api_key'], base_url=st.session_state['api_base'])
        
        with st.chat_message("assistant"):
            try:
                stream = client.chat.completions.create(
                    model="deepseek-chat",
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
elif menu == "📖 公共药库":  # <--- 新增路由分支
    show_catalog_viewer()
elif menu == "🤖 AI 药剂师":
    show_ai_doctor()