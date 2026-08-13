import streamlit as st
from engine.ui_helpers import inject_apple_theme

st.set_page_config(
    page_title="企业政策诊断辅导智能体",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入 Apple 风格全局主题
inject_apple_theme()

# 首页专属样式
st.markdown("""
<style>
/* 首页减少顶部 padding，让 Hero 更靠近顶部 */
.block-container {
    padding-top: 2rem !important;
}

/* Hero 区域 */
.home-hero {
    text-align: center;
    padding: 3rem 1rem 2.5rem;
}
.home-hero-title {
    font-size: 3.2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.75rem;
    background: linear-gradient(135deg, #1d1d1f 0%, #5e5e60 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.home-hero-subtitle {
    font-size: 1.3rem;
    font-weight: 400;
    color: var(--apple-muted);
    letter-spacing: 0.02em;
}

/* 快速入口卡片 */
.home-quick-links {
    margin-top: 1rem;
}
.home-card {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    padding: 2rem 1.5rem;
    height: 100%;
    transition: transform 0.35s cubic-bezier(0.25, 0.1, 0.25, 1), box-shadow 0.35s cubic-bezier(0.25, 0.1, 0.25, 1);
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .home-card {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}
.home-card:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-lg);
}
.home-card-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}
.home-card-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--apple-text);
    margin-bottom: 0.5rem;
    letter-spacing: -0.01em;
    text-decoration: none;
    display: inline-block;
    transition: color 0.25s ease;
}
a.home-card-title:hover,
a.home-card-title:focus {
    color: var(--apple-blue);
    text-decoration: none;
}
.home-card-desc {
    font-size: 0.92rem;
    color: var(--apple-muted);
    margin-bottom: 1.25rem;
    line-height: 1.55;
}
.capability-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
}
.capability-grid-item {
    background: var(--apple-card-solid);
    border: 1px solid var(--apple-border);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
    .capability-grid-item {
        background: var(--apple-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
}
.capability-grid-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.capability-grid-icon {
    font-size: 1.4rem;
    line-height: 1;
}
.capability-grid-text {
    font-size: 0.92rem;
    color: var(--apple-text);
    line-height: 1.5;
    font-weight: 500;
}

@media (max-width: 640px) {
    .home-hero-title { font-size: 2.1rem; }
    .home-hero-subtitle { font-size: 1rem; }
    .capability-grid { grid-template-columns: 1fr; }
    .home-card { padding: 1.5rem 1.25rem; }
}
</style>
""", unsafe_allow_html=True)

# ========== Hero 区域 ==========
st.markdown("""
<div class="home-hero">
    <div class="home-hero-title">🤖 企业政策诊断辅导智能体</div>
    <div class="home-hero-subtitle">发现政策 · 诊断差距 · 辅导申报 · 生成材料</div>
</div>
""", unsafe_allow_html=True)

# ========== 快速入口 ==========
st.markdown("<div style='text-align: center; margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

st.markdown('<div class="home-quick-links">', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="home-card">
        <div class="home-card-icon">🏢</div>
        <a href="企业画像" class="home-card-title">填写企业画像</a>
        <div class="home-card-desc">录入企业基本信息、经营数据、研发与知识产权，建立诊断基础。</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="home-card">
        <div class="home-card-icon">🔍</div>
        <a href="政策诊断" class="home-card-title">运行政策诊断</a>
        <div class="home-card-desc">基于硬条件匹配 + LLM 软条件评估，自动判断适合申报哪些政策。</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="home-card">
        <div class="home-card-icon">📋</div>
        <a href="诊断报告" class="home-card-title">查看诊断报告</a>
        <div class="home-card-desc">查看执行摘要、TOP3 政策路线图、雷达图，并导出 Word/PDF 报告。</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ========== 当前能力 ==========
st.subheader("✅ 当前能力")

st.markdown("""
<div class="capability-grid">
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🏢</div>
        <div class="capability-grid-text">企业画像录入（卡片分组，数据完整保存）</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">📊</div>
        <div class="capability-grid-text">企业能力雷达图（6 个维度能力评估）</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🔍</div>
        <div class="capability-grid-text">硬条件政策匹配引擎（12 条合肥/安徽示例政策）</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🧠</div>
        <div class="capability-grid-text">LLM 软条件打分（支持 Anthropic / OpenAI，演示模式免 API Key）</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">📋</div>
        <div class="capability-grid-text">诊断报告导出（Markdown / Word / PDF，含执行摘要、TOP3 路线图、雷达图）</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">📝</div>
        <div class="capability-grid-text">申报材料大纲生成（针对「立即申报」「培育申报」政策）</div>
    </div>
    <div class="capability-grid-item">
        <div class="capability-grid-icon">🎯</div>
        <div class="capability-grid-text">顶部步骤指示器（企业画像 → 政策诊断 → 诊断报告）</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.info("👈 也可以直接点击左侧菜单栏进入各页面")
