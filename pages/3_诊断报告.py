import streamlit as st
import json
import os
import sys
from datetime import datetime

# 添加引擎路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.report_export import (
    build_html_report,
    build_markdown_report,
    build_word_report,
    build_pdf_report,
    build_report_sections,
    select_top3_policies,
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
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.75rem;
}
.profile-item {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-md);
    padding: 0.9rem 1rem;
    box-shadow: var(--shadow-sm);
}
.profile-item-label {
    font-size: 0.8rem;
    color: var(--apple-muted);
    margin-bottom: 0.2rem;
}
.profile-item-value {
    font-size: 1rem;
    font-weight: 600;
    color: var(--apple-text);
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


# ========== 两大模块 Tab ==========
tab_result, tab_markdown = st.tabs(["📊 诊断结果", "📝 完整报告预览（Markdown）"])


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
            st.markdown(ep['text'])

            profile_items = [
                ("所属行业", f"{ep['industry']}（{ep['sub_industry']}）"),
                ("企业规模", f"{ep['scale']} / {ep['employees']} 人"),
                ("所在地区", ep['region']),
                ("成立年份", ep['founded_year']),
                ("上年度营收", f"{ep['revenue']} 万元"),
                ("上年度利润", f"{ep['profit']} 万元"),
                ("研发投入", f"{ep['rd_investment']} 万元"),
                ("研发占比", ep['rd_ratio']),
                ("研发人员", f"{ep['rd_team_size']} 人 / {ep['rd_team_ratio']}"),
                ("高新技术产品收入占比", ep['high_tech_income_ratio']),
                ("发明专利", ep['invention_patents']),
                ("实用新型", ep['utility_models']),
                ("软件著作权", ep['software_copyrights']),
                ("商标", ep['trademarks']),
                ("已获资质", "、".join(ep['qualifications']) if ep['qualifications'] else "—"),
                ("国家高新技术企业", "是" if ep['is_high_tech_enterprise'] else "否"),
                ("研发准备金制度", "已建立" if ep['rd_accounting_system'] else "未建立"),
                ("近三年重大事故", "有" if ep['has_major_accident'] else "无"),
            ]

            st.markdown('<div class="profile-grid">', unsafe_allow_html=True)
            for label, value in profile_items:
                st.markdown(f"""
                <div class="profile-item">
                    <div class="profile-item-label">{label}</div>
                    <div class="profile-item-value">{value}</div>
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
                            st.markdown(f"  - {item}")

                    if r.get('unknown'):
                        st.markdown("- **需补充数据**：")
                        for item in r['unknown']:
                            st.markdown(f"  - {item}")

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
