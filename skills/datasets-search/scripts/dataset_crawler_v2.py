#!/usr/bin/env python3
"""
数据集新闻爬虫脚本 V2
专注于爬取模型训练数据集相关新闻：
- 企业开源数据集
- 高质量数据集参评/认证
- 数据集评测/基准测试结果
"""

import argparse
import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests


# 企业名称映射
COMPANY_MAPPINGS = {
    '百度': '北京百度网讯科技有限公司',
    'Baidu': '北京百度网讯科技有限公司',
    '阿里': '阿里巴巴集团控股有限公司',
    '阿里巴巴': '阿里巴巴集团控股有限公司',
    'Alibaba': '阿里巴巴集团控股有限公司',
    '腾讯': '深圳市腾讯计算机系统有限公司',
    'Tencent': '深圳市腾讯计算机系统有限公司',
    '字节': '北京字节跳动科技有限公司',
    '字节跳动': '北京字节跳动科技有限公司',
    'ByteDance': '北京字节跳动科技有限公司',
    '华为': '华为技术有限公司',
    'Huawei': '华为技术有限公司',
    '京东': '北京京东世纪贸易有限公司',
    'JD': '北京京东世纪贸易有限公司',
    '美团': '北京三快科技有限公司',
    'Meituan': '北京三快科技有限公司',
    '小米': '小米科技有限责任公司',
    'Xiaomi': '小米科技有限责任公司',
    '网易': '广州网易计算机系统有限公司',
    'NetEase': '广州网易计算机系统有限公司',
    '快手': '北京快手科技有限公司',
    'Kuaishou': '北京快手科技有限公司',
    '滴滴': '北京小桔科技有限公司',
    'Didi': '北京小桔科技有限公司',
    '拼多多': '上海寻梦信息技术有限公司',
    'PDD': '上海寻梦信息技术有限公司',
    '商汤': '北京市商汤科技开发有限公司',
    'SenseTime': '北京市商汤科技开发有限公司',
    '旷视': '北京旷视科技有限公司',
    'Megvii': '北京旷视科技有限公司',
    '科大讯飞': '科大讯飞股份有限公司',
    'iFlytek': '科大讯飞股份有限公司',
    '智谱': '北京智谱华章科技有限公司',
    '智谱AI': '北京智谱华章科技有限公司',
    '月之暗面': '北京月之暗面科技有限公司',
    'Moonshot': '北京月之暗面科技有限公司',
    '零一万物': '零一万物（北京）科技有限公司',
    '01.AI': '零一万物（北京）科技有限公司',
    'MiniMax': 'MiniMax稀宇科技',
    '稀宇科技': 'MiniMax稀宇科技',
    '面壁智能': '北京面壁智能科技有限责任公司',
    'ModelBest': '北京面壁智能科技有限责任公司',
    '深度求索': '杭州深度求索人工智能基础技术研究有限公司',
    'DeepSeek': '杭州深度求索人工智能基础技术研究有限公司',
    '红伞': '北京红伞科技有限公司',
    '海天瑞声': '北京海天瑞声科技股份有限公司',
    '星环': '星环信息科技（上海）股份有限公司',
    '星环科技': '星环信息科技（上海）股份有限公司',
    '数据堂': '数据堂（北京）科技股份有限公司',
    '标贝': '标贝（北京）科技有限公司',
    '标贝科技': '标贝（北京）科技有限公司',
    '拓尔思': '拓尔思信息技术股份有限公司',
}


# 数据集相关精确关键词
DATASET_KEYWORDS = [
    # 开源相关
    '开源数据集', '开源数据', '数据开源', '开放数据集', '公开数据集',
    '发布数据集', '推出数据集', '上线数据集',
    
    # 高质量/参评相关
    '高质量数据集', '优质数据集', '数据集参评', '数据集认证',
    '数据质量评估', '数据集评估', '数据集评测', '数据集标准',
    '国家数据局', '数据局认证', '数据局参评', '数据局名单',
    '大模型训练数据', '训练数据集', '预训练数据集',
    
    # 评测/基准相关
    'benchmark', 'benchmark数据集',
    '评测数据集', '评估数据集', '测试数据集',
    'SOTA', 'state-of-the-art',
    
    # 特定数据集类型
    '对话数据集', '指令数据集', '问答数据集',
    '代码数据集', '语料库', 'corpus',
    '多模态数据集', '图文数据集', '语音数据集',
]


