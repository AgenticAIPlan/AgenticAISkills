#!/usr/bin/env python3
"""
ERNIE-Image 舆情监测主脚本
汇总各平台数据，输出结构化报告
- 包含发布时间字段，按发布时间降序排列
- 情感判断由调用本脚本的 Claude 根据语义完成
"""

import subprocess
import json
import sys
import re
from datetime import datetime
from pathlib import Path

OPENCLI = str(Path.home() / ".local/bin/opencli")
SEARCH_KEYWORDS = ["ERNIE-Image"]

# ERNIE-Image 发布日期（2026-04-14），仅收录此日期及之后的内容
SINCE_DATE = "2026-04-14"

# 内容相关性关键词：标题、正文、评论、标签中包含任一即视为相关
ERNIE_IMAGE_TERMS = ["ernie-image", "ernie-image-turbo", "ernie_image"]


# ── OpenCLI 调用 ──────────────────────────────────────────────
def run_opencli(args: list[str]) -> list[dict]:
    cmd = [OPENCLI] + args + ["-f", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"  [警告] 命令失败: {' '.join(args[:3])}", file=sys.stderr)
            return []
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  [错误] {e}", file=sys.stderr)
        return []


def _make_item(platform, account, title, content_snippet, url, published_at=""):
    """构造统一结构的条目（情感字段留空，由 Claude 语义判断）"""
    return {
        "platform": platform,
        "account": account,
        "title": title,
        "content_snippet": content_snippet,
        "published_at": published_at,
        "sentiment": "",
        "url": url,
    }


def is_ernie_image_relevant(title: str, snippet: str = "",
                             tags: list = None, comments: list = None) -> bool:
    """
    判断内容是否与 ERNIE-Image 直接相关。
    检查范围：标题、正文摘要、标签、评论——任一字段包含关键词即通过。
    """
    parts = [title, snippet]
    if tags:
        parts += [t if isinstance(t, str) else str(t) for t in tags]
    if comments:
        parts += [c if isinstance(c, str) else str(c) for c in comments]
    text = " ".join(parts).lower()
    return any(term in text for term in ERNIE_IMAGE_TERMS)


def _parse_date(date_str: str) -> str:
    """将各种日期格式统一转换为 YYYY-MM-DD，解析失败返回空字符串"""
    if not date_str:
        return ""
    # 已是 ISO 格式
    if re.match(r"^\d{4}-\d{2}-\d{2}", date_str):
        return date_str[:10]
    # 中文格式：2026年4月14日
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # YYYY/MM/DD
    m = re.match(r"(\d{4})/(\d{2})/(\d{2})", date_str)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def is_after_release_date(published_at: str) -> bool:
    """仅保留 SINCE_DATE（含）之后的内容；无法解析日期时默认保留"""
    parsed = _parse_date(published_at)
    if not parsed:
        return True   # 日期未知则保留，由 Claude 二次判断
    return parsed >= SINCE_DATE


def _extract_date_from_snippet(snippet: str) -> str:
    """从 Google 搜索摘要中提取日期"""
    # 常见格式：2026年4月16日、2026-04-16、Apr 16, 2026、2026/04/16
    patterns = [
        r"(\d{4}年\d{1,2}月\d{1,2}日)",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{4}/\d{2}/\d{2})",
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, snippet)
        if m:
            return m.group(1)
    return ""


# ── 各平台爬取 ────────────────────────────────────────────────
def fetch_zhihu(limit: int = 20) -> list[dict]:
    print("📌 正在搜索知乎...")
    results = []
    seen_urls = set()
    for kw in SEARCH_KEYWORDS:
        items = run_opencli(["zhihu", "search", kw, "--limit", str(limit)])
        for item in items:
            title = item.get("title", "")
            url = item.get("url", "")
            if url in seen_urls:
                continue
            pub = item.get("created_time", item.get("published_at", ""))
            tags = item.get("tags", []) or []
            comments = item.get("comments", []) or []
            # 过滤：标题、正文、标签、评论中任一含关键词
            if not is_ernie_image_relevant(title, title, tags, comments):
                continue
            # 过滤：仅保留发布日期 >= SINCE_DATE 的内容
            if not is_after_release_date(pub):
                continue
            seen_urls.add(url)
            results.append(_make_item(
                platform="知乎",
                account=item.get("author", "未知"),
                title=title,
                content_snippet=title,
                url=url,
                published_at=pub,
            ))
    return results


def fetch_xiaohongshu(limit: int = 20) -> list[dict]:
    print("📌 正在搜索小红书...")
    results = []
    seen_urls = set()
    for kw in SEARCH_KEYWORDS:
        items = run_opencli(["xiaohongshu", "search", kw, "--limit", str(limit)])
        for item in items:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            title = item.get("title", "")
            pub = item.get("published_at", "")
            tags = item.get("tags", []) or []
            comments = item.get("comments", []) or []
            # 过滤：标题、正文、标签、评论中任一含关键词
            if not is_ernie_image_relevant(title, title, tags, comments):
                continue
            # 过滤：仅保留发布日期 >= SINCE_DATE 的内容
            if not is_after_release_date(pub):
                continue
            seen_urls.add(url)
            results.append(_make_item(
                platform="小红书",
                account=item.get("author", "未知"),
                title=title,
                content_snippet=title,
                url=url,
                published_at=pub,
            ))
    return results


