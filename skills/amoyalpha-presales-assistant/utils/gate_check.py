#!/usr/bin/env python3
"""
程序化质量门禁。
读取 config/gate_rules.yaml，对方案文本执行检查，输出 gate_result.json。
AI 不可口头宣布"通过"，必须以本脚本输出为准。
"""

import sys
import os
import re
import json
import yaml
from pathlib import Path


def load_gate_rules() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "gate_rules.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_placeholders(text: str, patterns: list) -> list:
    found = []
    for pattern in patterns:
        if pattern in text:
            # 找出所有出现位置的上下文（前后20字符）
            idx = 0
            while True:
                pos = text.find(pattern, idx)
                if pos == -1:
                    break
                start = max(0, pos - 20)
                end = min(len(text), pos + len(pattern) + 20)
                found.append({
                    "pattern": pattern,
                    "context": "..." + text[start:end].replace("\n", " ") + "...",
                })
                idx = pos + 1
    return found


def check_suspicious_numbers(text: str) -> list:
    suspicious = []
    patterns = [
        (r"\d+%的[客用企政]", "百分比+群体，可能被编造"),
        (r"超过\d+家[企政单机]", "数量声明，可能被编造"),
        (r"节[省|约|省]\d+[万亿百千]", "节省金额，可能被编造"),
        (r"提[升|高]\d+[倍%]", "提升幅度，可能被编造"),
        (r"降低\d+[%倍]", "降低幅度，可能被编造"),
    ]
    for pattern, reason in patterns:
        matches = re.finditer(pattern, text)
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            context = "..." + text[start:end].replace("\n", " ") + "..."
            # 判断附近是否有来源标注
            nearby = text[max(0, m.start()-100):min(len(text), m.end()+100)]
            has_source = any(w in nearby for w in ["来源", "数据", "报告", "调研", "测算", "实测", "待核实"])
            if not has_source:
                suspicious.append({
                    "match": m.group(0),
                    "reason": reason,
                    "context": context,
                    "suggestion": "添加来源标注或替换为【待核实】占位符",
                })
    return suspicious


def check_competitor_violations(text: str) -> list:
    violations = []
    forbidden = ["比X差", "X不如我们", "有严重问题", "很烂", "垃圾", "坑", "踩雷"]
    competitor_names = ["华为", "阿里", "腾讯", "百度", "微软", "AWS", "OpenAI", "Google"]

    for comp in competitor_names:
        if comp in text:
            for bad in forbidden:
                bad_with_comp = bad.replace("X", comp)
                if bad_with_comp in text:
                    violations.append({
                        "competitor": comp,
                        "violation": bad_with_comp,
                        "suggestion": "使用客观对比表述，只说差异不做价值判断",
                    })
    return violations


def run_gate_check(proposal_text: str) -> dict:
    rules = load_gate_rules()
    result = {
        "passed": False,
        "errors": [],
        "warnings": [],
        "summary": {},
    }

    # 检查1：占位符残留
    placeholder_patterns = rules["gates"]["placeholder_check"]["patterns"]
    placeholders = check_placeholders(proposal_text, placeholder_patterns)
    result["summary"]["placeholders_remaining"] = placeholders
    if placeholders:
        result["warnings"].append({
            "gate": "placeholder_check",
            "count": len(placeholders),
            "items": placeholders,
            "message": f"发现 {len(placeholders)} 处占位符未填写，请在提交前逐一核实补充",
        })

    # 检查2：可疑数字
    suspicious = check_suspicious_numbers(proposal_text)
    result["summary"]["suspicious_numbers"] = suspicious
    if suspicious:
        result["warnings"].append({
            "gate": "fabricated_data_check",
            "count": len(suspicious),
            "items": suspicious,
            "message": f"发现 {len(suspicious)} 处数字缺乏来源标注",
        })

    # 检查3：竞品点名
    violations = check_competitor_violations(proposal_text)
    result["summary"]["competitor_violations"] = violations
    if violations:
        result["errors"].append({
            "gate": "competitor_naming",
            "count": len(violations),
            "items": violations,
            "message": "发现不当竞品评价，需修改为客观对比表述",
        })

    # 判断是否通过
    pass_criteria = rules["pass_criteria"]
    has_errors = len(result["errors"]) > 0
    too_many_warnings = len(result["warnings"]) > pass_criteria.get("max_warnings", 5)

    result["passed"] = not has_errors and not too_many_warnings
    result["verdict"] = "PASS ✅" if result["passed"] else "FAIL ❌"
    result["action_required"] = (
        "方案已通过质量门禁，可以提交。" if result["passed"]
        else f"方案未通过质量门禁：{len(result['errors'])} 个错误，{len(result['warnings'])} 个警告。请修复后重新检查。"
    )

    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python3 gate_check.py <方案文件路径>", file=sys.stderr)
        sys.exit(1)

    proposal_path = sys.argv[1]
    if not os.path.exists(proposal_path):
        print(f"文件不存在: {proposal_path}", file=sys.stderr)
        sys.exit(1)

    with open(proposal_path, "r", encoding="utf-8") as f:
        proposal_text = f.read()

    result = run_gate_check(proposal_text)

    # 输出到同目录的 gate_result.json
    output_dir = os.path.dirname(proposal_path)
    output_path = os.path.join(output_dir, "gate_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 同时打印摘要
    print(f"\n{'='*50}")
    print(f"门禁检查结果: {result['verdict']}")
    print(f"{'='*50}")
    print(result["action_required"])

    if result["errors"]:
        print(f"\n❌ 错误 ({len(result['errors'])} 项):")
        for err in result["errors"]:
            print(f"  • [{err['gate']}] {err['message']}")

    if result["warnings"]:
        print(f"\n⚠️  警告 ({len(result['warnings'])} 项):")
        for warn in result["warnings"]:
            print(f"  • [{warn['gate']}] {warn['message']}")

    if result["summary"].get("placeholders_remaining"):
        print(f"\n📋 待填清单 ({len(result['summary']['placeholders_remaining'])} 处):")
        for item in result["summary"]["placeholders_remaining"]:
            print(f"  • {item['pattern']}: {item['context']}")

    print(f"\n详细结果已保存至: {output_path}")

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
