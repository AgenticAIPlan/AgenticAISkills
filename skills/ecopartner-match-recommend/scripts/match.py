#!/usr/bin/env python3
"""
ecopartner-match-recommend - 中南片区生态伙伴智能匹配脚本

使用方法：
  python3 scripts/match.py --industry 金融 --tech OCR --city 广州
  python3 scripts/match.py --tech CV --top 10
  python3 scripts/match.py --json '{"industry":"工业","tech":"CV","city":"深圳"}'
  python3 scripts/match.py --industry 教育 --tech NLP --output report.html
"""

import json
import sys
import os
import argparse
from datetime import datetime

# 伙伴数据路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, '..', 'references', 'partner-data.json')
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, '..', 'references', 'report-template.html')


def load_partners():
    """加载中南片区伙伴数据"""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_template():
    """加载 HTML 报告模板"""
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


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
    """匹配中南片区伙伴 - 基于 ai_tags 主匹配逻辑"""
    results = []

    # 扩展行业关键词
    expanded_industries = expand_industries(industry) if industry else []

    for p in partners:
        score = 0
        reasons = []

        # === AI能力标签匹配（最高优先级，40分）===
        # 核心匹配逻辑：用户指定的 tech 必须出现在伙伴的 ai_tags 数组中
        if tech:
            p_ai_tags = p.get('ai_tags', [])
            if isinstance(p_ai_tags, list) and tech in p_ai_tags:
                score += 40
                reasons.append(f'AI能力匹配({tech})')
                # 同时检查产品介绍中的关键词作为加分
                p_intro = p.get('product_intro', '')
                tech_intro_keywords = {
                    'OCR': ['OCR', '文字识别', '票据', '表单', '手写'],
                    'CV': ['视觉', '图像', '检测', '缺陷', '质检', '分割'],
                    'NLP': ['自然语言', '文本', '语义', '审核', '抽取'],
                    'LLM': ['大模型', '对话', '生成', '文心', 'ERNIE'],
                    '时序': ['预测', '时序', '风控', '流量'],
                    '语音': ['语音', 'ASR', 'TTS', '合成'],
                }
                if tech in tech_intro_keywords:
                    for kw in tech_intro_keywords[tech]:
                        if kw in p_intro:
                            score += 5
                            reasons.append(f'产品介绍提及({kw})')
                            break

        # === 行业匹配（30分）===
        if industry:
            p_industry = p.get('industry1', '')
            for ind in expanded_industries:
                if ind and p_industry and (ind in p_industry or p_industry in ind):
                    score += 30
                    reasons.append(f'行业匹配({p_industry})')
                    break

        # === 城市匹配（20分）===
        if city:
            p_city = p.get('city', '')
            if city in p_city or p_city in city:
                score += 20
                reasons.append(f'同城({p_city})')

        # === 关键词匹配（10分）===
        if keyword:
            combined = p.get('product', '') + p.get('company', '') + p.get('industry1', '')
            if keyword in combined:
                score += 10
                reasons.append(f'关键词匹配')

        # 无任何匹配条件时，给默认分
        if not industry and not tech and not city and not keyword:
            score = 50

        if score > 0:
            results.append({
                **p,
                'score': score,
                'reasons': reasons,
            })

    # 按分数降序排列
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]


def get_star_rating(score):
    """根据分数返回星级"""
    if score >= 80:
        return 'sr'  # strongly recommend
    elif score >= 60:
        return 'r'   # recommend
    else:
        return 'b'   # backup


def get_tier_html(tier_name, tier_results, tier_class):
    """生成单个层级的 HTML"""
    tier_names = {'sr': '⭐⭐⭐⭐ 强烈推荐', 'r': '⭐⭐⭐ 推荐', 'b': '⭐⭐ 备选'}
    tier_name_zh = tier_names.get(tier_class, tier_name)

    if not tier_results:
        return ''

    cards_html = ''
    for r in tier_results:
        ai_tags_html = ''.join([f'<span class="tag">{tag}</span>' for tag in r.get('ai_tags', []) if tag])

        reasons_html = '、'.join(r.get('reasons', []))

        cards_html += f'''
        <div class="partner-card">
          <div class="partner-name">{r.get('company', '—')}</div>
          <div class="partner-product">{r.get('product', '—')}</div>
          <div class="partner-meta">
            <span class="meta-tag">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
              {r.get('city', '—')}
            </span>
            <span class="meta-tag">{r.get('tech', '—')}</span>
            <span class="meta-tag">{r.get('industry1', '—')}</span>
          </div>
          {ai_tags_html}
          <div class="partner-reason" style="margin-top:12px;">{reasons_html}</div>
        </div>'''

    return f'''
    <div class="tier">
      <div class="tier-header">
        <span class="tier-badge {tier_class}">{tier_name_zh}（{len(tier_results)}家）</span>
      </div>
      <div class="partner-list">
        {cards_html}
      </div>
    </div>'''


