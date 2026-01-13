# src/views/catalog.py
import streamlit as st
import pandas as pd
from src.services.catalog import load_catalog_data, upsert_catalog_item, delete_catalog_item

def show_catalog(dev_mode):
    st.header("📖 药品知识库")
    df = load_catalog_data()
    if df.empty:
        st.info("公共药库是空的，请去【药品操作】录入新药。")
        return

    # --- 布局：上方表格，下方编辑区 ---
    
    with st.expander("📊 查看所有数据", expanded=True):
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "is_standard": st.column_config.CheckboxColumn("官方", width="small"),
                "name": st.column_config.TextColumn("通用名", width="medium"),
                "manufacturer": "厂商", 
                "indications": "适应症",
                "barcode": "条形码"
            }
        )

    st.divider()
    st.subheader("🛠️ 修改与维护")

    # 1. 选择药品
    #以此格式显示: [官方/用户] 药名 (厂商) - 条码
    opts = {}
    for _, r in df.iterrows():
        tag = "🔒官方" if r['is_standard'] else "👤用户"
        label = f"[{tag}] {r['name']} ({r['manufacturer']}) - {r['barcode']}"
        opts[label] = r # 存整行数据
    
    selected_label = st.selectbox("选择要修改或删除的药品", list(opts.keys()), index=None, placeholder="请选择...")

    if selected_label:
        item = opts[selected_label]
        is_standard = item['is_standard']
        barcode = item['barcode']

        # 权限检查
        # 如果是官方数据(1) 且 不是开发者模式 -> 锁定
        is_locked = (is_standard == 1 and not dev_mode)

        if is_locked:
            st.warning("🔒 当前选中了【官方标准数据】，您处于用户模式，无法修改或删除。请在侧边栏开启维护者模式。")
        
        # 表单回填
        with st.form("edit_catalog_form"):
            st.caption(f"正在编辑条码: {barcode}")
            
            c1, c2, c3 = st.columns([1.5, 1, 1])
            name = c1.text_input("通用名 *", value=item['name'], disabled=is_locked)
            manuf = c2.text_input("厂商", value=item['manufacturer'], disabled=is_locked)
            spec = c3.text_input("规格", value=item['spec'], disabled=is_locked)
            
            c4, c5 = st.columns(2)
            forms = ["胶囊", "片剂", "颗粒", "口服液", "外用", "喷雾", "其他"]
            units = ["粒", "片", "袋", "ml", "瓶", "盒", "支"]
            
            # 索引保护
            f_idx = forms.index(item['form']) if item['form'] in forms else 0
            u_idx = units.index(item['unit']) if item['unit'] in units else 0
            
            form = c4.selectbox("剂型", forms, index=f_idx, disabled=is_locked)
            unit = c5.selectbox("单位", units, index=u_idx, disabled=is_locked)
            
            ind = st.text_area("适应症 *", value=item['indications'], height=70, disabled=is_locked)
            use = st.text_input("用法", value=item['std_usage'], disabled=is_locked)
            
            s1, s2 = st.columns(2)
            contra = s1.text_area("🚫 禁忌", value=item['contraindications'], disabled=is_locked)
            adv = s2.text_area("🤢 不良反应", value=item['adverse_reactions'], disabled=is_locked)
            prec = st.text_area("⚠️ 注意事项", value=item['precautions'], height=60, disabled=is_locked)
            
            p1, p2, p3 = st.columns(3)
            preg = p1.text_input("🤰 孕妇", value=item['pregnancy_lactation_use'], disabled=is_locked)
            child = p2.text_input("👶 儿童", value=item['child_use'], disabled=is_locked)
            old = p3.text_input("👴 老年", value=item['elderly_use'], disabled=is_locked)

            # 按钮区
            col_save, col_del = st.columns([1, 5]) # 调整比例让删除按钮靠左一点
            
            with col_save:
                if not is_locked:
                    save_label = "💾 更新官方数据" if dev_mode else "💾 更新 (用户)"
                    if st.form_submit_button(save_label, type="primary"):
                        if not name:
                            st.error("通用名不能为空")
                        else:
                            upsert_catalog_item(
                                barcode, name, manuf, spec, form, unit, 
                                ind, use, adv, contra, prec, preg, child, old, 
                                1 if dev_mode else 0
                            )
                            st.success("更新成功！")
                            st.rerun()
                else:
                    st.form_submit_button("🔒 只读", disabled=True)
            
            with col_del:
                # 删除逻辑单独处理，因为 form_submit_button 不支持二次确认弹窗很好的交互
                # 我们这里先放个按钮，点击后真正删除
                if not is_locked:
                    if st.form_submit_button("🗑️ 删除此条目"):
                        # 这里做一个简单的删除，实际生产环境通常加个 st.popover 确认，但 form 里加 popover 比较麻烦
                        # 我们可以依赖用户的点击操作
                        res = delete_catalog_item(barcode)
                        if res:
                            st.success(f"已删除 {name}")
                            st.rerun()
                        else:
                            st.error("删除失败，可能该药品仍有库存记录，请先清理库存。")