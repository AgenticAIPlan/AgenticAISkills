#!/usr/bin/env python3
"""
加工与分发层 (Processor & Distributor)
负责生成摘要、格式化报告、推送到目标渠道
支持飞书多维表格(Bitable)写入
"""

import os
import re
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from jinja2 import Template
import requests

from feishu_bitable import PolicyBitableWriter

logger = logging.getLogger(__name__)


class Processor:
    """报告生成与分发处理器"""

    def __init__(self, config: dict):
        self.config = config
        self.targets = config.get('targets', {})
        self.llm_config = config.get('llm', {})
        self.ops_config = config.get('ops', {})

        # 初始化Bitable写入器
        self.bitable_writer = PolicyBitableWriter(config)

        # LLM成本追踪
        self.llm_usage = {
            'calls': 0,
            'total_tokens': 0,
            'total_cost': 0.0
        }

    def generate_summary(self, policy: dict) -> str:
        """
        为单条政策生成摘要

        策略：
        1. 如果配置了LLM，使用LLM生成
        2. 否则，使用关键词上下文截取法
        """
        if self.llm_config.get('enabled', False):
            return self._generate_with_llm(policy)
        else:
            return self._generate_local(policy)

    def _generate_local(self, policy: dict) -> str:
        """本地摘要生成：关键词上下文截取"""
        title = policy.get('title', '')

        # 提取标题中包含关键词的部分作为简易摘要
        keywords = self.config.get('keywords', {})
        all_keywords = keywords.get('ai', []) + keywords.get('data', [])

        for kw in all_keywords:
            if kw in title:
                # 找到关键词位置，取前后50字
                idx = title.find(kw)
                start = max(0, idx - 30)
                end = min(len(title), idx + len(kw) + 30)
                context = title[start:end]
                return f"涉及「{kw}」: {context}..."

        # 无关键词匹配，返回标题前50字
        return title[:50] + "..." if len(title) > 50 else title

    def _generate_with_llm(self, policy: dict) -> str:
        """使用大模型生成摘要"""
        # 检查预算
        budget = self.llm_config.get('budget_daily', 0.1)
        if self.llm_usage['total_cost'] >= budget:
            logger.warning("LLM每日预算已用尽，降级到本地摘要法")
            return self._generate_local(policy)

        title = policy.get('title', '')
        url = policy.get('url', '')

        # 构建prompt
        prompt = f"""请用不超过80字的中文，概括以下政府政策文稿的核心内容，直接返回摘要，不加任何前缀和解释：

标题：{title}
链接：{url}"""

        try:
            result = self._call_llm(prompt)

            # 简单估算成本（实际应根据API返回的usage计算）
            estimated_tokens = len(prompt) + len(result)
            cost = estimated_tokens * 0.00001  # 假设价格

            self.llm_usage['calls'] += 1
            self.llm_usage['total_tokens'] += estimated_tokens
            self.llm_usage['total_cost'] += cost

            return result

        except Exception as e:
            logger.error(f"LLM调用失败: {e}，降级到本地摘要")
            return self._generate_local(policy)

    def _call_llm(self, prompt: str) -> str:
        """调用大模型API"""
        provider = self.llm_config.get('provider', 'deepseek')
        api_key = self.llm_config.get('api_key', '')
        base_url = self.llm_config.get('base_url', '')
        model = self.llm_config.get('model', 'deepseek-chat')

        if provider == 'deepseek':
            return self._call_deepseek(prompt, api_key, base_url, model)
        elif provider == 'qwen':
            return self._call_qwen(prompt, api_key, base_url, model)
        elif provider == 'openai':
            return self._call_openai(prompt, api_key, model)
        else:
            raise ValueError(f"不支持的LLM provider: {provider}")

    def _call_deepseek(self, prompt: str, api_key: str, base_url: str, model: str) -> str:
        """调用DeepSeek API"""
        url = f"{base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 200
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"DeepSeek API error: {result}")

    def _call_qwen(self, prompt: str, api_key: str, base_url: str, model: str) -> str:
        """调用通义千问API"""
        # 类似实现
        url = f"{base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': model,
            'input': {'prompt': prompt},
            'parameters': {'max_tokens': 200}
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()

        if 'output' in result and 'text' in result['output']:
            return result['output']['text']
        else:
            raise Exception(f"Qwen API error: {result}")

    def _call_openai(self, prompt: str, api_key: str, model: str) -> str:
        """调用OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 200
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenAI API error: {result}")

    def generate_report(self, policies: Dict[str, List[dict]], template_path: str = None) -> str:
        """
        生成格式化报告

        Args:
            policies: {'ai': [...], 'data': [...]}
            template_path: 模板文件路径

        Returns:
            str: 格式化的报告内容
        """
        ai_policies = policies.get('ai', [])
        data_policies = policies.get('data', [])

        # 为每条政策生成摘要
        for p in ai_policies + data_policies:
            if 'summary' not in p:
                p['summary'] = self.generate_summary(p)

        # 使用模板
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        else:
            # 内置默认模板
            template_content = self._get_default_template()

        template = Template(template_content)

        now = datetime.now()
        report = template.render(
            ai_policies=ai_policies,
            data_policies=data_policies,
            gen_date=now.strftime('%Y-%m-%d'),
            gen_time=now.strftime('%Y-%m-%d %H:%M:%S')
        )

        return report

    def _get_default_template(self) -> str:
        """获取默认报告模板"""
        return """{% if ai_policies or data_policies %}
