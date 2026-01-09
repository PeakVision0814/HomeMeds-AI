# app.py

import streamlit as st
import pandas as pd
from datetime import date
import os
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
from src.database import export_seed_data, SEED_FILE

st.set_page_config(page_title="HomeMeds Pro", page_icon="💊", layout="wide")

# ==========================================
# 侧边栏：全局配置
# ==========================================
with st.sidebar:
    st.title("🏥 家庭药箱助手 Pro")
    st.caption("v0.5 官方/用户数据隔离版")
    
    menu = st.radio("导航", ["🏠 药箱看板", "💊 药品操作", "📖 公共药库", "🤖 AI 药剂师"])
    st.divider()
    
    # --- 维护者模式开关 ---
    st.markdown("### 👨‍💻 维护者模式")
    dev_mode = st.checkbox("我是维护者/作者", help="勾选后可编辑官方标准数据，并可导出种子文件。普通用户请勿勾选。")
    
    if dev_mode:
        st.success("🔓 开发者模式已激活：您可以修改官方数据。")
        if st.button("📤 导出官方种子文件 (JSON)"):
            try:
                count = export_seed_data()
                st.toast(f"✅ 成功导出 {count} 条标准数据！")
            except Exception as e:
                st.error(f"导出失败: {e}")
    else:
        st.info("🔒 用户模式：官方数据只读，保障安全。")

    st.divider()
    
    # --- AI 设置 ---
    with st.expander("⚙️ AI 设置"):
        api_base = st.text_input("API Base", value="https://api.deepseek.com")
        api_key = st.text_input("API Key", type="password")
        if api_key:
            st.session_state['api_key'] = api_key
            st.session_state['api_base'] = api_base

# ==========================================
# 页面 1: 药箱看板
# ==========================================
def show_dashboard():
    st.header("📊 药箱实时看板")
    total, expired, soon = get_dashboard_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 总库存", total)
    c2.metric("🟡 临期预警", soon)
    c3.metric("🔴 已过期", expired, delta_color="inverse")
    
    st.divider()
    
    # 筛选
    col_s, col_f = st.columns([3, 1])
    search = col_s.text_input("🔍 搜索库存", placeholder="药名/适应症...")
    owner = col_f.selectbox("归属人", ["全部", "公用", "爸爸", "妈妈", "宝宝", "老人"])
    
    df = load_data()
    if not df.empty:
        # 过滤
        if search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            df = df[mask]
        if owner != "全部":
            df = df[df['owner'] == owner]
            
        # 样式：过期标红
        today = pd.to_datetime("today").normalize()
        def style_rows(row):
            exp = pd.to_datetime(row['expiry_date'])
            if exp < today: return ['background-color: #ffcccc'] * len(row)
            if exp < today + pd.Timedelta(days=90): return ['background-color: #ffffe0'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df.style.apply(style_rows, axis=1),
            use_container_width=True, hide_index=True,
            column_order=["name", "quantity_display", "expiry_date", "location", "owner", "indications", "is_standard"],
            column_config={
                "name": st.column_config.TextColumn("药品 (厂商)", width="medium"),
                "quantity_display": "剩余",
                "expiry_date": st.column_config.DateColumn("效期", format="YYYY-MM-DD"),
                "is_standard": st.column_config.CheckboxColumn("官方认证", width="small"),
            }
        )
    else:
        st.info("暂无库存")

# app.py

# ... (保持前面的 import 和 sidebar 代码不变) ...

