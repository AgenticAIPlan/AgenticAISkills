#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


MARKER = "<!-- skill-pr-ai-eval -->"
DIMENSION_ORDER = [
    "trigger_clarity",
    "input_contract",
    "execution_quality",
    "output_contract",
    "boundary_definition",
    "reference_support",
    "repository_fit",
]
DIMENSION_LABELS = {
    "trigger_clarity": "触发条件清晰度",
    "input_contract": "输入约定清晰度",
    "execution_quality": "执行步骤可操作性",
    "output_contract": "输出约定可检验性",
    "boundary_definition": "边界定义清晰度",
    "reference_support": "参考资料支撑度",
    "repository_fit": "仓库收录适配度",
}


def parse_review(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Review result file is empty.")
    return json.loads(text)


def score_badge(score: int) -> str:
    if score >= 90:
        return "强"
    if score >= 75:
        return "中"
    if score >= 60:
        return "弱"
    return "低"


def decision_label(decision: str) -> str:
    return {
        "approve": "建议通过",
        "needs-work": "建议修改后再看",
        "not-ready": "暂不建议合并",
    }.get(decision, decision)


def bullet_block(items: List[str], empty_text: str) -> List[str]:
    if not items:
        return [f"- {empty_text}"]
    return [f"- {item}" for item in items]


def render_scope(review_scope: Dict[str, Any]) -> List[str]:
    included = review_scope.get("included_files", []) or []
    skipped = review_scope.get("skipped_files", []) or []
    notes = review_scope.get("notes", []) or []

    lines: List[str] = []
    lines.append(f"- 已纳入审阅文件数: `{len(included)}`")
    if included:
        preview = ", ".join(
            f"`{item.get('path', '')}`" for item in included[:6] if item.get("path")
        )
        if len(included) > 6:
            preview += " ..."
        lines.append(f"- 代表文件: {preview}")

    lines.append(f"- 跳过文件数: `{len(skipped)}`")
    if skipped:
        preview = ", ".join(
            f"`{item.get('path', '')}`" for item in skipped[:6] if item.get("path")
        )
        if len(skipped) > 6:
            preview += " ..."
        lines.append(f"- 跳过示例: {preview}")

    lines.extend(
        bullet_block(
            [str(note).strip() for note in notes if str(note).strip()],
            "本次仅做静态文本审阅，未执行 Skill 附带脚本或外部依赖。",
        )
    )
    return lines


def render_comment(review: Dict[str, Any], skill_slug: str, model: str, pr_number: str) -> str:
    overall_score = int(review.get("overall_score", 0) or 0)
    lines: List[str] = [MARKER, "## Skill PR AI Review", ""]
    lines.append(f"- PR: #{pr_number}")
    lines.append(f"- Skill: `{skill_slug}`")
    lines.append(f"- 评审模型: `{model}`")
    lines.append(
        f"- 评审时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    lines.append(
        f"- 结论: **{decision_label(str(review.get('decision', 'unknown')))}** "
        f"（总分 `{overall_score}` / 100，强度 `{score_badge(overall_score)}`）"
    )
    lines.append("")
    lines.append("### 摘要")
    lines.append("")
    lines.append(str(review.get("summary", "")).strip() or "无摘要。")
    lines.append("")
    lines.append("### 评审范围")
    lines.append("")
    lines.extend(render_scope(review.get("review_scope", {}) or {}))
    lines.append("")
    lines.append("### 维度评分")
    lines.append("")
    lines.append("| 维度 | 分数 | 说明 |")
    lines.append("| --- | --- | --- |")

    dimensions = review.get("dimensions", {}) or {}
    for key in DIMENSION_ORDER:
        detail = dimensions.get(key, {}) or {}
        score = detail.get("score", "N/A")
        reason = str(detail.get("reason", "")).strip() or "无说明。"
        label = DIMENSION_LABELS.get(key, key)
        lines.append(f"| {label} | {score}/5 | {reason} |")

    routing = review.get("routing_assessment", {}) or {}
    lines.append("")
    lines.append("### 路由与边界判断")
    lines.append("")
    lines.append(
        f"- 区分度评分: `{routing.get('distinctiveness_score', 'N/A')}` / 5"
    )
    lines.append(
        f"- 判断说明: {str(routing.get('reason', '')).strip() or '无说明。'}"
    )
    lines.extend(
        bullet_block(
            list(routing.get("likely_conflicts", []) or []),
            "未发现明显的高风险冲突技能。",
        )
    )

    lines.append("")
    lines.append("### 阻塞问题")
    lines.append("")
    lines.extend(
        bullet_block(
            list(review.get("blocking_issues", []) or []),
            "当前未发现明确的阻塞问题。",
        )
    )

    lines.append("")
    lines.append("### 建议优化")
    lines.append("")
    lines.extend(
        bullet_block(
            list(review.get("non_blocking_suggestions", []) or []),
            "当前没有额外的非阻塞建议。",
        )
    )

    lines.append("")
    lines.append(
        "_该评论由维护者手动触发的 GitHub Action 生成，用于辅助 Skill PR 审阅，不直接替代人工判断。_"
    )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--skill-slug", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--pull-request-number", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    review = parse_review(Path(args.input))
    comment = render_comment(review, args.skill_slug, args.model, args.pull_request_number)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(comment, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
