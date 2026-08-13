"""
企业政策硬条件匹配引擎
用途：基于企业画像和政策库，输出每条政策的诊断结果
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Tuple


def load_json(file_path: str) -> Dict[str, Any]:
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path: str, data: Dict[str, Any]) -> None:
    """保存 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_condition(value: Any, condition: Dict[str, Any], condition_name: str) -> Tuple[bool, str]:
    """检查单个条件是否满足"""
    if value is None:
        return False, f"{condition_name}: 数据缺失，需补充"

    if 'min' in condition:
        if value < condition['min']:
            gap = condition['min'] - value
            return False, f"{condition_name}: 当前 {value}，要求 ≥ {condition['min']}，差 {gap:.2f}"

    if 'max' in condition:
        if value > condition['max']:
            gap = value - condition['max']
            return False, f"{condition_name}: 当前 {value}，要求 ≤ {condition['max']}，超出 {gap:.2f}"

    if 'required' in condition:
        required = condition['required']
        if bool(value) != required:
            status = "需要" if required else "不需要"
            return False, f"{condition_name}: 当前 {value}，要求{status}满足"

    if 'contains' in condition:
        required_items = condition['contains']
        if not isinstance(value, list):
            value = [value]
        missing = [item for item in required_items if item not in value]
        if missing:
            return False, f"{condition_name}: 缺少资质 {missing}"

    if 'in' in condition:
        allowed = condition['in']
        if value not in allowed:
            return False, f"{condition_name}: 当前 {value}，不在允许范围 {allowed} 内"

    return True, f"{condition_name}: 满足"


def match_policy(enterprise: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    """对单条政策进行硬条件匹配"""
    hard_conditions = policy.get('hard_conditions', {})
    passed = []
    failed = []
    unknown = []

    # 地区匹配
    policy_regions = policy.get('region', [])
    enterprise_region = enterprise.get('province', '') + enterprise.get('city', '')
    region_match = False
    for r in policy_regions:
        if r == '全国':
            region_match = True
            break
        if r in enterprise_region or enterprise_region in r:
            region_match = True
            break
    if not region_match:
        failed.append(f"地区: 当前 {enterprise.get('region')}，政策适用 {policy_regions}")
    else:
        passed.append(f"地区: {enterprise.get('region')} 在政策适用范围内")

    # 逐项检查硬条件
    for condition_name, condition in hard_conditions.items():
        value = enterprise.get(condition_name)
        is_passed, message = check_condition(value, condition, condition_name)

        if is_passed:
            passed.append(message)
        elif "数据缺失" in message:
            unknown.append(message)
        else:
            failed.append(message)

    diagnosis, reason = determine_diagnosis(passed, failed, unknown, policy)

    return {
        "policy_id": policy['policy_id'],
        "policy_name": policy['policy_name'],
        "level": policy['level'],
        "category": policy['category'],
        "deadline": policy.get('deadline', ''),
        "diagnosis": diagnosis,
        "reason": reason,
        "passed_count": len(passed),
        "failed_count": len(failed),
        "unknown_count": len(unknown),
        "passed": passed,
        "failed": failed,
        "unknown": unknown,
        "benefit": policy.get('benefit', ''),
        "priority": policy.get('priority', '中')
    }


def determine_diagnosis(passed: List[str], failed: List[str], unknown: List[str], policy: Dict[str, Any]) -> Tuple[str, str]:
    """根据条件检查结果判断诊断结果"""
    deadline_str = policy.get('deadline', '')

    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            if deadline < datetime.now():
                return "持续关注", "政策已过期"
            days_left = (deadline - datetime.now()).days
            if days_left < 7:
                return "立即申报", f"即将截止（剩 {days_left} 天），如条件满足请立即申报"
        except ValueError:
            pass

    total_conditions = len(passed) + len(failed) + len(unknown)
    if total_conditions > 0 and len(unknown) / total_conditions > 0.5:
        return "持续关注", "关键数据缺失，补充后可重新诊断"

    if len(failed) == 0 and len(unknown) == 0:
        return "立即申报", "所有硬条件均满足"

    if len(failed) > 0:
        if len(failed) <= 2:
            return "培育申报", f"存在 {len(failed)} 项可补齐差距，建议 1-2 年内培育"
        else:
            return "暂不适合", f"存在 {len(failed)} 项差距，短期内难以补齐"

    return "持续关注", "部分条件数据缺失，补充后进一步判断"


def calculate_match_score(result: Dict[str, Any]) -> int:
    """计算匹配度分数"""
    total = result['passed_count'] + result['failed_count'] + result['unknown_count']
    if total == 0:
        return 0
    score = (result['passed_count'] + result['unknown_count'] * 0.3) / total * 100
    return min(int(score), 100)


def run_diagnosis(enterprise: Dict[str, Any], policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """运行完整诊断"""
    results = []
    for policy in policies:
        result = match_policy(enterprise, policy)
        result['match_score'] = calculate_match_score(result)
        results.append(result)

    # 按诊断优先级排序
    diagnosis_order = {"立即申报": 0, "培育申报": 1, "持续关注": 2, "暂不适合": 3}
    results.sort(key=lambda x: (diagnosis_order.get(x['diagnosis'], 99), -x['match_score']))

    diagnosis_count = {}
    for r in results:
        diagnosis_count[r['diagnosis']] = diagnosis_count.get(r['diagnosis'], 0) + 1

    return {
        "enterprise_name": enterprise.get('name', ''),
        "diagnosis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "summary": diagnosis_count,
        "results": results
    }