def generate_html_report(results, industry, tech, city, output_path=None):
    """生成 HTML 报告"""
    template = load_template()

    # 统计信息
    ai_tags_set = set()
    city_set = set()
    for r in results:
        for tag in r.get('ai_tags', []):
            if tag:
                ai_tags_set.add(tag)
        if r.get('city'):
            city_set.add(r.get('city'))

    # 分层
    tier_sr = [r for r in results if r['score'] >= 80]
    tier_r = [r for r in results if 60 <= r['score'] < 80]
    tier_b = [r for r in results if r['score'] < 60]

    # 替换模板变量
    subs = {
        '{DATE}': datetime.now().strftime('%Y年%m月%d日'),
        '{TITLE}': '中南片区生态伙伴匹配报告',
        '{SUBTITLE}': f'{industry or "待定行业"} · {tech or "待定技术"} · {city or "不限城市"}',
        '{PARTNER_COUNT}': str(len(results)),
        '{AI_TAGS_COUNT}': str(len(ai_tags_set)),
        '{CITY_COUNT}': str(len(city_set)),
        '{CUSTOMER_SCENE}': industry or '待确认',
        '{AI_CAPABILITIES}': tech or '待确认',
        '{RECOMMENDED_TECH}': tech or '待确认',
        '{IMPLEMENTATION}': '生态伙伴对接',
        '{TIER_SR}': get_tier_html('强烈推荐', tier_sr, 'sr'),
        '{TIER_R}': get_tier_html('推荐', tier_r, 'r'),
        '{TIER_B}': get_tier_html('备选', tier_b, 'b'),
        '{NOTES}': '<div class="note-item"><span class="note-icon">⚠️</span>建议与推荐供应商深入沟通技术方案细节</div><div class="note-item"><span class="note-icon">💡</span>可根据预算选择本地部署或云端 API 方案</div>',
        '{QUESTIONS}': '<div class="question-card">您的预算范围是多少？<span class="question-hint">影响供应商选择</span></div><div class="question-card">数据规模预计多大？<span class="question-hint">影响部署方案</span></div><div class="question-card">是否有实时性要求？<span class="question-hint">影响技术选型</span></div>',
    }

    html = template
    for k, v in subs.items():
        html = html.replace(k, v)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path

    return html


def format_results(results, industry=None, tech=None, city=None):
    """格式化输出到终端"""
    if not results:
        print('❌ 未找到匹配的中南片区伙伴')
        print('💡 建议：放宽匹配条件或尝试全网搜索')
        return

    print('📋 需求概要')
    print(f'├─ 行业：{industry or "待确认"}')
    print(f'├─ 技术：{tech or "待确认"}')
    print(f'└─ 城市：{city or "不限"}')
    print()

    print(f'🤝 推荐中南片区伙伴（{len(results)}家）')
    for i, r in enumerate(results):
        stars = '⭐' * min(5, max(1, r['score'] // 20))
        print(f'├─ 【{r["company"]}】{stars}')
        print(f'│   ├─ 产品：{r.get("product", "—")}')
        print(f'│   ├─ 城市：{r.get("city", "—")}')
        print(f'│   ├─ 技术：{r.get("tech", "—")}')
        print(f'│   ├─ 行业：{r.get("industry1", "—")}')
        print(f'│   ├─ AI能力：{"/".join(r.get("ai_tags", [])) or "—"}')
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
            'LLM': 'ERNIE Bot / 文心一言',
            '智能体': 'Agent框架 + ERNIE',
        }
        print(f'├─ 推荐工具：{tool_map.get(tech, "PaddleX")}')
    print(f'├─ 部署方式：本地部署 / 云端API（按需选择）')
    print(f'└─ 预估周期：POC 2周，落地 4-6周')


def main():
    parser = argparse.ArgumentParser(description='中南片区生态伙伴智能匹配')
    parser.add_argument('--industry', '-i', help='行业（如：金融、工业、医疗）')
    parser.add_argument('--tech', '-t', help='AI能力需求（如：OCR、CV、NLP、LLM）')
    parser.add_argument('--city', '-c', help='城市偏好（如：厦门、广州、深圳）')
    parser.add_argument('--keyword', '-k', help='关键词搜索')
    parser.add_argument('--top', '-n', type=int, default=5, help='返回数量（默认5）')
    parser.add_argument('--output', '-o', help='HTML报告输出路径')
    parser.add_argument('--json', '-j', help='JSON格式输入需求')

    args = parser.parse_args()

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

    # 终端输出
    format_results(results, industry=args.industry, tech=args.tech, city=args.city)

    # 生成 HTML 报告
    if args.output:
        output_file = generate_html_report(results, args.industry, args.tech, args.city, args.output)
        print(f'\n📄 HTML 报告已生成：{output_file}')
    elif results:
        # 默认生成到当前目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_path = f'match-report-{timestamp}.html'
        output_file = generate_html_report(results, args.industry, args.tech, args.city, default_path)
        print(f'\n📄 HTML 报告已生成：{output_file}')


if __name__ == '__main__':
    main()