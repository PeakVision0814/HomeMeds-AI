import streamlit as st
import pandas as pd
from src.services.catalog import load_catalog_data, upsert_catalog_item, delete_catalog_item

# === 1. 定义弹窗组件 (Dialog) ===
@st.dialog("💊 药品详情档案")
def show_detail_modal(item):
    """
    弹窗显示药品的详细信息
    """
    # 标题区：药名 + 官方标记
    tag = "🔒 官方认证数据" if item['is_standard'] else "👤 用户录入数据"
    if item['is_standard']:
        st.info(f"**{item['name']}** ({tag})")
    else:
        st.warning(f"**{item['name']}** ({tag})")

    st.caption(f"条码: {item['barcode']}")
    st.divider()

    # 核心信息区
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**🏭 生产企业:**\n{item['manufacturer'] or '未知'}")
        st.markdown(f"**📦 规格:**\n{item['spec'] or '未知'}")
    with c2:
        st.markdown(f"**💊 剂型/单位:**\n{item['form']}/{item['unit']}")
        st.markdown(f"**🏷️ 标签:**\n{item['tags'] or '无'}") # 🆕 显示标签

    st.divider()

    # 详细文本区
    st.markdown("#### 🩺 适应症/功能主治")
    st.info(item['indications'] or "暂无")

    st.markdown("#### 📝 用法用量")
    st.write(item['std_usage'] or "暂无")

    # 安全信息区
    with st.expander("🛡️ 安全用药信息 (禁忌/不良反应)", expanded=True):
        if item['contraindications']:
            st.markdown("**🚫 禁忌:**")
            st.error(item['contraindications'])
        else:
            st.write("**🚫 禁忌:** 暂无记录")
            
        st.markdown("---")
        st.markdown(f"**🤢 不良反应:** {item['adverse_reactions'] or '暂无'}")
        st.markdown(f"**⚠️ 注意事项:** {item['precautions'] or '暂无'}")

    with st.expander("👶👵 特殊人群用药"):
        c_p, c_c, c_o = st.columns(3)
        c_p.markdown(f"**🤰 孕妇:**\n{item['pregnancy_lactation_use'] or '未知'}")
        c_c.markdown(f"**👶 儿童:**\n{item['child_use'] or '未知'}")
        c_o.markdown(f"**👴 老年:**\n{item['elderly_use'] or '未知'}")


# === 2. 主视图函数 ===
def show_catalog(dev_mode):
    st.header("📖 药品知识库")
    
    # 加载数据
    df = load_catalog_data()
    if df.empty:
        st.info("公共药库是空的，请去【药品操作】录入新药。")
        return

    # 搜索框
    search_term = st.text_input("🔍 搜索药库 (支持药名/厂商/条码/标签)", placeholder="输入关键字快速查找...")
    if search_term:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        df = df[mask]

    st.markdown(f"共找到 **{len(df)}** 种药品")
    st.divider()

    # === 卡片网格布局 ===
    COLS_PER_ROW = 3
    cols = st.columns(COLS_PER_ROW)

    for index, row in df.iterrows():
        col_idx = index % COLS_PER_ROW
        with cols[col_idx]:
            with st.container(border=True):
                # 1. 顶部：官方/用户 标签
                if row['is_standard']:
                    st.caption("🔒 官方")
                else:
                    st.caption("👤 用户")
                
                # 2. 中部：核心信息
                display_name = row['name']
                if len(display_name) > 10: display_name = display_name[:9] + "..."
                
                st.markdown(f"### {display_name}")
                st.text(f"厂商: {row['manufacturer'] or '未知'}")
                st.text(f"规格: {row['spec']}")
                
                # 3. 底部：详情按钮
                if st.button("📄 查看详情", key=f"btn_view_{row['barcode']}_{index}", use_container_width=True):
                    show_detail_modal(row)

    # === 底部：修改与维护区 ===
    st.divider()
    st.subheader("🛠️ 数据维护 (修改/删除)")
    
    with st.expander("点击展开编辑表单"):
        opts = {}
        for _, r in df.iterrows():
            tag = "🔒官方" if r['is_standard'] else "👤用户"
            manuf = r['manufacturer'] if r['manufacturer'] else "未知"
            label = f"[{tag}] {r['name']} ({manuf}) - {r['barcode']}"
            opts[label] = r 
        
        selected_label = st.selectbox("选择要编辑的药品", list(opts.keys()), index=None)

        if selected_label:
            item = opts[selected_label]
            is_standard = item['is_standard']
            barcode = item['barcode']
            is_locked = (is_standard == 1 and not dev_mode)

            if is_locked:
                st.warning("🔒 官方数据只读，需开启维护者模式修改。")
            
            with st.form("edit_catalog_form"):
                st.caption(f"编辑条码: {barcode}")
                
                c1, c2, c3 = st.columns([1.5, 1, 1])
                name = c1.text_input("通用名 *", value=item['name'], disabled=is_locked)
                manuf = c2.text_input("厂商", value=item['manufacturer'], disabled=is_locked)
                spec = c3.text_input("规格", value=item['spec'], disabled=is_locked)
                
                # 👇 修改第二行布局，增加 Tags
                c4, c5, c6 = st.columns([1, 1, 2])
                
                forms = ["胶囊", "片剂", "颗粒", "口服液", "外用", "喷雾", "其他"]
                units = ["粒", "片", "袋", "ml", "瓶", "盒", "支"]
                f_idx = forms.index(item['form']) if item['form'] in forms else 0
                u_idx = units.index(item['unit']) if item['unit'] in units else 0
                
                form = c4.selectbox("剂型", forms, index=f_idx, disabled=is_locked)
                unit = c5.selectbox("单位", units, index=u_idx, disabled=is_locked)
                
                # 🆕 标签输入
                curr_tags = item['tags'] if item['tags'] else ""
                tags = c6.text_input("🏷️ 标签", value=curr_tags, placeholder="如: 感冒 发烧", disabled=is_locked)
                
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

                col_save, col_del = st.columns([1, 5])
                with col_save:
                    if not is_locked:
                        lbl = "💾 保存"
                        if st.form_submit_button(lbl, type="primary"):
                            # 👇 传入 tags
                            upsert_catalog_item(barcode, name, manuf, spec, form, unit, tags, ind, use, adv, contra, prec, preg, child, old, 1 if dev_mode else 0)
                            st.success("已更新"); st.rerun()
                    else: st.form_submit_button("🔒", disabled=True)
                
                with col_del:
                    if not is_locked:
                        if st.form_submit_button("🗑️ 删除"):
                            if delete_catalog_item(barcode): st.success("已删除"); st.rerun()
                            else: st.error("删除失败，可能仍有库存")