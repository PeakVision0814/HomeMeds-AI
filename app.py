# app.py

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
    load_catalog_data,
    upsert_catalog_item,
    add_inventory_item
)

st.set_page_config(page_title="HomeMeds Pro", page_icon="💊", layout="wide")

# --- 侧边栏 ---
with st.sidebar:
    st.title("🏥 家庭药箱助手 Pro")
    st.caption("v0.4 专业版")
    menu = st.radio("导航", ["🏠 药箱看板", "💊 药品操作", "📖 公共药库", "🤖 AI 药剂师"])
    st.divider()
    with st.expander("⚙️ 系统设置"):
        api_base = st.text_input("API Base URL", value="https://api.deepseek.com")
        api_key = st.text_input("API Key", type="password")
        if api_key:
            st.session_state['api_key'] = api_key
            st.session_state['api_base'] = api_base
            st.success("API Key 已就绪")

# --- 页面 1: 药箱看板 ---
def show_dashboard():
    st.header("📊 药箱实时看板")
    total, expired, soon = get_dashboard_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 总库存", f"{total}")
    c2.metric("🟡 临期预警", f"{soon}")
    c3.metric("🔴 已过期", f"{expired}", delta_color="inverse")
    
    st.divider()
    
    # 搜索与筛选
    sc1, sc2 = st.columns([3, 1])
    search_term = sc1.text_input("🔍 搜索", placeholder="药名、适应症、厂家...")
    filter_owner = sc2.selectbox("归属人", ["全部", "公用", "爸爸", "妈妈", "宝宝", "老人"])
    
    df = load_data()
    if not df.empty:
        today = pd.to_datetime("today").normalize()
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        
        if search_term:
            mask = (
                df['name'].str.contains(search_term, case=False) | 
                df['manufacturer'].str.contains(search_term, case=False) | 
                df['indications'].str.contains(search_term, case=False)
            )
            df = df[mask]
        
        if filter_owner != "全部":
            df = df[df['owner'] == filter_owner]

        def highlight_expired(row):
            if row['expiry_date'] < today: return ['background-color: #ffcccc'] * len(row)
            elif row['expiry_date'] < today + pd.Timedelta(days=90): return ['background-color: #ffffe0'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df.style.apply(highlight_expired, axis=1), 
            use_container_width=True, hide_index=True,
            column_order=["id", "name", "quantity_display", "expiry_date", "location", "owner", "indications", "child_use"], 
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "name": st.column_config.TextColumn("药品名称 (厂商)", width="medium", help="点击查看详情"),
                "quantity_display": st.column_config.TextColumn("剩余", width="small"),
                "expiry_date": st.column_config.DateColumn("效期", format="YYYY-MM-DD"),
                "location": st.column_config.TextColumn("位置", width="small"),
                "owner": st.column_config.TextColumn("归属", width="small"),
                "indications": st.column_config.TextColumn("适应症", width="large"),
                "child_use": st.column_config.TextColumn("儿童用药", width="medium"),
            }
        )
    else:
        st.info("暂无数据")

