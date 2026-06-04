#!/usr/bin/env python3
"""
Energy Industry LLM Report Generator
Generates structured reports from collected news items.

Usage:
    python3 generate_report.py --input news.json [--period PERIOD] [--output report.md]
    python3 generate_report.py --template  # Print empty report template

Arguments:
    --input    JSON file with collected news items
    --period   Report period label (e.g., "2024年4月", "2024年Q2")
    --output   Output markdown file (default: stdout)
    --template Print empty report template and exit
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Dimension display names
DIMENSION_NAMES = {
    "data": "数据建设",
    "model": "行业模型",
    "application": "应用落地",
}

# Application sub-categories
APP_SUBCATEGORIES = [
    "智能运维与巡检",
    "电力调度与预测",
    "安全生产",
    "客服与用户服务",
    "知识管理与办公辅助",
    "工程设计",
    "碳管理与绿色发展",
    "市场交易",
    "其他场景",
]

# News item schema:
# {
#   "company": "国家电网",
#   "date": "2024-04-10",
#   "summary": "发布慧眼AI平台2.0",
#   "detail": "详细描述...",
#   "dimension": "model",          # data | model | application
#   "app_category": "智能运维与巡检",  # only if dimension == application
#   "credibility": 3,              # 1-3 stars
#   "source": "来源链接或出处",
# }


def credibility_stars(score):
    """Convert credibility score to star string."""
    return "⭐" * min(max(int(score), 1), 3)


def load_news(input_path):
    """Load news items from JSON file."""
    with open(input_path, encoding="utf-8") as f:
        return json.load(f)


def generate_summary_table(news_items):
    """Generate the company-dimension registry table (Part A)."""
    lines = []
    lines.append("## 二、企业大模型应用动态登记表\n")
    lines.append("| 企业 | 时间 | 事件摘要 | 维度 | 可信度 | 来源 |")
    lines.append("|------|------|---------|------|-------|------|")
    for item in sorted(news_items, key=lambda x: x.get("date", ""), reverse=True):
        dim_label = DIMENSION_NAMES.get(item.get("dimension", ""), item.get("dimension", ""))
        app_cat = item.get("app_category", "")
        dim_full = f"{dim_label}-{app_cat}" if app_cat else dim_label
        stars = credibility_stars(item.get("credibility", 2))
        source = item.get("source", "—")
        lines.append(
            f"| {item.get('company','—')} "
            f"| {item.get('date','—')} "
            f"| {item.get('summary','—')} "
            f"| {dim_full} "
            f"| {stars} "
            f"| {source} |"
        )
    return "\n".join(lines)


def generate_thematic_sections(news_items):
    """Generate Part B: thematic classification sections."""
    lines = []
    lines.append("## 三、主题分类动态\n")

    # Data dimension
    data_items = [i for i in news_items if i.get("dimension") == "data"]
    lines.append("### 3.1 数据建设\n")
    if data_items:
        for item in data_items:
            lines.append(
                f"- **{item.get('company', '—')}**（{item.get('date', '—')}）："
                f"{item.get('detail', item.get('summary', '—'))}。"
                f"来源：{item.get('source', '—')}"
            )
    else:
        lines.append("_本期暂无相关动态。_")
    lines.append("")

    # Model dimension
    model_items = [i for i in news_items if i.get("dimension") == "model"]
    lines.append("### 3.2 行业模型\n")
    if model_items:
        for item in model_items:
            lines.append(
                f"- **{item.get('company', '—')}**（{item.get('date', '—')}）："
                f"{item.get('detail', item.get('summary', '—'))}。"
                f"来源：{item.get('source', '—')}"
            )
    else:
        lines.append("_本期暂无相关动态。_")
    lines.append("")

    # Application dimension - grouped by sub-category
    lines.append("### 3.3 应用落地\n")
    app_items = [i for i in news_items if i.get("dimension") == "application"]
    if app_items:
        for subcat in APP_SUBCATEGORIES:
            cat_items = [i for i in app_items if i.get("app_category") == subcat]
            if not cat_items:
                # Check for uncategorized
                continue
            lines.append(f"#### {subcat}\n")
            for item in cat_items:
                lines.append(
                    f"- **{item.get('company', '—')}**（{item.get('date', '—')}）："
                    f"{item.get('detail', item.get('summary', '—'))}。"
                    f"来源：{item.get('source', '—')}"
                )
            lines.append("")
        # Uncategorized app items
        uncat = [i for i in app_items if not i.get("app_category")]
        if uncat:
            lines.append("#### 其他\n")
            for item in uncat:
                lines.append(
                    f"- **{item.get('company', '—')}**（{item.get('date', '—')}）："
                    f"{item.get('detail', item.get('summary', '—'))}。"
                    f"来源：{item.get('source', '—')}"
                )
    else:
        lines.append("_本期暂无相关动态。_")

    return "\n".join(lines)


def generate_report(news_items, period=None):
    """Generate the full report markdown."""
    period = period or datetime.now().strftime("%Y年%m月")
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(news_items)

    # Top 3 items by credibility for executive summary
    top_items = sorted(news_items, key=lambda x: x.get("credibility", 2), reverse=True)[:3]

    parts = []

    # Header
    parts.append(f"# 能源行业大模型应用动态报告")
    parts.append(f"\n> **报告周期**：{period}")
    parts.append(f"> **调研范围**：电力/电网行业为主，兼顾油气及新能源")
    parts.append(f"> **生成时间**：{today}")
    parts.append(f"> **动态条目**：共 {total} 条\n")
    parts.append("---\n")

    # Section 1: Executive summary
    parts.append("## 一、核心摘要\n")
    for item in top_items:
        parts.append(f"- **{item.get('company', '—')}** — {item.get('summary', '—')}")
    if not top_items:
        parts.append("_（暂无数据，请填充资讯后重新生成）_")
    parts.append("")

    # Section 2: Registry table
    parts.append(generate_summary_table(news_items))
    parts.append("")

    # Section 3: Thematic sections
    parts.append(generate_thematic_sections(news_items))
    parts.append("")

    # Section 4: Trend insights (placeholder)
    parts.append("## 四、趋势洞察\n")
    parts.append("> 根据以上动态，可归纳以下趋势（由 Claude 分析填写）：\n")
    parts.append("### 趋势一：[待分析]")
    parts.append("")
    parts.append("### 趋势二：[待分析]")
    parts.append("")

    # Section 5: Follow-up items
    parts.append("## 五、待跟踪事项\n")
    parts.append("- [ ] 待补充\n")

    return "\n".join(parts)


def print_template():
    """Print an empty news JSON template for manual data entry."""
    template = [
        {
            "company": "国家电网",
            "date": "2024-04-10",
            "summary": "发布慧眼AI平台2.0，新增知识问答能力",
            "detail": "国家电网发布慧眼AI平台2.0版本，集成大模型知识问答、智能运维等核心功能，已在10个省网试点部署。",
            "dimension": "model",
            "app_category": "",
            "credibility": 3,
            "source": "国家电网官网"
        },
        {
            "company": "南方电网",
            "date": "2024-04-05",
            "summary": "完成输电线路无人机AI巡检系统升级",
            "detail": "南方电网完成输电线路无人机AI巡检系统升级，引入视觉大模型缺陷识别，准确率提升至98.5%。",
            "dimension": "application",
            "app_category": "智能运维与巡检",
            "credibility": 2,
            "source": "北极星电力网"
        }
    ]
    print(json.dumps(template, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Energy LLM Report Generator")
    parser.add_argument("--input", help="JSON file with news items")
    parser.add_argument("--period", help="Report period label (e.g., 2024年4月)")
    parser.add_argument("--output", help="Output markdown file (default: stdout)")
    parser.add_argument("--template", action="store_true",
                        help="Print empty news JSON template and exit")

    args = parser.parse_args()

    if args.template:
        print_template()
        return

    if not args.input:
        print("错误：请指定 --input 参数或使用 --template 查看数据格式", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    news_items = load_news(args.input)
    report = generate_report(news_items, args.period)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"报告已生成: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
