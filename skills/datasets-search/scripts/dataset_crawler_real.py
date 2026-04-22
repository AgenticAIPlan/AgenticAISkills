#!/usr/bin/env python3
"""
数据集新闻爬虫 - 真实数据版本
只获取真实数据，不生成模拟数据
"""

import argparse
import json
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
}


class RealDatasetCrawler:
    """真实数据集爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        self.results = []
        self.failed_sources = []  # 记录失败的源

    def _get(self, url: str, timeout: int = 30) -> Optional[requests.Response]:
        """发送GET请求"""
        try:
            time.sleep(1)
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            return None

    def _expand_company(self, text: str) -> str:
        """扩展企业名称"""
        text = text.lower()
        for short, full in COMPANY_MAPPINGS.items():
            if short.lower() in text:
                return full
        return ''

    def crawl_github(self) -> List[Dict]:
        """爬取GitHub真实数据"""
        print("[1/4] 爬取 GitHub 开源数据集...")
        results = []
        
        queries = [
            'chinese dataset',
            'corpus NLP',
            'benchmark chinese',
        ]
        
        for query in queries[:2]:
            url = f'https://api.github.com/search/repositories?q={requests.utils.quote(query)}+sort:stars&per_page=20'
            resp = self._get(url)
            
            if resp and resp.status_code == 200:
                data = resp.json()
                for repo in data.get('items', []):
                    name = repo.get('full_name', '').split('/')[-1]
                    desc = repo.get('description', '') or ''
                    
                    # 检查是否是数据集相关
                    keywords = ['dataset', 'data', 'corpus', 'benchmark', '语料']
                    if any(kw in name.lower() or kw in desc.lower() for kw in keywords):
                        company = self._expand_company(name + ' ' + desc)
                        
                        results.append({
                            'dataset_name': name[:50],
                            'company_name': company or repo.get('owner', {}).get('login', '开源社区'),
                            'description': desc[:100] if desc else '开源数据集项目',
                            'stars': repo.get('stargazers_count', 0),
                            'url': repo.get('html_url', ''),
                            'type': '开源数据集',
                            'source': 'GitHub',
                            'date': repo.get('created_at', '')[:10],
                        })
            else:
                if 'GitHub API' not in [f['source'] for f in self.failed_sources]:
                    self.failed_sources.append({'source': 'GitHub API', 'reason': 'API限制或网络错误'})
        
        # 去重
        seen = set()
        unique = []
        for r in results:
            if r['dataset_name'] not in seen:
                seen.add(r['dataset_name'])
                unique.append(r)
        
        print(f"  ✓ 成功获取 {len(unique)} 条")
        return unique[:10]

    def crawl_chinaz(self) -> List[Dict]:
        """爬取站长之家AI频道"""
        print("[2/4] 爬取 站长之家AI频道...")
        results = []
        
        url = 'https://www.chinaz.com/ai/'
        resp = self._get(url)
        
        if not resp:
            self.failed_sources.append({'source': '站长之家', 'reason': '无法访问页面'})
            print("  ✗ 访问失败")
            return results
        
        resp.encoding = 'utf-8'
        html = resp.text
        
        # 提取新闻
        pattern = r'<h3>([^\n]+?)\s*</h3>.*?href="([^"]+)"'
        matches = re.findall(pattern, html, re.DOTALL)
        
        # 数据集相关关键词
        dataset_keywords = ['数据集', 'dataset', '语料', 'corpus', 'benchmark', '开源', '高质量', '训练数据']
        
        for title, link in matches[:15]:
            title_clean = re.sub(r'<[^>]+?>', '', title).strip()
            
            # 检查是否是数据集相关
            is_dataset = any(kw in title_clean for kw in dataset_keywords)
            
            if is_dataset:
                if link.startswith('/'):
                    link = 'https://www.chinaz.com' + link
                
                # 获取详情
                detail_resp = self._get(link)
                content = ''
                if detail_resp:
                    content = self._extract_content(detail_resp.text)
                
                # 提取企业
                company = self._expand_company(title_clean + ' ' + content)
                
                results.append({
                    'dataset_name': title_clean[:50],
                    'company_name': company or '未识别',
                    'description': content[:100] if content else title_clean[:100],
                    'url': link,
                    'type': '新闻报道',
                    'source': '站长之家AI',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                })
        
        print(f"  ✓ 成功获取 {len(results)} 条")
        return results

    def _extract_content(self, html: str) -> str:
        """提取正文"""
        patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
                return content
        
        return ''

    def crawl_huggingface(self) -> List[Dict]:
        """爬取HuggingFace数据集"""
        print("[3/4] 爬取 HuggingFace 数据集...")
        results = []
        
        # 尝试获取HuggingFace中文数据集
        url = 'https://huggingface.co/api/datasets?limit=20'
        resp = self._get(url)
        
        if resp and resp.status_code == 200:
            try:
                datasets = resp.json()
                for ds in datasets[:10]:
                    name = ds.get('id', '')
                    desc = ds.get('description', '') or ''
                    
                    # 检查是否有中文数据
                    if any(kw in name.lower() + desc.lower() for kw in ['chinese', '中文', 'china']):
                        results.append({
                            'dataset_name': name.split('/')[-1][:50],
                            'company_name': name.split('/')[0] if '/' in name else '开源社区',
                            'description': desc[:100] if desc else 'HuggingFace数据集',
                            'url': f"https://huggingface.co/datasets/{name}",
                            'type': '开源数据集',
                            'source': 'HuggingFace',
                            'date': datetime.now().strftime('%Y-%m-%d'),
                        })
            except:
                pass
        
        if not results:
            self.failed_sources.append({'source': 'HuggingFace', 'reason': 'API限制或无法访问'})
        
        print(f"  ✓ 成功获取 {len(results)} 条")
        return results

    def crawl_gov_websites(self) -> List[Dict]:
        """尝试爬取政府网站"""
        print("[4/4] 尝试访问政府数据源...")
        results = []
        
        # 尝试多个政府数据源
        gov_sources = [
            {'name': '北京市经信局', 'url': 'https://jxj.beijing.gov.cn/'},
            {'name': '上海数据交易所', 'url': 'https://www.chinadep.com/'},
            {'name': '深圳数据交易所', 'url': 'https://www.szdex.com.cn/'},
        ]
        
        for source in gov_sources:
            resp = self._get(source['url'], timeout=10)
            if resp:
                # 如果可访问，记录但暂时无法解析具体数据集
                self.failed_sources.append({
                    'source': source['name'], 
                    'reason': '网站可访问，但需要特定API Key或解析规则才能获取数据集信息'
                })
            else:
                self.failed_sources.append({
                    'source': source['name'], 
                    'reason': '网站无法访问（可能需要特定网络环境或授权）'
                })
        
        print(f"  ⚠ 政府数据源需要特殊授权，无法直接爬取")
        return results

    def crawl_all(self) -> List[Dict]:
        """爬取所有数据源"""
        print("=" * 60)
        print("开始爬取真实数据集数据...")
        print("=" * 60)
        print()
        
        # 1. GitHub（真实数据）
        github_data = self.crawl_github()
        self.results.extend(github_data)
        
        # 2. 站长之家（真实新闻）
        chinaz_data = self.crawl_chinaz()
        self.results.extend(chinaz_data)
        
        # 3. HuggingFace（真实数据）
        hf_data = self.crawl_huggingface()
        self.results.extend(hf_data)
        
        # 4. 政府网站（尝试访问）
        gov_data = self.crawl_gov_websites()
        self.results.extend(gov_data)
        
        print()
        print("=" * 60)
        print(f"总计获取: {len(self.results)} 条真实数据")
        if self.failed_sources:
            print(f"访问失败: {len(self.failed_sources)} 个数据源")
        print("=" * 60)
        print()
        
        return self.results

    def generate_report(self, output_file: str = None) -> str:
        """生成报告"""
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        lines = [
            f'# 数据集新闻报告（真实数据）',
            f'',
            f'**报告时间**: {now_str}',
            f'**数据类型**: 仅真实数据，无模拟数据',
            f'',
            '---',
            f'',
            f'## 📊 数据概览',
            f'',
            f'**总计获取**: {len(self.results)} 条真实数据',
            f'',
        ]
        
        if self.results:
            # 按来源分组
            by_source = {}
            for r in self.results:
                src = r.get('source', '未知')
                if src not in by_source:
                    by_source[src] = []
                by_source[src].append(r)
            
            lines.extend([
                f'**数据来源分布**:',
                f'',
            ])
            for src, items in by_source.items():
                lines.append(f'- {src}: {len(items)} 条')
            lines.append('')
            
            # 详细列表
            lines.extend([
                f'## 📋 详细数据',
                f'',
            ])
            
            for source, items in by_source.items():
                lines.extend([
                    f'### {source} ({len(items)}条)',
                    f'',
                ])
                
                for i, item in enumerate(items, 1):
                    name = item.get('dataset_name', '未知')
                    company = item.get('company_name', '未知')
                    desc = item.get('description', '')[:80]
                    url = item.get('url', '')
                    
                    lines.extend([
                        f'{i}. **{name}**',
                        f'   - 企业: {company}',
                        f'   - 描述: {desc}...' if len(item.get('description', '')) > 80 else f'   - 描述: {desc}',
                    ])
                    
                    if item.get('stars'):
                        lines.append(f'   - 星标: ⭐{item["stars"]}')
                    
                    if url:
                        lines.append(f'   - 链接: {url}')
                    
                    lines.append('')
        else:
            lines.extend([
                f'⚠️ **未获取到数据**',
                f'',
                f'可能原因：',
                f'- 所有数据源暂时无法访问',
                f'- 网络限制',
                f'- 需要API Key或特殊授权',
                f'',
            ])
        
        # 失败源说明
        if self.failed_sources:
            lines.extend([
                f'## ⚠️ 无法访问的数据源',
                f'',
                f'以下数据源无法获取数据：',
                f'',
            ])
            for f in self.failed_sources:
                lines.append(f"- **{f['source']}**: {f['reason']}")
            lines.append('')
        
        lines.extend([
            '---',
            f'',
            f'**说明**: 本报告仅包含真实爬取的数据，不包含任何模拟数据。',
            f'',
            f'*报告生成时间: {now_str}*',
        ])
        
        report = '\n'.join(lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存: {output_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description='数据集新闻爬虫 - 真实数据版本')
    parser.add_argument('--output', type=str, default='/tmp/dataset_real_report.md', help='输出文件路径')
    
    args = parser.parse_args()
    
    crawler = RealDatasetCrawler()
    crawler.crawl_all()
    
    report = crawler.generate_report(output_file=args.output)
    
    print("\n" + "=" * 60)
    print("报告预览:")
    print("=" * 60)
    print(report[:3000])
    if len(report) > 3000:
        print("...")
    print(f"\n完整报告: {args.output}")


if __name__ == '__main__':
    main()
