#!/usr/bin/env python3
"""
模块一：对话式客户信息采集。
借鉴 csm-ebr-qbr-prep-skill 的逐一问答模式。
采集完成后输出结构化客户画像 + 信息缺口清单 + 摸底问题建议。

使用方式：由 SKILL.md 中的 Claude 调用此脚本的 Prompt 模板。
本脚本提供：Prompt 模板生成、客户类型识别、信息缺口分析。
"""

import sys
import os
import json
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.input_parser import detect_client_type, parse_client_info
from utils.output_formatter import get_output_dir, save_output

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_client_profiles() -> dict:
    path = os.path.join(SKILL_DIR, "config", "client_profiles.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_collection_prompt(client_info: str = "") -> str:
    """
    构建客户信息采集的 Claude Prompt。
    使用逐一对话式采集（每次只问一个问题）。
    """
    profiles = load_client_profiles()

    # 如果已有初始信息，先做类型检测
    detection = {}
    if client_info:
        detection = detect_client_type(client_info)

    type_hint = ""
    if detection.get("type") and detection["type"] != "unknown":
        type_label = profiles[detection["type"]]["label"]
        keywords = "、".join(detection.get("matched_keywords", [])[:3])
        type_hint = f"\n\n> 初步识别：根据「{keywords}」等关键词，判断该客户为**{type_label}**（置信度：{detection.get('confidence', '中')}）。采集时请按对应模板重点收集信息。"

    prompt = f"""# 客户信息采集任务

你是一位资深售前工程师助手，正在帮助售前工程师收集拜访前的客户信息。

## 采集原则（务必遵守）

1. **逐一问答**：每次只提出一个问题，等对方回答后再问下一个。不要把所有问题一次性列出。
2. **反射确认**：收到回答后，先用一句话反射确认（如"我理解贵单位目前的情况是……"），再追问下一个问题。
3. **分区采集**：按 A→B→C→D 四个区块顺序采集，每个区块完成后给出摘要让用户校正。
4. **智能追问**：根据对方的回答，判断是否需要追问细节（比如对方说"有预算"，追问"大概在什么量级"）。
5. **不强制填写**：如果用户说"不知道"或"不方便说"，记录为"待确认"，继续下一个问题。

## 采集区块

**区块 A：基本信息**（2-3个问题）
- 客户公司/单位全称
- 行业/所属领域
- 规模（员工数/年收入量级/IT部门规模）

**区块 B：决策链**（2-3个问题）
- 本次项目的主要联系人是什么角色
- 最终决策者是谁（职位/角色）
- 预算审批流程是怎样的

**区块 C：技术现状**（2-3个问题）
- 目前在 AI/数字化方面已有哪些系统或工具
- 当前最大的技术痛点或瓶颈
- 是否有信创/国产化/数据合规的硬性要求

**区块 D：竞品与背景**（1-2个问题）
- 是否在同时评估其他供应商或方案
- 这次接触的背景/契机是什么{type_hint}

## 当前客户信息

{client_info if client_info else "（尚未提供，请从区块A第一个问题开始）"}

## 你的任务

现在开始采集。请提出区块A的第一个问题。采集完所有区块后，输出：
1. 结构化客户画像（JSON格式）
2. 信息缺口清单（哪些关键信息仍不明确）
3. 建议的摸底问题清单（首次拜访时要问的5-10个问题）
4. 初步机会评分（高/中/低，附理由）
"""
    return prompt


def generate_profile_report(collected_data: dict, client_type: str) -> str:
    """
    根据采集数据生成结构化客户画像报告。
    """
    profiles = load_client_profiles()
    profile = profiles.get(client_type, {})

    required_fields = {
        "government": ["预算来源", "采购方式", "信创要求", "主管领导角色", "历史项目情况"],
        "enterprise": ["技术栈现状", "决策链", "竞品评估情况", "预算范围", "时间节点"],
        "tech": ["技术框架", "团队规模", "商业模式", "当前瓶颈", "已评估方案"],
    }

    fields = required_fields.get(client_type, [])
    gaps = [f for f in fields if not collected_data.get(f)]

    risk_signals = profile.get("risk_signals", [])

    report = f"""# 客户画像报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 公司/单位 | {collected_data.get('company_name', '【待补充】')} |
| 客户类型 | {profile.get('label', client_type)} |
| 行业 | {collected_data.get('industry', '【待补充】')} |
| 规模 | {collected_data.get('size', '【待补充】')} |
| 接触背景 | {collected_data.get('contact_context', '【待补充】')} |

## 决策链分析

"""
    for role_info in profile.get("decision_chain", []):
        report += f"- **{role_info['role']}**：{role_info['concern']}\n"

    report += f"""
## 核心痛点（基于客户类型的高频痛点）

"""
    for pain in profile.get("core_pains", []):
        report += f"- {pain}\n"

    report += f"""
## 信息缺口清单

> ⚠️ 以下信息尚不明确，建议在首次接触中确认：

"""
    if gaps:
        for i, gap in enumerate(gaps, 1):
            report += f"{i}. {gap}\n"
    else:
        report += "> ✅ 信息收集完整\n"

    report += f"""
## 风险信号提示

"""
    for signal in risk_signals:
        report += f"- ⚠️ {signal}\n"

    report += f"""
## 关键卖点（针对该客户类型）

"""
    for point in profile.get("key_selling_points", []):
        report += f"- ✅ {point}\n"

    return report


def main():
    client_info = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

    # 构建采集 Prompt
    prompt = build_collection_prompt(client_info)

    # 如果有初始信息，做类型检测并输出
    if client_info:
        detection = detect_client_type(client_info)
        print(f"客户类型识别：{detection['type']} （置信度：{detection['confidence']}）")
        if detection["matched_keywords"]:
            print(f"匹配关键词：{', '.join(detection['matched_keywords'])}")
        print()

    print(prompt)


if __name__ == "__main__":
    main()
