import json
import os
import sys
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

# 添加引擎路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.ui_helpers import inject_apple_theme

st.set_page_config(page_title="政策库管理", page_icon="📚", layout="wide")

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
/* 让主按钮更醒目 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--apple-blue) 0%, var(--apple-blue-dark) 100%) !important;
    box-shadow: 0 4px 16px rgba(0, 113, 227, 0.25) !important;
}
/* 表格样式 */
.stDataFrame {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📚 政策库管理</div>', unsafe_allow_html=True)
st.markdown('<div class="help-text">在这里批量导入、导出和维护政策数据。支持 Excel / CSV 格式，方便你在表格软件里整理后一键上传。</div>', unsafe_allow_html=True)

DATA_FILE = "data/policies.json"
TEMPLATE_FILE = "data/policies_template.xlsx"


def load_policies():
    """加载当前政策库"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_policies(policies):
    """保存政策库到 JSON 文件"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(policies, f, ensure_ascii=False, indent=2)


def policy_to_row(policy):
    """把单个政策对象转为一行扁平数据"""
    return {
        "policy_id": policy.get("policy_id", ""),
        "policy_name": policy.get("policy_name", ""),
        "level": policy.get("level", ""),
        "region": ",".join(policy.get("region", [])) if isinstance(policy.get("region"), list) else policy.get("region", ""),
        "category": policy.get("category", ""),
        "deadline": policy.get("deadline", ""),
        "benefit": policy.get("benefit", ""),
        "priority": policy.get("priority", ""),
        "hard_conditions": json.dumps(policy.get("hard_conditions", {}), ensure_ascii=False),
    }


def row_to_policy(row):
    """把一行扁平数据转为政策对象"""
    region = row.get("region", "")
    if isinstance(region, str):
        region = [r.strip() for r in region.split(",") if r.strip()]

    hard_conditions = {}
    hc_value = row.get("hard_conditions", "")
    if isinstance(hc_value, str) and hc_value.strip():
        try:
            hard_conditions = json.loads(hc_value)
        except json.JSONDecodeError:
            raise ValueError(f"政策 [{row.get('policy_id', '?')}] 的 hard_conditions 不是合法 JSON")
    elif isinstance(hc_value, dict):
        hard_conditions = hc_value

    policy = {
        "policy_id": str(row.get("policy_id", "")).strip(),
        "policy_name": str(row.get("policy_name", "")).strip(),
        "level": str(row.get("level", "")).strip(),
        "region": region,
        "category": str(row.get("category", "")).strip(),
        "deadline": str(row.get("deadline", "")).strip(),
        "benefit": str(row.get("benefit", "")).strip(),
        "priority": str(row.get("priority", "")).strip(),
        "hard_conditions": hard_conditions,
    }
    return policy


def validate_policies(policies):
    """验证政策列表，返回 (是否通过, 错误列表)"""
    errors = []
    ids = set()
    for idx, p in enumerate(policies, 1):
        if not p.get("policy_id"):
            errors.append(f"第 {idx} 行：policy_id 不能为空")
        elif p["policy_id"] in ids:
            errors.append(f"第 {idx} 行：policy_id [{p['policy_id']}] 重复")
        else:
            ids.add(p["policy_id"])

        if not p.get("policy_name"):
            errors.append(f"第 {idx} 行：policy_name 不能为空")

        if not p.get("level"):
            errors.append(f"第 {idx} 行：level 不能为空")

        if not p.get("category"):
            errors.append(f"第 {idx} 行：category 不能为空")

        deadline = p.get("deadline", "")
        if deadline:
            try:
                datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                errors.append(f"第 {idx} 行：deadline [{deadline}] 格式错误，应为 YYYY-MM-DD")

        priority = p.get("priority", "")
        if priority and priority not in ["高", "中", "低"]:
            errors.append(f"第 {idx} 行：priority 只能是「高 / 中 / 低」之一")

    return len(errors) == 0, errors


def build_template_excel():
    """生成带示例的 Excel 模板"""
    sample = [
        {
            "policy_id": "HF-013",
            "policy_name": "示例政策名称",
            "level": "市级",
            "region": "合肥市",
            "category": "研发创新",
            "deadline": "2026-12-31",
            "benefit": "按研发投入10%补助，最高100万",
            "priority": "高",
            "hard_conditions": json.dumps({
                "rd_ratio": {"min": 0.03, "desc": "研发投入占比≥3%"},
                "revenue": {"min": 1000, "desc": "上年度营收≥1000万"}
            }, ensure_ascii=False),
        }
    ]
    df = pd.DataFrame(sample)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="政策模板")
        # 写入说明表
        instructions = pd.DataFrame({
            "字段": ["policy_id", "policy_name", "level", "region", "category", "deadline", "benefit", "priority", "hard_conditions"],
            "说明": [
                "政策唯一编号，不可重复",
                "政策名称",
                "政策级别，如：国家级、省级、市级",
                "适用地区，多个用英文逗号分隔，如：合肥市,安徽省",
                "政策类别，如：资质认定、研发创新、智能制造、产业扶持、人才引育",
                "申报截止日期，格式 YYYY-MM-DD，可为空",
                "政策奖励/补贴内容",
                "优先级：高 / 中 / 低",
                "硬条件 JSON，示例见第一行"
            ]
        })
        instructions.to_excel(writer, index=False, sheet_name="填写说明")
    buffer.seek(0)
    return buffer