class DatasetCrawlerV2:
    """数据集新闻爬虫 V2"""

    def __init__(self, delay: tuple = (1, 3)):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.results: List[Dict] = []

    def _get(self, url: str) -> Optional[requests.Response]:
        """发送GET请求"""
        try:
            time.sleep(1)  # 简单延迟
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"请求失败: {url}, 错误: {e}")
            return None

    def _expand_company_name(self, name: str) -> str:
        """将企业简称扩展为全称"""
        if not name:
            return name
        for short, full in COMPANY_MAPPINGS.items():
            if short in name or name in short:
                return full
        return name

    def _is_dataset_related(self, title: str, content: str = '') -> tuple:
        """
        判断是否是与数据集强相关的新闻
        返回: (是否相关, 匹配的关键词, 相关类型)
        """
        full_text = f"{title} {content}".lower()
        
        # 检查强相关关键词
        strong_keywords = [
            '开源数据集', '高质量数据集', '数据集参评', '数据集认证',
            '数据局', '大模型训练数据', 'benchmark数据集', '预训练数据集',
            '数据开源', '开放数据集',
        ]
        
        for kw in strong_keywords:
            if kw in full_text:
                return True, kw, 'strong'
        
        # 检查中等相关关键词
        medium_keywords = [
            '数据集', 'dataset', 'corpus', '语料库',
            'benchmark', '评测数据', '评估数据',
        ]
        
        matched = []
        for kw in medium_keywords:
            if kw in full_text:
                matched.append(kw)
        
        if len(matched) >= 1:
            return True, matched[0], 'medium'
        
        return False, None, None

    def _extract_dataset_info(self, title: str, content: str, url: str) -> Optional[Dict]:
        """提取数据集信息"""
        full_text = f"{title} {content}"
        
        # 提取数据集名称
        dataset_name = None
        patterns = [
            r'["\'"\'«»]([^"\'"\'«»]*?(?:数据集|dataset|语料|corpus)[^"\'"\'«»]{2,30})["\'"\'«»]',
            r'开源(?:了)?([^，。\n]{3,40}?(?:数据集|dataset|语料库))',
            r'发布(?:了)?([^，。\n]{3,40}?(?:数据集|dataset|语料库))',
            r'推出(?:了)?([^，。\n]{3,40}?(?:数据集|dataset|语料库))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                dataset_name = match.group(1).strip()
                if 3 < len(dataset_name) < 50:
                    break
        
        # 如果没找到，尝试从标题提取
        if not dataset_name:
            # 移除常见后缀
            clean_title = re.sub(r'[：:].*$', '', title)
            clean_title = re.sub(r'[|丨].*$', '', clean_title)
            if len(clean_title) > 5 and len(clean_title) < 50:
                dataset_name = clean_title
        
        # 提取企业名称
        company_name = None
        for short_name, full_name in COMPANY_MAPPINGS.items():
            if short_name in full_text:
                company_name = full_name
                break
        
        # 判断类型
        news_type = 'other'
        if '开源' in full_text or '开放' in full_text or 'github' in full_text.lower():
            news_type = '开源数据集'
        elif '高质量' in full_text or '参评' in full_text or '认证' in full_text or '数据局' in full_text:
            news_type = '高质量数据集'
        elif 'benchmark' in full_text.lower() or '评测' in full_text or '评估' in full_text:
            news_type = '评测数据集'
        elif '训练' in full_text:
            news_type = '训练数据集'
        
        # 检查是否高质量
        is_high_quality = any(kw in full_text for kw in [
            '高质量', '优质', 'official', 'verified', 'standard',
            '认证', '参评', '数据局', 'benchmark'
        ])
        
        # 提取链接
        links = []
        github_match = re.search(r'https?://github\.com/[^\s\)"<>]+', full_text)
        if github_match:
            links.append(('GitHub', github_match.group()))
        
        huggingface_match = re.search(r'https?://huggingface\.co/[^\s\)"<>]+', full_text)
        if huggingface_match:
            links.append(('HuggingFace', huggingface_match.group()))
        
        # 提取描述
        description = content[:150].replace('\n', ' ').strip() if content else title[:150]
        if len(description) > 150:
            description = description[:150] + '...'
        
        # 只有提取到数据集名称才返回
        if not dataset_name:
            return None
        
        return {
            'dataset_name': dataset_name,
            'company_name': company_name or '未识别',
            'news_type': news_type,
            'description': description,
            'is_high_quality': is_high_quality,
            'source_url': url,
            'links': links,
            'publish_date': datetime.now().strftime('%Y-%m-%d'),
        }

    def crawl_chinaz_ai(self) -> List[Dict]:
        """爬取站长之家AI频道"""
        results = []
        url = 'https://www.chinaz.com/ai/'
        
        resp = self._get(url)
        if not resp:
            return results
        
        resp.encoding = 'utf-8'
        html = resp.text
        
        # 提取新闻标题和链接
        pattern = r'<h3>([^\n]+?)\s*</h3>.*?href="([^"]+)"'
        matches = re.findall(pattern, html, re.DOTALL)
        
        print(f"找到 {len(matches)} 条新闻，开始筛选...")
        
        for title, link in matches:
            title_clean = re.sub(r'<[^>]+?>', '', title).strip()
            
            # 检查是否数据集相关
            is_related, keyword, level = self._is_dataset_related(title_clean)
            
            if is_related and level in ['strong', 'medium']:
                # 补全URL
                if link.startswith('/'):
                    link = 'https://www.chinaz.com' + link
                elif not link.startswith('http'):
                    link = 'https://www.chinaz.com/' + link
                
                # 获取详情
                content = self._fetch_article_content(link)
                
                # 提取信息
                info = self._extract_dataset_info(title_clean, content, link)
                if info:
                    info['source'] = '站长之家AI'
                    info['match_keyword'] = keyword
                    results.append(info)
                    print(f"  ✓ 找到数据集新闻: {info['dataset_name'][:30]}...")
        
        return results

    def _fetch_article_content(self, url: str) -> str:
        """获取文章正文"""
        try:
            resp = self._get(url)
            if not resp:
                return ''
            
            html = resp.text
            
            # 尝试多种内容选择器
            patterns = [
                r'<article[^>]*>(.*?)</article>',
                r'<div[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
                r'<div[^>]*class=["\'][^"\']*article[^"\']*["\'][^>]*>(.*?)</div>',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1)
                    content = re.sub(r'<[^>]+>', ' ', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                    return content
            
            return ''
        except:
            return ''

    def crawl_aibase(self) -> List[Dict]:
        """爬取AIbase数据集频道"""
        results = []
        # AIbase有专门的数据集板块
        urls = [
            'https://www.aibase.com/zh/news/dataset',
            'https://www.aibase.com/zh/news/open-source',
        ]
        
        for url in urls:
            resp = self._get(url)
            if not resp:
                continue
            
            html = resp.text
            # 提取新闻列表
            # 这里需要根据实际页面结构调整
            pattern = r'<h[23][^>]*>([^[^<]+)</h[23]>.*?href="([^"]+)"'
            matches = re.findall(pattern, html, re.DOTALL)
            
            for title, link in matches[:10]:
                title = title.strip()
                is_related, keyword, level = self._is_dataset_related(title)
                
                if is_related:
                    if link.startswith('/'):
                        link = urljoin(url, link)
                    
                    content = self._fetch_article_content(link)
                    info = self._extract_dataset_info(title, content, link)
                    if info:
                        info['source'] = 'AIbase'
                        results.append(info)
        
        return results

    def crawl_github_trending(self) -> List[Dict]:
        """从GitHub搜索数据集相关仓库"""
        results = []
        
        # 使用GitHub API搜索
        queries = [
            'chinese dataset NLP',
            'training dataset LLM',
            'benchmark dataset',
        ]
        
        for query in queries[:1]:  # 限制查询数量避免限流
            url = f'https://api.github.com/search/repositories?q={query}+sort:updated+language:python&per_page=10'
            try:
                resp = self.session.get(url, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    for repo in data.get('items', []):
                        name = repo.get('full_name', '').split('/')[-1]
                        desc = repo.get('description', '') or ''
                        
                        # 检查是否是数据集
                        if any(kw in name.lower() + ' ' + desc.lower() for kw in ['dataset', 'data', 'corpus', 'benchmark']):
                            info = {
                                'dataset_name': name,
                                'company_name': repo.get('owner', {}).get('login', '开源社区'),
                                'news_type': '开源数据集',
                                'description': desc[:150] if desc else 'GitHub开源项目',
                                'is_high_quality': repo.get('stargazers_count', 0) > 50,
                                'source_url': repo.get('html_url', ''),
                                'links': [('GitHub', repo.get('html_url', ''))],
                                'publish_date': repo.get('created_at', '')[:10],
                                'source': 'GitHub',
                                'stars': repo.get('stargazers_count', 0),
                            }
                            results.append(info)
            except Exception as e:
                print(f"GitHub API错误: {e}")
        
        return results

    def crawl_all(self) -> List[Dict]:
        """爬取所有数据源"""
        all_results = []
        
        print("开始爬取数据集相关新闻...")
        print()
        
        # 1. 爬取站长之家
        print("[1/3] 爬取站长之家AI频道...")
        results = self.crawl_chinaz_ai()
        all_results.extend(results)
        print(f"  找到 {len(results)} 条数据集相关新闻")
        print()
        
        # 2. 爬取AIbase
        print("[2/3] 爬取AIbase...")
        results = self.crawl_aibase()
        all_results.extend(results)
        print(f"  找到 {len(results)} 条数据集相关新闻")
        print()
        
        # 3. 爬取GitHub
        print("[3/3] 爬取GitHub...")
        results = self.crawl_github_trending()
        all_results.extend(results)
        print(f"  找到 {len(results)} 条数据集相关新闻")
        print()
        
        # 去重
        seen = set()
        unique_results = []
        for r in all_results:
            key = (r.get('dataset_name', ''), r.get('company_name', ''))
            if key not in seen and key[0]:
                seen.add(key)
                unique_results.append(r)
        
        self.results = unique_results
        print(f"总计: {len(unique_results)} 条唯一数据集新闻")
        return unique_results

    def generate_report(self, output_file: str = None) -> str:
        """生成Markdown报告"""
        if not self.results:
            return "未找到数据集相关新闻。"
        
        # 按类型分组
        open_source = [r for r in self.results if r.get('news_type') == '开源数据集']
        high_quality = [r for r in self.results if r.get('news_type') == '高质量数据集']
        benchmark = [r for r in self.results if r.get('news_type') == '评测数据集']
        others = [r for r in self.results if r.get('news_type') not in ['开源数据集', '高质量数据集', '评测数据集']]
        
        lines = [
            f"# 数据集新闻报告 ({datetime.now().strftime('%Y-%m-%d')})",
            "",
            "## 概览",
            "",
            f"- **总计**: {len(self.results)} 条数据集相关新闻",
            f"- **开源数据集**: {len(open_source)} 条",
            f"- **高质量数据集**: {len(high_quality)} 条",
            f"- **评测数据集**: {len(benchmark)} 条",
            f"- **其他**: {len(others)} 条",
            "",
            "---",
            "",
        ]
        
        # 开源数据集
        if open_source:
            lines.extend([
                f"## 开源数据集 ({len(open_source)}条)",
                "",
                "| 序号 | 数据集名称 | 企业/组织 | 描述 | 高质量 | 链接 |",
                "|:---:|:---|:---|:---|:---:|:---|",
            ])
            for i, r in enumerate(open_source, 1):
                name = r['dataset_name'][:40].replace('|', '\\|')
                company = r['company_name'].replace('|', '\\|')
                desc = r['description'][:50].replace('|', '\\|') + '...' if len(r['description']) > 50 else r['description'].replace('|', '\\|')
                quality = "⭐" if r['is_high_quality'] else "-"
                links = " ".join([f"[{n}]({u})" for n, u in r.get('links', [])]) or "-"
                lines.append(f"| {i} | {name} | {company} | {desc} | {quality} | {links} |")
            lines.append("")
        
        # 高质量数据集
        if high_quality:
            lines.extend([
                f"## 高质量数据集参评/认证 ({len(high_quality)}条)",
                "",
                "| 序号 | 数据集名称 | 企业/组织 | 描述 | 链接 |",
                "|:---:|:---|:---|:---|:---|",
            ])
            for i, r in enumerate(high_quality, 1):
                name = r['dataset_name'][:40].replace('|', '\\|')
                company = r['company_name'].replace('|', '\\|')
                desc = r['description'][:50].replace('|', '\\|') + '...' if len(r['description']) > 50 else r['description'].replace('|', '\\|')
                links = " ".join([f"[{n}]({u})" for n, u in r.get('links', [])]) or "[查看原文]({})".format(r.get('source_url', '#'))
                lines.append(f"| {i} | {name} | {company} | {desc} | {links} |")
            lines.append("")
        
        # 评测数据集
        if benchmark:
            lines.extend([
                f"## 评测/Benchmark数据集 ({len(benchmark)}条)",
                "",
                "| 序号 | 数据集名称 | 企业/组织 | 描述 | 链接 |",
                "|:---:|:---|:---|:---|:---|",
            ])
            for i, r in enumerate(benchmark, 1):
                name = r['dataset_name'][:40].replace('|', '\\|')
                company = r['company_name'].replace('|', '\\|')
                desc = r['description'][:50].replace('|', '\\|') + '...' if len(r['description']) > 50 else r['description'].replace('|', '\\|')
                links = " ".join([f"[{n}]({u})" for n, u in r.get('links', [])]) or "-"
                lines.append(f"| {i} | {name} | {company} | {desc} | {links} |")
            lines.append("")
        
        # 其他
        if others:
            lines.extend([
                f"## 其他数据集相关 ({len(others)}条)",
                "",
                "| 序号 | 数据集名称 | 企业/组织 | 类型 | 描述 |",
                "|:---:|:---|:---|:---|:---|",
            ])
            for i, r in enumerate(others, 1):
                name = r['dataset_name'][:40].replace('|', '\\|')
                company = r['company_name'].replace('|', '\\|')
                news_type = r.get('news_type', '其他')
                desc = r['description'][:50].replace('|', '\\|') + '...' if len(r['description']) > 50 else r['description'].replace('|', '\\|')
                lines.append(f"| {i} | {name} | {company} | {news_type} | {desc} |")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## 数据来源",
            "",
            "- 站长之家AI频道 (chinaz.com/ai)",
            "- AIbase数据集频道",
            "- GitHub Trending",
            "",
            f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])
        
        report = '\n'.join(lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n✅ 报告已保存至: {output_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description='数据集新闻爬虫 V2')
    parser.add_argument('--output', type=str, default='/tmp/dataset_report_v2.md', help='输出文件路径')
    
    args = parser.parse_args()
    
    # 创建爬虫并执行
    crawler = DatasetCrawlerV2()
    crawler.crawl_all()
    
    # 生成报告
    report = crawler.generate_report(output_file=args.output)
    
    print("\n" + "="*60)
    print(report[:1500])
    print("...")
    print(f"\n完整报告见: {args.output}")


if __name__ == '__main__':
    main()