# ==========================================
# 页面 2: 药品操作 (修复版：补全所有字段)
# ==========================================
def show_operations():
    st.header("💊 药品管理")
    tab1, tab2, tab3 = st.tabs(["🥣 吃药/更新", "➕ 新药入库", "🗑️ 删库"])
    
    # --- Tab 1: 更新库存 (保持不变) ---
    with tab1:
        df = load_data()
        if not df.empty:
            opts = {f"{r['id']} - {r['name']} ({r['location']})": r['id'] for _, r in df.iterrows()}
            if opts:
                sel_id = opts[st.selectbox("选择药品", list(opts.keys()))]
                curr = df[df['id'] == sel_id].iloc[0]
                
                c1, c2 = st.columns(2)
                new_val = c1.number_input("新数量", value=float(curr['quantity_val']), step=1.0)
                if c2.button("💾 更新库存"):
                    if new_val <= 0:
                        delete_medicine(sel_id)
                        st.success("已用完移除")
                    else:
                        update_quantity(sel_id, new_val)
                        st.success("更新成功")
                    st.rerun()
            else:
                 st.info("暂无数据")
        else:
            st.info("暂无库存数据")

    # --- Tab 2: 入库 (修复核心：补全字段) ---
    with tab2:
        st.subheader("专业入库流程")
        barcode = st.text_input("📸 1. 扫码或输码", placeholder="例如 69xxx", key="op_barcode")
        
        catalog_exists = False
        is_locked = False
        # 初始化所有字段
        default_vals = {k: "" for k in ["name", "manuf", "spec", "form", "unit", "ind", "use", "adv", "contra", "prec", "preg", "child", "old"]}
        default_vals.update({"form": "胶囊", "unit": "粒"})
        
        if barcode:
            found = get_catalog_info(barcode)
            if found:
                catalog_exists = True
                # 权限判断
                if found.get('is_standard') == 1 and not dev_mode:
                    is_locked = True
                    st.toast(f"🔒 已调取官方数据: {found['name']} (只读)")
                else:
                    st.toast(f"✅ 已调取数据: {found['name']}")
                
                # 回填数据 (注意 key 要对应)
                default_vals.update({
                    "name": found['name'], "manuf": found['manufacturer'], "spec": found['spec'],
                    "form": found['form'], "unit": found['unit'], "ind": found['indications'],
                    "use": found['std_usage'], "adv": found['adverse_reactions'], 
                    "contra": found['contraindications'], "prec": found['precautions'],
                    "preg": found['pregnancy_lactation_use'], "child": found['child_use'],
                    "old": found['elderly_use']
                })
            else:
                st.info("🆕 新药，请录入信息")

        st.divider()
        
        if barcode:
            # === 基础信息表单 ===
            lock_msg = " (🔒 官方锁定)" if is_locked else ""
            with st.expander(f"1️⃣ 基础信息{lock_msg}", expanded=True):
                with st.form("cat_form"):
                    if is_locked:
                        st.info("ℹ️ 此为官方维护的标准数据，保障安全，无法修改。如需修改请在侧边栏开启维护者模式。")
                    
                    # 第一行：基本信息
                    c1, c2, c3 = st.columns([1.5, 1, 1])
                    name = c1.text_input("通用名 *", value=default_vals['name'], disabled=is_locked)
                    manuf = c2.text_input("生产企业", value=default_vals['manuf'], disabled=is_locked)
                    spec = c3.text_input("规格", value=default_vals['spec'], disabled=is_locked)
                    
                    # 第二行：剂型单位
                    c4, c5 = st.columns(2)
                    form = c4.selectbox("剂型", ["胶囊", "片剂", "颗粒", "口服液", "外用", "喷雾", "其他"], index=0 if not default_vals['form'] else ["胶囊", "片剂", "颗粒", "口服液", "外用", "喷雾", "其他"].index(default_vals['form']) if default_vals['form'] in ["胶囊", "片剂", "颗粒", "口服液", "外用", "喷雾", "其他"] else 6, disabled=is_locked)
                    unit = c5.selectbox("单位", ["粒", "片", "袋", "ml", "瓶", "盒", "支"], index=0 if not default_vals['unit'] else ["粒", "片", "袋", "ml", "瓶", "盒", "支"].index(default_vals['unit']) if default_vals['unit'] in ["粒", "片", "袋", "ml", "瓶", "盒", "支"] else 5, disabled=is_locked)
                    
                    # 第三行：核心功效
                    ind = st.text_area("适应症 *", value=default_vals['ind'], height=70, disabled=is_locked)
                    use = st.text_input("说明书用法", value=default_vals['use'], disabled=is_locked)
                    
                    st.markdown("---")
                    st.markdown("**🛡️ 安全用药信息**")
                    
                    # 第四行：禁忌与不良反应 (并排展示)
                    s1, s2 = st.columns(2)
                    contra = s1.text_area("🚫 禁忌", value=default_vals['contra'], height=70, disabled=is_locked, placeholder="如：对青霉素过敏者禁用")
                    adv = s2.text_area("🤢 不良反应", value=default_vals['adv'], height=70, disabled=is_locked)
                    
                    # 第五行：注意事项
                    prec = st.text_area("⚠️ 注意事项", value=default_vals['prec'], height=60, disabled=is_locked)
                    
                    # 第六行：特殊人群 (三列并排)
                    st.caption("👶👵 特殊人群用药")
                    p1, p2, p3 = st.columns(3)
                    preg = p1.text_input("🤰 孕妇/哺乳", value=default_vals['preg'], disabled=is_locked)
                    child = p2.text_input("👶 儿童用药", value=default_vals['child'], disabled=is_locked)
                    old = p3.text_input("👴 老年用药", value=default_vals['old'], disabled=is_locked)

                    # 提交按钮逻辑
                    if not is_locked:
                        btn_text = "💾 保存为官方标准数据" if dev_mode else "💾 保存"
                        if st.form_submit_button(btn_text):
                            if not name: 
                                st.error("通用名不能为空")
                            else:
                                # 这里调用 upsert 必须传入所有新字段
                                upsert_catalog_item(
                                    barcode, name, manuf, spec, form, unit, 
                                    ind, use, adv, contra, prec, preg, child, old,
                                    is_standard=1 if dev_mode else 0
                                )
                                st.success("基础信息已保存！")
                                st.rerun()
                    else:
                        st.form_submit_button("🔒 官方认证数据 (只读)", disabled=True)

            # === 库存表单 (保持不变) ===
            if catalog_exists:
                st.markdown("#### 2️⃣ 入库 (Inventory)")
                with st.form("inv_form", clear_on_submit=True):
                    i1, i2 = st.columns(2)
                    qty = i1.number_input("数量", min_value=1.0, value=1.0)
                    exp = i2.date_input("过期日期")
                    i3, i4, i5 = st.columns(3)
                    loc = i3.selectbox("位置", ["电视柜", "餐边柜", "冰箱", "急救包", "主卧"])
                    own = i4.selectbox("归属", ["公用", "爸爸", "妈妈", "宝宝", "老人"])
                    note = i5.text_input("备注/医嘱")
                    
                    if st.form_submit_button("📥 确认入库"):
                        add_inventory_item(barcode, exp, qty, loc, own, note)
                        st.success("入库成功")

    # --- Tab 3: 删库 (保持不变) ---
    with tab3:
        st.subheader("批量清理")
        df = load_data()
        if not df.empty:
            dels = st.multiselect("选择删除", [f"{r['id']}-{r['name']}" for _,r in df.iterrows()])
            if st.button("确认删除"):
                for d in dels: delete_medicine(int(d.split('-')[0]))
                st.success("已删除"); st.rerun()



