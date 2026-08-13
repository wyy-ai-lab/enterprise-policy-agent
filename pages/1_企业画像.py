import streamlit as st
import json
import os
import sys

# 添加引擎路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.radar_chart import calculate_dimension_scores, build_radar_chart, get_dimension_assessment
from engine.ui_helpers import render_step_indicator, inject_apple_theme

st.set_page_config(page_title="企业画像", page_icon="🏢", layout="wide")

# 注入 Apple 风格主题
inject_apple_theme()

# 页面专属微调样式
st.markdown("""
<style>
.main-title {
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--apple-text);
    margin-bottom: 0.25rem;
    letter-spacing: -0.02em;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--apple-card-solid) !important;
    border: 1px solid var(--apple-border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 1.5rem !important;
    margin-bottom: 1.25rem !important;
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--apple-card) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
    }
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
.help-text {
    color: var(--apple-muted);
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}
/* 让保存按钮更醒目 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--apple-blue) 0%, var(--apple-blue-dark) 100%) !important;
    box-shadow: 0 4px 16px rgba(0, 113, 227, 0.25) !important;
}
</style>
""", unsafe_allow_html=True)

render_step_indicator("profile")

st.markdown('<div class="main-title">🏢 企业画像录入</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">请填写企业基本信息，系统将自动保存并用于后续政策诊断。数据越完整，诊断结果越准确。</div>', unsafe_allow_html=True)

