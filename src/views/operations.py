# src/views/operations.py
import streamlit as st
from src.services.queries import load_data
from src.services.inventory import update_quantity, delete_medicine, decrease_quantity, add_inventory_item
from src.services.catalog import get_catalog_info, upsert_catalog_item

def show_operations(dev_mode):
    st.header("💊 药品管理")
    tab1, tab2, tab3 = st.tabs(["🥣 吃药/更新", "➕ 新药入库", "🗑️ 删库"])
    
    # --- Tab 1 ---
    with tab1:
        st.subheader("💊 用药打卡与库存管理")
        df = load_data()
        if df.empty:
            st.info("📭 暂无库存")
        else:
            opts = {f"{r['name']} | 剩: {r['quantity_display']}": r['id'] for _, r in df.iterrows()}
            sel_id = opts[st.selectbox("👉 选择药品", list(opts.keys()))]
            curr = df[df['id'] == sel_id].iloc[0]
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🥣 吃药")
                if curr['unit'] in ['ml', 'g']: st.info("💡 液体建议用右侧修正")
                val = st.number_input(f"用量 ({curr['unit']})", 0.1, 1.0, 0.5)
                if st.button("💊 确认服药", type="primary", use_container_width=True):
                    ok, res = decrease_quantity(sel_id, val)
                    if ok: st.success(f"剩余: {res}"); st.rerun()
            
            with c2:
                st.markdown("#### 📝 修正")
                val = st.number_input(f"实际剩余 ({curr['unit']})", 0.0, float(curr['quantity_val']), 1.0)
                if st.button("💾 确认修正", use_container_width=True):
                    if val == 0: st.warning("数量为0"); update_quantity(sel_id, 0); st.rerun()
                    else: update_quantity(sel_id, val); st.success("已修正"); st.rerun()

            with st.expander("❓ 药膏怎么办"):
                st.write("推荐使用百分比法：入库填1，用一半改成0.5")

    # --- Tab 2 ---
    with tab2:
        st.subheader("专业入库流程")
        c_in, c_btn = st.columns([4, 1])
        user_input = c_in.text_input("🔍 扫码或输入药名", key="op_search")
        c_btn.write(""); c_btn.write("")
        c_btn.button("🔎 查询", type="primary", use_container_width=True)

        # 逻辑变量
        catalog_exists, is_locked, target_barcode = False, False, user_input
        defaults = {k: "" for k in ["name", "manuf", "spec", "form", "unit", "ind", "use", "adv", "contra", "prec", "preg", "child", "old"]}
        defaults.update({"form": "胶囊", "unit": "粒"})

        if user_input:
            found = get_catalog_info(user_input)
            if found:
                catalog_exists = True
                target_barcode = found['barcode']
                is_locked = (found.get('is_standard') == 1 and not dev_mode)
                if is_locked: st.toast(f"🔒 官方数据: {found['name']}")
                else: st.toast(f"✅ 已调取: {found['name']}")
                defaults.update({
                    "name": found['name'], "manuf": found['manufacturer'], "spec": found['spec'],
                    "form": found['form'], "unit": found['unit'], "ind": found['indications'],
                    "use": found['std_usage'], "adv": found['adverse_reactions'], 
                    "contra": found['contraindications'], "prec": found['precautions'],
                    "preg": found['pregnancy_lactation_use'], "child": found['child_use'],
                    "old": found['elderly_use']
                })
            else:
                if user_input.isdigit(): st.info("🆕 新条码")
                else: st.warning("⚠️ 未找到药名，请输入条码录入")

        st.divider()
        if target_barcode:
            with st.expander(f"1️⃣ 基础信息 {'(🔒)' if is_locked else ''}", expanded=True):
                st.caption(f"条码: {target_barcode}")
                with st.form("cat_form"):
                    c1, c2, c3 = st.columns([1.5, 1, 1])
                    name = c1.text_input("通用名 *", defaults['name'], disabled=is_locked)
                    manuf = c2.text_input("厂商", defaults['manuf'], disabled=is_locked)
                    spec = c3.text_input("规格", defaults['spec'], disabled=is_locked)
                    
                    c4, c5 = st.columns(2)
                    forms = ["胶囊", "片剂", "颗粒", "口服液", "外用", "喷雾", "其他"]
                    units = ["粒", "片", "袋", "ml", "瓶", "盒", "支"]
                    f_idx = forms.index(defaults['form']) if defaults['form'] in forms else 0
                    u_idx = units.index(defaults['unit']) if defaults['unit'] in units else 0
                    form = c4.selectbox("剂型", forms, index=f_idx, disabled=is_locked)
                    unit = c5.selectbox("单位", units, index=u_idx, disabled=is_locked)
                    
                    ind = st.text_area("适应症 *", defaults['ind'], height=70, disabled=is_locked)
                    use = st.text_input("用法", defaults['use'], disabled=is_locked)
                    
                    s1, s2 = st.columns(2)
                    contra = s1.text_area("🚫 禁忌", defaults['contra'], disabled=is_locked)
                    adv = s2.text_area("🤢 不良", defaults['adv'], disabled=is_locked)
                    prec = st.text_area("⚠️ 注意", defaults['prec'], height=60, disabled=is_locked)
                    
                    p1, p2, p3 = st.columns(3)
                    preg = p1.text_input("🤰 孕妇", defaults['preg'], disabled=is_locked)
                    child = p2.text_input("👶 儿童", defaults['child'], disabled=is_locked)
                    old = p3.text_input("👴 老年", defaults['old'], disabled=is_locked)

                    if not is_locked:
                        lbl = "💾 保存为官方" if dev_mode else "💾 保存"
                        if st.form_submit_button(lbl):
                            if not name: st.error("缺通用名")
                            else:
                                upsert_catalog_item(target_barcode, name, manuf, spec, form, unit, ind, use, adv, contra, prec, preg, child, old, 1 if dev_mode else 0)
                                st.success("保存成功"); st.rerun()
                    else:
                        st.form_submit_button("🔒 只读", disabled=True)

            if catalog_exists:
                st.markdown("#### 2️⃣ 入库")
                with st.form("inv_form", clear_on_submit=True):
                    i1, i2 = st.columns(2)
                    qty = i1.number_input("数量", 1.0)
                    exp = i2.date_input("过期日期")
                    i3, i4 = st.columns(2)
                    own = i3.selectbox("归属", ["公用", "爸爸", "妈妈", "宝宝", "老人"])
                    note = i4.text_input("备注")
                    if st.form_submit_button("📥 入库"):
                        add_inventory_item(target_barcode, exp, qty, own, note)
                        st.success("入库成功")

    # --- Tab 3 ---
    with tab3:
        df = load_data()
        if not df.empty:
            dels = st.multiselect("删谁", [f"{r['id']}-{r['name']}" for _, r in df.iterrows()])
            if st.button("确认删除"):
                for d in dels: delete_medicine(int(d.split('-')[0]))
                st.success("已删除"); st.rerun()