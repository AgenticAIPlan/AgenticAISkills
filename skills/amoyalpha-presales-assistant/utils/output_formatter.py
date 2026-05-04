#!/usr/bin/env python3
"""
Markdown / JSON 输出格式化工具。
统一各模块的输出风格，支持写入 outputs/ 目录。
"""

import os
import json
from datetime import date
from pathlib import Path


def get_output_dir(client_name: str) -> Path:
    """获取客户的输出目录，按 {客户名}_{日期} 命名。"""
    base = Path(__file__).parent.parent / "outputs"
    today = date.today().strftime("%Y-%m-%d")
    # 清理非法文件名字符
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in client_name)
    output_dir = base / f"{safe_name}_{today}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_output(content: str, client_name: str, filename: str) -> str:
    """将内容保存到对应客户目录，返回保存路径。"""
    output_dir = get_output_dir(client_name)
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return str(filepath)


def format_section_header(title: str, level: int = 2) -> str:
    prefix = "#" * level
    return f"\n{prefix} {title}\n"


def format_info_gap_list(gaps: list) -> str:
    """格式化信息缺口清单。"""
    if not gaps:
        return "\n> ✅ 信息收集完整，无明显缺口。\n"
    lines = ["\n> ⚠️ **以下信息尚不明确，建议在首次接触中确认：**\n"]
    for i, gap in enumerate(gaps, 1):
        lines.append(f"> {i}. {gap}")
    return "\n".join(lines) + "\n"


def format_placeholder_list(placeholders: list) -> str:
    """格式化待填清单。"""
    if not placeholders:
        return ""
    lines = ["\n---\n\n## 📋 待填清单（提交前必须逐项核实）\n"]
    for item in placeholders:
        lines.append(f"- [ ] **{item['pattern']}** — {item['context']}")
    return "\n".join(lines)


def format_objection_card(objection: dict) -> str:
    """格式化单条异议应对卡片。"""
    return f"""
### {objection.get('id', '')} — 触发词：{', '.join(objection.get('trigger_keywords', [])[:3])}

**背后顾虑：** {objection.get('underlying_concern', '')}

**第一层（共情）：** {objection.get('response_layer_1', '')}

**第二层（重框架）：** {objection.get('response_layer_2', '')}

**第三层（证据）：** {objection.get('response_layer_3', '')}

> ❌ **红线（绝对不说）：** {' / '.join(objection.get('red_lines', []))}
"""


def format_score_card(score: int, items: list) -> str:
    """格式化 Close Readiness 评分卡。"""
    verdict = (
        "🟢 **可以推进报价/投标**" if score >= 7
        else "🟡 **建议继续需求深化**" if score >= 4
        else "🔴 **建议重新鉴定商机**"
    )
    lines = [f"\n## 商机推进评分：{score}/8 — {verdict}\n"]
    for item in items:
        status = "✅" if item["passed"] else "❌"
        lines.append(f"- {status} {item['name']}: {item['note']}")
    return "\n".join(lines)