# ==========================================
# 页面 3: 公共药库
# ==========================================
def show_catalog():
    st.header("📖 药品知识库")
    df = load_catalog_data()
    if not df.empty:
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={
                "is_standard": st.column_config.CheckboxColumn("官方", width="small"),
                "name": "通用名", "manufacturer": "厂商",
                "indications": "适应症"
            }
        )

# ==========================================
# 页面 4: AI 药剂师
# ==========================================
def show_ai():
    st.header("🤖 AI 药剂师")
    if 'api_key' not in st.session_state: 
        st.warning("请先设置 API Key")
        return
        
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages: st.chat_message(m["role"]).write(m["content"])
    
    if prompt := st.chat_input("输入症状..."):
        st.session_state.messages.append({"role":"user", "content":prompt})
        st.chat_message("user").write(prompt)
        
        ctx = get_inventory_str_for_ai()
        sys = f"基于库存回答。严格检查禁忌。库存信息：\n{ctx}"
        
        from openai import OpenAI
        client = OpenAI(api_key=st.session_state['api_key'], base_url=st.session_state['api_base'])
        try:
            stream = client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role":"system","content":sys},{"role":"user","content":prompt}], 
                stream=True
            )
            resp = st.write_stream(stream)
            st.session_state.messages.append({"role":"assistant", "content":resp})
        except Exception as e:
            st.error(str(e))

# 路由
if menu == "🏠 药箱看板": show_dashboard()
elif menu == "💊 药品操作": show_operations()
elif menu == "📖 公共药库": show_catalog()
elif menu == "🤖 AI 药剂师": show_ai()