def build_current_excel(policies):
    """把当前政策库导出为 Excel"""
    rows = [policy_to_row(p) for p in policies]
    df = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="政策库")
    buffer.seek(0)
    return buffer


# ========== 当前政策库概览 ==========
policies = load_policies()

with st.container(border=True):
    st.markdown('<div class="section-title">📊 当前政策库概览</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("政策总数", len(policies))
    categories = {}
    for p in policies:
        cat = p.get("category", "未分类")
        categories[cat] = categories.get(cat, 0) + 1
    c2.metric("政策类别数", len(categories))
    levels = {}
    for p in policies:
        lv = p.get("level", "未知")
        levels[lv] = levels.get(lv, 0) + 1
    c3.metric("政策级别数", len(levels))
    high_priority = sum(1 for p in policies if p.get("priority") == "高")
    c4.metric("高优先级", high_priority)

    if categories:
        st.caption("类别分布：" + " ｜ ".join([f"{k}: {v}" for k, v in sorted(categories.items(), key=lambda x: -x[1])]))

# ========== 下载模板 / 导出当前库 ==========
with st.container(border=True):
    st.markdown('<div class="section-title">⬇️ 下载模板 / 导出数据</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-text">推荐先下载「带示例的模板」看看填写格式，也可以下载当前政策库在本地编辑后再上传。</div>', unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button(
            label="📥 下载带示例的 Excel 模板",
            data=build_template_excel(),
            file_name="政策库导入模板.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_b:
        if policies:
            st.download_button(
                label="📤 导出当前政策库（Excel）",
                data=build_current_excel(policies),
                file_name=f"政策库导出_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.button("📤 导出当前政策库（Excel）", disabled=True, use_container_width=True)
    with col_c:
        json_str = json.dumps(policies, ensure_ascii=False, indent=2)
        st.download_button(
            label="📄 导出当前政策库（JSON）",
            data=json_str,
            file_name=f"policies_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
        )

# ========== 上传并导入 ==========
with st.container(border=True):
    st.markdown('<div class="section-title">⬆️ 上传政策库文件</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-text">支持 .xlsx 或 .csv 格式。上传后会先预览和校验，确认无误再保存。</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("选择文件", type=["xlsx", "csv"], label_visibility="collapsed")

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, dtype=str).fillna("")
            else:
                df = pd.read_excel(uploaded_file, sheet_name=0, dtype=str).fillna("")

            st.success(f"成功读取 {len(df)} 条政策记录")
            st.markdown("**字段映射预览（前 5 行）：**")
            st.dataframe(df.head(5), use_container_width=True, hide_index=True)

            new_policies = []
            parse_errors = []
            for idx, row in df.iterrows():
                try:
                    new_policies.append(row_to_policy(row.to_dict()))
                except ValueError as e:
                    parse_errors.append(str(e))

            if parse_errors:
                st.error("解析出错：")
                for err in parse_errors[:10]:
                    st.write(f"- {err}")
                if len(parse_errors) > 10:
                    st.write(f"... 还有 {len(parse_errors) - 10} 条错误")
            else:
                is_valid, errors = validate_policies(new_policies)
                if not is_valid:
                    st.error("校验未通过，请修正后重新上传：")
                    for err in errors[:15]:
                        st.write(f"- {err}")
                    if len(errors) > 15:
                        st.write(f"... 还有 {len(errors) - 15} 条错误")
                else:
                    st.markdown("**校验通过，即将导入的政策列表：**")
                    preview_df = pd.DataFrame([policy_to_row(p) for p in new_policies])
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)

                    merge_option = st.radio(
                        "保存方式",
                        ["覆盖现有政策库", "合并导入（相同 policy_id 覆盖，其他保留）"],
                        index=1,
                    )

                    if st.button("💾 保存到政策库", type="primary", use_container_width=True):
                        if merge_option == "覆盖现有政策库":
                            final_policies = new_policies
                        else:
                            existing_map = {p["policy_id"]: p for p in policies}
                            for p in new_policies:
                                existing_map[p["policy_id"]] = p
                            final_policies = list(existing_map.values())

                        save_policies(final_policies)
                        st.success(f"已保存 {len(final_policies)} 条政策到 {DATA_FILE}")
                        st.balloons()
                        st.info("刷新页面后可在「政策诊断」中使用最新政策库。")

        except Exception as e:
            st.error(f"读取文件失败：{e}")

# ========== 当前政策列表 ==========
with st.container(border=True):
    st.markdown('<div class="section-title">📝 当前政策列表</div>', unsafe_allow_html=True)
    if policies:
        list_df = pd.DataFrame([{
            "编号": p.get("policy_id"),
            "名称": p.get("policy_name"),
            "级别": p.get("level"),
            "类别": p.get("category"),
            "截止日": p.get("deadline"),
            "优先级": p.get("priority"),
        } for p in policies])
        st.dataframe(list_df, use_container_width=True, hide_index=True)
    else:
        st.info("当前政策库为空，请上传政策文件或检查 data/policies.json。")
