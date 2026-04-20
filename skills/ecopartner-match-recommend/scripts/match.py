#!/usr/bin/env python3
"""
ecopartner-match-recommend - 中南片区生态伙伴智能匹配脚本

使用方法：
  python3 scripts/match.py "客户想做票据识别，每天5000张"
  python3 scripts/match.py --industry 金融 --tech OCR --city 广州
  python3 scripts/match.py --json '{"industry":"工业","tech":"CV","city":"深圳"}'
"""

import json
import sys
import os
import argparse

# 伙伴数据路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, '..', 'references', 'partner-data.json')


def load_partners():
    """加载中南片区伙伴数据"""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# 行业模糊匹配映射
INDUSTRY_ALIASES = {
    '质检': ['工业', '机械'],
    '检测': ['工业', '机械'],
    '票据': ['金融', '企业服务'],
    '文档': ['金融', '企业服务', '政务'],
    '客服': ['企业服务', '消费服务'],
    '对话': ['企业服务', '消费服务'],
    '教学': ['教育'],
    '培训': ['教育'],
    '政务': ['政务'],
    '办公': ['政务', '企业服务'],
    '医疗': ['医疗'],
    '影像': ['医疗', '工业'],
    '法律': ['法律'],
    '出海': ['法律', '企业服务'],
    '农业': ['农业'],
    '能源': ['能源', '能源电力'],
    '物流': ['物流供应链'],
    '建筑': ['建筑', '建筑建造'],
    '营销': ['营销', '消费服务'],
    '文旅': ['文旅', '文旅文博'],
    '通信': ['电子通信'],
}


def expand_industries(industry):
    """扩展行业关键词，支持模糊匹配"""
    industries = [industry]
    for keyword, aliases in INDUSTRY_ALIASES.items():
        if keyword in industry or industry in keyword:
            industries.extend(aliases)
    return list(set(industries))


def match_partners(partners, industry=None, tech=None, city=None, keyword=None, top_n=5):
    """匹配中南片区伙伴"""
    results = []

    # 扩展行业关键词
    expanded_industries = expand_industries(industry) if industry else []

    for p in partners:
        score = 0
        reasons = []

        # 行业匹配（40分）
        if industry:
            p_industry = p.get('industry', '')
            matched = False
            for ind in expanded_industries:
                if ind and p_industry and (ind in p_industry or p_industry in ind):
                    score += 40
                    reasons.append(f'行业匹配({p_industry})')
                    matched = True
                    break
            # 没匹配上行业不给分

        # 技术匹配（30分）
        if tech:
            p_tech = p.get('tech', '')
            p_product = p.get('product', '')
            p_name = p.get('name', '')
            # 精确匹配技术标签
            if tech in p_tech:
                score += 20
                reasons.append(f'技术匹配({p_tech})')
            # 产品名或企业名包含技术关键词
            combined = p_product + p_name
            tech_keywords = {
                'OCR': ['OCR', '文字识别', '票据', '识别系统'],
                'CV': ['视觉', '图像', '检测', '识别', '质检'],
                'NLP': ['自然语言', '文本', '语义', '知识'],
                '大模型': ['大模型', '文心', 'ERNIE', '对话', '生成'],
                '智能体': ['智能体', 'Agent', '助手', '机器人'],
                'RAG': ['RAG', '检索增强', '知识库'],
            }
            for main_tech, keywords in tech_keywords.items():
                if main_tech == tech or tech in keywords:
                    for kw in keywords:
                        if kw in combined:
                            score += 10
                            reasons.append(f'产品相关({kw})')
                            break
                    break

        # 城市匹配（20分）
        if city:
            p_city = p.get('city', '')
            if city in p_city or p_city in city:
                score += 20
                reasons.append(f'同城({p_city})')

        # 关键词匹配（10分）
        if keyword:
            combined = p.get('product', '') + p.get('name', '') + p.get('industry', '')
            if keyword in combined:
                score += 10
                reasons.append(f'关键词匹配')

        # 无任何匹配条件时，按默认排序
        if not industry and not tech and not city and not keyword:
            score = 50  # 默认分

        if score > 0:
            results.append({
                **p,
                'score': score,
                'reasons': reasons,
            })

    # 按分数降序排列
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]


