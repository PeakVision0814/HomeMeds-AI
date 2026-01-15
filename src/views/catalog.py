# src/views/catalog.py

import streamlit as st
import pandas as pd
from src.services.catalog import load_catalog_data, upsert_catalog_item, delete_catalog_item

# === 0. 辅助样式: 渲染漂亮的标签 (CSS) ===
def render_custom_css():
    st.markdown("""
    <style>
    /* 定义标签的样式 */
    .med-tag {
        display: inline-block;
        background-color: #e3f2fd; /* 浅蓝色背景 */
        color: #1565c0;            /* 深蓝色文字 */
        padding: 2px 8px;
        border-radius: 12px;       /* 圆角 */
        font-size: 0.75rem;
        margin-right: 4px;
        margin-bottom: 4px;
        border: 1px solid #bbdefb;
    }
    /* 暗色模式适配 */
    @media (prefers-color-scheme: dark) {
        .med-tag {
            background-color: #1e3a8a;
            color: #bfdbfe;
            border: 1px solid #2563eb;
        }
    }
    /* 药名大标题样式 */
    .med-title {
        font-weight: 700;
        font-size: 1.1rem;
        margin: 8px 0 4px 0;
        line-height: 1.4;
        white-space: nowrap;       /* 不换行 */
        overflow: hidden;          /* 超出隐藏 */
        text-overflow: ellipsis;   /* 省略号 */
    }
    /* 顶部元数据 (条码) */
    .med-meta {
        font-size: 0.75rem;
        color: #64748b;
        display: flex;
        justify_content: space-between;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

def render_tags_html(tags_str):
    """将空格分隔的字符串转换为 HTML 标签组"""
    if not tags_str: 
        return ""
    # 分割并过滤空字符
    tags = [t.strip() for t in tags_str.split() if t.strip()]
    if not tags: return ""
    
    html = ""
    for t in tags:
        html += f'<span class="med-tag">{t}</span>'
    return html

# === 1. 定义弹窗组件 (Dialog) ===
@st.dialog("💊 药品详情档案", width="large")
def show_detail_modal(item):
    """
    弹窗显示药品的详细信息
    """
    # 标题区
    tag = "🔒 官方认证" if item['is_standard'] else "👤 用户录入"
    st.subheader(f"{item['name']}")
    st.caption(f"{tag} | 条码: {item['barcode']} | 收录: {item['created_at']}")
    
    # 核心信息卡片
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("生产企业", item['manufacturer'] or '未知')
        c2.metric("规格", item['spec'] or '未知')
        c3.metric("剂型/单位", f"{item['form']}/{item['unit']}")
        
        # 标签展示
        if item['tags']:
            st.markdown("**🏷️ 核心功效/标签:**")
            st.markdown(render_tags_html(item['tags']), unsafe_allow_html=True)

    st.divider()

    # 详细文本区
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("#### 🩺 适应症/功能主治")
        st.info(item['indications'] or "暂无")
        
        st.markdown("#### 📝 用法用量")
        st.write(item['std_usage'] or "暂无")

    with c_right:
        st.markdown("#### 🛡️ 安全用药 (禁忌/不良反应)")
        if item['contraindications']:
            st.error(f"**🚫 禁忌:**\n{item['contraindications']}")
        else:
            st.success("🚫 禁忌: 暂无明确记录")
        
        st.caption(f"**🤢 不良反应:** {item['adverse_reactions'] or '暂无'}")
        st.caption(f"**⚠️ 注意事项:** {item['precautions'] or '暂无'}")

    st.markdown("---")
    st.markdown("#### 👶👵 特殊人群用药")
    c_p, c_c, c_o = st.columns(3)
    c_p.markdown(f"**🤰 孕妇:**\n{item['pregnancy_lactation_use'] or '未知'}")
    c_c.markdown(f"**👶 儿童:**\n{item['child_use'] or '未知'}")
    c_o.markdown(f"**👴 老年:**\n{item['elderly_use'] or '未知'}")


# === 2. 主视图函数 ===
def show_catalog(dev_mode):
    # 注入 CSS
    render_custom_css()
    
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

    st.caption(f"共找到 {len(df)} 种药品")

    # === 卡片网格布局 (Responsive Grid Simulation) ===
    # 为了更紧凑，我们使用 4 列布局
    COLS_PER_ROW = 4
    cols = st.columns(COLS_PER_ROW)

    for index, row in df.iterrows():
        col_idx = index % COLS_PER_ROW
        with cols[col_idx]:
            # 创建带边框的卡片容器
            with st.container(border=True):
                # 1. 顶部：条码 + 官方标记 (Flex布局)
                is_std = row['is_standard']
                icon = "🔒" if is_std else "👤"
                color_style = "color: #059669; font-weight:bold;" if is_std else "color: #64748b;"
                
                # 使用 HTML 渲染顶部元数据，实现左右对齐
                st.markdown(f"""
                <div class="med-meta">
                    <span>{row['barcode']}</span>
                    <span style="{color_style}">{icon}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. 中部：药名 (大字号)
                st.markdown(f'<div class="med-title" title="{row["name"]}">{row["name"]}</div>', unsafe_allow_html=True)
                
                # 3. 中下部：厂商 (小字号)
                manuf_display = row['manufacturer'] if row['manufacturer'] else "未知厂商"
                if len(manuf_display) > 12: manuf_display = manuf_display[:11] + "..."
                st.caption(f"🏭 {manuf_display}")
                
                # 4. 底部：Tags (胶囊标签)
                # 预留一定高度，防止卡片高度不一
                tags_html = render_tags_html(row['tags'])
                if tags_html:
                    # overflow: hidden 保持不变，防止标签太多破坏卡片对齐，但增加了高度
                    # st.markdown(f'<div style="margin-top:4px; min-height: 30px; line-height: 1.6;">{tags_html}</div>', unsafe_allow_html=True)
                    st.markdown(f'''
                    <div style="
                        margin-top: 4px; 
                        height: 32px; 
                        overflow: hidden; 
                        white-space: nowrap;
                        display: flex;
                        align-items: center;
                        mask-image: linear-gradient(to right, black 80%, transparent 100%);
                        -webkit-mask-image: linear-gradient(to right, black 80%, transparent 100%);
                    ">
                        {tags_html}
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    # 占位符也同步调整
                    st.markdown('<div style="margin-top:4px; height: 30px; color:#ccc; font-size:0.8rem; display:flex; align-items:center;">无标签</div>', unsafe_allow_html=True)
                
                st.write("") # 撑开一点间距

                # 5. 按钮
                if st.button("详情", key=f"btn_{row['barcode']}_{index}", use_container_width=True):
                    show_detail_modal(row)

    # === 底部：修改与维护区 ===
    st.divider()
    st.subheader("🛠️ 数据维护")
    
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
            barcode = item['barcode']
            is_locked = (item['is_standard'] == 1 and not dev_mode)

            if is_locked:
                st.warning("🔒 官方数据只读，需开启维护者模式修改。")
            
            with st.form("edit_catalog_form"):
                st.caption(f"编辑条码: {barcode}")
                
                # 第一行
                c1, c2, c3 = st.columns([1.5, 1, 1])
                name = c1.text_input("通用名 *", value=item['name'], disabled=is_locked)
                manuf = c2.text_input("厂商", value=item['manufacturer'], disabled=is_locked)
                spec = c3.text_input("规格", value=item['spec'], disabled=is_locked)
                
                # 第二行：Tags 重点放在这里
                c4, c5, c6 = st.columns([1, 1, 2])
                
                forms = ["胶囊", "片剂", "颗粒", "口服液", "外用", "喷雾", "其他"]
                units = ["粒", "片", "袋", "ml", "瓶", "盒", "支"]
                f_idx = forms.index(item['form']) if item['form'] in forms else 0
                u_idx = units.index(item['unit']) if item['unit'] in units else 0
                
                form = c4.selectbox("剂型", forms, index=f_idx, disabled=is_locked)
                unit = c5.selectbox("单位", units, index=u_idx, disabled=is_locked)
                
                # Tags 输入
                curr_tags = item['tags'] if item['tags'] else ""
                tags = c6.text_input("🏷️ 标签 (空格分隔)", value=curr_tags, placeholder="如: 感冒 发烧 儿童", disabled=is_locked)
                
                # 文本域
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
                            upsert_catalog_item(barcode, name, manuf, spec, form, unit, tags, ind, use, adv, contra, prec, preg, child, old, 1 if dev_mode else 0)
                            st.success("已更新"); st.rerun()
                    else: st.form_submit_button("🔒", disabled=True)
                
                with col_del:
                    if not is_locked:
                        if st.form_submit_button("🗑️ 删除"):
                            if delete_catalog_item(barcode): st.success("已删除"); st.rerun()
                            else: st.error("删除失败，可能仍有库存")