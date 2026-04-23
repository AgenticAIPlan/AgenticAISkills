#!/usr/bin/env python3
"""
信息采集层 (Collector)
负责从配置的数据源获取HTML内容
"""

import random
import time
import logging
from typing import Optional, Dict, List
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class Collector:
    """网页内容采集器"""

    def __init__(self, config: dict):
        self.config = config
        self.collector_config = config.get('collector', {})
        self.user_agents = self.collector_config.get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ])
        self.timeout_connect = self.collector_config.get('timeout_connect', 5)
        self.timeout_read = self.collector_config.get('timeout_read', 10)
        self.max_retries = self.collector_config.get('max_retries', 2)
        self.retry_backoff = self.collector_config.get('retry_backoff', 2)

        # 创建session并配置重试
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建配置了重试策略的session"""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_random_ua(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)

    def _build_headers(self, url: str = '') -> dict:
        """构建请求头，模拟真实浏览器访问"""
        headers = {
            'User-Agent': self._get_random_ua(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

        # 添加Referer，模拟从搜索引擎进入
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            headers['Referer'] = f"https://www.baidu.com/s?wd={parsed.netloc}"

        return headers

    def fetch(self, source: dict) -> Dict[str, any]:
        """
        获取单个数据源的内容

        Args:
            source: 数据源配置，包含 id, name, url, encoding 等

        Returns:
            dict: {
                'success': bool,
                'source_id': str,
                'html': str,
                'error': str,
                'status_code': int
            }
        """
        source_id = source.get('id', 'unknown')
        url = source.get('url', '')
        encoding = source.get('encoding', 'utf-8')

        logger.info(f"开始抓取数据源: {source_id} - {url}")

        try:
            response = self.session.get(
                url,
                headers=self._build_headers(url),
                timeout=(self.timeout_connect, self.timeout_read),
                allow_redirects=True
            )

            if response.status_code == 200:
                # 处理编码
                try:
                    html = response.content.decode(encoding)
                except UnicodeDecodeError:
                    html = response.content.decode('utf-8', errors='ignore')

                logger.info(f"成功抓取 {source_id}, 内容长度: {len(html)}")
                return {
                    'success': True,
                    'source_id': source_id,
                    'source_name': source.get('name', source_id),
                    'html': html,
                    'url': url,
                    'status_code': 200
                }

            elif response.status_code == 404:
                logger.warning(f"[{source_id}] URL 404, please check config: {url}")
                return {
                    'success': False,
                    'source_id': source_id,
                    'source_name': source.get('name', source_id),
                    'error': f'404 Not Found: {url}',
                    'status_code': 404
                }

            elif response.status_code in (403, 503):
                logger.error(f"[{source_id}] 请求被拒绝({response.status_code}), 跳过重试: {url}")
                return {
                    'success': False,
                    'source_id': source_id,
                    'source_name': source.get('name', source_id),
                    'error': f'{response.status_code} Forbidden/Service Unavailable',
                    'status_code': response.status_code
                }

            else:
                logger.warning(f"[{source_id}] HTTP {response.status_code}: {url}")
                return {
                    'success': False,
                    'source_id': source_id,
                    'source_name': source.get('name', source_id),
                    'error': f'HTTP {response.status_code}',
                    'status_code': response.status_code
                }

        except requests.Timeout:
            logger.error(f"[{source_id}] 请求超时: {url}")
            return {
                'success': False,
                'source_id': source_id,
                'source_name': source.get('name', source_id),
                'error': 'Connection timeout',
                'status_code': 0
            }

        except requests.ConnectionError as e:
            logger.error(f"[{source_id}] 网络连接错误: {e}")
            return {
                'success': False,
                'source_id': source_id,
                'source_name': source.get('name', source_id),
                'error': f'Connection error: {str(e)}',
                'status_code': 0
            }

        except Exception as e:
            logger.error(f"[{source_id}] 未知错误: {e}")
            return {
                'success': False,
                'source_id': source_id,
                'source_name': source.get('name', source_id),
                'error': str(e),
                'status_code': 0
            }

    def fetch_all(self, sources: List[dict]) -> List[Dict[str, any]]:
        """
        并发获取所有数据源内容

        Args:
            sources: 数据源配置列表

        Returns:
            list: 每个数据源的抓取结果
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        max_concurrent = self.collector_config.get('max_concurrent', 5)
        results = []

        logger.info(f"开始并发抓取 {len(sources)} 个数据源, 最大并发: {max_concurrent}")

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {executor.submit(self.fetch, source): source for source in sources}

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    source = futures[future]
                    logger.error(f"抓取异常: {source.get('id')}, error: {e}")
                    results.append({
                        'success': False,
                        'source_id': source.get('id', 'unknown'),
                        'source_name': source.get('name', 'unknown'),
                        'error': str(e),
                        'status_code': 0
                    })

        # 统计
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"抓取完成: 成功 {success_count}/{len(sources)}")

        return results


def test_connection() -> bool:
    """测试基础网络连接"""
    try:
        response = requests.get('https://www.baidu.com', timeout=5)
        return response.status_code == 200
    except Exception:
        return False