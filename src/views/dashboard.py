# src/views/dashboard.py

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from src.services.queries import load_data, get_dashboard_metrics
from src.services.members import get_all_members

# === 0. CSS 样式 (复用并微调) ===
def render_dashboard_css():
    st.markdown("""
    <style>
    /* 标签样式 */
    .med-tag {
        display: inline-block;
        background-color: #f1f5f9; /* 灰底，比药库淡一点 */
        color: #475569;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-right: 4px;
        border: 1px solid #e2e8f0;
    }
    /* 药名样式 */
    .dash-title {
        font-weight: 700;
        font-size: 1.15rem;
        margin: 8px 0 4px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: #0f172a;
    }
    /* 数量高亮 */
    .dash-qty {
        font-size: 0.9rem;
        color: #2563eb; /* 蓝色高亮数量 */
        font-weight: 600;
    }
    /* 顶部元数据栏 */
    .dash-meta {
        font-size: 0.8rem;
        display: flex;
        justify_content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

def render_tags_html(tags_str):
    if not tags_str: return ""
    tags = [t.strip() for t in tags_str.split() if t.strip()]
    if not tags: return ""
    html = ""
    for t in tags:
        html += f'<span class="med-tag">{t}</span>'
    return html

# === 1. 详情弹窗 ===
@st.dialog("📦 库存详情档案", width="large")
def show_inventory_modal(row):
    # 计算过期状态
    today = pd.to_datetime("today").normalize()
    exp_date = pd.to_datetime(row['expiry_date'])
    days_left = (exp_date - today).days
    
    # 状态横幅
    if days_left < 0:
        st.error(f"⚠️ 已过期 {abs(days_left)} 天！建议立即处理。")
    elif days_left <= 90:
        st.warning(f"⏳ 临期预警：仅剩 {days_left} 天。")
    else:
        st.success(f"✅ 状态正常，有效期充足。")

    st.divider()

    # 第一行：库存核心信息 (大字号)
    c1, c2, c3 = st.columns(3)
    c1.metric("💊 药名", row['name'])
    c2.metric("📊 剩余数量", row['quantity_display'])
    c3.metric("📅 过期日期", row['expiry_date'].strftime('%Y-%m-%d'))
    
    # 第二行：归属与位置
    c4, c5 = st.columns(2)
    c4.markdown(f"**👤 归属人:** {row['owner']}")
    # 如果以后加回位置，这里可以放位置
    
    st.divider()
    
    # 药品信息区 (来自公共库)
    st.caption("以下信息来自公共药品库：")
    
    with st.expander("🩺 适应症与用法", expanded=True):
        st.markdown(f"**功能主治:** {row['indications']}")
        # 兼容 my_dosage (医嘱) 和 std_usage (说明书)
        usage = row['my_dosage'] if row['my_dosage'] else row.get('std_usage', '暂无')
        st.markdown(f"**用法用量:** {usage}")

    with st.expander("🛡️ 安全警示 (禁忌/儿童/孕妇)"):
        if row['contraindications']:
            st.error(f"🚫 禁忌: {row['contraindications']}")
        c_k, c_p = st.columns(2)
        c_k.markdown(f"**👶 儿童:** {row['child_use'] or '详见说明书'}")
        c_p.markdown(f"**🤰 孕妇:** {row.get('pregnancy_lactation_use', '详见说明书')}")

# === 2. 主看板视图 ===
def show_dashboard():
    # 注入 CSS
    render_dashboard_css()
    
    st.header("📊 药箱实时看板")
    
    # 顶部统计卡片
    total, expired, soon = get_dashboard_metrics()
    m1, m2, m3 = st.columns(3)
    m1.metric("🟢 总库存", total)
    m2.metric("🟡 临期预警", soon)
    m3.metric("🔴 已过期", expired, delta_color="inverse")
    
    st.divider()
    
    # 筛选区
    col_s, col_f = st.columns([3, 1])
    search = col_s.text_input("🔍 搜索库存", placeholder="药名/适应症/标签...")
    members_list = ["全部"] + get_all_members()
    owner_filter = col_f.selectbox("归属人筛选", members_list)
    
    # 加载数据
    df = load_data()
    
    if df.empty:
        st.info("📭 药箱现在是空的，快去【药品操作】入库吧！")
        return

    # 执行筛选
    if search:
        # 支持搜药名、适应症、标签
        mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df = df[mask]
    if owner_filter != "全部":
        df = df[df['owner'] == owner_filter]

    st.caption(f"当前展示 {len(df)} 个库存条目")

    # === 卡片网格 ===
    today = pd.to_datetime("today").normalize()
    
    COLS_PER_ROW = 4
    cols = st.columns(COLS_PER_ROW)

    for index, row in df.iterrows():
        col_idx = index % COLS_PER_ROW
        
        # 计算过期逻辑
        exp_date = pd.to_datetime(row['expiry_date'])
        days_left = (exp_date - today).days
        
        # 状态视觉配置
        if days_left < 0:
            status_icon = "🔴"
            status_text = f"已过期 {abs(days_left)}天"
            status_color = "#ef4444" # 红
            bg_color = "#fef2f2" # 极淡红背景提示
        elif days_left <= 90:
            status_icon = "🟡"
            status_text = f"剩 {days_left}天"
            status_color = "#f59e0b" # 黄
            bg_color = "#fffbeb"
        else:
            status_icon = "🟢"
            status_text = "正常"
            status_color = "#10b981" # 绿
            bg_color = "#ffffff"

        with cols[col_idx]:
            with st.container(border=True):
                # 1. 顶部：状态 + 归属人
                st.markdown(f"""
                <div class="dash-meta">
                    <span style="color: {status_color}; font-weight:bold;">
                        {status_icon} {status_text}
                    </span>
                    <span style="color: #64748b; background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">
                        👤 {row['owner']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. 中部：药名 (大标题)
                st.markdown(f'<div class="dash-title" title="{row["name"]}">{row["name"]}</div>', unsafe_allow_html=True)
                
                # 3. 数据：数量 + 效期
                # 这里用 caption 或者小字展示效期
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                    <span class="dash-qty">{row['quantity_display']}</span>
                    <span style="color:#94a3b8; font-size:0.8rem;">{row['expiry_date'].strftime('%Y-%m-%d')}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # 4. 底部：Tags (高度统一 32px)
                tags_html = render_tags_html(row['tags'])
                if tags_html:
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
                    st.markdown('<div style="margin-top:4px; height: 32px; line-height:32px; color:#ccc; font-size:0.8rem;">无标签</div>', unsafe_allow_html=True)

                # 5. 按钮
                if st.button("查看详情", key=f"d_btn_{row['id']}", use_container_width=True):
                    show_inventory_modal(row)