# --- 页面 2: 药品操作 (核心修改) ---
def show_operations():
    st.header("💊 药品管理")
    tab1, tab2, tab3 = st.tabs(["🥣 我要吃药/更新", "➕ 新药入库", "🗑️ 删库"])
    
    # Tab 1: 更新数量 (保持精简)
    with tab1:
        st.subheader("更新剩余数量")
        df = load_data()
        if not df.empty:
            med_options = {f"{r['id']} - {r['name']}": r['id'] for _, r in df.iterrows()}
            sel_label = st.selectbox("选择药品", list(med_options.keys()))
            sel_id = med_options[sel_label]
            curr = df[df['id'] == sel_id].iloc[0]
            
            st.info(f"当前: {curr['quantity_val']} {curr['unit']} ({curr['location']})")
            new_val = st.number_input("新数量", value=float(curr['quantity_val']), min_value=0.0)
            if st.button("更新"):
                if new_val == 0:
                    delete_medicine(sel_id)
                    st.success("已用完移除")
                else:
                    update_quantity(sel_id, new_val)
                    st.success("更新成功")
                st.rerun()

    # Tab 2: 入库 (Pro 版表单)
    with tab2:
        st.subheader("专业入库流程")
        col_scan, _ = st.columns([2, 1])
        barcode_input = col_scan.text_input("📸 扫码/输码", placeholder="69xxx...", key="barcode_op")
        
        catalog_exists = False
        default_vals = {k: "" for k in ["name", "manuf", "spec", "form", "unit", "ind", "use", "adv", "contra", "prec", "preg", "child", "old"]}
        default_vals["form"] = "胶囊"
        default_vals["unit"] = "粒"

        if barcode_input:
            found = get_catalog_info(barcode_input)
            if found:
                catalog_exists = True
                st.toast(f"✅ 已调取: {found['name']}")
                default_vals.update({
                    "name": found['name'], "manuf": found['manufacturer'], "spec": found['spec'],
                    "form": found['form'], "unit": found['unit'], "ind": found['indications'],
                    "use": found['std_usage'], "adv": found['adverse_reactions'], 
                    "contra": found['contraindications'], "prec": found['precautions'],
                    "preg": found['pregnancy_lactation_use'], "child": found['child_use'],
                    "old": found['elderly_use']
                })
            else:
                st.info("🆕 新药，请完善以下专业信息")

        st.divider()

        if barcode_input:
            # === 1. 公共信息表单 ===
            title = "1️⃣ 药品基础信息 (Catalog)" + (" [已存在]" if catalog_exists else " [新建]")
            with st.expander(title, expanded=not catalog_exists):
                with st.form("cat_form"):
                    c1, c2, c3 = st.columns(3)
                    name = c1.text_input("通用名 *", value=default_vals['name'])
                    manuf = c2.text_input("生产企业", value=default_vals['manuf'])
                    spec = c3.text_input("规格", value=default_vals['spec'])
                    
                    c4, c5 = st.columns(2)
                    form = c4.selectbox("剂型", ["胶囊", "片剂", "颗粒", "口服液", "外用", "喷雾", "其他"], index=0)
                    unit = c5.selectbox("单位", ["粒", "片", "袋", "ml", "瓶", "支", "盒"], index=0)
                    
                    ind = st.text_area("适应症 *", value=default_vals['ind'], height=70)
                    use = st.text_input("说明书用法", value=default_vals['use'])
                    
                    st.markdown("---")
                    st.markdown("**🛡️ 安全用药信息 (选填)**")
                    
                    s1, s2 = st.columns(2)
                    contra = s1.text_area("🚫 禁忌", value=default_vals['contra'], placeholder="如: 对青霉素过敏者禁用")
                    adv = s2.text_area("🤢 不良反应", value=default_vals['adv'])
                    
                    prec = st.text_area("⚠️ 注意事项", value=default_vals['prec'])
                    
                    p1, p2, p3 = st.columns(3)
                    preg = p1.text_input("🤰 孕妇/哺乳", value=default_vals['preg'])
                    child = p2.text_input("👶 儿童用药", value=default_vals['child'])
                    old = p3.text_input("👴 老年用药", value=default_vals['old'])

                    if st.form_submit_button("💾 保存基础信息"):
                        if not name or not ind:
                            st.error("药名和适应症必填")
                        else:
                            res = upsert_catalog_item(
                                barcode_input, name, manuf, spec, form, unit, 
                                ind, use, adv, contra, prec, preg, child, old
                            )
                            if res: 
                                st.success("已保存"); st.rerun()

            # === 2. 库存表单 ===
            if catalog_exists:
                st.markdown("#### 2️⃣ 入库 (Inventory)")
                with st.form("inv_form", clear_on_submit=True):
                    i1, i2 = st.columns(2)
                    qty = i1.number_input("数量", min_value=0.1, value=1.0)
                    exp = i2.date_input("过期日期")
                    
                    i3, i4, i5 = st.columns(3)
                    loc = i3.selectbox("位置", ["电视柜", "餐边柜", "主卧", "冰箱", "急救包"])
                    own = i4.selectbox("归属", ["公用", "爸爸", "妈妈", "宝宝", "老人"])
                    note = i5.text_input("备注")
                    
                    if st.form_submit_button("📥 入库"):
                        if add_inventory_item(barcode_input, exp, qty, loc, own, note):
                            st.success("入库成功")

    # Tab 3: 删除 (保持精简)
    with tab3:
        st.subheader("批量清理")
        df = load_data()
        if not df.empty:
            dels = st.multiselect("选择删除", [f"{r['id']}-{r['name']}" for _,r in df.iterrows()])
            if st.button("确认删除"):
                for d in dels: delete_medicine(int(d.split('-')[0]))
                st.success("已删除"); st.rerun()

# --- 页面 3: 公共药库 ---
def show_catalog_viewer():
    st.header("📖 药品知识库")
    df = load_catalog_data()
    if not df.empty:
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={
                "name": "通用名", "manufacturer": "厂家", "indications": "适应症",
                "contraindications": "禁忌", "child_use": "儿童用药"
            }
        )
    else:
        st.info("暂无数据")

# --- 页面 4: AI ---
def show_ai_doctor():
    st.header("🤖 Pro版 AI 药剂师")
    if 'api_key' not in st.session_state: st.warning("请先设置 API Key"); return
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages: 
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("如: 宝宝3岁发烧能吃布洛芬吗？"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        context = get_inventory_str_for_ai()
        sys_prompt = f"""
        你是一位严谨的家庭药剂师。基于以下家庭库存回答：
        {context}
        
        严格规则：
        1. **禁忌优先**：如果库存药物的【禁忌】或【儿童用药】字段明确禁止当前用户（如儿童、孕妇），必须大写加粗警告！
        2. **信息匹配**：只能推荐库存有的药。
        3. **用药指导**：结合【适应症】和【说明书用法】给出建议。
        """
        
        from openai import OpenAI
        client = OpenAI(api_key=st.session_state['api_key'], base_url=st.session_state['api_base'])
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat", messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}], stream=True
            )
            response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

if menu == "🏠 药箱看板": show_dashboard()
elif menu == "💊 药品操作": show_operations()
elif menu == "📖 公共药库": show_catalog_viewer()
elif menu == "🤖 AI 药剂师": show_ai_doctor()