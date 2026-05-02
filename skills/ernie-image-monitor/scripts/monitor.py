#!/usr/bin/env python3
"""
ERNIE-Image 舆情监测主脚本
汇总各平台数据，输出结构化报告
- 搜索关键词覆盖 ERNIE-Image / ERNIE-Image-Turbo / ERNIE_Image 变体
- 在标题、正文、评论、标签中检索
- 仅保留发布日期 >= 2026-04-14 的内容（ERNIE-Image 正式发布日）
- 情感判断由调用本脚本的 Claude 根据语义完成
"""

import subprocess
import json
import sys
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional

OPENCLI = str(Path.home() / ".local/bin/opencli")

# 所有检索关键词变体（含 Turbo、下划线拼写）
SEARCH_KEYWORDS = [
    "ERNIE-Image",
    "ERNIE-Image-Turbo",
    "ERNIE_Image",
    "文心图像",
    "百度文心图像生成",
]

# 相关性过滤词：标题/摘要/正文中需含至少一个（不区分大小写）
RELEVANCE_KEYWORDS = [
    "ernie-image",
    "ernie_image",
    "ernie image",
    "ernie-image-turbo",
    "文心图像",
    "百度文心图像",
]

# 仅保留此日期之后（含）的内容；日期未知的条目保留（交由 Claude 判断）
DATE_FILTER = date(2026, 4, 14)


# ── 工具函数 ──────────────────────────────────────────────────
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


def _make_item(platform, account, title, content_snippet, url, published_at="", tags=""):
    """构造统一结构的条目（情感字段留空，由 Claude 语义判断）"""
    return {
        "platform": platform,
        "account": account,
        "title": title,
        "content_snippet": content_snippet,
        "tags": tags,
        "published_at": published_at,
        "sentiment": "",
        "url": url,
    }


def _is_relevant(text: str) -> bool:
    """判断文本是否含 ERNIE-Image 相关关键词"""
    t = text.lower()
    return any(k.lower() in t for k in RELEVANCE_KEYWORDS)


_MONTH_ABBR = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def _parse_date(pub: str) -> Optional[date]:
    """将各种日期字符串解析为 date 对象，解析失败返回 None"""
    if not pub:
        return None
    # 标准格式 2026-04-15
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", pub)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # 中文格式 2026年4月15日
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", pub)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # 斜线格式 2026/04/15
    m = re.match(r"(\d{4})/(\d{2})/(\d{2})", pub)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # 英文月份缩写格式 Apr 16, 2026
    m = re.match(r"([A-Z][a-z]{2})\s+(\d{1,2}),?\s+(\d{4})", pub)
    if m:
        month = _MONTH_ABBR.get(m.group(1))
        if month:
            return date(int(m.group(3)), month, int(m.group(2)))
    return None


def _passes_date_filter(published_at: str) -> bool:
    """日期 >= DATE_FILTER 返回 True；日期未知也返回 True（保留，待人工判断）"""
    d = _parse_date(published_at)
    if d is None:
        return True  # 未知日期保留
    return d >= DATE_FILTER


def _extract_date_from_snippet(snippet: str) -> str:
    """从 Google 搜索摘要中提取日期"""
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


def _fetch_xhs_note_detail(note_id: str) -> tuple[str, str]:
    """
    获取小红书笔记正文和标签（用于丰富 content_snippet）
    返回 (body_snippet, tags_str)，失败返回 ("", "")
    """
    if not note_id:
        return "", ""
    items = run_opencli(["xiaohongshu", "note", note_id])
    if not items:
        return "", ""
    note = items[0] if isinstance(items, list) else items
    body = note.get("content", note.get("body", note.get("desc", "")))[:200]
    tags_raw = note.get("tags", note.get("tag_list", []))
    if isinstance(tags_raw, list):
        tags = " ".join(f"#{t}" if not str(t).startswith("#") else str(t) for t in tags_raw[:10])
    else:
        tags = str(tags_raw)
    return body, tags


def _extract_note_id_from_url(url: str) -> str:
    """从小红书 URL 中提取 note_id"""
    # 格式：/search_result/<note_id>?  或  /explore/<note_id>
    m = re.search(r"/(?:search_result|explore)/([a-f0-9]+)", url)
    return m.group(1) if m else ""


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
            # 相关性过滤：标题中需含关键词
            if not _is_relevant(title):
                continue
            published_at = item.get("created_time", item.get("published_at", ""))
            # 日期过滤
            if not _passes_date_filter(published_at):
                continue
            excerpt = item.get("excerpt", "")
            # 相关性过滤：标题、正文摘要任一命中即通过
            if not _is_relevant(f"{title} {excerpt}"):
                continue
            seen_urls.add(url)
            results.append(_make_item(
                platform="知乎",
                account=item.get("author", "未知"),
                title=title,
                content_snippet=(excerpt or title)[:200],
                url=url,
                published_at=published_at,
            ))
    return results


