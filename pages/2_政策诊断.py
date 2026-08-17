import streamlit as st
import json
import os
import sys

# 添加引擎路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.matcher import load_json, run_diagnosis, humanize_gap_item
from engine.diagnosis import run_enhanced_diagnosis
from engine.llm_scorer import generate_material_outline
from engine.dashboard import compute_dashboard_metrics, get_deadline_status, sort_results_for_display
from engine.ui_helpers import render_step_indicator, check_prerequisite, inject_apple_theme

st.set_page_config(page_title="政策诊断", page_icon="🔍", layout="wide")

# 注入 Apple 风格主题
inject_apple_theme()

# 页面专属样式
st.markdown("""
<style>
/* 页面标题 */
.main-title {
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--apple-text);
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
}

/* 行动看板：包裹 st.metric 的卡片 */
.metric-card [data-testid="stMetric"] {
    background: var(--apple-card-solid);
    border-radius: var(--radius-md);
    padding: 1rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--apple-border);
    text-align: center;
}
.metric-card [data-testid="stMetricLabel"] {
    font-size: 0.85rem;
    color: var(--apple-muted);
    justify-content: center;
}
.metric-card [data-testid="stMetricValue"] {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--apple-text);
    justify-content: center;
}

/* 四类诊断结果颜色 */
.metric-card-green [data-testid="stMetric"] { background: var(--apple-green-light); border-color: var(--apple-green); }
.metric-card-green [data-testid="stMetricLabel"] { color: #1a6b2d; }
.metric-card-green [data-testid="stMetricValue"] { color: var(--apple-green); }

.metric-card-amber [data-testid="stMetric"] { background: var(--apple-orange-light); border-color: var(--apple-orange); }
.metric-card-amber [data-testid="stMetricLabel"] { color: #8a5a10; }
.metric-card-amber [data-testid="stMetricValue"] { color: var(--apple-orange); }

.metric-card-blue [data-testid="stMetric"] { background: var(--apple-blue-light); border-color: var(--apple-blue); }
.metric-card-blue [data-testid="stMetricLabel"] { color: #0a4a8a; }
.metric-card-blue [data-testid="stMetricValue"] { color: var(--apple-blue); }

.metric-card-red [data-testid="stMetric"] { background: var(--apple-red-light); border-color: var(--apple-red); }
.metric-card-red [data-testid="stMetricLabel"] { color: #8a1c15; }
.metric-card-red [data-testid="stMetricValue"] { color: var(--apple-red); }

/* 政策卡片 */
.policy-card {
    background: var(--apple-card-solid);
    border-radius: var(--radius-md);
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--apple-border);
    border-left: 5px solid #d1d1d6;
}
.policy-card-立即申报 { border-left-color: var(--apple-green); background: var(--apple-green-light); }
.policy-card-培育申报 { border-left-color: var(--apple-orange); background: var(--apple-orange-light); }
.policy-card-持续关注 { border-left-color: var(--apple-blue); background: var(--apple-blue-light); }
.policy-card-暂不适合 { border-left-color: var(--apple-red); background: var(--apple-red-light); }

/* 状态徽章 */
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-pill);
    font-size: 0.75rem;
    font-weight: 600;
    color: #ffffff;
    margin-right: 0.5rem;
}
.status-badge-立即申报 { background: var(--apple-green); }
.status-badge-培育申报 { background: var(--apple-orange); }
.status-badge-持续关注 { background: var(--apple-blue); }
.status-badge-暂不适合 { background: var(--apple-red); }

/* 截止日徽章 */
.deadline-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
}
.deadline-normal { background: #f2f2f7; color: var(--apple-text); }
.deadline-urgent { background: var(--apple-red-light); color: #8a1c15; }
.deadline-expired { background: #e5e5ea; color: var(--apple-muted); }

/* 优先推荐标签 */
.priority-tag {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: var(--radius-pill);
    background: var(--apple-red);
    color: #ffffff;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 0.5rem;
}

/* 统计数字 */
.stat-number {
    font-size: 1.1rem;
    font-weight: 700;
}
.stat-label {
    font-size: 0.8rem;
    color: var(--apple-muted);
}

/* 差距项 */
.gap-item {
    padding: 0.35rem 0;
    border-bottom: 1px solid var(--apple-border);
}
.gap-item:last-child { border-bottom: none; }

/* 顶部企业信息颜色 */
.enterprise-info {
    color: var(--apple-text);
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🔍 政策诊断结果</div>', unsafe_allow_html=True)

# 检查前置条件
if not check_prerequisite("enterprise", "diagnosis"):
    st.stop()

render_step_indicator("diagnosis")

# 检查数据文件是否存在
enterprise_file = "data/enterprise.json"
policies_file = "data/policies.json"

if not os.path.exists(policies_file):
    st.error("❌ 政策库文件不存在")
    st.stop()

# 加载数据
enterprise = load_json(enterprise_file)
policies = load_json(policies_file)
policy_map = {p['policy_id']: p for p in policies}

# 页面顶部企业信息
info_col1, info_col2, info_col3 = st.columns(3)
with info_col1:
    st.markdown(f"**企业名称**：{enterprise.get('name', '未命名')}")
with info_col2:
    st.markdown(f"**所属行业**：{enterprise.get('industry', '')} - {enterprise.get('sub_industry', '')}")
with info_col3:
    st.markdown(f"**注册地区**：{enterprise.get('region', '')}")

st.divider()

# 侧边栏：LLM 配置
with st.sidebar:
    st.subheader("🤖 LLM 软条件打分配置")

    use_demo = st.toggle("使用演示模式（不调用真实 LLM）", value=True)

    provider = st.selectbox(
        "选择 LLM 提供商",
        ["anthropic", "openai"],
        disabled=use_demo
    )

    api_key = st.text_input(
        f"输入 {provider} API Key",
        type="password",
        disabled=use_demo,
        help="如果已有 .env 文件配置，可留空"
    )

    max_soft_score = st.slider(
        "软条件打分政策数量",
        min_value=1,
        max_value=12,
        value=5,
        help="控制 LLM 调用次数，降低成本"
    )

    if use_demo:
        st.info("演示模式：使用模拟的软条件评分结果")
    else:
        if not api_key:
            st.warning("未输入 API Key，将尝试读取 .env 文件配置")
        else:
            st.success("已输入 API Key")

# 运行诊断按钮
btn_col1, btn_col2 = st.columns(2)

with btn_col1:
    run_hard = st.button("🚀 仅硬条件诊断", type="secondary", use_container_width=True)

with btn_col2:
    run_enhanced = st.button("🚀🧠 硬条件 + LLM 软条件诊断", type="primary", use_container_width=True)

if run_hard:
    with st.spinner("正在进行硬条件匹配..."):
        diagnosis_result = run_diagnosis(enterprise, policies)

    os.makedirs("output", exist_ok=True)
    with open("output/diagnosis_result.json", 'w', encoding='utf-8') as f:
        json.dump(diagnosis_result, f, ensure_ascii=False, indent=2)

    st.session_state['diagnosis_result'] = diagnosis_result
    st.session_state['diagnosis_mode'] = "hard"
    st.success("✅ 硬条件诊断完成！")

if run_enhanced:
    with st.spinner("正在进行硬条件匹配和 LLM 软条件评估..."):
        diagnosis_result = run_enhanced_diagnosis(
            enterprise=enterprise,
            policies=policies,
            provider=provider,
            api_key=api_key if api_key else None,
            use_demo=use_demo,
            max_policies_for_soft_score=max_soft_score
        )

    os.makedirs("output", exist_ok=True)
    with open("output/diagnosis_result.json", 'w', encoding='utf-8') as f:
        json.dump(diagnosis_result, f, ensure_ascii=False, indent=2)

    st.session_state['diagnosis_result'] = diagnosis_result
    st.session_state['diagnosis_mode'] = "enhanced"
    st.success("✅ 综合诊断完成！")


def save_outlines_to_result(result, session_state):
    """把 session_state 中已生成的大纲同步保存到诊断结果文件"""
    for key, value in session_state.items():
        if key.startswith("outline_"):
            policy_id = key.replace("outline_", "")
            for r in result.get('results', []):
                if r.get('policy_id') == policy_id:
                    r['material_outline'] = value
                    break

    os.makedirs("output", exist_ok=True)
    with open("output/diagnosis_result.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


# 显示结果
if 'diagnosis_result' in st.session_state:
    result = st.session_state['diagnosis_result']
    is_enhanced = st.session_state.get('diagnosis_mode') == "enhanced"

    # 每次显示结果时，把已有大纲同步回结果文件
    save_outlines_to_result(result, st.session_state)

    # 显示诊断模式
    if is_enhanced:
        llm_config = result.get('llm_config', {})
        provider_display = "演示模式" if llm_config.get('use_demo') else llm_config.get('provider', 'unknown')
        st.info(f"当前为综合诊断模式 | LLM：{provider_display} | 软条件评估政策数：{llm_config.get('max_policies_for_soft_score', 0)} 条")
    else:
        st.info("当前为硬条件诊断模式")

    # ========== 行动看板 ==========
    metrics = compute_dashboard_metrics(result)

    st.subheader("📊 行动看板")

    # 第一行：匹配总数 + 三类诊断结果
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🔍 匹配政策总数", metrics['total'])
        st.markdown('</div>', unsafe_allow_html=True)
    with m_col2:
        st.markdown('<div class="metric-card metric-card-green">', unsafe_allow_html=True)
        st.metric("🟢 立即申报", metrics['immediate'])
        st.markdown('</div>', unsafe_allow_html=True)
    with m_col3:
        st.markdown('<div class="metric-card metric-card-amber">', unsafe_allow_html=True)
        st.metric("🟡 培育申报", metrics['cultivate'])
        st.markdown('</div>', unsafe_allow_html=True)
    with m_col4:
        st.markdown('<div class="metric-card metric-card-blue">', unsafe_allow_html=True)
        st.metric("🔵 持续关注", metrics['watch'])
        st.markdown('</div>', unsafe_allow_html=True)

    # 第二行：暂不适合 + 平均匹配度 + 紧急截止 + 已过期
    m_col5, m_col6, m_col7, m_col8 = st.columns(4)
    with m_col5:
        st.markdown('<div class="metric-card metric-card-red">', unsafe_allow_html=True)
        st.metric("🔴 暂不适合", metrics['unsuitable'])
        st.markdown('</div>', unsafe_allow_html=True)
    with m_col6:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📈 平均综合匹配度", f"{metrics['avg_score']} 分")
        st.markdown('</div>', unsafe_allow_html=True)
    with m_col7:
        urgent_card_class = "metric-card-red" if metrics['urgent_count'] > 0 else "metric-card"
        st.markdown(f'<div class="metric-card {urgent_card_class}">', unsafe_allow_html=True)
        st.metric("🔥 30 天内截止", metrics['urgent_count'])
        st.markdown('</div>', unsafe_allow_html=True)
    with m_col8:
        expired_card_class = "metric-card-red" if metrics['expired_count'] > 0 else "metric-card"
        st.markdown(f'<div class="metric-card {expired_card_class}">', unsafe_allow_html=True)
        st.metric("⏰ 已过期政策", metrics['expired_count'])
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ========== 筛选与排序 ==========
    st.subheader("🔎 政策匹配详情")

    diagnosis_types = ["立即申报", "培育申报", "持续关注", "暂不适合"]

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 2, 1, 1])
    with filter_col1:
        filter_options = st.multiselect(
            "筛选诊断结果",
            diagnosis_types,
            default=diagnosis_types,
            key="filter_diagnosis"
        )
    with filter_col2:
        sort_by = st.selectbox(
            "排序方式",
            ["行动优先级", "综合分数降序", "截止日由近到远", "政策优先级"],
            index=0,
            key="sort_by"
        )
    with filter_col3:
        only_urgent = st.toggle("仅 30 天内截止", value=False, key="only_urgent")
    with filter_col4:
        hide_unsuitable = st.toggle("隐藏暂不适合", value=False, key="hide_unsuitable")

    # 应用筛选
    display_results = [r for r in result['results'] if r['diagnosis'] in filter_options]
    if hide_unsuitable:
        display_results = [r for r in display_results if r['diagnosis'] != '暂不适合']
    if only_urgent:
        display_results = [r for r in display_results if get_deadline_status(r.get('deadline', ''))['is_urgent']]

    # 应用排序
    display_results = sort_results_for_display(display_results, sort_by)

    if not display_results:
        st.info("没有符合当前筛选条件的政策")
    else:
        st.markdown(f"共展示 **{len(display_results)}** 条政策")

    # ========== 卡片式政策展示 ==========
    for idx, r in enumerate(display_results):
        deadline_status = get_deadline_status(r.get('deadline', ''))

        if deadline_status['is_expired']:
            deadline_class = "deadline-expired"
            deadline_badge = f"截止：{r['deadline']} {deadline_status['status_text']}"
        elif deadline_status['is_urgent']:
            deadline_class = "deadline-urgent"
            deadline_badge = f"截止：{r['deadline']} {deadline_status['status_text']}"
        else:
            deadline_class = "deadline-normal"
            deadline_badge = f"截止：{r['deadline']} {deadline_status['status_text']}"

        # 分数文本
        if is_enhanced and 'combined_score' in r:
            score_text = f"综合 {r['combined_score']} 分 | 硬 {r['hard_score']} | 软 {r.get('soft_score', 'N/A')}"
        else:
            score_text = f"匹配度 {r['match_score']} 分"

        # 是否是最优先推荐（仅对第一条「立即申报」政策展示）
        is_top_recommend = (idx == 0 and r['diagnosis'] == '立即申报')
        priority_html = '<span class="priority-tag">🔥 建议优先</span>' if is_top_recommend else ''

        st.markdown(f"""
        <div class="policy-card policy-card-{r['diagnosis']}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--apple-text);">
                        {r['policy_name']} {priority_html}
                    </div>
                    <div style="margin-top: 0.35rem;">
                        <span class="status-badge status-badge-{r['diagnosis']}">{r['diagnosis']}</span>
                        <span style="color: var(--apple-muted); font-size: 0.85rem;">{r['level']} · {r['category']}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: var(--apple-blue);">{score_text}</div>
                    <div class="deadline-badge {deadline_class}" style="margin-top: 0.35rem;">{deadline_badge}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 卡片身体：两列布局
        body_col1, body_col2 = st.columns([2, 1])

        with body_col1:
            st.markdown(f"**扶持内容**：{r['benefit']}")
            st.markdown(f"**诊断理由**：{r['reason']}")

            if r['failed']:
                st.markdown("**❌ 不满足条件：**")
                for item in r['failed']:
                    st.markdown(f"- {humanize_gap_item(item)}")

            if r['unknown']:
                st.markdown("**❓ 缺失数据：**")
                for item in r['unknown']:
                    st.markdown(f"- {humanize_gap_item(item)}")

        with body_col2:
            # 统计数字
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div class="stat-number" style="color: var(--apple-green);">{r['passed_count']}</div>
                    <div class="stat-label">通过</div>
                </div>
                """, unsafe_allow_html=True)
            with stat_col2:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div class="stat-number" style="color: var(--apple-red);">{r['failed_count']}</div>
                    <div class="stat-label">不满足</div>
                </div>
                """, unsafe_allow_html=True)
            with stat_col3:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div class="stat-number" style="color: var(--apple-orange);">{r['unknown_count']}</div>
                    <div class="stat-label">缺失</div>
                </div>
                """, unsafe_allow_html=True)

            # 软条件评估摘要
            if is_enhanced and r.get('soft_score') is not None:
                st.markdown("---")
                st.markdown(f"**🧠 软条件 {r['soft_score']} 分**（置信度：{r.get('confidence', '未知')}）")
                st.markdown(f"{r.get('soft_assessment', '')}")

        # 软条件展开详情
        if is_enhanced and r.get('soft_score') is not None:
            with st.expander("查看软条件详细评估", expanded=False):
                if r.get('strengths'):
                    st.markdown("**💪 优势：**")
                    for item in r['strengths']:
                        st.markdown(f"- {item}")

                if r.get('weaknesses'):
                    st.markdown("**⚠️ 短板：**")
                    for item in r['weaknesses']:
                        st.markdown(f"- {item}")

                if r.get('cultivation_suggestions'):
                    st.markdown("**🌱 培育建议：**")
                    for item in r['cultivation_suggestions']:
                        st.markdown(f"- {item}")

        # 申报材料大纲生成
        if r['diagnosis'] in ['立即申报', '培育申报']:
            outline_key = f"outline_{r['policy_id']}"

            if outline_key not in st.session_state:
                if st.button(f"📝 生成《{r['policy_name']}》申报大纲",
                            key=f"btn_outline_{r['policy_id']}",
                            use_container_width=True,
                            type="primary"):
                    with st.spinner("正在生成申报材料大纲..."):
                        policy = policy_map.get(r['policy_id'], {})
                        soft_result = {
                            "soft_score": r.get('soft_score'),
                            "soft_assessment": r.get('soft_assessment', ''),
                            "strengths": r.get('strengths', []),
                            "weaknesses": r.get('weaknesses', []),
                            "cultivation_suggestions": r.get('cultivation_suggestions', [])
                        }
                        outline = generate_material_outline(
                            enterprise=enterprise,
                            policy=policy,
                            hard_result=r,
                            soft_result=soft_result,
                            provider=provider,
                            api_key=api_key if api_key else None,
                            use_demo=use_demo
                        )
                        st.session_state[outline_key] = outline
                        save_outlines_to_result(result, st.session_state)
                        st.rerun()
            else:
                outline = st.session_state[outline_key]
                st.success(f"✅ 已生成《{r['policy_name']}》申报大纲")

                outline_col1, outline_col2 = st.columns([1, 1])
                with outline_col1:
                    st.markdown(f"**申报可行性**：{outline.get('applicability', '')}")

                    if outline.get('outline'):
                        st.markdown("**📋 申报材料大纲：**")
                        for section in outline['outline']:
                            st.markdown(f"**{section.get('section', '')}**")
                            for point in section.get('content', []):
                                st.markdown(f"- {point}")

                with outline_col2:
                    if outline.get('key_attachments'):
                        st.markdown("**📎 关键附件清单：**")
                        for item in outline['key_attachments']:
                            st.markdown(f"- {item}")

                    if outline.get('gap_fill_plan'):
                        st.markdown("**🔧 差距补齐计划：**")
                        for item in outline['gap_fill_plan']:
                            st.markdown(f"- {item}")

                    if outline.get('notes'):
                        st.markdown(f"**⚠️ 特别提醒**：{outline['notes']}")

                if st.button("🔄 重新生成", key=f"btn_regenerate_{r['policy_id']}", use_container_width=True):
                    del st.session_state[outline_key]
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.info("💡 提示：点击左侧「诊断报告」查看完整报告")
else:
    st.info("👆 点击诊断按钮查看结果")