# 加载现有数据
data_file = "data/enterprise.json"
if os.path.exists(data_file):
    with open(data_file, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
else:
    existing_data = {}


# 选项列表
INDUSTRY_OPTIONS = [
    "医疗器械制造", "电子元器件制造", "工业软件", "汽车零部件制造",
    "新材料", "高端装备", "其他制造业"
]
SCALE_OPTIONS = ["小型企业", "中型企业", "大型企业", "规模以上"]
QUALIFICATION_OPTIONS = [
    "国家高新技术企业", "安徽省专精特新中小企业", "国家级专精特新小巨人",
    "科技型中小企业", "创新型中小企业", "ISO9001", "ISO13485",
    "CE认证", "医疗器械生产许可证", "医疗器械产品注册证"
]


def get_select_index(options, value, default=0):
    """根据已保存值获取 selectbox 的 index，修复硬编码回显 bug"""
    if value in options:
        return options.index(value)
    return default


# ========== 基础信息 ==========
with st.container(border=True):
    st.markdown('<div class="section-title">📋 基础信息</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("企业名称", value=existing_data.get('name', ''))
    with col2:
        industry = st.selectbox(
            "所属行业",
            INDUSTRY_OPTIONS,
            index=get_select_index(INDUSTRY_OPTIONS, existing_data.get('industry'), default=0)
        )
    with col3:
        sub_industry = st.text_input("细分行业", value=existing_data.get('sub_industry', ''))

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        province = st.text_input("省份", value=existing_data.get('province', '安徽省'))
    with col5:
        city = st.text_input("城市", value=existing_data.get('city', '合肥市'))
    with col6:
        region = st.text_input("注册地区", value=existing_data.get('region', '安徽省合肥市高新区'))
    with col7:
        founded_year = st.number_input("成立年份", min_value=1900, max_value=2030, value=existing_data.get('founded_year', 2002))

    col8, col9 = st.columns(2)
    with col8:
        scale = st.selectbox(
            "企业规模",
            SCALE_OPTIONS,
            index=get_select_index(SCALE_OPTIONS, existing_data.get('scale'), default=0)
        )
    with col9:
        employees = st.number_input("员工人数", min_value=1, value=existing_data.get('employees', 44))


# ========== 经营数据 ==========
with st.container(border=True):
    st.markdown('<div class="section-title">💰 经营数据</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        revenue = st.number_input("上年度营收（万元）", min_value=0, value=existing_data.get('revenue', 4267))
    with col2:
        profit = st.number_input("上年度利润（万元）", min_value=0, value=existing_data.get('profit', 240))
    with col3:
        high_tech_income_ratio = st.slider(
            "高新技术产品收入占比",
            min_value=0.0, max_value=1.0,
            value=existing_data.get('high_tech_income_ratio') or 0.0,
            step=0.01, format="%.2f"
        )


# ========== 研发数据 ==========
with st.container(border=True):
    st.markdown('<div class="section-title">🔬 研发数据</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        rd_investment = st.number_input("上年度研发投入（万元）", min_value=0, value=existing_data.get('rd_investment') or 0)
    with col2:
        rd_ratio = st.slider(
            "研发投入占比",
            min_value=0.0, max_value=1.0,
            value=existing_data.get('rd_ratio') or 0.0,
            step=0.01, format="%.2f"
        )
    with col3:
        rd_team_size = st.number_input("研发人员数量", min_value=0, value=existing_data.get('rd_team_size') or 0)
    with col4:
        rd_team_ratio = st.slider(
            "研发人员占比",
            min_value=0.0, max_value=1.0,
            value=existing_data.get('rd_team_ratio') or 0.0,
            step=0.01, format="%.2f"
        )

    col5, col6 = st.columns(2)
    with col5:
        rd_accounting_system = st.checkbox(
            "是否建立研发准备金制度",
            value=existing_data.get('rd_accounting_system', False)
        )
    with col6:
        is_high_tech_field = st.checkbox(
            "是否属于高新技术领域",
            value=existing_data.get('is_high_tech_field', False)
        )


# ========== 知识产权与资质 ==========
with st.container(border=True):
    st.markdown('<div class="section-title">🏅 知识产权与资质</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        invention_patents = st.number_input("授权发明专利数量", min_value=0, value=existing_data.get('invention_patents', 0))
        utility_models = st.number_input("实用新型专利数量", min_value=0, value=existing_data.get('utility_models', 2))
        software_copyrights = st.number_input("软件著作权数量", min_value=0, value=existing_data.get('software_copyrights', 5))
        trademarks = st.number_input("商标数量", min_value=0, value=existing_data.get('trademarks', 2))

    with col2:
        qualifications = st.multiselect(
            "已获资质",
            QUALIFICATION_OPTIONS,
            default=existing_data.get('qualifications', [])
        )
        is_high_tech_enterprise = st.checkbox(
            "是否已认定为国家高新技术企业",
            value=existing_data.get('is_high_tech_enterprise', False)
        )
        market_share_proof = st.checkbox(
            "是否有市场占有率证明",
            value=existing_data.get('market_share_proof', False)
        )


# ========== 其他信息 ==========
with st.container(border=True):
    st.markdown('<div class="section-title">📝 其他信息</div>', unsafe_allow_html=True)

    has_major_accident = st.checkbox(
        "近三年有重大安全/质量/环保事故",
        value=existing_data.get('has_major_accident', False)
    )
    st.caption("勾选表示存在事故，可能影响部分政策申报资格")


# 保存按钮
if st.button("💾 保存企业画像并查看雷达图", type="primary", use_container_width=True):
    enterprise_data = {
        "name": name,
        "industry": industry,
        "sub_industry": sub_industry,
        "province": province,
        "city": city,
        "region": region,
        "founded_year": founded_year,
        "scale": scale,
        "employees": employees,
        "revenue": revenue,
        "profit": profit,
        "qualifications": qualifications,
        "invention_patents": invention_patents,
        "utility_models": utility_models,
        "software_copyrights": software_copyrights,
        "trademarks": trademarks,
        "rd_investment": rd_investment if rd_investment > 0 else None,
        "rd_ratio": rd_ratio if rd_ratio > 0 else None,
        "rd_team_size": rd_team_size if rd_team_size > 0 else None,
        "rd_team_ratio": rd_team_ratio if rd_team_ratio > 0 else None,
        "high_tech_income_ratio": high_tech_income_ratio if high_tech_income_ratio > 0 else None,
        "is_high_tech_field": is_high_tech_field,
        "is_high_tech_enterprise": is_high_tech_enterprise,
        "market_share_proof": market_share_proof,
        "rd_accounting_system": rd_accounting_system,
        "has_major_accident": has_major_accident,
        "years_in_operation": 2026 - founded_year,
        "years_in_segment": 2026 - founded_year
    }

    # 确保目录存在
    os.makedirs("data", exist_ok=True)

    # 计算能力分数
    capability_scores = calculate_dimension_scores(enterprise_data)
    enterprise_data["capability_scores"] = capability_scores

    # 保存
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(enterprise_data, f, ensure_ascii=False, indent=2)

    st.success(f"✅ 企业画像已保存：{name}")

    st.subheader("📊 企业能力雷达图")
    fig = build_radar_chart(capability_scores, title=f"{name} 综合能力评估")
    st.plotly_chart(fig, use_container_width=True)

    # 展示维度分数和短板建议
    score_cols = st.columns(6)
    for i, (dim, score) in enumerate(capability_scores.items()):
        with score_cols[i]:
            st.metric(label=dim, value=f"{score} 分")

    suggestions = get_dimension_assessment(capability_scores)
    if suggestions:
        st.markdown("**💡 重点关注：**")
        for s in suggestions:
            st.markdown(f"- {s}")
    else:
        st.markdown("**💡 整体能力较均衡，可重点关注高匹配度政策申报**")

st.info("💡 提示：填写完成后，请点击左侧「政策诊断」查看匹配结果，或进入「诊断报告」查看完整报告。")