def format_results(results, industry=None, tech=None, city=None):
    """格式化输出"""
    if not results:
        print('❌ 未找到匹配的华南区伙伴')
        print('💡 建议：放宽匹配条件或尝试全网搜索')
        return

    print('📋 需求概要')
    print(f'├─ 行业：{industry or "待确认"}')
    print(f'├─ 技术：{tech or "待确认"}')
    print(f'└─ 城市：{city or "不限"}')
    print()

    print(f'🤝 推荐华南区伙伴（{len(results)}家）')
    for i, r in enumerate(results):
        stars = '⭐' * min(5, max(1, r['score'] // 20))
        print(f'├─ 【{r["name"]}】{stars}')
        print(f'│   ├─ 产品：{r.get("product", "—")}')
        print(f'│   ├─ 城市：{r.get("city", "—")}')
        print(f'│   ├─ 技术：{r.get("tech", "—")}')
        print(f'│   ├─ 行业：{r.get("industry", "—")}')
        if r.get('reasons'):
            print(f'│   ├─ 匹配理由：{"、".join(r["reasons"])}')
        if r.get('pricing'):
            print(f'│   └─ 定价：{r["pricing"]}')
    print()

    # 推荐方案
    print('🛠 推荐方案')
    if tech:
        tool_map = {
            'OCR': 'PP-OCRv5',
            'CV': 'PaddleDetection / PaddleX',
            'NLP': 'ERNIE SDK',
            '大模型': 'ERNIE Bot / 文心一言',
            '智能体': 'Agent框架 + ERNIE',
        }
        print(f'├─ 推荐工具：{tool_map.get(tech, "PaddleX")}')
    print(f'├─ 部署方式：本地部署 / 云端API（按需选择）')
    print(f'└─ 预估周期：POC 2周，落地 4-6周')


def interactive_mode():
    """交互模式"""
    partners = load_partners()
    print('🎯 中南片区生态伙伴智能匹配')
    print('─' * 40)
    print(f'已加载 {len(partners)} 家生态伙伴数据')
    print()

    while True:
        query = input('请输入客户需求（输入 q 退出）：').strip()
        if query.lower() == 'q':
            break
        if not query:
            continue

        # 简单关键词提取（完整版需 LLM）
        print()
        print(f'🔍 正在匹配：「{query}」')
        print()

        # 尝试从输入中提取关键信息
        industry = None
        tech = None
        city = None

        # 行业提取
        industry_keywords = ['金融', '工业', '医疗', '教育', '政务', '法律', '农业', '能源', '物流',
                           '建筑', '消费', '文旅', '企业服务', '营销', '通信', '电子']
        for kw in industry_keywords:
            if kw in query:
                industry = kw
                break

        # 技术提取
        tech_keywords = ['OCR', 'CV', 'NLP', '大模型', '智能体', 'Agent', 'RAG',
                        '文字识别', '图像识别', '目标检测', '质检', '对话']
        for kw in tech_keywords:
            if kw in query:
                tech = kw
                break

        # 城市提取
        city_keywords = ['厦门', '广州', '深圳', '重庆', '香港', '珠海', '澳门', '长沙', '福州',
                        '东莞', '中山', '四川']
        for kw in city_keywords:
            if kw in query:
                city = kw
                break

        results = match_partners(partners, industry=industry, tech=tech, city=city, keyword=query)
        format_results(results, industry=industry, tech=tech, city=city)
        print()


def main():
    parser = argparse.ArgumentParser(description='中南片区生态伙伴智能匹配')
    parser.add_argument('query', nargs='?', help='需求描述（自然语言）')
    parser.add_argument('--industry', '-i', help='行业（如：金融、工业、医疗）')
    parser.add_argument('--tech', '-t', help='技术需求（如：OCR、CV、NLP、大模型）')
    parser.add_argument('--city', '-c', help='城市偏好（如：厦门、广州、深圳）')
    parser.add_argument('--keyword', '-k', help='关键词搜索')
    parser.add_argument('--top', '-n', type=int, default=5, help='返回数量（默认5）')
    parser.add_argument('--interactive', action='store_true', help='交互模式')
    parser.add_argument('--json', '-j', help='JSON格式输入需求')

    args = parser.parse_args()

    # 交互模式
    if args.interactive:
        interactive_mode()
        return

    # JSON 输入
    if args.json:
        try:
            data = json.loads(args.json)
            args.industry = args.industry or data.get('industry')
            args.tech = args.tech or data.get('tech')
            args.city = args.city or data.get('city')
            args.keyword = args.keyword or data.get('keyword')
        except json.JSONDecodeError:
            print('❌ JSON 格式错误')
            return

    # 自然语言输入
    if args.query and not args.industry and not args.tech:
        args.keyword = args.query

    # 加载数据并匹配
    partners = load_partners()
    results = match_partners(
        partners,
        industry=args.industry,
        tech=args.tech,
        city=args.city,
        keyword=args.keyword,
        top_n=args.top,
    )
    format_results(results, industry=args.industry, tech=args.tech, city=args.city)


if __name__ == '__main__':
    main()
