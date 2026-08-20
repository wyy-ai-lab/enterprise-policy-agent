import streamlit as st
import json
import os
import sys
from datetime import datetime

# 添加引擎路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.matcher import humanize_gap_item
from engine.report_export import (
    build_html_report,
    build_markdown_report,
    build_word_report,
    build_pdf_report,
    build_roadmap_word_report,
    build_roadmap_pdf_report,
    build_roadmap_html_report,
    build_report_sections,
    select_top3_policies,
)
from engine.cultivation_roadmap import (
    generate_enterprise_roadmap,
    generate_enhanced_roadmap,
    build_roadmap_markdown,
    PHASE_LABELS,
    PHASE_ORDER,
    save_roadmap,
)
from engine.report_charts import (
    build_diagnosis_pie_chart,
    build_timeline_chart,
    build_capability_bar_chart,
    build_gap_bar_chart,
)
from engine.radar_chart import calculate_dimension_scores, build_radar_chart, fig_to_image_bytes
from engine.ui_helpers import render_step_indicator, check_prerequisite, inject_apple_theme

st.set_page_config(page_title="诊断报告", page_icon="📋", layout="wide")

# 注入 Apple 风格主题
inject_apple_theme()

# 页面专属样式
st.markdown("""
<style>
.main-title {
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--apple-text);
    margin-bottom: 0.25rem;
    letter-spacing: -0.02em;
}
.section-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--apple-text);
    margin-bottom: 1rem;
    padding-bottom: 0.65rem;
    border-bottom: 1px solid var(--apple-border);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.metric-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--apple-text);
    letter-spacing: -0.02em;
}
.metric-label {
    font-size: 0.85rem;
    color: var(--apple-muted);
    margin-top: 0.25rem;
}
.top3-card {
    background: var(--apple-card-solid);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.25rem;
    margin-bottom: 0.85rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--apple-border);
    border-left: 5px solid #d1d1d6;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.top3-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.top3-card-立即申报 { border-left-color: var(--apple-green); background: var(--apple-green-light); }
.top3-card-培育申报 { border-left-color: var(--apple-orange); background: var(--apple-orange-light); }
.top3-card-持续关注 { border-left-color: var(--apple-blue); background: var(--apple-blue-light); }
.top3-card-暂不适合 { border-left-color: var(--apple-red); background: var(--apple-red-light); }

.executive-summary-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 1rem;
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .executive-summary-card {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}

.profile-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
}
.profile-item {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-md);
    padding: 0.55rem 0.7rem;
    box-shadow: var(--shadow-sm);
}
.profile-item-label {
    font-size: 0.72rem;
    color: var(--apple-muted);
    margin-bottom: 0.15rem;
}
.profile-item-value {
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--apple-text);
    line-height: 1.3;
}
.profile-item.full-width {
    grid-column: 1 / -1;
}
.profile-subtitle {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--apple-muted);
    margin: 0.75rem 0 0.35rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.action-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
    height: 100%;
}
.action-card h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--apple-text);
}
.action-card ul {
    margin: 0;
    padding-left: 1.1rem;
    color: var(--apple-text);
    font-size: 0.92rem;
    line-height: 1.6;
}
.action-card li { margin-bottom: 0.35rem; }

.expander-policy-name {
    font-weight: 600;
    color: var(--apple-text);
}

.export-section {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .export-section {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}

/* Tab 样式：柔和的胶囊分段控制器 */
.stTabs [role="tablist"] {
    gap: 0.5rem;
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    padding: 0.4rem;
    box-shadow: var(--shadow-sm);
}
.stTabs [role="tab"] {
    border-radius: var(--radius-md) !important;
    padding: 0.7rem 1.4rem !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: var(--apple-text) !important;
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    transition: background 0.2s ease, color 0.2s ease;
}
.stTabs [role="tab"]::before,
.stTabs [role="tab"]::after {
    display: none !important;
}
.stTabs [role="tab"]:hover {
    background: rgba(0, 0, 0, 0.04) !important;
}
.stTabs [role="tab"][aria-selected="true"] {
    background: var(--apple-blue-light) !important;
    color: var(--apple-blue) !important;
}

/* 培育路线图样式 */
.roadmap-phase-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--apple-text);
    margin: 1.25rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--apple-border);
}
.roadmap-action-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-sm);
    border-left: 5px solid var(--apple-blue);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.roadmap-action-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.roadmap-action-card-phase-immediate { border-left-color: var(--apple-red); background: var(--apple-red-light); }
.roadmap-action-card-phase-short { border-left-color: var(--apple-orange); background: var(--apple-orange-light); }
.roadmap-action-card-phase-medium { border-left-color: var(--apple-blue); background: var(--apple-blue-light); }
.roadmap-action-card-phase-long { border-left-color: var(--apple-green); background: var(--apple-green-light); }
.roadmap-action-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--apple-text);
    margin-bottom: 0.35rem;
}
.roadmap-action-meta {
    font-size: 0.8rem;
    color: var(--apple-muted);
    margin-bottom: 0.35rem;
}
.roadmap-action-desc {
    font-size: 0.92rem;
    color: var(--apple-text);
    line-height: 1.5;
    margin-bottom: 0.5rem;
}
.roadmap-action-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
}
.roadmap-tag {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: var(--radius-pill);
    font-size: 0.75rem;
    font-weight: 500;
    background: var(--apple-blue-light);
    color: var(--apple-blue);
}
.roadmap-tag-owner { background: #f2f2f7; color: var(--apple-text); }
.roadmap-tag-difficulty-low { background: rgba(52, 199, 89, 0.12); color: #1a6b2d; }
.roadmap-tag-difficulty-medium { background: rgba(255, 149, 0, 0.12); color: #8a5a10; }
.roadmap-tag-difficulty-high { background: rgba(255, 59, 48, 0.12); color: #8a1c15; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📋 诊断报告</div>', unsafe_allow_html=True)

# 检查前置条件
if not check_prerequisite("diagnosis", "report"):
    st.stop()

render_step_indicator("report")

result_file = "output/diagnosis_result.json"

with open(result_file, 'r', encoding='utf-8') as f:
    result = json.load(f)

enterprise_name = result['enterprise_name']
diagnosis_date = result['diagnosis_date']
results = result['results']

# 生成能力分数
enterprise_file = "data/enterprise.json"
if os.path.exists(enterprise_file):
    with open(enterprise_file, 'r', encoding='utf-8') as f:
        enterprise = json.load(f)
    capability_scores = enterprise.get('capability_scores') or calculate_dimension_scores(enterprise)
else:
    enterprise = {}
    capability_scores = calculate_dimension_scores({})

# 生成报告章节数据
sections = build_report_sections(result, capability_scores)
metrics = sections['metrics']
top3 = sections['top3_policies']

# 生成图表
fig_radar = build_radar_chart(capability_scores, title=f"{enterprise_name} 综合能力评估")
fig_pie = build_diagnosis_pie_chart(sections['summary_counts'])
fig_timeline = build_timeline_chart(top3)
fig_capability = build_capability_bar_chart(capability_scores)
fig_gap = build_gap_bar_chart(sections['gap_analysis'])

# 尝试将雷达图转为图片（供 Word/PDF 嵌入）
radar_image_bytes = None
kaleido_available = False
try:
    radar_image_bytes = fig_to_image_bytes(fig_radar, format='png')
    kaleido_available = True
except ImportError:
    kaleido_available = False
except Exception as e:
    st.warning(f"雷达图转图片失败：{e}，Word/PDF 将使用维度分数表格替代")

# 日期前缀，用于导出文件名
date_prefix = datetime.now().strftime('%Y%m%d')
file_name_base = f"{date_prefix}_{enterprise_name}_政策诊断报告"

# 预生成 Markdown 与 HTML 报告
report = build_markdown_report(result)
html_report = build_html_report(
    result,
    capability_scores=capability_scores,
    fig_radar=fig_radar,
    fig_pie=fig_pie,
    fig_timeline=fig_timeline,
    fig_capability=fig_capability,
    fig_gap=fig_gap,
)


# ========== 三大模块 Tab ==========
tab_result, tab_roadmap, tab_markdown = st.tabs(["📊 诊断结果", "🌱 培育路线图", "📝 完整报告预览（Markdown）"])


with tab_result:
    # ---------- 报告头 / 关键指标 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">📊 诊断概览</div>', unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5)
        metric_items = [
            ("匹配政策", sections['total_policies'], "条"),
            ("平均匹配度", sections['avg_score'], "分"),
            ("立即申报", metrics['immediate'], "条"),
            ("培育申报", metrics['cultivate'], "条"),
            ("紧急截止", metrics['urgent_count'], "条"),
        ]
        for col, (label, value, unit) in zip([c1, c2, c3, c4, c5], metric_items):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{value}{unit}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

    # ---------- 执行摘要 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">📄 执行摘要</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="executive-summary-card">
            {sections['executive_summary']}
        </div>
        """, unsafe_allow_html=True)

    # ---------- 企业画像快照 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">🏢 企业画像快照</div>', unsafe_allow_html=True)

        ep = sections['enterprise_profile']
        if ep['available']:
            # 顶部一句话概要，紧凑显示
            st.markdown(
                f"<p style='color: var(--apple-muted); font-size: 0.9rem; margin-bottom: 0.75rem;'>"
                f"{ep['text']}</p>",
                unsafe_allow_html=True
            )

            # 基础信息
            st.markdown('<div class="profile-subtitle">基础信息</div>', unsafe_allow_html=True)
            basic_items = [
                ("所属行业", f"{ep['industry']}（{ep['sub_industry']}）"),
                ("企业规模", f"{ep['scale']} / {ep['employees']} 人"),
                ("所在地区", ep['region']),
                ("成立年份", ep['founded_year']),
                ("上年度营收", f"{ep['revenue']} 万元"),
                ("上年度利润", f"{ep['profit']} 万元"),
            ]
            st.markdown('<div class="profile-grid">', unsafe_allow_html=True)
            for label, value in basic_items:
                st.markdown(f"""
                <div class="profile-item">
                    <div class="profile-item-label">{label}</div>
                    <div class="profile-item-value">{value}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # 研发能力
            st.markdown('<div class="profile-subtitle">研发能力</div>', unsafe_allow_html=True)
            rd_items = [
                ("研发投入", f"{ep['rd_investment']} 万元"),
                ("研发占比", ep['rd_ratio']),
                ("研发人员", f"{ep['rd_team_size']} 人 / {ep['rd_team_ratio']}"),
                ("高新收入占比", ep['high_tech_income_ratio']),
            ]
            st.markdown('<div class="profile-grid">', unsafe_allow_html=True)
            for label, value in rd_items:
                st.markdown(f"""
                <div class="profile-item">
                    <div class="profile-item-label">{label}</div>
                    <div class="profile-item-value">{value}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # 资质与知识产权
            st.markdown('<div class="profile-subtitle">资质与知识产权</div>', unsafe_allow_html=True)
            ip_items = [
                ("发明专利", ep['invention_patents']),
                ("实用新型", ep['utility_models']),
                ("软件著作权", ep['software_copyrights']),
                ("商标", ep['trademarks']),
                ("国家高企", "是" if ep['is_high_tech_enterprise'] else "否"),
                ("研发准备金", "已建立" if ep['rd_accounting_system'] else "未建立"),
                ("重大事故", "有" if ep['has_major_accident'] else "无"),
            ]
            st.markdown('<div class="profile-grid">', unsafe_allow_html=True)
            for label, value in ip_items:
                st.markdown(f"""
                <div class="profile-item">
                    <div class="profile-item-label">{label}</div>
                    <div class="profile-item-value">{value}</div>
                </div>
                """, unsafe_allow_html=True)
            # 已获资质单独占满一行
            if ep['qualifications']:
                st.markdown(f"""
                <div class="profile-item full-width">
                    <div class="profile-item-label">已获资质</div>
                    <div class="profile-item-value">{'、'.join(ep['qualifications'])}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info(ep['text'])

    # ---------- 诊断结果总览 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">🔍 诊断结果总览</div>', unsafe_allow_html=True)

        overview_col1, overview_col2 = st.columns([1, 1.2])
        with overview_col1:
            st.plotly_chart(fig_pie, use_container_width=True, key="report_pie")

        with overview_col2:
            st.markdown("**分类统计**")
            count_data = []
            for diagnosis in ["立即申报", "培育申报", "持续关注", "暂不适合"]:
                count_data.append({
                    "诊断结果": diagnosis,
                    "数量": sections['summary_counts'].get(diagnosis, 0),
                })
            st.dataframe(count_data, use_container_width=True, hide_index=True)

            st.markdown("**关键指标**")
            metric_data = [
                {"指标": "平均综合匹配度", "数值": f"{sections['avg_score']} 分"},
                {"指标": "紧急截止政策", "数值": f"{metrics['urgent_count']} 条"},
                {"指标": "已过期政策", "数值": f"{metrics['expired_count']} 条"},
            ]
            if metrics['nearest_deadline']:
                metric_data.append({
                    "指标": "最近截止日",
                    "数值": f"{metrics['nearest_deadline']}（剩 {metrics['nearest_days']} 天）",
                })
            st.dataframe(metric_data, use_container_width=True, hide_index=True)

    # ---------- TOP3 推荐政策路线图 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">🎯 TOP3 推荐政策路线图</div>', unsafe_allow_html=True)

        if top3:
            st.plotly_chart(fig_timeline, use_container_width=True, key="report_timeline")

            for p in top3:
                deadline_text = f"截止：{p['deadline']}（{p['deadline_status']['status_text']}）" if p['deadline'] else "无固定截止日"
                st.markdown(f"""
                <div class="top3-card top3-card-{p['diagnosis']}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: var(--apple-text);">{p['rank']}. {p['policy_name']}</div>
                            <div style="margin-top: 0.3rem; color: var(--apple-muted); font-size: 0.85rem;">
                                {p['diagnosis']} · 综合 {p['combined_score']} 分 · 政策优先级 {p['priority']}
                            </div>
                            <div style="margin-top: 0.3rem; color: var(--apple-text);"><strong>时间线：</strong>{p['timeline_advice']}</div>
                            <div style="margin-top: 0.2rem; color: var(--apple-muted); font-size: 0.85rem;">{deadline_text}</div>
                            <div style="margin-top: 0.3rem; color: var(--apple-text); font-size: 0.9rem;"><strong>扶持内容：</strong>{p['benefit']}</div>
                            {f"<div style='margin-top: 0.2rem; color: var(--apple-muted); font-size: 0.85rem;'><strong>关键差距：</strong>{'、'.join(p['key_gaps'])}</div>" if p['key_gaps'] else ""}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无推荐政策。")

    # ---------- 企业能力雷达图与差距分析 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">📈 企业能力与差距分析</div>', unsafe_allow_html=True)

        cap_col1, cap_col2 = st.columns([1, 1])
        with cap_col1:
            st.plotly_chart(fig_radar, use_container_width=True, key="report_radar")

        with cap_col2:
            st.plotly_chart(fig_capability, use_container_width=True, key="report_capability_bar")

        gap_col1, gap_col2 = st.columns([1, 1])
        with gap_col1:
            st.markdown("**维度分数**")
            score_data = []
            for dim, score in capability_scores.items():
                level = "强" if score >= 80 else "良" if score >= 60 else "弱"
                score_data.append({"维度": dim, "分数": score, "评价": level})
            st.dataframe(score_data, use_container_width=True, hide_index=True)

        with gap_col2:
            st.markdown("**高频差距 / 缺失项 TOP5**")
            st.plotly_chart(fig_gap, use_container_width=True, key="report_gap_bar")

        st.markdown("**💡 维度短板建议**")
        for item in sections['capability_assessment']:
            st.markdown(f"- {item}")

    # ---------- 详细诊断结果 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">📝 详细诊断结果</div>', unsafe_allow_html=True)

        diagnosis_order = ["立即申报", "培育申报", "持续关注", "暂不适合"]
        for diagnosis in diagnosis_order:
            items = [r for r in results if r.get('diagnosis') == diagnosis]
            if not items:
                continue

            with st.expander(f"{diagnosis}（{len(items)} 条）", expanded=(diagnosis in ["立即申报", "培育申报"])):
                for r in items:
                    st.markdown(f"<div class='expander-policy-name'>{r['policy_name']}</div>", unsafe_allow_html=True)

                    if sections['is_enhanced'] and 'combined_score' in r:
                        st.markdown(f"- **综合匹配度**：{r['combined_score']} 分（硬 {r['hard_score']} + 软 {r.get('soft_score', 'N/A')}）")
                    else:
                        st.markdown(f"- **匹配度**：{r['match_score']} 分")

                    st.markdown(f"- **政策层级**：{r['level']}")
                    st.markdown(f"- **申报截止**：{r['deadline']}")
                    st.markdown(f"- **扶持内容**：{r['benefit']}")
                    st.markdown(f"- **诊断理由**：{r['reason']}")

                    if r.get('failed'):
                        st.markdown("- **差距**：")
                        for item in r['failed']:
                            st.markdown(f"  - {humanize_gap_item(item)}")

                    if r.get('unknown'):
                        st.markdown("- **需补充数据**：")
                        for item in r['unknown']:
                            st.markdown(f"  - {humanize_gap_item(item)}")

                    if sections['is_enhanced'] and r.get('soft_score') is not None:
                        st.markdown(f"- **LLM 软条件评估**：{r['soft_score']} 分（置信度：{r.get('confidence', '未知')}）")
                        st.markdown(f"- **综合评估**：{r.get('soft_assessment', '')}")

                        if r.get('strengths'):
                            st.markdown("- **优势**：")
                            for item in r['strengths']:
                                st.markdown(f"  - {item}")

                        if r.get('weaknesses'):
                            st.markdown("- **短板**：")
                            for item in r['weaknesses']:
                                st.markdown(f"  - {item}")

                        if r.get('cultivation_suggestions'):
                            st.markdown("- **培育建议**：")
                            for item in r['cultivation_suggestions']:
                                st.markdown(f"  - {item}")

                    if r.get('material_outline'):
                        outline = r['material_outline']
                        st.markdown(f"- **申报可行性**：{outline.get('applicability', '')}")
                        st.markdown("- **申报材料大纲**：")
                        for section in outline.get('outline', []):
                            st.markdown(f"  - **{section.get('section', '')}**：{'; '.join(section.get('content', []))}")
                        if outline.get('key_attachments'):
                            st.markdown("- **关键附件清单**：")
                            for item in outline['key_attachments']:
                                st.markdown(f"  - {item}")
                        if outline.get('gap_fill_plan'):
                            st.markdown("- **差距补齐计划**：")
                            for item in outline['gap_fill_plan']:
                                st.markdown(f"  - {item}")
                        if outline.get('notes'):
                            st.markdown(f"- **特别提醒**：{outline['notes']}")

                    st.divider()

    # ---------- 下一步行动建议 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">🚀 下一步行动建议</div>', unsafe_allow_html=True)

        a_col1, a_col2, a_col3 = st.columns(3)
        action_map = [
            ("立即行动（0-30 天）", sections['next_steps']['immediate'], "⚡"),
            ("中期培育（1-12 个月）", sections['next_steps']['medium'], "🌱"),
            ("长期关注（1-2 年）", sections['next_steps']['long'], "🔭"),
        ]
        for col, (title, items, icon) in zip([a_col1, a_col2, a_col3], action_map):
            with col:
                items_html = "".join([f"<li>{item}</li>" for item in items])
                st.markdown(f"""
                <div class="action-card">
                    <h4>{icon} {title}</h4>
                    <ul>{items_html}</ul>
                </div>
                """, unsafe_allow_html=True)


with tab_roadmap:
    # ---------- 培育路线图生成 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">🌱 个性化培育路线图</div>', unsafe_allow_html=True)
        st.markdown("根据诊断结果中的差距项，生成按阶段、可执行的培育动作清单。")

        roadmap_col1, roadmap_col2, roadmap_col3 = st.columns([2, 2, 1])
        with roadmap_col1:
            use_llm_roadmap = st.toggle(
                "使用 LLM 增强（更具体）",
                value=False,
                key="roadmap_use_llm",
                help="开启后会调用 LLM 生成更个性化的培育建议，需配置 API Key"
            )
        with roadmap_col2:
            roadmap_top_n = st.slider(
                "培育政策数量",
                min_value=1,
                max_value=8,
                value=3,
                key="roadmap_top_n",
                help="对前 N 条培育申报/暂不适合政策生成路线图"
            )
        with roadmap_col3:
            st.markdown("&nbsp;")
            if st.button("生成路线图", type="primary", use_container_width=True, key="btn_generate_roadmap"):
                with st.spinner("正在生成培育路线图..."):
                    try:
                        if use_llm_roadmap and (not api_key and not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY")):
                            st.warning("未配置 API Key，将使用规则生成模式。请在侧边栏输入 Key 或配置 .env 文件。")
                            use_llm_roadmap = False

                        if use_llm_roadmap:
                            roadmap = generate_enhanced_roadmap(
                                enterprise=enterprise,
                                diagnosis_result=result,
                                provider=provider,
                                api_key=api_key if api_key else None,
                                use_demo=False,
                                top_n=roadmap_top_n,
                            )
                        else:
                            roadmap = generate_enterprise_roadmap(
                                diagnosis_result=result,
                                top_n=roadmap_top_n,
                            )

                        save_roadmap(roadmap)
                        st.session_state['roadmap'] = roadmap
                        st.session_state['roadmap_markdown'] = build_roadmap_markdown(roadmap)
                        st.success("✅ 培育路线图生成完成！")
                    except Exception as e:
                        st.error(f"生成路线图失败：{e}")

    # ---------- 路线图展示 ----------
    if 'roadmap' in st.session_state:
        roadmap = st.session_state['roadmap']

        # 概览指标
        summary = roadmap.get('summary', {})
        r_col1, r_col2, r_col3, r_col4 = st.columns(4)
        with r_col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("目标政策", summary.get('target_policies', 0))
            st.markdown('</div>', unsafe_allow_html=True)
        with r_col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("培育动作", summary.get('total_actions', 0))
            st.markdown('</div>', unsafe_allow_html=True)
        with r_col3:
            st.markdown('<div class="metric-card metric-card-red">', unsafe_allow_html=True)
            st.metric("立即行动", summary.get('phase_counts', {}).get('immediate', 0))
            st.markdown('</div>', unsafe_allow_html=True)
        with r_col4:
            st.markdown('<div class="metric-card metric-card-orange">', unsafe_allow_html=True)
            st.metric("中期培育", summary.get('phase_counts', {}).get('medium', 0))
            st.markdown('</div>', unsafe_allow_html=True)

        # LLM 增强标识
        if roadmap.get('llm_enhanced'):
            st.info(f"🧠 本路线图已使用 {roadmap.get('llm_provider', 'LLM')} 增强")
        else:
            st.info("ℹ️ 当前为规则生成的路线图，开启 LLM 增强可获得更具体建议")

        st.divider()

        # 阶段动作卡片
        phased_actions = roadmap.get('phased_actions', {})
        for phase in PHASE_ORDER:
            actions = phased_actions.get(phase, [])
            if not actions:
                continue

            st.markdown(f'<div class="roadmap-phase-title">{PHASE_LABELS[phase]}（{len(actions)} 项）</div>', unsafe_allow_html=True)

            for action in actions:
                difficulty = action.get('difficulty', '中')
                diff_class = {
                    "低": "roadmap-tag-difficulty-low",
                    "中": "roadmap-tag-difficulty-medium",
                    "高": "roadmap-tag-difficulty-high",
                }.get(difficulty, "roadmap-tag-difficulty-medium")

                related = action.get('related_policies', [])
                related_html = f'<span class="roadmap-tag">关联：{"、".join(related[:3])}</span>' if related else ""

                st.markdown(f"""
                <div class="roadmap-action-card roadmap-action-card-phase-{phase}">
                    <div class="roadmap-action-title">{action.get('title', '')}</div>
                    <div class="roadmap-action-meta">{action.get('trigger_gap', '')}</div>
                    <div class="roadmap-action-desc">{action.get('description', '')}</div>
                    <div class="roadmap-action-tags">
                        <span class="roadmap-tag roadmap-tag-owner">{action.get('owner', '')}</span>
                        <span class="roadmap-tag {diff_class}">难度：{difficulty}</span>
                        <span class="roadmap-tag">⏱ {action.get('estimated_time', '')}</span>
                        <span class="roadmap-tag">💰 {action.get('estimated_cost', '')}</span>
                        {related_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 按政策展开的详细路线图
        st.divider()
        st.markdown('<div class="section-title">📋 按政策查看培育动作</div>', unsafe_allow_html=True)
        for pr in roadmap.get('policy_roadmaps', []):
            with st.expander(f"《{pr['policy_name']}》({pr['diagnosis']}，{pr['combined_score']} 分)"):
                if pr['actions']:
                    for action in pr['actions']:
                        st.markdown(f"**{action.get('title', '')}**（{PHASE_LABELS.get(action.get('phase', ''), action.get('phase', ''))}）")
                        st.markdown(f"- 说明：{action.get('description', '')}")
                        st.markdown(f"- 负责方：{action.get('owner', '')} | 难度：{action.get('difficulty', '')} | 预计：{action.get('estimated_time', '')} / {action.get('estimated_cost', '')}")
                else:
                    st.info("该政策暂无培育动作，可能为立即申报或差距较小。")

        # 导出
        st.divider()
        st.markdown('<div class="section-title">📥 导出培育路线图</div>', unsafe_allow_html=True)
        roadmap_md = st.session_state.get('roadmap_markdown', build_roadmap_markdown(roadmap))
        c_md, c_docx = st.columns(2)
        c_pdf, c_html = st.columns(2)
        with c_md:
            st.download_button(
                label="Markdown (.md)",
                data=roadmap_md,
                file_name=f"{date_prefix}_{enterprise_name}_培育路线图.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_roadmap_md"
            )
        with c_docx:
            st.download_button(
                label="Word (.docx)",
                data=build_roadmap_word_report(roadmap),
                file_name=f"{date_prefix}_{enterprise_name}_培育路线图.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="download_roadmap_docx"
            )
        with c_pdf:
            st.download_button(
                label="PDF (.pdf)",
                data=build_roadmap_pdf_report(roadmap),
                file_name=f"{date_prefix}_{enterprise_name}_培育路线图.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_roadmap_pdf"
            )
        with c_html:
            st.download_button(
                label="HTML (.html)",
                data=build_roadmap_html_report(roadmap),
                file_name=f"{date_prefix}_{enterprise_name}_培育路线图.html",
                mime="text/html",
                use_container_width=True,
                key="download_roadmap_html"
            )
    else:
        st.info("👆 点击「生成路线图」按钮，系统将根据诊断结果自动生成培育建议。")


with tab_markdown:
    # ---------- 完整报告预览 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">📝 完整报告预览（Markdown）</div>', unsafe_allow_html=True)
        st.markdown(report)

    # ---------- 报告导出 ----------
    with st.container(border=True):
        st.markdown('<div class="section-title">📥 报告导出</div>', unsafe_allow_html=True)

        if not kaleido_available:
            st.info("ℹ️ 未安装 `kaleido`，Word/PDF 导出将使用「维度分数表格」替代雷达图。如需嵌入雷达图，请运行 `pip install kaleido` 后重启应用。")

        download_col1, download_col2, download_col3, download_col4 = st.columns(4)

        with download_col1:
            st.download_button(
                label="Markdown (.md)",
                data=report,
                file_name=f"{file_name_base}.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_markdown"
            )

        with download_col2:
            word_error = None
            word_bytes = None
            try:
                word_bytes = build_word_report(result, capability_scores, radar_image_bytes=radar_image_bytes)
            except Exception as e:
                word_error = str(e)

            if word_error:
                st.button(
                    label="Word 导出不可用",
                    disabled=True,
                    use_container_width=True,
                    help=f"Word 导出失败：{word_error}"
                )
                st.error(f"❌ Word 导出失败：{word_error}")
            else:
                st.download_button(
                    label="Word (.docx)",
                    data=word_bytes,
                    file_name=f"{file_name_base}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="download_word"
                )

        with download_col3:
            pdf_error = None
            pdf_bytes = None
            try:
                pdf_bytes = build_pdf_report(result, capability_scores, radar_image_bytes=radar_image_bytes)
            except Exception as e:
                pdf_error = str(e)

            if pdf_error:
                st.button(
                    label="PDF 导出不可用",
                    disabled=True,
                    use_container_width=True,
                    help=f"PDF 导出失败：{pdf_error}"
                )
                st.error(f"❌ PDF 导出失败：{pdf_error}")
            else:
                st.download_button(
                    label="PDF (.pdf)",
                    data=pdf_bytes,
                    file_name=f"{file_name_base}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_pdf"
                )

        with download_col4:
            st.download_button(
                label="HTML (.html)",
                data=html_report,
                file_name=f"{file_name_base}.html",
                mime="text/html",
                use_container_width=True,
                key="download_html"
            )

st.info("💡 提示：可以把这份报告保存下来，作为企业申报规划的参考。")
