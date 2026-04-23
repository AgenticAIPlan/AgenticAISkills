#!/usr/bin/env python3
"""AI 硬件生态监测与分析脚本。

能力包括：
- 生成 AI 硬件生态监测计划
- 读取 JSON / JSONL / CSV 格式的已采集记录
- 识别产业链环节、主题、模型厂商、竞品与风险
- 输出关键新闻、上下游动态、模型厂商动态、风险与 KOL 分析
- 支持模块化执行与风险预警
- Markdown / JSON / CSV 报告输出
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

LEVEL_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
IMPACT_RANK = {"low": 0, "medium": 1, "high": 2}


def safe_int(value) -> int:
    if value in (None, "", "null"):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def normalize_title_key(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]", "", text)
    return text


def parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    value = str(value).strip()
    patterns = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    ]
    for pattern in patterns:
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_list(raw: str) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        text = normalize_space(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def level_meets(level: str, minimum: str) -> bool:
    return LEVEL_RANK[level.lower()] >= LEVEL_RANK[minimum.lower()]


def json_default(obj):
    if isinstance(obj, Counter):
        return dict(obj)
    return str(obj)


class AIHardwareEcosystemMonitor:
    def __init__(
        self,
        brand: str = "",
        products: Optional[List[str]] = None,
        competitors: Optional[List[str]] = None,
        model_vendors: Optional[List[str]] = None,
    ):
        self.brand = brand or "未指定"
        self.products = [item.strip() for item in (products or []) if item.strip()]
        self.competitors = [item.strip() for item in (competitors or []) if item.strip()]
        self.model_vendors = [item.strip() for item in (model_vendors or []) if item.strip()] or [
            "OpenAI", "Anthropic", "Google", "Meta", "xAI", "DeepSeek", "阿里", "百度", "腾讯", "字节", "智谱"
        ]
        self.platforms = self._load_platforms()

        self.default_keyword_groups = {
            "upstream": [
                "HBM", "DRAM", "wafer", "CoWoS", "substrate", "yield", "封装", "良率", "光模块", "电源", "散热",
            ],
            "midstream": [
                "GPU", "NPU", "ASIC", "accelerator", "server", "rack", "liquid cooling", "interconnect", "NIC", "switch",
            ],
            "downstream": [
                "cloud", "datacenter", "cluster", "training", "inference", "deployment", "enterprise", "capex",
            ],
            "risk": [
                "缺货", "跳票", "断供", "制裁", "出口管制", "兼容问题", "价格波动", "砍单", "过热", "召回",
            ],
        }

        self.topic_keywords = {
            "product_release": ["发布", "发布会", "launch", "roadmap", "路线图", "sample", "tape-out"],
            "upstream_supply": ["HBM", "CoWoS", "wafer", "yield", "良率", "封装", "substrate", "memory", "capacity"],
            "compute_infrastructure": ["server", "rack", "cluster", "liquid cooling", "switch", "NIC", "datacenter", "机柜", "液冷"],
            "model_vendor_strategy": ["model vendor", "OpenAI", "Anthropic", "DeepSeek", "模型", "训练", "推理", "部署"],
            "cloud_deployment": ["cloud", "AWS", "Azure", "GCP", "阿里云", "集群", "上架", "deployment", "service"],
            "price_capacity": ["price", "pricing", "报价", "capex", "lead time", "交付", "库存", "溢价"],
            "partnership_ecosystem": ["合作", "伙伴", "认证", "case study", "案例", "adoption", "migration"],
            "software_stack": ["driver", "SDK", "firmware", "CUDA", "ROCm", "toolkit", "compatibility", "部署工具"],
            "policy_compliance": ["sanction", "export control", "合规", "监管", "restriction", "禁售", "制裁"],
            "technical_issue": ["bug", "crash", "overheat", "黑屏", "蓝屏", "兼容问题", "故障", "召回"],
            "competitor_watch": ["versus", "vs", "替代", "竞品", "竞争", "抢量", "better than"],
        }

        self.layer_keywords = {
            "upstream": ["HBM", "DRAM", "wafer", "CoWoS", "substrate", "封装", "良率", "光模块", "电源", "散热"],
            "midstream": ["GPU", "NPU", "ASIC", "server", "rack", "liquid cooling", "NIC", "switch", "board", "加速卡"],
            "downstream": ["cloud", "datacenter", "enterprise", "deployment", "cluster", "inference", "training", "集群", "数据中心"],
            "model_vendor": self.model_vendors,
            "external": ["policy", "制裁", "export control", "融资", "并购", "监管", "capital", "capex"],
        }

        self.positive_words = [
            "扩产", "改善", "恢复", "stable", "improved", "expands", "launch", "available", "认证完成", "部署提速",
            "供给改善", "良率提升", "合作扩大", "成本下降", "交付恢复", "生态扩张",
        ]
        self.negative_words = [
            "缺货", "跳票", "断供", "制裁", "禁售", "delay", "shortage", "overheat", "崩溃", "compatibility issue",
            "兼容问题", "价格上涨", "砍单", "召回", "bug", "export control", "restriction",
        ]
        self.risk_keywords = {
            "供应链风险": ["缺货", "跳票", "断供", "HBM 紧张", "lead time", "交付延期", "良率"],
            "技术栈风险": ["driver", "SDK", "compatibility", "兼容问题", "部署失败", "firmware", "toolkit"],
            "价格与资本开支风险": ["price", "报价", "溢价", "capex", "资本开支", "成本", "砍单"],
            "合规与政策风险": ["制裁", "export control", "监管", "restriction", "禁售", "合规"],
            "生态协同风险": ["合作受阻", "迁移", "替代", "伙伴流失", "route change", "切换"],
            "竞品冲击风险": ["领先", "替代", "抢量", "better than", "竞争"],
            "质量与稳定性风险": ["overheat", "崩溃", "故障", "召回", "返修", "部署事故"],
            "传闻误导风险": ["据传", "未证实", "rumor", "leak", "爆料"],
        }
        self.role_keywords = {
            "行业媒体": ["media", "editor", "记者", "tom's", "anandtech", "semianalysis", "semi analysis", "desk"],
            "分析师 / 研究机构": ["analyst", "research", "advisor", "consulting", "研报"],
            "工程师 / 技术专家": ["engineer", "developer", "maintainer", "kernel", "driver", "sdk"],
            "渠道 / 集成商 / ODM": ["channel", "integrator", "odm", "oem", "分销", "经销"],
            "云厂商 / 企业客户": ["cloud", "infra", "enterprise", "采购", "datacenter", "it team"],
            "模型厂商 / AI 实验室": self.model_vendors + ["model vendor", "ai lab", "research lab", "模型"],
        }

    def _load_platforms(self) -> Dict[str, Dict]:
        return {
            "industry_media": {"name": "行业媒体 / 科技媒体", "priority": "high", "route": "web-research", "notes": "新品、路线图、结构变化"},
            "official_sites": {"name": "厂商官网 / 伙伴页面", "priority": "high", "route": "web-research / chrome-devtools", "notes": "新闻稿、案例、认证、交付"},
            "model_vendor_sites": {"name": "模型厂商 / 云厂商公告", "priority": "high", "route": "web-research / chrome-devtools", "notes": "采购、部署、服务、合作"},
            "reddit": {"name": "Reddit", "priority": "high", "route": "web-research", "notes": "国际社区讨论和部署反馈"},
            "github": {"name": "GitHub Issues / Releases", "priority": "high", "route": "web-research / chrome-devtools", "notes": "SDK、驱动、兼容和开源生态"},
            "hackernews": {"name": "Hacker News", "priority": "medium", "route": "web-research", "notes": "行业观察和技术讨论"},
            "weibo": {"name": "微博", "priority": "medium", "route": "daily-hot-news / web-research", "notes": "热点扩散、行业舆论"},
            "x": {"name": "X / LinkedIn", "priority": "medium", "route": "web-research", "notes": "国际机构和高管动态"},
            "xiaohongshu": {"name": "小红书", "priority": "low", "route": "xiaohongshu", "notes": "消费级 AI 硬件和装机体验"},
            "bilibili": {"name": "B站", "priority": "low", "route": "daily-hot-news / web-research", "notes": "视频评测和拆机"},
            "douyin": {"name": "抖音", "priority": "low", "route": "daily-hot-news / playwright-mcp", "notes": "短视频热点"},
            "zhihu": {"name": "知乎", "priority": "low", "route": "daily-hot-news / web-research", "notes": "问答、专栏和专业讨论"},
            "wechat": {"name": "微信公众号", "priority": "medium", "route": "wechat-article-to-markdown", "notes": "厂商、渠道与行业媒体文章"},
            "finance_policy": {"name": "财报 / 政策 / 监管站点", "priority": "high", "route": "web-research", "notes": "资本开支、政策和监管变化"},
        }

    def resolve_time_range(self, args) -> Tuple[str, str]:
        if args.period:
            end_dt = datetime.now()
            if args.period == "day":
                start_dt = end_dt - timedelta(days=1)
            elif args.period == "week":
                start_dt = end_dt - timedelta(days=7)
            else:
                start_dt = end_dt - timedelta(days=30)
            return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")
        return args.start or "", args.end or ""

    def selected_platforms(self, raw_platforms: Optional[List[str]]) -> List[str]:
        if not raw_platforms:
            return list(self.platforms.keys())
        selected = []
        for item in raw_platforms:
            key = item.strip()
            if key in self.platforms:
                selected.append(key)
        return selected or list(self.platforms.keys())

    def build_keyword_groups(self, topic: str = "") -> Dict[str, List[str]]:
        core = dedupe_keep_order([self.brand] + self.products)
        upstream = dedupe_keep_order(self.default_keyword_groups["upstream"])
        midstream = dedupe_keep_order(self.default_keyword_groups["midstream"])
        downstream = dedupe_keep_order(self.default_keyword_groups["downstream"])
        model_vendors = dedupe_keep_order(self.model_vendors)
        competitors = dedupe_keep_order(self.competitors)
        risk = dedupe_keep_order(([topic] if topic else []) + self.default_keyword_groups["risk"])
        return {
            "core": core,
            "upstream": upstream,
            "midstream": midstream,
            "downstream": downstream,
            "model_vendor": model_vendors,
            "competitor": competitors,
            "risk": risk,
        }

    def build_collection_plan(self, start_date: str, end_date: str, platforms: List[str], topic: str, module: str) -> Dict:
        keyword_groups = self.build_keyword_groups(topic)
        platform_details = []
        for key in platforms:
            cfg = self.platforms.get(key)
            if not cfg:
                continue
            platform_details.append({
                "key": key,
                "name": cfg["name"],
                "priority": cfg["priority"],
                "route": cfg["route"],
                "notes": cfg["notes"],
            })
        return {
            "brand": self.brand,
            "products": self.products,
            "competitors": self.competitors,
            "model_vendors": self.model_vendors,
            "topic": topic,
            "module": module,
            "start_date": start_date,
            "end_date": end_date,
            "platforms": platform_details,
            "keyword_groups": keyword_groups,
        }

    def generate_plan_markdown(self, plan: Dict) -> str:
        lines = []
        lines.append("# AI 硬件生态监测计划")
        lines.append("")
        lines.append(f"- 监测主体：{plan['brand']}")
        lines.append(f"- 重点产品 / 对象：{', '.join(plan['products']) if plan['products'] else '未指定'}")
        lines.append(f"- 竞品：{', '.join(plan['competitors']) if plan['competitors'] else '未指定'}")
        lines.append(f"- 模型厂商：{', '.join(plan['model_vendors']) if plan['model_vendors'] else '未指定'}")
        lines.append(f"- 专项主题：{plan['topic'] or '未指定'}")
        lines.append(f"- 执行模块：{plan['module']}")
        lines.append(f"- 时间范围：{plan['start_date'] or '未限制'} 至 {plan['end_date'] or '未限制'}")
        lines.append("")
        lines.append("## 一、关键词包")
        lines.append("")
        labels = {
            "core": "核心词",
            "upstream": "上游词",
            "midstream": "中游词",
            "downstream": "下游词",
            "model_vendor": "模型厂商词",
            "competitor": "竞品词",
            "risk": "风险词",
        }
        for key in ["core", "upstream", "midstream", "downstream", "model_vendor", "competitor", "risk"]:
            value = plan["keyword_groups"].get(key, [])
            lines.append(f"- **{labels[key]}**：{', '.join(value) if value else '无'}")
        lines.append("")
        lines.append("## 二、平台优先级与采集路由")
        lines.append("")
        lines.append("| 平台 | 优先级 | 建议路由 | 备注 |")
        lines.append("|------|--------|----------|------|")
        for item in plan["platforms"]:
            lines.append(f"| {item['name']} | {item['priority']} | {item['route']} | {item['notes']} |")
        lines.append("")
        lines.append("## 三、执行提示")
        lines.append("")
        lines.append("1. 至少覆盖行业媒体、官方页面、社区和模型厂商 / 云厂商信息源四类来源。")
        lines.append("2. 对供给、交付、价格、capex 和合作信息标明核验状态。")
        lines.append("3. 对高风险样本保留原始链接、时间、机构、关键引用和二次来源链路。")
        return "\n".join(lines)

    def load_records(self, path: str) -> List[Dict]:
        suffix = os.path.splitext(path)[1].lower()
        if suffix == ".json":
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            records = payload.get("records", []) if isinstance(payload, dict) else payload
        elif suffix == ".jsonl":
            records = []
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        elif suffix == ".csv":
            with open(path, "r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                records = list(reader)
        else:
            raise ValueError("仅支持 .json / .jsonl / .csv 输入")
        return [self.normalize_record(item) for item in records]

    def normalize_record(self, record: Dict) -> Dict:
        alias_map = {
            "published_at": ["published_at", "publish_time", "date", "time", "created_at"],
            "author": ["author", "user", "username", "media", "publisher", "institution"],
            "followers": ["followers", "fans", "fans_count", "subscribers"],
            "views": ["views", "read_count", "plays", "impressions"],
            "source_type": ["source_type", "type"],
            "entity_layer": ["entity_layer", "layer"],
            "company_type": ["company_type", "org_type"],
            "component_type": ["component_type", "component"],
            "model_vendor": ["model_vendor", "model_company"],
            "region": ["region", "market"],
        }
        normalized = dict(record)
        for target, aliases in alias_map.items():
            if normalized.get(target) not in (None, ""):
                continue
            for alias in aliases:
                if record.get(alias) not in (None, ""):
                    normalized[target] = record.get(alias)
                    break

        for field in ["platform", "title", "content", "author", "url", "published_at", "source_type", "entity_layer", "company_type", "component_type", "brand", "product", "model_vendor", "region"]:
            normalized[field] = normalize_space(str(normalized.get(field, "")))

        if not normalized["platform"]:
            normalized["platform"] = "unknown"
        if not normalized["author"]:
            normalized["author"] = "匿名"
        if not normalized["title"]:
            normalized["title"] = normalize_space(str(record.get("content", "")))[:60]

        for field in ["likes", "comments", "shares", "views", "followers", "raw_engagement"]:
            normalized[field] = safe_int(normalized.get(field, 0))

        tags = normalized.get("tags", [])
        if isinstance(tags, str):
            tags = [item.strip() for item in tags.split(",") if item.strip()]
        elif not isinstance(tags, list):
            tags = []
        normalized["tags"] = tags

        combined_parts = [
            normalized.get("title", ""),
            normalized.get("content", ""),
            normalized.get("brand", ""),
            normalized.get("product", ""),
            normalized.get("model_vendor", ""),
            normalized.get("component_type", ""),
            normalized.get("company_type", ""),
        ]
        normalized["combined_text"] = " ".join(part for part in combined_parts if part)
        return normalized

    def filter_records(self, records: List[Dict], start: str = "", end: str = "", platforms: Optional[List[str]] = None) -> List[Dict]:
        start_dt = parse_datetime(start) if start else None
        end_dt = parse_datetime(end) if end else None
        platforms_set = {item.strip().lower() for item in (platforms or []) if item.strip()}
        filtered = []
        for record in records:
            published = parse_datetime(record.get("published_at", ""))
            if start_dt and published and published < start_dt:
                continue
            if end_dt and published and published > end_dt:
                continue
            if platforms_set and record.get("platform", "").lower() not in platforms_set:
                continue
            filtered.append(record)
        return filtered

    def deduplicate(self, records: List[Dict]) -> List[Dict]:
        seen_urls = set()
        seen_titles = set()
        results = []
        for record in records:
            url = record.get("url") or ""
            title_key = normalize_title_key(record.get("title", ""))
            if url and url in seen_urls:
                continue
            if title_key and title_key in seen_titles:
                continue
            if url:
                seen_urls.add(url)
            if title_key:
                seen_titles.add(title_key)
            results.append(record)
        return results

    def classify_topics(self, record: Dict) -> Tuple[str, List[str]]:
        text = record.get("combined_text", "").lower()
        matches = []
        best_topic = "other"
        best_score = 0
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            if score:
                matches.append(topic)
            if score > best_score:
                best_topic = topic
                best_score = score
        return best_topic, matches

    def detect_layers(self, record: Dict) -> List[str]:
        preset = record.get("entity_layer", "")
        if preset:
            return [preset]
        text = record.get("combined_text", "").lower()
        layers = []
        for name, keywords in self.layer_keywords.items():
            if any(keyword.lower() in text for keyword in keywords):
                layers.append(name)
        return layers or ["unknown"]

    def detect_model_vendors(self, record: Dict) -> List[str]:
        text = record.get("combined_text", "").lower()
        preset = record.get("model_vendor", "")
        found = []
        if preset:
            found.append(preset)
        for vendor in self.model_vendors:
            if vendor.lower() in text and vendor not in found:
                found.append(vendor)
        return found

    def detect_competitors(self, record: Dict) -> List[str]:
        text = record.get("combined_text", "").lower()
        return [name for name in self.competitors if name.lower() in text]

    def analyze_sentiment(self, record: Dict) -> Dict:
        text = record.get("combined_text", "").lower()
        positive_hits = [word for word in self.positive_words if word.lower() in text]
        negative_hits = [word for word in self.negative_words if word.lower() in text]
        if positive_hits and negative_hits:
            sentiment = "mixed"
        elif negative_hits:
            sentiment = "negative"
        elif positive_hits:
            sentiment = "positive"
        else:
            sentiment = "neutral"
        reason = ", ".join((negative_hits or positive_hits)[:3]) if (negative_hits or positive_hits) else "未命中显著信号词"
        return {
            "sentiment": sentiment,
            "positive_hits": positive_hits,
            "negative_hits": negative_hits,
            "reason": reason,
        }

    def classify_role(self, author: str, text: str) -> str:
        combined = f"{author} {text}".lower()
        author_only = (author or "").lower()
        if any(vendor.lower() in author_only for vendor in self.model_vendors):
            return "模型厂商 / AI 实验室"
        best_role = "普通观察对象"
        best_score = 0
        for role, keywords in self.role_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in combined)
            if score > best_score:
                best_role = role
                best_score = score
        return best_role

    def engagement_score(self, record: Dict) -> float:
        raw_engagement = record.get("raw_engagement", 0)
        if raw_engagement:
            return float(raw_engagement)
        return (
            record.get("likes", 0) * 1.0
            + record.get("comments", 0) * 4.0
            + record.get("shares", 0) * 6.0
            + record.get("views", 0) * 0.03
        )

    def impact_level(self, record: Dict, topic: str, layers: List[str], model_vendors: List[str], sentiment: str) -> str:
        score = 0
        source_type = (record.get("source_type", "") or "").lower()
        if source_type in {"official", "media", "policy", "finance"}:
            score += 2
        if model_vendors:
            score += 2
        if any(layer in {"upstream", "midstream", "downstream", "model_vendor"} for layer in layers):
            score += 1
        if topic in {"upstream_supply", "model_vendor_strategy", "policy_compliance", "price_capacity"}:
            score += 2
        if sentiment in {"negative", "mixed"}:
            score += 1
        engagement = self.engagement_score(record)
        if engagement >= 1500:
            score += 2
        elif engagement >= 300:
            score += 1
        if score >= 6:
            return "high"
        if score >= 3:
            return "medium"
        return "low"

    def detect_risks(self, record: Dict) -> List[Dict]:
        text = record.get("combined_text", "").lower()
        risks = []
        engagement = self.engagement_score(record)
        sentiment = record.get("sentiment", "neutral")
        impact = record.get("impact_level", "low")
        for risk_type, keywords in self.risk_keywords.items():
            hits = [keyword for keyword in keywords if keyword.lower() in text]
            if not hits:
                continue
            score = len(hits) * 15 + min(engagement / 50, 35)
            if sentiment == "negative":
                score += 15
            elif sentiment == "mixed":
                score += 8
            score += {"low": 0, "medium": 8, "high": 15}.get(impact, 0)
            if score >= 75:
                level = "Critical"
            elif score >= 55:
                level = "High"
            elif score >= 35:
                level = "Medium"
            else:
                level = "Low"
            risks.append({
                "type": risk_type,
                "hits": hits,
                "level": level,
                "score": round(score, 1),
                "engagement": round(engagement, 1),
            })
        return risks

    def enrich_records(self, records: List[Dict]) -> List[Dict]:
        enriched = []
        for index, record in enumerate(records, start=1):
            topic, topic_matches = self.classify_topics(record)
            layers = self.detect_layers(record)
            model_vendors = self.detect_model_vendors(record)
            competitors = self.detect_competitors(record)
            sentiment_info = self.analyze_sentiment(record)
            role = self.classify_role(record.get("author", ""), record.get("combined_text", ""))
            engagement = self.engagement_score(record)
            impact = self.impact_level(record, topic, layers, model_vendors, sentiment_info["sentiment"])

            temp_record = dict(record)
            temp_record.update(sentiment_info)
            temp_record["impact_level"] = impact
            risks = self.detect_risks(temp_record)

            item = dict(record)
            item["id"] = f"N{index:04d}"
            item["topic"] = topic
            item["topic_matches"] = topic_matches
            item["layers"] = layers
            item["model_vendors_detected"] = model_vendors
            item["competitor_hits"] = competitors
            item["role"] = role
            item["engagement_score"] = round(engagement, 1)
            item["impact_level"] = impact
            item.update(sentiment_info)
            item["risks"] = risks
            enriched.append(item)
        return enriched

    def summarize(self, records: List[Dict]) -> Dict:
        platform_counter = Counter(record.get("platform", "unknown") for record in records)
        topic_counter = Counter(record.get("topic", "other") for record in records)
        sentiment_counter = Counter(record.get("sentiment", "neutral") for record in records)
        layer_counter = Counter(layer for record in records for layer in record.get("layers", []))
        model_vendor_counter = Counter(vendor for record in records for vendor in record.get("model_vendors_detected", []))
        impact_counter = Counter(record.get("impact_level", "low") for record in records)

        key_news = sorted(
            records,
            key=lambda item: (
                IMPACT_RANK.get(item.get("impact_level", "low"), 0),
                item.get("engagement_score", 0),
                parse_datetime(item.get("published_at", "")) or datetime.min,
            ),
            reverse=True,
        )[:10]
        latest_news = sorted(
            records,
            key=lambda item: parse_datetime(item.get("published_at", "")) or datetime.min,
            reverse=True,
        )[:10]
        return {
            "platforms": platform_counter,
            "topics": topic_counter,
            "sentiments": sentiment_counter,
            "layers": layer_counter,
            "model_vendors": model_vendor_counter,
            "impact_levels": impact_counter,
            "key_news": key_news,
            "latest_news": latest_news,
        }

    def build_layer_digest(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        digest = {"upstream": [], "midstream": [], "downstream": []}
        for layer in digest:
            matched = [record for record in records if layer in record.get("layers", [])]
            digest[layer] = sorted(
                matched,
                key=lambda item: (
                    IMPACT_RANK.get(item.get("impact_level", "low"), 0),
                    item.get("engagement_score", 0),
                ),
                reverse=True,
            )[:5]
        return digest

    def identify_kols(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        authors: Dict[str, Dict] = {}
        for record in records:
            key = f"{record.get('author', '匿名')}@{record.get('platform', 'unknown')}"
            if key not in authors:
                authors[key] = {
                    "name": record.get("author", "匿名"),
                    "platform": record.get("platform", "unknown"),
                    "role": record.get("role", "普通观察对象"),
                    "posts": 0,
                    "followers": 0,
                    "engagement": 0.0,
                    "positive": 0,
                    "negative": 0,
                    "mixed": 0,
                    "neutral": 0,
                    "top_link": record.get("url", ""),
                    "top_engagement": 0.0,
                }
            author = authors[key]
            author["posts"] += 1
            author["followers"] = max(author["followers"], record.get("followers", 0))
            author["engagement"] += record.get("engagement_score", 0.0)
            author[record.get("sentiment", "neutral")] = author.get(record.get("sentiment", "neutral"), 0) + 1
            if record.get("engagement_score", 0.0) > author.get("top_engagement", 0.0):
                author["top_engagement"] = record.get("engagement_score", 0.0)
                author["top_link"] = record.get("url", "")

        tiers = {"S": [], "A": [], "B": [], "C": []}
        for author in authors.values():
            influence = author["engagement"] + author["followers"] * 0.03 + author["posts"] * 25
            author["influence_score"] = round(influence, 1)
            if author.get("negative", 0) > author.get("positive", 0) + author.get("mixed", 0):
                author["stance"] = "负面"
            elif author.get("positive", 0) > author.get("negative", 0):
                author["stance"] = "正面"
            elif author.get("mixed", 0):
                author["stance"] = "混合"
            else:
                author["stance"] = "中立"

            if influence >= 4500:
                tiers["S"].append(author)
            elif influence >= 1800:
                tiers["A"].append(author)
            elif influence >= 700:
                tiers["B"].append(author)
            elif influence >= 200:
                tiers["C"].append(author)

        for level in tiers:
            tiers[level] = sorted(tiers[level], key=lambda item: item["influence_score"], reverse=True)
        return tiers

    def model_vendor_watch(self, records: List[Dict]) -> List[Dict]:
        results = []
        for vendor in self.model_vendors:
            matched = [record for record in records if vendor in record.get("model_vendors_detected", [])]
            topic_counter = Counter(record.get("topic", "other") for record in matched)
            layer_counter = Counter(layer for record in matched for layer in record.get("layers", []))
            results.append({
                "name": vendor,
                "mentions": len(matched),
                "topics": dict(topic_counter.most_common(3)),
                "layers": dict(layer_counter.most_common(3)),
            })
        return sorted(results, key=lambda item: item["mentions"], reverse=True)

    def competitor_watch(self, records: List[Dict]) -> List[Dict]:
        if not self.competitors:
            return []
        results = []
        for competitor in self.competitors:
            matched = [record for record in records if competitor in record.get("competitor_hits", [])]
            topic_counter = Counter(record.get("topic", "other") for record in matched)
            results.append({
                "name": competitor,
                "mentions": len(matched),
                "topics": dict(topic_counter.most_common(3)),
            })
        return sorted(results, key=lambda item: item["mentions"], reverse=True)

    def collect_risks(self, records: List[Dict], minimum_level: str = "low") -> List[Dict]:
        risk_items = []
        for record in records:
            for risk in record.get("risks", []):
                if not level_meets(risk["level"], minimum_level):
                    continue
                risk_items.append({
                    "content_id": record.get("id"),
                    "title": record.get("title"),
                    "platform": record.get("platform"),
                    "author": record.get("author"),
                    "url": record.get("url"),
                    "published_at": record.get("published_at"),
                    "layers": record.get("layers", []),
                    **risk,
                })
        return sorted(
            risk_items,
            key=lambda item: (LEVEL_RANK[item["level"].lower()], item["score"], item["engagement"]),
            reverse=True,
        )

    def build_actions(
        self,
        summary: Dict,
        risks: List[Dict],
        modules: Dict[str, bool],
        model_vendor_updates: List[Dict],
        competitors: List[Dict],
    ) -> List[str]:
        actions = []
        if modules["risk"] and risks and risks[0]["level"] in {"Critical", "High"}:
            actions.append("优先核实最高等级风险的事实、影响范围和时间线，并准备统一对外说明。")
        if modules["supply_chain"] and summary["layers"].get("upstream", 0):
            actions.append("把上游供给、封装、HBM 与交付信息单列成供应链专题，区分真实瓶颈与市场情绪。")
        if modules["model_vendor"] and any(item["mentions"] > 0 for item in model_vendor_updates[:3]):
            actions.append("对模型厂商动态补做关系核验，区分正式合作、测试验证和市场猜测。")
        if modules["competitor"] and competitors:
            actions.append("对竞品高提及主题补做对比验证，判断是否已形成真实替代趋势。")
        if summary["impact_levels"].get("high", 0) >= 3:
            actions.append("将高影响新闻拆成供给、部署、合作、政策四类，分别标注业务负责人和跟进时限。")
        if not actions:
            actions.append("当前生态动态以常规新闻为主，建议维持周报节奏并持续观察关键机构与模型厂商。")
        return actions

    def generate_markdown(self, data: Dict) -> str:
        summary = data["summary"]
        plan = data["plan"]
        modules = data["modules"]
        layer_digest = data["layer_digest"]
        model_vendor_updates = data["model_vendor_updates"]
        competitors = data["competitors"]
        kols = data["kols"]
        risks = data["risks"]
        actions = data["actions"]

        lines = []
        lines.append("# AI 硬件生态情报报告")
        lines.append("")
        lines.append("## 零、监测策略")
        lines.append("")
        lines.append(f"- 监测主体：{data['brand']}")
        lines.append(f"- 重点对象：{', '.join(data['products']) if data['products'] else '未指定'}")
        lines.append(f"- 模型厂商：{', '.join(data['model_vendors_input']) if data['model_vendors_input'] else '未指定'}")
        lines.append(f"- 竞品：{', '.join(data['competitors_input']) if data['competitors_input'] else '未指定'}")
        lines.append(f"- 专项主题：{data['topic'] or '未指定'}")
        lines.append(f"- 执行模块：{data['module']}")
        lines.append(f"- 时间范围：{data['start'] or '未限制'} 至 {data['end'] or '未限制'}")
        lines.append(f"- 平台覆盖：{', '.join(item['name'] for item in plan['platforms'])}")
        lines.append("")
        lines.append("### 0.1 关键词包")
        lines.append(f"- 核心词：{', '.join(plan['keyword_groups']['core']) if plan['keyword_groups']['core'] else '无'}")
        lines.append(f"- 上游词：{', '.join(plan['keyword_groups']['upstream'])}")
        lines.append(f"- 中游词：{', '.join(plan['keyword_groups']['midstream'])}")
        lines.append(f"- 下游词：{', '.join(plan['keyword_groups']['downstream'])}")
        lines.append(f"- 模型厂商词：{', '.join(plan['keyword_groups']['model_vendor'])}")
        lines.append(f"- 风险词：{', '.join(plan['keyword_groups']['risk'])}")
        lines.append("")

        lines.append("## 一、生态总览")
        lines.append("")
        lines.append(f"- 原始样本数：{data['raw_count']}")
        lines.append(f"- 过滤后样本数：{data['filtered_count']}")
        lines.append(f"- 去重后样本数：{data['deduplicated_count']}")
        lines.append("")
        lines.append("### 1.1 渠道分布")
        lines.append("| 渠道 | 数量 |")
        lines.append("|------|------|")
        for platform, count in summary["platforms"].most_common():
            lines.append(f"| {platform} | {count} |")
        lines.append("")
        lines.append("### 1.2 主题分布")
        lines.append("| 主题 | 数量 |")
        lines.append("|------|------|")
        for topic, count in summary["topics"].most_common():
            lines.append(f"| {topic} | {count} |")
        lines.append("")
        lines.append("### 1.3 环节分布")
        lines.append("| 环节 | 数量 |")
        lines.append("|------|------|")
        for layer, count in summary["layers"].most_common():
            lines.append(f"| {layer} | {count} |")
        lines.append("")

        lines.append("## 二、关键新闻")
        lines.append("")
        if modules["news"]:
            lines.append("| 标题 | 平台 | 机构 / 作者 | 关联环节 | 影响判断 | 链接 |")
            lines.append("|------|------|-------------|----------|----------|------|")
            for item in summary["key_news"]:
                layers = ", ".join(item.get("layers", []))
                lines.append(
                    f"| {item.get('title', '')[:44]} | {item.get('platform', '')} | {item.get('author', '')[:20]} | {layers} | {item.get('impact_level', '')} | {item.get('url', '')} |"
                )
        else:
            lines.append("- 当前未执行 news 模块。")
        lines.append("")

        lines.append("## 三、上下游动态")
        lines.append("")
        if modules["supply_chain"]:
            for layer, title in [("upstream", "3.1 上游动态"), ("midstream", "3.2 中游动态"), ("downstream", "3.3 下游动态")]:
                lines.append(f"### {title}")
                if not layer_digest[layer]:
                    lines.append("- 暂无")
                    lines.append("")
                    continue
                lines.append("| 对象 / 标题 | 平台 | 影响判断 | 链接 |")
                lines.append("|-------------|------|----------|------|")
                for item in layer_digest[layer]:
                    lines.append(
                        f"| {item.get('title', '')[:44]} | {item.get('platform', '')} | {item.get('impact_level', '')} | {item.get('url', '')} |"
                    )
                lines.append("")
        else:
            lines.append("- 当前未执行 supply-chain 模块。")
            lines.append("")

        lines.append("## 四、模型厂商动态")
        lines.append("")
        if modules["model_vendor"]:
            if model_vendor_updates:
                lines.append("| 厂商 | 提及量 | 高频主题 | 主要环节 |")
                lines.append("|------|--------|----------|----------|")
                for item in model_vendor_updates:
                    if item["mentions"] == 0:
                        continue
                    topics = ", ".join(f"{k}:{v}" for k, v in item.get("topics", {}).items()) or "-"
                    layers = ", ".join(f"{k}:{v}" for k, v in item.get("layers", {}).items()) or "-"
                    lines.append(f"| {item['name']} | {item['mentions']} | {topics} | {layers} |")
            else:
                lines.append("- 未配置模型厂商。")
        else:
            lines.append("- 当前未执行 model-vendor 模块。")
        lines.append("")

        lines.append("## 五、风险看板")
        lines.append("")
        if modules["risk"]:
            if risks:
                lines.append("| 类型 | 等级 | 平台 | 关联环节 | 标题 | 命中词 |")
                lines.append("|------|------|------|----------|------|--------|")
                for risk in risks[:10]:
                    layers = ", ".join(risk.get("layers", []))
                    lines.append(
                        f"| {risk.get('type')} | {risk.get('level')} | {risk.get('platform')} | {layers} | {risk.get('title', '')[:40]} | {', '.join(risk.get('hits', [])[:3])} |"
                    )
            else:
                lines.append("- 未识别到满足当前阈值的风险。")
        else:
            lines.append("- 当前未执行 risk 模块。")
        lines.append("")

        lines.append("## 六、关键机构 / KOL")
        lines.append("")
        if modules["kol"]:
            for tier in ["S", "A", "B", "C"]:
                lines.append(f"### {tier} 级")
                if not kols[tier]:
                    lines.append("- 暂无")
                    lines.append("")
                    continue
                lines.append("| 名称 | 平台 | 角色 | 影响力分 | 态度 | 链接 |")
                lines.append("|------|------|------|----------|------|------|")
                for item in kols[tier][:10]:
                    lines.append(
                        f"| {item.get('name')} | {item.get('platform')} | {item.get('role')} | {item.get('influence_score')} | {item.get('stance')} | {item.get('top_link', '')} |"
                    )
                lines.append("")
        else:
            lines.append("- 当前未执行 kol 模块。")
            lines.append("")

        lines.append("## 七、竞品与行业变化")
        lines.append("")
        if modules["competitor"]:
            if competitors:
                lines.append("| 竞品 | 提及量 | 高频主题 |")
                lines.append("|------|--------|----------|")
                for item in competitors:
                    topics = ", ".join(f"{k}:{v}" for k, v in item.get("topics", {}).items()) or "-"
                    lines.append(f"| {item['name']} | {item['mentions']} | {topics} |")
            else:
                lines.append("- 未配置竞品或样本中未命中竞品词。")
        else:
            lines.append("- 当前未执行 competitor 模块。")
        lines.append("")

        lines.append("## 八、行动建议")
        lines.append("")
        for idx, action in enumerate(actions, start=1):
            lines.append(f"{idx}. {action}")
        lines.append("")

        lines.append("## 九、数据口径说明")
        lines.append("")
        lines.append("- 本报告基于输入文件中的公开记录做规则分析，适合快速初筛，不替代人工复核。")
        lines.append(f"- 风险过滤阈值：{data['risk_level'].upper()}")
        return "\n".join(lines)

    def generate_csv(self, records: List[Dict]) -> str:
        fieldnames = [
            "id", "platform", "title", "author", "published_at", "topic", "layers", "impact_level",
            "sentiment", "model_vendors_detected", "competitor_hits", "url",
        ]
        lines = [",".join(fieldnames)]
        for record in records:
            row = []
            for field in fieldnames:
                value = record.get(field, "")
                if isinstance(value, list):
                    value = "|".join(value)
                text = str(value).replace('"', '""')
                row.append(f'"{text}"')
            lines.append(",".join(row))
        return "\n".join(lines)

    def maybe_print_alerts(self, risks: List[Dict], minimum_level: str) -> None:
        alertable = [risk for risk in risks if level_meets(risk["level"], minimum_level)]
        if not alertable:
            return
        print(f"⚠️ 检测到 {len(alertable)} 条 {minimum_level.upper()} 及以上风险：", file=sys.stderr)
        for item in alertable[:5]:
            layers = ",".join(item.get("layers", []))
            print(f"- [{item['level']}] {item['type']} / {layers} / {item['title'][:60]}", file=sys.stderr)

    def run(self, args) -> Dict:
        start_date, end_date = self.resolve_time_range(args)
        selected_platforms = self.selected_platforms(args.platforms)
        module = args.module or "all"
        risk_level = (args.risk_level or "low").lower()

        plan = self.build_collection_plan(start_date, end_date, selected_platforms, args.topic or "", module)
        if args.plan_only:
            output = json.dumps(plan, ensure_ascii=False, indent=2, default=json_default) if args.export_json else self.generate_plan_markdown(plan)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as handle:
                    handle.write(output)
            else:
                print(output)
            return {"plan": plan}

        if not args.input:
            raise ValueError("未提供 --input。若只想输出监测计划，请加 --plan-only。")

        raw_records = self.load_records(args.input)
        filtered = self.filter_records(raw_records, start=start_date, end=end_date, platforms=selected_platforms)
        deduplicated = self.deduplicate(filtered)
        enriched = self.enrich_records(deduplicated)
        summary = self.summarize(enriched)
        layer_digest = self.build_layer_digest(enriched)

        modules = {
            "news": module in {"news", "all"},
            "supply_chain": module in {"supply-chain", "all"},
            "model_vendor": module in {"model-vendor", "all"},
            "competitor": module in {"competitor", "all"},
            "kol": module in {"kol", "all"},
            "risk": module in {"risk", "all"},
        }

        kols = self.identify_kols(enriched) if modules["kol"] else {"S": [], "A": [], "B": [], "C": []}
        model_vendor_updates = self.model_vendor_watch(enriched) if modules["model_vendor"] else []
        competitors = self.competitor_watch(enriched) if modules["competitor"] else []
        risks = self.collect_risks(enriched, minimum_level=risk_level) if modules["risk"] else []
        actions = self.build_actions(summary, risks, modules, model_vendor_updates, competitors)

        payload = {
            "brand": self.brand,
            "products": self.products,
            "competitors_input": self.competitors,
            "model_vendors_input": self.model_vendors,
            "topic": args.topic or "",
            "module": module,
            "risk_level": risk_level,
            "start": start_date,
            "end": end_date,
            "raw_count": len(raw_records),
            "filtered_count": len(filtered),
            "deduplicated_count": len(deduplicated),
            "plan": plan,
            "summary": summary,
            "layer_digest": layer_digest,
            "kols": kols,
            "model_vendor_updates": model_vendor_updates,
            "competitors": competitors,
            "risks": risks,
            "actions": actions,
            "records": enriched,
            "modules": modules,
        }

        if args.export_json:
            output = json.dumps(payload, ensure_ascii=False, indent=2, default=json_default)
        elif args.export_csv:
            output = self.generate_csv(enriched)
        else:
            output = self.generate_markdown(payload)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(output)
        else:
            print(output)

        if args.alert and modules["risk"]:
            self.maybe_print_alerts(risks, minimum_level=risk_level)
        return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI 硬件生态监测与分析工具")
    parser.add_argument("--input", help="输入文件路径（json/jsonl/csv）")
    parser.add_argument("--brand", default="", help="监测主体 / 品牌 / 机构")
    parser.add_argument("--products", default="", help="重点产品或对象，逗号分隔")
    parser.add_argument("--competitors", default="", help="竞品列表，逗号分隔")
    parser.add_argument("--model-vendors", default="", help="重点模型厂商，逗号分隔")
    parser.add_argument("--topic", default="", help="专项监测主题，例如 HBM 供给 / 模型厂商采购")
    parser.add_argument("--period", choices=["day", "week", "month"], help="监测周期（day/week/month）")
    parser.add_argument("--start", default="", help="开始日期，例如 2026-04-01")
    parser.add_argument("--end", default="", help="结束日期，例如 2026-04-07")
    parser.add_argument("--platforms", nargs="*", default=None, help="只分析指定平台键")
    parser.add_argument("--module", choices=["news", "supply-chain", "model-vendor", "competitor", "kol", "risk", "all"], default="all", help="执行模块")
    parser.add_argument("--plan-only", action="store_true", help="只输出监测计划，不跑分析")
    parser.add_argument("--risk-level", choices=["low", "medium", "high", "critical"], default="low", help="风险过滤阈值")
    parser.add_argument("--alert", action="store_true", help="对达到阈值的风险打印即时预警")
    parser.add_argument("--output", "-o", default="", help="输出文件路径")
    parser.add_argument("--export-json", action="store_true", help="导出 JSON")
    parser.add_argument("--export-csv", action="store_true", help="导出 CSV")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.export_json and args.export_csv:
        parser.error("--export-json 与 --export-csv 不能同时使用")
    if not args.plan_only and not args.input:
        parser.error("必须提供 --input，除非使用 --plan-only")

    monitor = AIHardwareEcosystemMonitor(
        brand=args.brand,
        products=parse_list(args.products),
        competitors=parse_list(args.competitors),
        model_vendors=parse_list(args.model_vendors),
    )
    try:
        monitor.run(args)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