def fetch_weixin_via_google(limit: int = 10) -> list[dict]:
    """通过 Google 搜索微信公众号文章"""
    print("📌 正在搜索微信公众号（via Google）...")
    results = []
    seen_urls = set()
    for kw in SEARCH_KEYWORDS[:2]:
        query = f"{kw} 公众号"
        items = run_opencli(["google", "search", query, "--limit", str(limit), "--lang", "zh"])
        for item in items:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            if "mp.weixin.qq.com" not in url and "weixin" not in url.lower():
                continue
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            pub = _extract_date_from_snippet(snippet)
            tags = item.get("tags", []) or []
            # 过滤：标题、摘要、标签中任一含关键词
            if not is_ernie_image_relevant(title, snippet, tags):
                continue
            # 过滤：仅保留发布日期 >= SINCE_DATE 的内容
            if not is_after_release_date(pub):
                continue
            seen_urls.add(url)
            results.append(_make_item(
                platform="微信公众号",
                account=_extract_wechat_account(snippet),
                title=title,
                content_snippet=snippet[:200],
                url=url,
                published_at=pub,
            ))
    return results


def _extract_wechat_account(snippet: str) -> str:
    patterns = [r"【(.{2,20})】", r"「(.{2,20})」", r"^([^·\n]{2,20})·"]
    for pat in patterns:
        m = re.search(pat, snippet)
        if m:
            return m.group(1)
    return "未知公众号"


def fetch_baidu(limit: int = 20) -> list[dict]:
    """通过 Google 搜索百度收录结果"""
    print("📌 正在搜索百度（via Google）...")
    results = []
    seen_urls = set()
    for kw in SEARCH_KEYWORDS[:2]:
        items = run_opencli(["google", "search", kw, "--limit", str(limit), "--lang", "zh"])
        for item in items:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            baidu_domains = ["baidu.com", "baijiahao", "zhidao", "tieba"]
            if not any(d in url for d in baidu_domains):
                continue
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            pub = _extract_date_from_snippet(snippet)
            tags = item.get("tags", []) or []
            # 过滤：标题、摘要、标签中任一含关键词
            if not is_ernie_image_relevant(title, snippet, tags):
                continue
            # 过滤：仅保留发布日期 >= SINCE_DATE 的内容
            if not is_after_release_date(pub):
                continue
            seen_urls.add(url)
            results.append(_make_item(
                platform="百度搜索",
                account=_extract_site_name(url),
                title=title,
                content_snippet=snippet[:200],
                url=url,
                published_at=pub,
            ))
    return results


def _extract_site_name(url: str) -> str:
    if "baijiahao" in url:
        return "百家号"
    if "zhidao" in url:
        return "百度知道"
    if "tieba" in url:
        return "百度贴吧"
    return "百度"


def _sort_key(item: dict) -> str:
    """排序键：有日期的按日期降序，无日期的排末尾"""
    pub = item.get("published_at", "")
    if pub:
        return "0_" + pub  # 有日期的排前面（字典序，0开头）
    return "9_"             # 无日期的排末尾


def sort_results(results: list[dict]) -> list[dict]:
    """按发布时间降序排列，无日期的排末尾"""
    return sorted(results, key=_sort_key, reverse=True)


# ── 报告输出（情感字段由 Claude 语义分析后填入）────────────────
def print_report(all_results: list[dict]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(all_results)

    print("\n" + "=" * 70)
    print(f"  ERNIE-Image 舆情监测报告  |  {now}")
    print("=" * 70)
    print(f"  共收录 {total} 条（已去重，按发布时间排序，情感由 Claude 语义分析）")
    print("=" * 70)

    platforms = sorted(set(r["platform"] for r in all_results))
    for platform in platforms:
        items = [r for r in all_results if r["platform"] == platform]
        print(f"\n【{platform}】 ({len(items)} 条)")
        print("-" * 60)
        for r in items:
            print(f"  账号名称 : {r['account']}")
            print(f"  标题     : {r['title'][:80]}")
            snippet = r.get("content_snippet", "")
            if snippet and snippet != r["title"]:
                print(f"  内容大意 : {snippet[:120]}")
            pub = r.get("published_at", "")
            print(f"  发布时间 : {pub if pub else '未知'}")
            print(f"  情感判断 : （待 Claude 语义分析）")
            print(f"  来源链接 : {r['url']}")
            print()


def save_json(all_results: list[dict], output_dir: str = ".") -> str:
    path = Path(output_dir) / f"ernie_image_monitor_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2))
    print(f"\n📄 JSON 报告已保存: {path}")
    return str(path)


# ── 入口 ─────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="ERNIE-Image 多平台舆情监测")
    parser.add_argument("--limit", type=int, default=20, help="每平台最大条数")
    parser.add_argument("--save", action="store_true", help="保存 JSON 报告")
    parser.add_argument("--output-dir", default=".", help="JSON 保存目录")
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["zhihu", "xhs", "weixin", "baidu", "all"],
        default=["all"],
        help="指定爬取平台",
    )
    args = parser.parse_args()

    platforms = args.platforms
    all_results = []

    if "all" in platforms or "zhihu" in platforms:
        all_results += fetch_zhihu(args.limit)
    if "all" in platforms or "xhs" in platforms:
        all_results += fetch_xiaohongshu(args.limit)
    if "all" in platforms or "weixin" in platforms:
        all_results += fetch_weixin_via_google(args.limit)
    if "all" in platforms or "baidu" in platforms:
        all_results += fetch_baidu(args.limit)

    # 按发布时间排序
    all_results = sort_results(all_results)

    print_report(all_results)

    if args.save:
        save_json(all_results, args.output_dir)


if __name__ == "__main__":
    main()