## 📋 政策追踪日报

**{{ gen_date }}**

---

{% if ai_policies %}
### 🤖 人工智能政策

{% for item in ai_policies %}
* **[{{ item.source_name }}]** {{ item.title }}
  * {{ item.summary }}
  * 发布日期：{{ item.pub_date }} | [原文链接]({{ item.url }})
{% endfor %}
{% else %}
* 暂无更新
{% endif %}

---

{% if data_policies %}
### 📊 数据要素政策

{% for item in data_policies %}
* **[{{ item.source_name }}]** {{ item.title }}
  * {{ item.summary }}
  * 发布日期：{{ item.pub_date }} | [原文链接]({{ item.url }})
{% endfor %}
{% else %}
* 暂无更新
{% endif %}

---

_以上信息由AI自动生成，引用前请核对原文。_
{% else %}
## 📋 政策追踪日报

**{{ gen_date }}**

今日暂无符合关键词的政策更新。

---
_政策追踪系统 · {{ gen_time }}_
{% endif %}"""

    def distribute(self, report: str) -> Dict[str, bool]:
        """
        分发报告到各目标渠道

        Returns:
            dict: {'feishu': bool, 'dingding': bool, 'email': bool}
        """
        results = {}

        # 飞书群机器人推送
        if self.targets.get('feishu', {}).get('enabled', False):
            results['feishu'] = self._send_to_feishu(report)

        # 钉钉推送
        if self.targets.get('dingding', {}).get('enabled', False):
            results['dingding'] = self._send_to_dingding(report)

        # 邮件推送
        if self.targets.get('email', {}).get('enabled', False):
            results['email'] = self._send_to_email(report)

        return results

    def write_to_bitable(self, policies: List[dict]) -> Dict[str, int]:
        """
        将政策数据写入飞书多维表格

        Args:
            policies: 政策数据列表

        Returns:
            dict: {'success': int, 'failed': int}
        """
        if not self.bitable_writer.is_ready():
            logger.info("Bitable未配置，跳过写入")
            return {'success': 0, 'failed': 0}

        logger.info("="*20 + " 写入飞书多维表格 " + "="*20)

        # 合并AI政策和数据政策
        all_policies = []
        if isinstance(policies, dict):
            all_policies = policies.get('ai', []) + policies.get('data', [])
        elif isinstance(policies, list):
            all_policies = policies

        if not all_policies:
            logger.info("无政策数据需要写入")
            return {'success': 0, 'failed': 0}

        # 为每条政策生成摘要
        for policy in all_policies:
            if 'summary' not in policy or not policy['summary']:
                policy['summary'] = self.generate_summary(policy)

        # 批量写入
        result = self.bitable_writer.write_policies(all_policies)
        logger.info(f"Bitable写入完成: 成功 {result['success']}, 失败 {result['failed']}")

        return result

    def _send_to_feishu(self, content: str) -> bool:
        """推送到飞书群机器人"""
        webhook = self.targets.get('feishu', {}).get('webhook', '')
        if not webhook:
            logger.error("飞书Webhook未配置")
            return False

        # 飞书支持markdown
        payload = {
            'msg_type': 'interactive',
            'card': {
                'header': {
                    'title': {
                        'tag': 'plain_text',
                        'content': '政策追踪日报'
                    },
                    'template': 'blue'
                },
                'elements': [
                    {
                        'tag': 'markdown',
                        'content': content[:30000]  # 飞书卡片有大小限制
                    }
                ]
            }
        }

        try:
            response = requests.post(webhook, json=payload, timeout=10)
            result = response.json()

            if result.get('code') == 0:
                logger.info("飞书推送成功")
                return True
            else:
                logger.error(f"飞书推送失败: {result}")
                return False

        except Exception as e:
            logger.error(f"飞书推送异常: {e}")
            return False

    def _send_to_dingding(self, content: str) -> bool:
        """推送到钉钉群机器人"""
        webhook = self.targets.get('dingding', {}).get('webhook', '')
        if not webhook:
            logger.error("钉钉Webhook未配置")
            return False

        # 钉钉支持markdown
        payload = {
            'msgtype': 'markdown',
            'markdown': {
                'title': '政策追踪日报',
                'text': content[:30000]
            }
        }

        try:
            response = requests.post(webhook, json=payload, timeout=10)
            result = response.json()

            if result.get('errcode') == 0:
                logger.info("钉钉推送成功")
                return True
            else:
                logger.error(f"钉钉推送失败: {result}")
                return False

        except Exception as e:
            logger.error(f"钉钉推送异常: {e}")
            return False

    def _send_to_email(self, content: str) -> bool:
        """发送邮件"""
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header

        email_config = self.targets.get('email', {})
        smtp_server = email_config.get('smtp', '')
        smtp_port = email_config.get('port', 465)
        use_ssl = email_config.get('use_ssl', True)
        username = email_config.get('username', '')
        password = email_config.get('password', '')
        from_addr = email_config.get('from', username)
        to_addrs = email_config.get('to', [])

        if not smtp_server or not to_addrs:
            logger.error("邮件配置不完整")
            return False

        # 构建邮件
        msg = MIMEText(content, 'markdown', 'utf-8')
        msg['Subject'] = Header('政策追踪日报', 'utf-8')
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs)

        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()

            server.login(username, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
            server.quit()

            logger.info("邮件发送成功")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def send_summary(self, stats: dict) -> bool:
        """发送执行摘要到运维群"""
        if not self.ops_config.get('summary_enabled', True):
            return False

        webhook = self.ops_config.get('summary_webhook', '')
        if not webhook:
            return False

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        content = f"""**政策追踪任务执行摘要**

- 时间：{now}
- 总数据源：{stats.get('total_sources', 0)}
- 成功：{stats.get('success_sources', 0)} | 失败：{stats.get('failed_sources', 0)}
- 采集条目：{stats.get('total_items', 0)} 条
- 命中AI关键词：{stats.get('ai_count', 0)} 条
- 命中数据关键词：{stats.get('data_count', 0)} 条
- LLM调用：{self.llm_usage.get('calls', 0)} 次，费用 {self.llm_usage.get('total_cost', 0):.4f} 元"""

        payload = {
            'msg_type': 'interactive',
            'card': {
                'header': {
                    'title': {
                        'tag': 'plain_text',
                        'content': '政策追踪任务完成'
                    },
                    'template': 'green' if stats.get('failed_sources', 0) == 0 else 'red'
                },
                'elements': [
                    {
                        'tag': 'markdown',
                        'content': content
                    }
                ]
            }
        }

        try:
            response = requests.post(webhook, json=payload, timeout=10)
            return response.json().get('code') == 0
        except Exception:
            return False