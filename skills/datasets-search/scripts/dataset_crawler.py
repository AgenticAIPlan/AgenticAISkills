#!/usr/bin/env python3
"""
数据集新闻爬虫脚本
爬取网络上关于数据集的新闻，提取关键信息并生成报告
"""

import argparse
import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# 默认请求头
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 数据源配置
DATA_SOURCES = {
    'jiqizhixin': {
        'name': '机器之心',
        'base_url': 'https://www.jiqizhixin.com',
        'search_url': 'https://www.jiqizhixin.com/search?query={query}',
        'enabled': True,
    },
    'infoq': {
        'name': 'InfoQ',
        'base_url': 'https://www.infoq.cn',
        'search_url': 'https://www.infoq.cn/search?query={query}',
        'enabled': True,
    },
    'oschina': {
        'name': '开源中国',
        'base_url': 'https://www.oschina.net',
        'search_url': 'https://www.oschina.net/search?search={query}',
        'enabled': True,
    },
}

# 企业简称到全称的映射
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


class DatasetCrawler:
    """数据集新闻爬虫"""

    def __init__(self, delay: tuple = (2, 5)):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.results: List[Dict] = []

    def _random_delay(self):
        """随机延迟，避免请求过快"""
        time.sleep(random.uniform(*self.delay))

    def _get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送GET请求"""
        try:
            self._random_delay()
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"请求失败: {url}, 错误: {e}")
            return None

    def _expand_company_name(self, name: str) -> str:
        """将企业简称扩展为全称"""
        if not name:
            return name
        # 直接匹配
        if name in COMPANY_MAPPINGS:
            return COMPANY_MAPPINGS[name]
        # 尝试部分匹配
        for short, full in COMPANY_MAPPINGS.items():
            if short in name or name in short:
                return full
        return name

    def _is_high_quality(self, text: str) -> bool:
        """判断是否为高质量数据集"""
        quality_keywords = [
            '高质量数据集', '高质量数据', '优质数据集',
            '认证数据集', '官方数据集', '标准数据集',
            'benchmark', 'high-quality', 'verified',
        ]
        text_lower = text.lower()
        return any(kw in text_lower or kw in text for kw in quality_keywords)

    def _extract_dataset_info(self, title: str, content: str, url: str) -> Optional[Dict]:
        """从标题和正文中提取数据集信息"""
        full_text = f"{title} {content}"

        # 提取数据集名称（使用正则匹配常见模式）
        dataset_patterns = [
            r'["""'']([^"""'']*?(?:数据集|dataset|语料|corpus)[^"""'']*)["""'']',
            r'发布(?:了)?([^，。\n]{3,30}?(?:数据集|dataset))',
            r'开源(?:了)?([^，。\n]{3,30}?(?:数据集|dataset))',
            r'([A-Z][a-zA-Z0-9]*(?:Dataset|Corpus|Benchmark))',
        ]

        dataset_name = None
        for pattern in dataset_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                dataset_name = match.group(1).strip()
                if len(dataset_name) > 3:
                    break

        if not dataset_name:
            # 如果无法提取，尝试从标题中提取
            dataset_name = title.split('｜')[0].split('|')[0].strip()[:50]

        # 提取企业名称
        company_name = None
        for short_name in COMPANY_MAPPINGS.keys():
            if short_name in full_text:
                company_name = short_name
                break

        if company_name:
            company_name = self._expand_company_name(company_name)

        # 提取描述（取正文前200字）
        description = content[:200].replace('\n', ' ').strip()
        if len(description) > 150:
            description = description[:150] + '...'

        # 检查是否为高质量数据集
        is_high_quality = self._is_high_quality(full_text)

        # 提取链接
        links = []
        if 'github.com' in full_text.lower():
            gh_match = re.search(r'https?://github\.com/[^\s\)"<>]+', full_text)
            if gh_match:
                links.append(('GitHub', gh_match.group()))
        if 'huggingface' in full_text.lower():
            hf_match = re.search(r'https?://huggingface\.co/[^\s\)"<>]+', full_text)
            if hf_match:
                links.append(('HuggingFace', hf_match.group()))

        return {
            'dataset_name': dataset_name,
            'company_name': company_name or '未知',
            'description': description,
            'is_high_quality': is_high_quality,
            'source_url': url,
            'links': links,
            'publish_date': datetime.now().strftime('%Y-%m-%d'),
        }

    def crawl_jiqizhixin(self, days: int = 7) -> List[Dict]:
        """爬取机器之心的数据集新闻"""
        results = []
        keywords = ['数据集', 'dataset', '开源数据', '语料']

        for keyword in keywords:
            url = DATA_SOURCES['jiqizhixin']['search_url'].format(query=keyword)
            response = self._get(url)
            if not response:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('div', class_='article-item') or soup.find_all('article')

            for article in articles[:10]:  # 限制数量
                try:
                    title_elem = article.find('h3') or article.find('h2') or article.find('a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text().strip()
                    link = title_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = urljoin(DATA_SOURCES['jiqizhixin']['base_url'], link)

                    # 获取正文
                    content = ''
                    if link:
                        content_response = self._get(link)
                        if content_response:
                            content_soup = BeautifulSoup(content_response.text, 'html.parser')
                            content_elem = content_soup.find('div', class_='article-content') or content_soup.find('article')
                            if content_elem:
                                content = content_elem.get_text()

                    info = self._extract_dataset_info(title, content or title, link or url)
                    if info:
                        info['source'] = '机器之心'
                        results.append(info)

                except Exception as e:
                    print(f"解析文章失败: {e}")
                    continue

        return results

    def crawl_infoq(self, days: int = 7) -> List[Dict]:
        """爬取InfoQ的数据集新闻"""
        results = []
        # InfoQ需要登录或API，这里使用模拟数据示例
        # 实际实现需要根据InfoQ的API或页面结构进行调整
        return results

    def crawl_oschina(self, days: int = 7) -> List[Dict]:
        """爬取开源中国的数据集新闻"""
        results = []
        # 类似实现
        return results

    def crawl_all(self, sources: List[str] = None, days: int = 7) -> List[Dict]:
        """爬取所有数据源"""
        all_results = []
        sources = sources or list(DATA_SOURCES.keys())

        for source in sources:
            if source not in DATA_SOURCES or not DATA_SOURCES[source].get('enabled'):
                continue

            print(f"正在爬取: {DATA_SOURCES[source]['name']}")

            if source == 'jiqizhixin':
                results = self.crawl_jiqizhixin(days)
            elif source == 'infoq':
                results = self.crawl_infoq(days)
            elif source == 'oschina':
                results = self.crawl_oschina(days)
            else:
                continue

            all_results.extend(results)
            print(f"  获取到 {len(results)} 条数据")

        # 去重
        seen = set()
        unique_results = []
        for r in all_results:
            key = (r.get('dataset_name', ''), r.get('company_name', ''))
            if key not in seen and key[0]:
                seen.add(key)
                unique_results.append(r)

        self.results = unique_results
        return unique_results

    def filter_incremental(self, state_file: str) -> List[Dict]:
        """筛选增量数据"""
        # 加载历史状态
        history = set()
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                history = set(tuple(item) for item in state.get('datasets', []))

        # 筛选新增数据
        new_results = []
        for r in self.results:
            key = (r.get('dataset_name', ''), r.get('company_name', ''))
            if key not in history:
                new_results.append(r)
                history.add(key)

        # 保存新状态
        state = {
            'last_run': datetime.now().isoformat(),
            'datasets': [list(item) for item in history],
        }
        os.makedirs(os.path.dirname(state_file) or '.', exist_ok=True)
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        return new_results

    def generate_report(self, output_file: str = None, incremental: bool = False, state_file: str = None) -> str:
        """生成Markdown报告"""
        results = self.results

        if incremental and state_file:
            results = self.filter_incremental(state_file)
            print(f"增量模式: 发现 {len(results)} 条新数据")

        if not results:
            return "未找到数据集相关新闻。"

        # 生成Markdown
        lines = [
            f"# 数据集新闻报告 ({datetime.now().strftime('%Y-%m-%d')})",
            "",
            f"## {'本周新增' if incremental else '本次采集'}数据集 ({len(results)}条)",
            "",
            "| 序号 | 数据集名称 | 企业名称 | 数据集描述 | 高质量标记 | 相关链接 |",
            "|:---:|:---|:---|:---|:---:|:---|",
        ]

        for i, r in enumerate(results, 1):
            quality_mark = "⭐" if r.get('is_high_quality') else "-"
            links = " ".join([f"[{name}]({url})" for name, url in r.get('links', [])]) or "-"
            company = r.get('company_name', '未知')
            description = r.get('description', '-').replace('|', '\\|')
            dataset_name = r.get('dataset_name', '-').replace('|', '\\|')

            lines.append(f"| {i} | {dataset_name} | {company} | {description} | {quality_mark} | {links} |")

        lines.extend([
            "",
            "## 数据来源",
            "",
            "本报告数据来自以下渠道：",
            "- 机器之心 (jiqizhixin.com)",
            "- InfoQ (infoq.cn)",
            "- 开源中国 (oschina.net)",
            "",
            "---",
            f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])

        report = '\n'.join(lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"报告已保存至: {output_file}")

        return report


def main():
    parser = argparse.ArgumentParser(description='数据集新闻爬虫')
    parser.add_argument('--days', type=int, default=7, help='采集最近N天的数据')
    parser.add_argument('--sources', type=str, default='jiqizhixin', help='数据源，逗号分隔')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--incremental', action='store_true', help='增量模式，仅输出新增数据')
    parser.add_argument('--state-file', type=str, default='~/.dataset_crawler_state.json', help='状态文件路径')
    parser.add_argument('--delay', type=str, default='2,5', help='请求延迟范围(秒)')

    args = parser.parse_args()

    # 解析参数
    sources = [s.strip() for s in args.sources.split(',')]
    delay = tuple(float(x) for x in args.delay.split(','))
    state_file = os.path.expanduser(args.state_file)

    # 创建爬虫并执行
    crawler = DatasetCrawler(delay=delay)
    crawler.crawl_all(sources=sources, days=args.days)

    # 生成报告
    report = crawler.generate_report(
        output_file=args.output,
        incremental=args.incremental,
        state_file=state_file,
    )

    if not args.output:
        print("\n" + "="*60)
        print(report)


if __name__ == '__main__':
    main()