def fetch_xiaohongshu(limit: int = 20, fetch_detail: bool = True) -> list[dict]:
    print("📌 正在搜索小红书...")
    results = []
    seen_urls = set()
    for kw in SEARCH_KEYWORDS:
        items = run_opencli(["xiaohongshu", "search", kw, "--limit", str(limit)])
        for item in items:
            url = item.get("url", "")
            title = item.get("title", "")
            published_at = item.get("published_at", "")
            if url in seen_urls:
                continue
            # 日期过滤
            if not _passes_date_filter(published_at):
                continue

            # 尝试抓取正文和标签以做相关性判断
            body, tags = "", ""
            if fetch_detail:
                note_id = _extract_note_id_from_url(url)
                if note_id:
                    body, tags = _fetch_xhs_note_detail(note_id)

            # 相关性过滤：标题 + 正文 + 标签中至少一处含关键词
            combined = f"{title} {body} {tags}"
            if not _is_relevant(combined):
                continue

            seen_urls.add(url)
            snippet = body if body else title
            results.append(_make_item(
                platform="小红书",
                account=item.get("author", "未知"),
                title=title,
                content_snippet=snippet[:200],
                url=url,
                published_at=published_at,
                tags=tags,
            ))
    return results


def fetch_weixin_via_google(limit: int = 10) -> list[dict]:
    """通过 Google 搜索微信公众号文章"""
    print("📌 正在搜索微信公众号（via Google）...")
    results = []
    seen_urls = set()
    # 全关键词变体检索
    for kw in SEARCH_KEYWORDS[:3]:
        query = f"site:mp.weixin.qq.com {kw}"
        items = run_opencli(["google", "search", query, "--limit", str(limit), "--lang", "zh"])
        for item in items:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            if "mp.weixin.qq.com" not in url:
                continue
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            published_at = _extract_date_from_snippet(snippet)
            # 日期过滤
            if not _passes_date_filter(published_at):
                continue
            # 相关性过滤
            if not _is_relevant(f"{title} {snippet}"):
                continue
            seen_urls.add(url)
            results.append(_make_item(
                platform="微信公众号",
                account=_extract_wechat_account(snippet),
                title=title,
                content_snippet=snippet[:200],
                url=url,
                published_at=published_at,
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
    """通过 Google 搜索百度系内容（百家号、知道、贴吧等）"""
    print("📌 正在搜索百度（via Google）...")
    results = []
    seen_urls = set()
    baidu_domains = ["baidu.com", "baijiahao", "zhidao", "tieba"]
    for kw in SEARCH_KEYWORDS[:3]:
        items = run_opencli(["google", "search", kw, "--limit", str(limit), "--lang", "zh"])
        for item in items:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            if not any(d in url for d in baidu_domains):
                continue
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            published_at = _extract_date_from_snippet(snippet)
            # 日期过滤
            if not _passes_date_filter(published_at):
                continue
            # 相关性过滤
            if not _is_relevant(f"{title} {snippet}"):
                continue
            seen_urls.add(url)
            results.append(_make_item(
                platform="百度搜索",
                account=_extract_site_name(url),
                title=title,
                content_snippet=snippet[:200],
                url=url,
                published_at=published_at,
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


# ── 排序 ──────────────────────────────────────────────────────
def _sort_key(item: dict) -> str:
    pub = item.get("published_at", "")
    if pub:
        return "0_" + pub
    return "9_"


def sort_results(results: list[dict]) -> list[dict]:
    return sorted(results, key=_sort_key, reverse=True)


# ── 报告输出（情感字段由 Claude 语义分析后填入）────────────────
def print_report(all_results: list[dict]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(all_results)

    print("\n" + "=" * 70)
    print(f"  ERNIE-Image 舆情监测报告  |  {now}")
    print("=" * 70)
    print(f"  共收录 {total} 条（已去重 · 日期 ≥ 2026-04-14 · 情感由 Claude 语义分析）")
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
            if snippet and snippet.strip() != r["title"].strip():
                print(f"  内容大意 : {snippet[:150]}")
            tags = r.get("tags", "")
            if tags:
                print(f"  标签     : {tags[:100]}")
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
    parser.add_argument("--limit", type=int, default=20, help="每平台每关键词最大条数")
    parser.add_argument("--save", action="store_true", help="保存 JSON 报告")
    parser.add_argument("--output-dir", default=".", help="JSON 保存目录")
    parser.add_argument("--no-detail", action="store_true", help="跳过小红书正文抓取（加速）")
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
        all_results += fetch_xiaohongshu(args.limit, fetch_detail=not args.no_detail)
    if "all" in platforms or "weixin" in platforms:
        all_results += fetch_weixin_via_google(args.limit)
    if "all" in platforms or "baidu" in platforms:
        all_results += fetch_baidu(args.limit)

    all_results = sort_results(all_results)
    print_report(all_results)

    if args.save:
        save_json(all_results, args.output_dir)


if __name__ == "__main__":
    main()
