---
name: ernie-image-monitor
description: "This skill should be used when the user wants to monitor, search, or analyze social media and web content about ERNIE-Image across Chinese platforms including Zhihu, Xiaohongshu, WeChat Official Accounts, and Baidu Search."
---

# ERNIE-Image 舆情监测

Monitor mentions of ERNIE-Image across Zhihu, Xiaohongshu, WeChat Official Accounts, and Baidu Search. Collect structured data including account name, content, sentiment judgment, and source URL.

## Prerequisites

- OpenCLI installed at `~/.local/bin/opencli` (v1.7.4+)
- Chrome browser extension installed for cookie-based platforms (Zhihu, XHS)
- Run `~/.local/bin/opencli doctor` to verify browser bridge connectivity

If OpenCLI is not installed, run:
```bash
npm install -g @jackwener/opencli --prefix ~/.local
```

For Chrome extension: load unpacked from `~/.local/lib/node_modules/@jackwener/opencli/extension/`.

## Quick Start

Run a full multi-platform scan (with XHS detail fetch):
```bash
python3 scripts/monitor.py --limit 20 --save
```

Run without XHS detail fetch (faster):
```bash
python3 scripts/monitor.py --limit 20 --save --no-detail
```

Run on specific platforms:
```bash
python3 scripts/monitor.py --platforms zhihu xhs --limit 20
python3 scripts/monitor.py --platforms weixin baidu --limit 10
```

## Output Fields

Each collected item includes:

| Field | Description |
|-------|-------------|
| `platform` | 知乎 / 小红书 / 微信公众号 / 百度搜索 |
| `account` | 发布者账号或公众号名称 |
| `title` | 标题 |
| `content_snippet` | 内容摘要（前 200 字） |
| `sentiment` | 正面 ✅ / 负面 ❌ / 中性 ➖ |
| `url` | 来源链接 |
| `fetched_at` | 采集时间 |

## Sentiment Analysis (Semantic — by Claude)

The script collects raw data with `sentiment` field left empty. **Claude must fill in sentiment judgment semantically** after receiving the results — do NOT use keyword matching.

For each item, read `title` + `content_snippet` and judge:
- **正面 ✅**: Content praises, recommends, expresses satisfaction, or is objectively positive toward ERNIE-Image
- **负面 ❌**: Content criticizes, complains, expresses disappointment, compares unfavorably, or raises concerns
- **中性 ➖**: Factual introduction, news report, tutorial, or neutral discussion without clear positive/negative stance

When presenting results to the user, include the sentiment label for each item and provide a summary count at the top (e.g., "共 N 条 | 正面 X ✅ 负面 Y ❌ 中性 Z ➖").

## Published Time & Sort Order

Each item includes a `published_at` field:
- Zhihu: from `created_time` or `published_at` field in API response
- 小红书: from `published_at` field in API response
- 微信公众号 / 百度搜索: extracted via regex from Google snippet text

Results are **sorted by `published_at` descending** (newest first). Items without a date appear at the end.

## Feishu Upload (Required Every Run)

**Every monitoring run must upload results to Feishu as a NEW document** — never overwrite existing documents.

After generating the Markdown report:
1. Write report to `~/feishu_report.md`
2. Upload using lark-cli (must run from `~` directory with relative path):
   ```bash
   cd ~ && ~/.local/bin/lark-cli docs +create --title "ERNIE-Image 舆情监测报告 <crawl_time>" --markdown @feishu_report.md
   ```
3. The document title must include the crawl timestamp (format: `YYYY-MM-DD HH:MM`)
4. Share the resulting Feishu document URL with the user

## Detailed Investigation

For deeper analysis of individual posts found during monitoring:

**知乎问题详情:**
```bash
python3 scripts/zhihu_detail.py <question-id-or-url> --limit 10
```

**小红书笔记详情 + 评论:**
```bash
python3 scripts/xhs_detail.py <note-id-or-url> --comments --limit 20
```

## Platform Coverage

| Platform | Method | Requires Login |
|----------|--------|----------------|
| 知乎 | `opencli zhihu search` | Yes (cookie) |
| 小红书 | `opencli xiaohongshu search` | Yes (cookie) |
| 微信公众号 | Google `site:mp.weixin.qq.com` | No |
| 百度搜索 | Google `site:baidu.com` 系列 | No |

For full OpenCLI command reference, load `references/opencli_commands.md`.

## Search Keywords Used

- `ERNIE-Image`
- `ERNIE-Image-Turbo`
- `ERNIE_Image`
- `文心图像`
- `百度文心图像生成`

To add more keywords, edit the `SEARCH_KEYWORDS` list in `scripts/monitor.py`.

## Date Filtering

Only content published on or after **2026-04-14** (ERNIE-Image official release date) is kept.
Items with unknown dates are retained for manual review.

This is enforced via `DATE_FILTER = date(2026, 4, 14)` in `monitor.py`.

## Relevance Filtering

Each item must contain at least one of these keywords in title + body + tags:
`ernie-image`, `ernie_image`, `ernie image`, `ernie-image-turbo`, `文心图像`, `百度文心图像`

## Xiaohongshu Detail Fetching

For each XHS search result, the script calls `opencli xiaohongshu note <note-id>` to fetch:
- Full post body (`content` / `desc` field, up to 200 chars)
- Tag list (used for relevance filtering and report display)

Use `--no-detail` flag to skip this step and speed up execution.

## Report Fields

Each collected item in the final report includes:

| Field | Description |
|-------|-------------|
| `platform` | 知乎 / 小红书 / 微信公众号 / 百度搜索 |
| `account` | 发布者账号或公众号名称 |
| `title` | 标题 |
| `content_snippet` | 内容大意（正文前 200 字或摘要） |
| `tags` | 标签（小红书） |
| `published_at` | 发布时间 |
| `sentiment` | 正面 ✅ / 负面 ❌ / 中性 ➖（Claude 语义分析） |
| `url` | 来源链接 |
