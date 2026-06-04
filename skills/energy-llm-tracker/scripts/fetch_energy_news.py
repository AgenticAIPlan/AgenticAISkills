#!/usr/bin/env python3
"""
Energy Industry LLM News Fetcher
Aggregates news about large model (LLM) applications in the energy sector.

Usage:
    python3 fetch_energy_news.py [--company COMPANY] [--dimension DIMENSION] [--days DAYS] [--output OUTPUT]

Arguments:
    --company     Filter by company name (e.g., "国家电网", "南方电网")
    --dimension   Filter by dimension: data|model|application (default: all)
    --days        Number of days to look back (default: 7)
    --output      Output file path (default: stdout)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


# ============================================================
# Search query templates for energy LLM research
# ============================================================

# Base search queries by dimension
SEARCH_QUERIES = {
    "data": [
        "电力行业 数据中台 大模型",
        "能源企业 知识图谱 知识库建设",
        "电力 工业数据集 人工智能",
        "能源 数据治理 AI",
        "电网 数字孪生 数据建设",
    ],
    "model": [
        "电力大模型 发布",
        "能源行业 垂直大模型",
        "国家电网 人工智能 模型",
        "南方电网 大模型",
        "电力 LLM 行业模型",
        "华为盘古 能源大模型",
        "能源 预训练模型 微调",
    ],
    "application": [
        "电力 智能巡检 大模型",
        "电力调度 AI 负荷预测",
        "电网 安全生产 人工智能",
        "电力 智能客服 数字员工",
        "能源企业 知识问答 大模型",
        "电力工程 辅助设计 AI",
        "碳管理 大模型 能源",
        "电力市场 AI 交易辅助",
    ],
}

# Key companies to track
KEY_COMPANIES = [
    "国家电网", "南方电网",
    "华能集团", "大唐集团", "华电集团", "国家能源集团",
    "中国电建", "中国能建",
    "国电南瑞", "远光软件", "东方电子", "许继电气",
    "阳光电源", "远景能源", "金风科技",
    "协鑫能科", "宁德时代",
]

# Dimension labels
DIMENSION_LABELS = {
    "data": "数据建设",
    "model": "行业模型",
    "application": "应用落地",
}


def build_search_queries(company=None, dimension=None, days=7):
    """Build search query list based on filters."""
    queries = []

    # Select dimensions to search
    dims = [dimension] if dimension and dimension in SEARCH_QUERIES else list(SEARCH_QUERIES.keys())

    for dim in dims:
        for base_query in SEARCH_QUERIES[dim]:
            if company:
                queries.append(f"{company} {base_query}")
            else:
                queries.append(base_query)

    # Add company-specific queries if specified
    if company:
        queries.append(f"{company} 大模型 {datetime.now().year}")
        queries.append(f"{company} 人工智能 应用")

    return queries


def format_search_instructions(company=None, dimension=None, days=7):
    """
    Generate structured search instructions for Claude to execute.
    Returns a markdown-formatted guide for the search workflow.
    """
    queries = build_search_queries(company, dimension, days)
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    output = []
    output.append("# 能源行业大模型资讯搜索指引")
    output.append(f"\n**搜索时间范围**: {date_from} 至今 ({days}天)")
    if company:
        output.append(f"**聚焦企业**: {company}")
    if dimension:
        output.append(f"**聚焦维度**: {DIMENSION_LABELS.get(dimension, dimension)}")
    output.append(f"\n**共 {len(queries)} 条搜索查询**\n")

    # Group by dimension
    dims = [dimension] if dimension and dimension in SEARCH_QUERIES else list(SEARCH_QUERIES.keys())
    for dim in dims:
        output.append(f"## {DIMENSION_LABELS[dim]}相关搜索")
        for q in SEARCH_QUERIES[dim]:
            final_q = f"{company} {q}" if company else q
            output.append(f"- `{final_q}`")
        output.append("")

    # Add recommended sources
    output.append("## 推荐信息来源")
    output.append("- 北极星电力网 (bjx.com.cn)")
    output.append("- 中国电力新闻网 (cpnn.com.cn)")
    output.append("- 国家能源局官网 (nea.gov.cn)")
    output.append("- 各企业官网新闻中心")
    output.append("- 中电联发布报告 (cec.org.cn)")
    output.append("")

    # Add key companies to check
    if not company:
        output.append("## 重点企业逐一检索")
        for c in KEY_COMPANIES:
            output.append(f"- [ ] {c}")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Energy LLM News Fetcher - Search Query Generator")
    parser.add_argument("--company", help="Filter by company name")
    parser.add_argument("--dimension", choices=["data", "model", "application"],
                        help="Filter by research dimension")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")

    args = parser.parse_args()

    if args.format == "json":
        result = {
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "company": args.company,
                "dimension": args.dimension,
                "days": args.days,
            },
            "queries": build_search_queries(args.company, args.dimension, args.days),
            "key_companies": KEY_COMPANIES,
            "dimensions": DIMENSION_LABELS,
        }
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_search_instructions(args.company, args.dimension, args.days)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"搜索指引已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
