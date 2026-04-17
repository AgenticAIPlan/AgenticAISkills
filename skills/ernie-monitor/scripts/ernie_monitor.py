#!/usr/bin/env python3
"""
文心大模型全网监测脚本

用法:
    python3 ernie_monitor.py --period week --output report.md
    python3 ernie_monitor.py --start 2024-04-10 --end 2024-04-17 --output report.md
    python3 ernie_monitor.py --module kol --export-csv
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import pandas as pd
from collections import Counter


class ErnieMonitor:
    """文心大模型监测主类"""

    def __init__(self, config: Optional[Dict] = None):
        """初始化监测器

        Args:
            config: 配置字典，包含API密钥、监测参数等
        """
        self.config = config or {}
        self.keywords = self._load_keywords()
        self.platforms = self._load_platforms()

    def _load_keywords(self) -> Dict[str, List[str]]:
        """加载监测关键词"""
        return {
            "core": [
                "文心大模型", "ERNIE", "文心一言", "百度大模型", "文心",
                "文心4.0", "ERNIE 4.0", "文心4T", "文心Speed", "文心Lite",
                "文心文生图", "文心一格", "文心百中",
                "文心代码", "Comate", "文心开发者平台"
            ],
            "extended": [
                "百度AI", "百度大模型发布",
                "文心大模型评测", "文心大模型对比", "文心大模型体验",
                "文心大模型问题", "文心大模型bug", "文心大模型故障"
            ],
            "competitor": [
                "GPT", "ChatGPT", "Claude", "通义千问", "讯飞星火", "智谱", "月之暗面",
                "Kimi", "DeepSeek", "Minimax", "混元",
                "Sora", "DALL-E", "Midjourney",
                "AutoGPT", "Agent", "世界模型"
            ]
        }

    def _load_platforms(self) -> Dict[str, Dict]:
        """加载平台配置"""
        return {
            "wechat": {
                "name": "微信公众号",
                "search_url": "https://mp.weixin.qq.com/cgi-bin/search",
                "api_available": True,
                "priority": "high"
            },
            "weibo": {
                "name": "微博",
                "search_url": "https://s.weibo.com/weibo",
                "api_available": True,
                "priority": "high"
            },
            "xiaohongshu": {
                "name": "小红书",
                "search_url": "https://www.xiaohongshu.com/search_result",
                "api_available": False,
                "priority": "medium"
            },
            "bilibili": {
                "name": "B站",
                "search_url": "https://search.bilibili.com/all",
                "api_available": True,
                "priority": "medium"
            },
            "douyin": {
                "name": "抖音",
                "search_url": "https://www.douyin.com/search",
                "api_available": False,
                "priority": "high"
            },
            "zhihu": {
                "name": "知乎",
                "search_url": "https://www.zhihu.com/search",
                "api_available": True,
                "priority": "medium"
            },
            "ai_community": {
                "name": "AI社区",
                "sources": ["Hugging Face", "GitHub", "Reddit", "Discord"],
                "api_available": True,
                "priority": "medium"
            },
            "media": {
                "name": "媒体网站",
                "sources": ["36氪", "虎嗅", "机器之心", "量子位", "钛媒体"],
                "api_available": True,
                "priority": "high"
            }
        }

    def collect_content(self, platforms: List[str], keywords: List[str],
                       start_date: str, end_date: str) -> List[Dict]:
        """收集内容

        Args:
            platforms: 平台列表
            keywords: 关键词列表
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            内容列表
        """
        content_list = []

        for platform in platforms:
            if platform not in self.platforms:
                print(f"警告: 未知平台 {platform}")
                continue

            platform_config = self.platforms[platform]
            print(f"正在收集 {platform_config['name']} 内容...")

            # 这里应该是实际的数据收集逻辑
            # 由于需要API密钥和具体实现，这里返回模拟数据
            platform_content = self._collect_from_platform(
                platform, keywords, start_date, end_date
            )
            content_list.extend(platform_content)

        return content_list

    def _collect_from_platform(self, platform: str, keywords: List[str],
                              start_date: str, end_date: str) -> List[Dict]:
        """从单个平台收集内容（模拟实现）"""
        # 实际实现需要调用各平台API或使用爬虫
        # 这里返回模拟数据
        return [
            {
                "platform": platform,
                "title": f"关于文心大模型的深度分析",
                "author": "AI观察者",
                "publish_time": datetime.now().strftime("%Y-%m-%d"),
                "content": "文心大模型在中文理解方面具有天然优势...",
                "url": f"https://example.com/article/{hash(platform)}",
                "likes": 1000,
                "comments": 200,
                "shares": 50,
                "views": 10000
            }
        ]

    def deduplicate_content(self, content_list: List[Dict]) -> List[Dict]:
        """内容去重

        Args:
            content_list: 原始内容列表

        Returns:
            去重后的内容列表
        """
        seen_urls = set()
        seen_titles = {}

        deduplicated = []

        for content in content_list:
            url = content.get("url", "")
            title = content.get("title", "")

            # URL去重
            if url in seen_urls:
                continue

            # 标题去重（简单相似度）
            title_similar = False
            for seen_title in seen_titles:
                if self._title_similarity(title, seen_title) > 0.9:
                    title_similar = True
                    break

            if not title_similar:
                seen_urls.add(url)
                seen_titles[title] = True
                deduplicated.append(content)

        return deduplicated

    def _title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        set1 = set(title1)
        set2 = set(title2)
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union) if union else 0

    def classify_content(self, content_list: List[Dict]) -> List[Dict]:
        """内容分类

        Args:
            content_list: 内容列表

        Returns:
            分类后的内容列表
        """
        categories = {
            "product_release": ["发布", "更新", "版本", "上线", "新功能"],
            "user_experience": ["体验", "使用", "评测", "测试", "感受"],
            "technical_analysis": ["技术", "分析", "性能", "对比", "评测"],
            "industry_view": ["观点", "行业", "分析", "趋势", "展望"],
            "controversy": ["争议", "问题", "bug", "故障", "质疑"],
            "tutorial": ["教程", "指南", "技巧", "方法", "如何"],
            "competitor": ["友商", "竞争", "对比", "vs", "GPT", "Claude"]
        }

        for content in content_list:
            title = content.get("title", "")
            content_text = content.get("content", "")
            full_text = f"{title} {content_text}"

            # 简单的关键词匹配分类
            max_score = 0
            best_category = "other"

            for category, keywords in categories.items():
                score = sum(1 for kw in keywords if kw in full_text)
                if score > max_score:
                    max_score = score
                    best_category = category

            content["category"] = best_category

        return content_list

    def analyze_sentiment(self, content_list: List[Dict]) -> Dict:
        """情感分析

        Args:
            content_list: 内容列表

        Returns:
            情感分析结果
        """
        # 情感词典（简化版）
        positive_words = [
            "好", "棒", "优秀", "出色", "厉害", "强", "赞", "推荐",
            "喜欢", "满意", "惊喜", "超越", "领先", "先进", "创新",
            "稳定", "流畅", "快速", "准确", "智能", "强大"
        ]

        negative_words = [
            "差", "弱", "不好", "糟糕", "失望", "问题", "bug", "故障",
            "慢", "卡顿", "不准确", "错误", "落后", "不如", "差劲",
            "质疑", "批评", "吐槽", "抱怨", "不满"
        ]

        sentiment_stats = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "mixed": 0,
            "positive_examples": [],
            "negative_examples": [],
            "details": []
        }

        for content in content_list:
            title = content.get("title", "")
            content_text = content.get("content", "")
            full_text = f"{title} {content_text}"

            positive_count = sum(1 for word in positive_words if word in full_text)
            negative_count = sum(1 for word in negative_words if word in full_text)

            # 简单的情感判断
            if positive_count > 0 and negative_count > 0:
                sentiment = "mixed"
            elif positive_count > 0:
                sentiment = "positive"
            elif negative_count > 0:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            sentiment_stats[sentiment] += 1
            content["sentiment"] = sentiment

            # 收集示例
            if sentiment == "positive" and len(sentiment_stats["positive_examples"]) < 5:
                sentiment_stats["positive_examples"].append({
                    "title": title,
                    "author": content.get("author", ""),
                    "platform": content.get("platform", ""),
                    "reason": self._extract_reason(full_text, positive_words)
                })

            if sentiment == "negative" and len(sentiment_stats["negative_examples"]) < 5:
                sentiment_stats["negative_examples"].append({
                    "title": title,
                    "author": content.get("author", ""),
                    "platform": content.get("platform", ""),
                    "reason": self._extract_reason(full_text, negative_words)
                })

            sentiment_stats["details"].append({
                "url": content.get("url", ""),
                "sentiment": sentiment,
                "positive_score": positive_count,
                "negative_score": negative_count
            })

        return sentiment_stats

    def _extract_reason(self, text: str, words: List[str]) -> str:
        """提取情感原因"""
        for word in words:
            if word in text:
                # 找到包含该词的句子
                sentences = text.split("。")
                for sentence in sentences:
                    if word in sentence:
                        return sentence.strip()
        return "未提取到具体原因"

    def identify_kol(self, content_list: List[Dict]) -> Dict[str, List[Dict]]:
        """识别KOL

        Args:
            content_list: 内容列表

        Returns:
            分层的KOL列表
        """
        # 统计每个作者的内容和互动
        author_stats = {}

        for content in content_list:
            author = content.get("author", "")
            platform = content.get("platform", "")

            key = f"{author}@{platform}"

            if key not in author_stats:
                author_stats[key] = {
                    "name": author,
                    "platform": platform,
                    "content_count": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0,
                    "total_views": 0,
                    "sentiment_scores": []
                }

            author_stats[key]["content_count"] += 1
            author_stats[key]["total_likes"] += content.get("likes", 0)
            author_stats[key]["total_comments"] += content.get("comments", 0)
            author_stats[key]["total_shares"] += content.get("shares", 0)
            author_stats[key]["total_views"] += content.get("views", 0)

            # 情感评分（简化）
            sentiment = content.get("sentiment", "neutral")
            sentiment_score = {"positive": 1, "neutral": 0, "negative": -1, "mixed": 0}.get(sentiment, 0)
            author_stats[key]["sentiment_scores"].append(sentiment_score)

        # 计算平均情感分
        for key, stats in author_stats.items():
            if stats["sentiment_scores"]:
                stats["avg_sentiment"] = sum(stats["sentiment_scores"]) / len(stats["sentiment_scores"])
            else:
                stats["avg_sentiment"] = 0

            # 计算综合互动分
            stats["engagement_score"] = (
                stats["total_likes"] * 1 +
                stats["total_comments"] * 5 +
                stats["total_shares"] * 10 +
                stats["total_views"] * 0.01
            )

        # 分层
        kols = {
            "S": [],  # 顶级KOL
            "A": [],  # 核心KOL
            "B": [],  # 潜力KOL
            "C": []   # 友好用户
        }

        for key, stats in author_stats.items():
            # 分层逻辑
            if stats["engagement_score"] > 10000 and stats["avg_sentiment"] > 0.5:
                tier = "S"
            elif stats["engagement_score"] > 1000 and stats["avg_sentiment"] > 0.3:
                tier = "A"
            elif stats["engagement_score"] > 100 and stats["avg_sentiment"] > 0:
                tier = "B"
            elif stats["avg_sentiment"] > 0.3:
                tier = "C"
            else:
                continue

            kols[tier].append(stats)

        return kols

    def monitor_competitors(self, keywords: List[str], start_date: str, end_date: str) -> Dict:
        """监测友商动态

        Args:
            keywords: 友商关键词
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            友商动态报告
        """
        # 重点友商列表
        competitors = {
            "OpenAI": ["GPT", "ChatGPT", "Sora", "DALL-E"],
            "Anthropic": ["Claude"],
            "Google": ["Gemini", "Bard"],
            "阿里": ["通义千问"],
            "腾讯": ["混元"],
            "讯飞": ["星火"],
            "智谱": ["GLM"],
            "月之暗面": ["Kimi"],
            "DeepSeek": ["DeepSeek"],
            "Minimax": ["Minimax"]
        }

        competitor_news = {}

        for competitor, comp_keywords in competitors.items():
            # 收集该友商的相关内容
            relevant_keywords = [kw for kw in keywords if any(k in kw for k in comp_keywords)]

            if relevant_keywords:
                competitor_news[competitor] = {
                    "keywords": comp_keywords,
                    "mentions": len(relevant_keywords),
                    "recent_updates": self._get_competitor_updates(competitor, start_date, end_date),
                    "risk_level": self._assess_competitor_risk(competitor)
                }

        return competitor_news

    def _get_competitor_updates(self, competitor: str, start_date: str, end_date: str) -> List[Dict]:
        """获取友商更新（模拟）"""
        # 实际实现需要调用相关API或爬取官网
        return [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "title": f"{competitor}发布新功能",
                "description": "具体描述...",
                "impact": "medium"
            }
        ]

    def _assess_competitor_risk(self, competitor: str) -> str:
        """评估友商风险等级"""
        risk_mapping = {
            "OpenAI": "high",
            "Anthropic": "high",
            "Google": "high",
            "阿里": "medium",
            "腾讯": "medium",
            "智谱": "medium",
            "月之暗面": "medium",
            "讯飞": "low",
            "DeepSeek": "low",
            "Minimax": "low"
        }
        return risk_mapping.get(competitor, "low")

    def assess_risks(self, content_list: List[Dict]) -> List[Dict]:
        """评估风险

        Args:
            content_list: 内容列表

        Returns:
            风险列表
        """
        risks = []

        # 识别高风险内容
        for content in content_list:
            if content.get("sentiment") == "negative":
                engagement = (
                    content.get("likes", 0) +
                    content.get("comments", 0) * 5 +
                    content.get("shares", 0) * 10
                )

                if engagement > 500:  # 高互动的负面内容
                    risks.append({
                        "id": f"R{len(risks)+1:03d}",
                        "type": "舆情风险",
                        "description": content.get("title", ""),
                        "platform": content.get("platform", ""),
                        "author": content.get("author", ""),
                        "engagement": engagement,
                        "url": content.get("url", ""),
                        "level": "high" if engagement > 2000 else "medium",
                        "status": "待处理"
                    })

        # 添加产品缺陷风险
        technical_issues = [
            content for content in content_list
            if any(kw in content.get("content", "") for kw in ["bug", "故障", "崩溃", "错误"])
        ]

        if technical_issues:
            risks.append({
                "id": f"R{len(risks)+1:03d}",
                "type": "产品缺陷",
                "description": f"检测到{len(technical_issues)}条技术问题反馈",
                "count": len(technical_issues),
                "level": "high" if len(technical_issues) > 10 else "medium",
                "status": "待分析"
            })

        return risks

    def generate_report(self, data: Dict, output_format: str = "markdown") -> str:
        """生成报告

        Args:
            data: 监测数据
            output_format: 输出格式 (markdown, json, csv)

        Returns:
            报告内容
        """
        if output_format == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif output_format == "csv":
            return self._generate_csv(data)
        else:
            return self._generate_markdown(data)

    def _generate_markdown(self, data: Dict) -> str:
        """生成Markdown格式报告"""
        lines = []
        lines.append("# 文心大模型全网监测报告\n")

        # 监测总览
        lines.append("## 一、监测总览\n")
        lines.append(f"**监测时间**：{data.get('start_date', '')} 至 {data.get('end_date', '')}")
        lines.append(f"**监测平台**：{', '.join(data.get('platforms', []))}")
        lines.append(f"**收集内容数**：{data.get('total_content', 0)}条")
        lines.append(f"**去重后内容数**：{data.get('deduplicated_content', 0)}条\n")

        # 情感分析
        sentiment = data.get("sentiment", {})
        lines.append("## 二、情感分析\n")
        lines.append(f"- 正向：{sentiment.get('positive', 0)}条")
        lines.append(f"- 负向：{sentiment.get('negative', 0)}条")
        lines.append(f"- 中性：{sentiment.get('neutral', 0)}条")
        lines.append(f"- 混合：{sentiment.get('mixed', 0)}条\n")

        # KOL信息
        kols = data.get("kols", {})
        lines.append("## 三、KOL识别\n")
        lines.append(f"- S级（顶级KOL）：{len(kols.get('S', []))}人")
        lines.append(f"- A级（核心KOL）：{len(kols.get('A', []))}人")
        lines.append(f"- B级（潜力KOL）：{len(kols.get('B', []))}人")
        lines.append(f"- C级（友好用户）：{len(kols.get('C', []))}人\n")

        # 风险预警
        risks = data.get("risks", [])
        lines.append("## 四、风险预警\n")
        if risks:
            for risk in risks[:5]:  # 只显示前5个
                lines.append(f"- **{risk.get('id', '')}** [{risk.get('level', '').upper()}] {risk.get('type', '')}: {risk.get('description', '')}")
        else:
            lines.append("- 当前无显著风险")
        lines.append("")

        # 友商动态
        competitors = data.get("competitors", {})
        lines.append("## 五、友商动态\n")
        for competitor, info in competitors.items():
            lines.append(f"- **{competitor}**: {info.get('mentions', 0)}条提及，风险等级：{info.get('risk_level', '').upper()}")
        lines.append("")

        return "\n".join(lines)

    def _generate_csv(self, data: Dict) -> str:
        """生成CSV格式报告"""
        # 将情感分析详情转换为CSV
        details = data.get("sentiment", {}).get("details", [])

        if not details:
            return "URL,Sentiment,Positive Score,Negative Score\n"

        lines = ["URL,Sentiment,Positive Score,Negative Score"]
        for detail in details:
            lines.append(f"{detail.get('url', '')},{detail.get('sentiment', '')},{detail.get('positive_score', 0)},{detail.get('negative_score', 0)}")

        return "\n".join(lines)

    def run(self, args):
        """执行监测

        Args:
            args: 命令行参数
        """
        # 确定时间范围
        if args.period:
            end_date = datetime.now()
            if args.period == "day":
                start_date = end_date - timedelta(days=1)
            elif args.period == "week":
                start_date = end_date - timedelta(weeks=1)
            elif args.period == "month":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(args.start, "%Y-%m-%d")
            end_date = datetime.strptime(args.end, "%Y-%m-%d")

        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        print(f"文心大模型全网监测启动")
        print(f"时间范围: {start_date_str} 至 {end_date_str}")
        print(f"监测模块: {args.module or '全部'}")

        # 确定监测平台
        if args.platforms:
            platforms = args.platforms.split(",")
        else:
            platforms = list(self.platforms.keys())

        # 合并关键词
        all_keywords = self.keywords["core"] + self.keywords["extended"]
        if args.topic:
            all_keywords.extend([args.topic])

        # 执行监测
        results = {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "platforms": platforms,
            "keywords": all_keywords,
            "total_content": 0,
            "deduplicated_content": 0,
            "sentiment": {},
            "kols": {},
            "risks": [],
            "competitors": {}
        }

        # 根据模块执行不同任务
        if args.module in [None, "content", "all"]:
            print("\n[1/5] 收集内容...")
            content_list = self.collect_content(platforms, all_keywords, start_date_str, end_date_str)
            results["total_content"] = len(content_list)

            print(f"[2/5] 去重处理...")
            content_list = self.deduplicate_content(content_list)
            results["deduplicated_content"] = len(content_list)

            print(f"[3/5] 内容分类...")
            content_list = self.classify_content(content_list)

            print(f"[4/5] 情感分析...")
            results["sentiment"] = self.analyze_sentiment(content_list)

            print(f"[5/5] 风险评估...")
            results["risks"] = self.assess_risks(content_list)

        if args.module in [None, "kol", "all"]:
            if "content_list" not in locals():
                content_list = self.collect_content(platforms, all_keywords, start_date_str, end_date_str)
                content_list = self.deduplicate_content(content_list)
            print("\n识别KOL...")
            results["kols"] = self.identify_kol(content_list)

        if args.module in [None, "competitor", "all"]:
            print("\n监测友商...")
            results["competitors"] = self.monitor_competitors(
                self.keywords["competitor"], start_date_str, end_date_str
            )

        # 生成报告
        output_format = "json" if args.export_json else ("csv" if args.export_csv else "markdown")
        report = self.generate_report(results, output_format)

        # 输出
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n报告已生成: {args.output}")
        else:
            print("\n" + "="*50)
            print(report)
            print("="*50)

        # 风险预警
        high_risks = [r for r in results.get("risks", []) if r.get("level") == "high"]
        if high_risks and args.alert:
            print(f"\n⚠️  检测到 {len(high_risks)} 个高风险内容，需要立即关注！")
            for risk in high_risks:
                print(f"  - [{risk.get('id')}] {risk.get('description')[:50]}...")

        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="文心大模型全网监测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  生成周报:
    python3 ernie_monitor.py --period week --output report.md

  自定义时间范围:
    python3 ernie_monitor.py --start 2024-04-10 --end 2024-04-17 --output report.md

  只生成KOL报告:
    python3 ernie_monitor.py --module kol --output kol_report.md

  导出CSV格式:
    python3 ernie_monitor.py --export-csv --output data.csv

  风险预警:
    python3 ernie_monitor.py --period day --risk-level high --alert
        """
    )

    parser.add_argument(
        "--period",
        choices=["day", "week", "month"],
        help="监测周期（day/week/month）"
    )
    parser.add_argument("--start", help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--platforms", help="监测平台，逗号分隔（如: wechat,weibo,zhihu）")
    parser.add_argument("--topic", help="专项监测主题")
    parser.add_argument("--module", choices=["content", "kol", "competitor", "all"], help="监测模块")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--export-json", action="store_true", help="导出为JSON格式")
    parser.add_argument("--export-csv", action="store_true", help="导出为CSV格式")
    parser.add_argument("--risk-level", choices=["high", "medium", "low"], help="风险等级筛选")
    parser.add_argument("--alert", action="store_true", help="启用风险预警")

    args = parser.parse_args()

    # 验证参数
    if not args.period and not (args.start and args.end):
        parser.error("必须指定 --period 或同时指定 --start 和 --end")

    # 创建监测器并运行
    monitor = ErnieMonitor()
    monitor.run(args)


if __name__ == "__main__":
    main()
