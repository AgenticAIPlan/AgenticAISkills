#!/usr/bin/env python3
"""
解析与筛选层 (Parser & Filter)
严格解析，宁缺毋滥
"""

import re
import logging
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class Parser:
    """HTML解析与关键词筛选器 - 严格模式"""

    def __init__(self, config: dict):
        self.config = config
        self.keywords = config.get('keywords', {})
        self.ai_keywords = self.keywords.get('ai', [])
        self.data_keywords = self.keywords.get('data', [])

    def parse_source(self, fetch_result: dict) -> Dict[str, any]:
        """
        解析单个数据源的HTML内容
        """
        source_id = fetch_result.get('source_id', 'unknown')
        source_name = fetch_result.get('source_name', source_id)
        base_url = fetch_result.get('url', '')

        if not fetch_result.get('success'):
            return {
                'success': False,
                'source_id': source_id,
                'source_name': source_name,
                'policies': [],
                'error': fetch_result.get('error', 'Fetch failed')
            }

        html = fetch_result.get('html', '')
        
        # 严格解析
        policies = self._strict_parse(html, base_url, source_id, source_name)
        
        logger.info(f"[{source_id}] 解析完成，找到 {len(policies)} 条有效政策")

        return {
            'success': True,
            'source_id': source_id,
            'source_name': source_name,
            'policies': policies
        }

    def _strict_parse(self, html: str, base_url: str, source_id: str, source_name: str) -> List[dict]:
        """
        严格解析：必须有真实日期和有效链接
        """
        policies = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
        except Exception as e:
            logger.error(f"[{source_id}] HTML解析失败: {e}")
            return []

        # 查找政策列表项
        list_items = self._find_policy_items(soup)
        
        if not list_items:
            logger.warning(f"[{source_id}] 未找到政策列表")
            return []

        for item in list_items:
            try:
                policy = self._extract_strict(item, base_url, source_name)
                if policy and self._validate_policy(policy):
                    # 检查关键词匹配
                    categories = self._match_keywords(policy['title'])
                    if categories:
                        policy['categories'] = categories
                        policies.append(policy)
            except Exception as e:
                logger.debug(f"解析条目失败: {e}")
                continue

        return policies

    def _find_policy_items(self, soup: BeautifulSoup) -> List:
        """查找政策列表项"""
        # 优先查找包含日期和链接的列表项
        selectors = [
            'ul.news-list li', 'ul.list li', '.news-item', 
            '.policy-list li', 'table.news-table tr',
            'ul.con-list li', 'ul.newslist li'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if len(items) >= 2:
                logger.debug(f"[{selector}] 找到 {len(items)} 项")
                return items
        
        # 备选：查找所有包含链接和日期的li或div
        items = []
        for elem in soup.find_all(['li', 'div', 'tr']):
            if elem.find('a') and self._has_date_element(elem):
                items.append(elem)
        
        return items[:50]  # 最多50条

    def _has_date_element(self, elem) -> bool:
        """检查元素是否包含日期"""
        text = elem.get_text()
        # 查找YYYY-MM-DD格式
        return bool(re.search(r'20\d{2}[\-\/]\d{1,2}[\-\/]\d{1,2}', text))

    def _extract_strict(self, item, base_url: str, source_name: str) -> Optional[dict]:
        """
        严格提取：必须有标题、链接和真实日期
        """
        # 提取标题和链接
        a_tag = item.find('a')
        if not a_tag:
            return None
        
        title = a_tag.get_text(strip=True)
        href = a_tag.get('href', '')
        
        if not title or len(title) < 5:
            return None
        
        if not href or href.startswith('#') or href.startswith('javascript:'):
            return None
        
        # 构建完整URL
        full_url = urljoin(base_url, href)
        
        # 提取日期 - 必须有真实日期
        parsed_date = self._extract_real_date(item)
        if not parsed_date:
            # 尝试从URL或标题提取
            parsed_date = self._extract_date_from_url(full_url) or self._extract_date_from_title(title)
        
        if not parsed_date:
            logger.debug(f"跳过：无法提取日期 - {title[:30]}")
            return None
        
        # 检查日期范围（2026年4月及以后）
        if parsed_date.year < 2026 or (parsed_date.year == 2026 and parsed_date.month < 4):
            return None
        
        return {
            'title': title,
            'url': full_url,
            'pub_date': parsed_date.isoformat(),
            'source_name': source_name
        }

    def _extract_real_date(self, item) -> Optional[date]:
        """从元素中提取真实日期"""
        # 常见的日期选择器
        date_selectors = [
            '.date', '.time', '.pub-date', '.pub-time',
            'span.date', 'span.time', 'em.date', 'i.date'
        ]
        
        for selector in date_selectors:
            elem = item.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                parsed = self._parse_date_strict(text)
                if parsed:
                    return parsed
        
        # 从所有文本中提取
        full_text = item.get_text(strip=True)
        
        # 优先匹配YYYY-MM-DD格式
        match = re.search(r'(20\d{2})[\-\/](\d{1,2})[\-\/](\d{1,2})', full_text)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if 2020 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                    return date(year, month, day)
            except:
                pass
        
        return None

    def _extract_date_from_url(self, url: str) -> Optional[date]:
        """从URL中提取日期 /2026/04/15/ 或 20260415"""
        # 匹配 /2026/04/15/ 格式
        match = re.search(r'/(20\d{2})[/\-](\d{1,2})[/\-](\d{1,2})/', url)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return date(year, month, day)
            except:
                pass
        
        # 匹配 20260415 格式
        match = re.search(r'(20\d{2})(\d{2})(\d{2})', url)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return date(year, month, day)
            except:
                pass
        
        return None

    def _extract_date_from_title(self, title: str) -> Optional[date]:
        """从标题中提取日期"""
        match = re.search(r'(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', title)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return date(year, month, day)
            except:
                pass
        return None

    def _parse_date_strict(self, date_str: str) -> Optional[date]:
        """严格解析日期字符串"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # 格式: 2026-04-22 或 2026/04/22
        match = re.match(r'(\d{4})[\-\/](\d{1,2})[\-\/](\d{1,2})', date_str)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if 2020 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                    return date(year, month, day)
            except:
                pass
        
        # 格式: 2026年4月22日
        match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return date(year, month, day)
            except:
                pass
        
        return None

    def _validate_policy(self, policy: dict) -> bool:
        """验证政策数据是否有效"""
        # 验证URL格式
        url = policy.get('url', '')
        if not url.startswith('http'):
            return False
        
        # 验证标题
        title = policy.get('title', '')
        if len(title) < 5 or len(title) > 200:
            return False
        
        # 验证日期存在
        if not policy.get('pub_date'):
            return False
        
        return True

    def _match_keywords(self, title: str) -> List[str]:
        """匹配关键词"""
        categories = []
        title_lower = title.lower()

        for kw in self.ai_keywords:
            if kw.lower() in title_lower or kw in title:
                if 'ai' not in categories:
                    categories.append('ai')
                break

        for kw in self.data_keywords:
            if kw.lower() in title_lower or kw in title:
                if 'data' not in categories:
                    categories.append('data')
                break

        return categories

    def parse_all(self, fetch_results: List[dict]) -> Dict[str, List[dict]]:
        """解析所有数据源"""
        all_policies = []

        for result in fetch_results:
            parsed = self.parse_source(result)
            if parsed.get('success'):
                all_policies.extend(parsed.get('policies', []))

        # 按类别分组
        ai_policies = [p for p in all_policies if 'ai' in p.get('categories', [])]
        data_policies = [p for p in all_policies if 'data' in p.get('categories', [])]

        # 去重
        ai_policies = self._deduplicate(ai_policies)
        data_policies = self._deduplicate(data_policies)

        logger.info(f"筛选完成: AI政策 {len(ai_policies)} 条, 数据政策 {len(data_policies)} 条")

        return {
            'ai': ai_policies,
            'data': data_policies,
            'all': all_policies
        }

    def _deduplicate(self, policies: List[dict]) -> List[dict]:
        """按标题去重"""
        seen = set()
        result = []
        for p in policies:
            norm_title = p['title'].lower().replace(' ', '').replace('\u3000', '')
            if norm_title not in seen:
                seen.add(norm_title)
                result.append(p)
        return result
