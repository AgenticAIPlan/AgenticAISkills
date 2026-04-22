#!/usr/bin/env python3
"""
Knowledge Coverage Scorer for Project Handover Skill

Analyzes collected materials against a question checklist and generates
a coverage report across 6 handover dimensions.

!!! Accuracy Disclaimer !!!
This tool uses KEYWORD-BASED matching to estimate coverage. It is designed
as a FAST PRE-SCREENING tool, NOT a precise assessment. Limitations:
- Cannot understand semantic meaning (a document with many "流程" keywords
  but irrelevant content will be over-scored)
- Thresholds are heuristic, not calibrated against real data
- Score should be treated as a LOWER BOUND, not exact coverage

For accurate assessment, use LLM-based evaluation or manual review.

Usage:
    python3 knowledge_coverage_scorer.py --questions <questions_file> --materials <materials_dir> [--output <output_file>]
    python3 knowledge_coverage_scorer.py --questions <questions_file> --materials <materials_dir> --json
    python3 knowledge_coverage_scorer.py --interactive  # Run interactively without files

Options:
    --questions    Path to the question checklist (markdown or plain text)
    --materials    Path to directory containing collected materials
    --output       Path to write the coverage report (default: stdout)
    --json         Output as JSON instead of markdown
    --interactive  Run in interactive mode (answer questions one by one)
    --depth        Research depth: quick / standard / deep (default: standard)
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class CoverageStatus(Enum):
    COVERED = "covered"           # Material contains clear answer
    PARTIAL = "partial"           # Some relevant info, but incomplete
    NOT_COVERED = "not_covered"   # No relevant information found
    NEEDS_ORAL = "needs_oral"     # Only obtainable through handover person's oral input


@dataclass
class Question:
    dimension: str
    number: str       # e.g. "1.1"
    text: str
    status: CoverageStatus = CoverageStatus.NOT_COVERED
    source: str = ""
    note: str = ""


@dataclass
class DimensionResult:
    name: str
    questions: list = field(default_factory=list)
    covered: int = 0
    partial: int = 0
    not_covered: int = 0
    needs_oral: int = 0

    @property
    def coverage_rate(self) -> float:
        answerable = self.covered + self.partial + self.not_covered
        if answerable == 0:
            return 0.0
        return (self.covered * 1.0 + self.partial * 0.5) / answerable * 100


DIMENSION_NAMES = {
    "1": "业务流程",
    "2": "项目与待办",
    "3": "联系人",
    "4": "隐性知识与决策",
    "5": "模板与资产",
    "6": "风险与异常",
}

# Keywords for each dimension to detect relevant content
DIMENSION_KEYWORDS = {
    "1": ["流程", "步骤", "操作", "SOP", "每天", "每周", "每月", "工具", "系统", "登录",
           "process", "step", "workflow", "routine", "daily", "weekly", "monthly",
           "操作手册", "使用指南", "教程"],
    "2": ["项目", "待办", "进度", "计划", "截止", "里程碑", "任务", "进行中",
           "project", "todo", "task", "deadline", "milestone", "progress", "plan"],
    "3": ["联系", "对接", "团队", "部门", "合作", "群", "权限", "账号",
           "contact", "team", "partner", "stakeholder", "permission", "group"],
    "4": ["为什么", "原因", "决策", "经验", "教训", "踩坑", "建议", "判断",
           "规则", "背景", "历史", "know-how", "decision", "lesson", "best practice"],
    "5": ["模板", "话术", "资产", "脚本", "工具", "数据表", "知识库",
           "template", "script", "asset", "reusable", "boilerplate"],
    "6": ["风险", "异常", "故障", "问题", "隐患", "应急", "单点", "依赖",
           "risk", "issue", "bug", "failure", "incident", "emergency", "downtime"],
}


def parse_questions(filepath: str) -> list:
    """Parse a question checklist file into Question objects."""
    questions = []
    current_dimension = ""

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Detect dimension headers (e.g., "### 维度1：业务流程" or "## 1. 业务流程")
            dim_match = re.match(r"#+\s*(?:维度\s*)?(\d+)[\.\：:]", line)
            if dim_match:
                dim_num = dim_match.group(1)
                current_dimension = DIMENSION_NAMES.get(dim_num, f"维度{dim_num}")
                continue

            # Detect questions (e.g., "- [ ] Q1.1: xxx" or "- Q1.1: xxx")
            q_match = re.match(r"[-*]\s*(?:\[[ x]\]\s*)?(?:Q)?(\d+)\.(\d+)\s*[:：]?\s*(.+)", line)
            if q_match:
                dim_num = q_match.group(1)
                sub_num = q_match.group(2)
                text = q_match.group(3).strip()
                dim_name = DIMENSION_NAMES.get(dim_num, current_dimension or f"维度{dim_num}")
                questions.append(Question(
                    dimension=dim_name,
                    number=f"{dim_num}.{sub_num}",
                    text=text,
                ))

    return questions


def score_question(question: Question, materials_dir: str) -> Question:
    """Score a single question against collected materials.

    Uses a two-factor scoring model:
    - dimension_score: how well the material matches the dimension topic (0-100)
    - question_score: how well the material matches the specific question (0-100)
    - Combined: requires BOTH factors to be above threshold for COVERED.

    This prevents a document with many generic dimension keywords (e.g. "流程",
    "步骤") from being marked as COVERED when it doesn't address the specific question.
    """
    if not os.path.isdir(materials_dir):
        return question

    dim_num = "1"
    for num, name in DIMENSION_NAMES.items():
        if name == question.dimension:
            dim_num = num
            break

    dim_keywords = DIMENSION_KEYWORDS.get(dim_num, [])
    question_keywords = extract_keywords(question.text)

    material_files = []
    for ext in ("*.md", "*.txt", "*.json", "*.yaml", "*.yml"):
        material_files.extend(Path(materials_dir).rglob(ext))

    best_dim_score = 0
    best_question_score = 0
    best_source = ""

    for material_path in material_files:
        try:
            content = material_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Factor 1: dimension keyword match (breadth check)
        dim_hits = sum(1 for kw in dim_keywords if kw.lower() in content.lower())
        dim_score = min(dim_hits / max(len(dim_keywords), 1) * 100, 100)

        # Factor 2: question-specific keyword match (depth check)
        q_hits = 0
        for kw in question_keywords:
            count = content.lower().count(kw.lower())
            if count > 0:
                q_hits += 1
                q_hits += (count - 1) * 0.5  # Bonus for repeated mentions
        question_score = min(q_hits / max(len(question_keywords), 1) * 100, 100)

        # Combined: use harmonic mean to require BOTH factors
        # This prevents high dim_score + low question_score from inflating result
        if dim_score + question_score > 0:
            combined = 2 * dim_score * question_score / (dim_score + question_score)
        else:
            combined = 0

        if combined > (best_dim_score + best_question_score):
            best_dim_score = dim_score
            best_question_score = question_score
            best_source = material_path.name

    # Map combined score to coverage status
    # Thresholds calibrated for harmonic mean (range 0-100):
    #   COVERED:     both factors strong (combined >= 45)
    #   PARTIAL:     at least one factor moderate (combined >= 15)
    #   NOT_COVERED: weak or no match (combined < 15)
    combined = 2 * best_dim_score * best_question_score / max(best_dim_score + best_question_score, 1)

    if combined >= 45 and best_question_score >= 30:
        question.status = CoverageStatus.COVERED
    elif combined >= 15 or best_question_score >= 20:
        question.status = CoverageStatus.PARTIAL
    else:
        question.status = CoverageStatus.NOT_COVERED

    question.source = best_source if combined > 0 else ""
    question.note = f"dim={best_dim_score:.0f}% q={best_question_score:.0f}%"
    return question


def extract_keywords(text: str) -> list:
    """Extract meaningful keywords from a question text."""
    # Remove common stop words
    stop_words = {"的", "了", "是", "在", "有", "和", "与", "或", "不", "也",
                  "都", "要", "会", "能", "把", "被", "让", "给", "对", "等",
                  "the", "a", "an", "is", "are", "was", "were", "be", "been",
                  "to", "of", "in", "for", "on", "with", "at", "by", "from",
                  "what", "how", "which", "who", "when", "where", "why",
                  "吗", "呢", "什么", "怎么", "哪些", "如何", "有没有"}
    # Extract meaningful words (2+ chars for Chinese, 3+ for English)
    words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', text)
    return [w for w in words if w.lower() not in stop_words]


def calculate_results(questions: list) -> dict:
    """Calculate coverage results grouped by dimension."""
    results = {}
    for q in questions:
        dim = q.dimension
        if dim not in results:
            results[dim] = DimensionResult(name=dim)
        results[dim].questions.append(q)

        if q.status == CoverageStatus.COVERED:
            results[dim].covered += 1
        elif q.status == CoverageStatus.PARTIAL:
            results[dim].partial += 1
        elif q.status == CoverageStatus.NEEDS_ORAL:
            results[dim].needs_oral += 1
        else:
            results[dim].not_covered += 1

    return results


def generate_markdown_report(questions: list, results: dict, depth: str = "standard") -> str:
    """Generate a markdown coverage report."""
    lines = [
        "# 知识覆盖度报告\n",
    ]

    # Overview table
    total_covered = sum(r.covered for r in results.values())
    total_partial = sum(r.partial for r in results.values())
    total_not_covered = sum(r.not_covered for r in results.values())
    total_needs_oral = sum(r.needs_oral for r in results.values())
    total_questions = sum(len(r.questions) for r in results.values())

    total_answerable = total_covered + total_partial + total_not_covered
    total_rate = (total_covered * 1.0 + total_partial * 0.5) / total_answerable * 100 if total_answerable > 0 else 0

    # Dimension order
    dim_order = ["业务流程", "项目与待办", "联系人", "隐性知识与决策", "模板与资产", "风险与异常"]

    lines.append("## 1. 覆盖度总览\n")
    lines.append("| 维度 | 问题总数 | ✅ 已覆盖 | ⚠️ 部分覆盖 | ❌ 未覆盖 | 🔍 需口述补充 | 覆盖率 |")
    lines.append("|------|---------|----------|------------|----------|-------------|--------|")

    for dim_name in dim_order:
        if dim_name in results:
            r = results[dim_name]
            lines.append(
                f"| {dim_name} | {len(r.questions)} | {r.covered} | {r.partial} "
                f"| {r.not_covered} | {r.needs_oral} | {r.coverage_rate:.0f}% |"
            )

    lines.append(f"| **总计** | **{total_questions}** | **{total_covered}** | **{total_partial}** "
                 f"| **{total_not_covered}** | **{total_needs_oral}** | **{total_rate:.0f}%** |")
    lines.append("")

    # Grade
    if total_rate >= 80:
        grade = "✅ 优秀（≥ 80%）—— 可直接输出正式交接手册"
    elif total_rate >= 60:
        grade = "✅ 达标（60%-79%）—— 可输出手册，建议补充后更新"
    elif total_rate >= 40:
        grade = "⚠️ 不足（40%-59%）—— 需补充材料后重新评估"
    else:
        grade = "❌ 严重不足（< 40%）—— 建议重新规划交接方案"

    lines.append(f"**覆盖度等级**：{grade}\n")

    # Per-dimension detail
    lines.append("## 2. 各维度详情\n")
    for dim_name in dim_order:
        if dim_name in results:
            r = results[dim_name]
            lines.append(f"### {dim_name}（覆盖率 {r.coverage_rate:.0f}%）\n")
            lines.append("| # | 问题 | 状态 | 来源 | 备注 |")
            lines.append("|---|------|------|------|------|")
            for q in r.questions:
                status_map = {
                    CoverageStatus.COVERED: "✅ 已覆盖",
                    CoverageStatus.PARTIAL: "⚠️ 部分覆盖",
                    CoverageStatus.NOT_COVERED: "❌ 未覆盖",
                    CoverageStatus.NEEDS_ORAL: "🔍 需口述补充",
                }
                lines.append(
                    f"| Q{q.number} | {q.text} | {status_map[q.status]} | {q.source} | {q.note} |"
                )
            lines.append("")

    # Gaps
    gaps = [q for q in questions if q.status in (CoverageStatus.NOT_COVERED, CoverageStatus.NEEDS_ORAL)]
    if gaps:
        lines.append("## 3. 信息缺口\n")
        lines.append("| 维度 | 问题编号 | 问题内容 | 状态 |")
        lines.append("|------|---------|---------|------|")
        for q in gaps:
            status = "需口述补充" if q.status == CoverageStatus.NEEDS_ORAL else "未覆盖"
            lines.append(f"| {q.dimension} | Q{q.number} | {q.text} | {status} |")
        lines.append("")

    return "\n".join(lines)


def generate_json_report(questions: list, results: dict) -> str:
    """Generate a JSON coverage report."""
    total_covered = sum(r.covered for r in results.values())
    total_partial = sum(r.partial for r in results.values())
    total_not_covered = sum(r.not_covered for r in results.values())
    total_answerable = total_covered + total_partial + total_not_covered
    total_rate = (total_covered * 1.0 + total_partial * 0.5) / total_answerable * 100 if total_answerable > 0 else 0

    report = {
        "overall_coverage": round(total_rate, 1),
        "grade": "excellent" if total_rate >= 80 else "pass" if total_rate >= 60 else "insufficient",
        "dimensions": {},
        "gaps": [],
    }

    for dim_name, r in results.items():
        report["dimensions"][dim_name] = {
            "coverage_rate": round(r.coverage_rate, 1),
            "covered": r.covered,
            "partial": r.partial,
            "not_covered": r.not_covered,
            "needs_oral": r.needs_oral,
            "total_questions": len(r.questions),
            "questions": [
                {
                    "number": q.number,
                    "text": q.text,
                    "status": q.status.value,
                    "source": q.source,
                }
                for q in r.questions
            ],
        }
        for q in r.questions:
            if q.status in (CoverageStatus.NOT_COVERED, CoverageStatus.NEEDS_ORAL):
                report["gaps"].append({
                    "dimension": dim_name,
                    "number": q.number,
                    "text": q.text,
                    "status": q.status.value,
                })

    return json.dumps(report, ensure_ascii=False, indent=2)


def run_interactive():
    """Run in interactive mode - ask user to answer each question."""
    print("=== 项目交接知识覆盖度评估（交互模式）===\n")

    depth = input("调研深度（quick/standard/deep，默认 standard）: ").strip().lower() or "standard"
    questions_per_dim = {"quick": 3, "standard": 5, "deep": 7}.get(depth, 5)

    questions = []
    for dim_num in sorted(DIMENSION_NAMES.keys()):
        dim_name = DIMENSION_NAMES[dim_num]
        print(f"\n--- {dim_name} ---")

        count = 0
        while count < questions_per_dim:
            q_text = input(f"  问题 {dim_num}.{count + 1}（直接回车结束此维度）: ").strip()
            if not q_text:
                break
            questions.append(Question(
                dimension=dim_name,
                number=f"{dim_num}.{count + 1}",
                text=q_text,
            ))
            count += 1

    if not questions:
        print("未输入任何问题，退出。")
        return

    # Now ask coverage status for each question
    print("\n\n=== 评估覆盖状态 ===\n")
    status_options = {
        "1": CoverageStatus.COVERED,
        "2": CoverageStatus.PARTIAL,
        "3": CoverageStatus.NOT_COVERED,
        "4": CoverageStatus.NEEDS_ORAL,
    }
    status_labels = "1=✅已覆盖 2=⚠️部分覆盖 3=❌未覆盖 4=🔍需口述补充"

    for q in questions:
        while True:
            status_input = input(f"[{q.dimension}] Q{q.number}: {q.text}\n  状态? ({status_labels}): ").strip()
            if status_input in status_options:
                q.status = status_options[status_input]
                break
            if status_input == "":
                q.status = CoverageStatus.NOT_COVERED
                break
            print("  无效输入，请输入 1-4")

    results = calculate_results(questions)
    report = generate_markdown_report(questions, results, depth)
    print("\n" + "=" * 50)
    print(report)


def main():
    parser = argparse.ArgumentParser(description="Knowledge Coverage Scorer for Project Handover")
    parser.add_argument("--questions", help="Path to question checklist file")
    parser.add_argument("--materials", help="Path to materials directory")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--interactive", action="store_true", help="Run interactively")
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard",
                        help="Research depth (default: standard)")

    args = parser.parse_args()

    if args.interactive:
        run_interactive()
        return

    if not args.questions:
        parser.error("--questions is required (or use --interactive)")

    if not os.path.isfile(args.questions):
        print(f"Error: Questions file not found: {args.questions}", file=sys.stderr)
        sys.exit(1)

    questions = parse_questions(args.questions)

    if not questions:
        print("Error: No questions found in the file.", file=sys.stderr)
        print("Expected format: '- Q1.1: question text' under dimension headers.", file=sys.stderr)
        sys.exit(1)

    # Score questions against materials
    if args.materials and os.path.isdir(args.materials):
        for i, q in enumerate(questions):
            questions[i] = score_question(q, args.materials)
            print(f"  Q{q.number}: {q.status.value} ({q.source})", file=sys.stderr)

    results = calculate_results(questions)

    if args.json:
        report = generate_json_report(questions, results)
    else:
        report = generate_markdown_report(questions, results, args.depth)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
