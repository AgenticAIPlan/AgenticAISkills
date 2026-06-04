---
name: energy-llm-tracker
description: 调研能源行业（电力/电网为主，兼顾油气及新能源）上下游企业大模型应用动态的专项技能。覆盖数据建设、行业模型、应用落地三个维度。当用户需要了解能源企业AI/大模型最新进展、生成行业动态报告、查询特定企业或场景的落地案例时，应使用此技能。
---

# 能源行业大模型应用动态调研技能

## 概述

本技能用于系统性调研电力/电网、油气、新能源等能源行业企业在大模型（LLM）方向的最新应用动态，输出结构化的行业洞察报告。调研维度涵盖**数据建设**、**行业模型**、**应用落地**三个核心方向。

## 使用场景

以下请求应触发本技能：
- "帮我调研国家电网最近的大模型应用进展"
- "生成本周电力行业AI动态月报"
- "查找能源企业知识图谱建设相关的案例"
- "对比电力行业头部企业的大模型落地成熟度"
- "整理电力调度AI应用相关资讯"

## 调研工作流

### Step 1：明确调研范围

收到调研请求后，首先确认以下参数：
- **时间范围**：默认近7天（周报）或近30天（月报）
- **聚焦企业**：全行业或指定企业名称
- **聚焦维度**：全部维度，或指定数据建设/行业模型/应用落地

参考 `references/energy_companies.md` 获取重点企业名单和信息来源列表。

### Step 2：生成搜索查询

运行搜索查询生成脚本，获取结构化搜索指引：

```bash
# 生成全行业搜索指引（默认近7天）
python3 scripts/fetch_energy_news.py

# 聚焦特定企业
python3 scripts/fetch_energy_news.py --company "国家电网" --days 30

# 聚焦特定维度
python3 scripts/fetch_energy_news.py --dimension application --days 14

# 输出 JSON 格式（便于后续处理）
python3 scripts/fetch_energy_news.py --format json --output queries.json
```

### Step 3：执行信息检索

按照脚本生成的搜索指引，**组合使用以下两种搜索方式**，覆盖国内外信息源：

#### 国内搜索（优先）— 使用 `china-search` 技能

能源行业资讯以中文为主，优先通过国内搜索引擎获取：

```bash
# 百度搜索：综合新闻、官网公告
curl -s -L "https://www.baidu.com/s?wd=国家电网+大模型+2024" \
  -H "User-Agent: Mozilla/5.0"

# 搜狗微信搜索：公众号深度文章（行业分析、案例报道）
curl -s -L "https://weixin.sogou.com/weixin?query=电力行业+大模型+落地" \
  -H "User-Agent: Mozilla/5.0"

# Bing 中国：兼顾国际信息与国内可访问性
curl -s -L "https://cn.bing.com/search?q=电力调度+AI+应用" \
  -H "User-Agent: Mozilla/5.0"
```

搜狗微信搜索特别适合查找行业媒体公众号的深度报道，是百度搜索的重要补充。

#### 国际/英文搜索 — 使用 WebSearch 工具

用于检索国际机构报告、英文学术资讯等：
- IEA（国际能源署）能源数字化报告
- 外资能源企业（Shell、BP、Equinor 等）AI 应用进展

#### 信息可信度评级

| 来源类型 | 可信度 | 示例 |
|---------|-------|------|
| 企业官网新闻中心 | ⭐⭐⭐ | sgcc.com.cn、csg.cn |
| 政府官网发布 | ⭐⭐⭐ | nea.gov.cn、sasac.gov.cn |
| 主流行业媒体 | ⭐⭐ | 北极星电力网、中国电力新闻网 |
| 微信公众号文章 | ⭐⭐ | 已认证的行业机构账号 |
| 自媒体/未注明来源 | ⭐ | 待核实 |

参考 `references/research_dimensions.md` 中的维度框架和关键词，提升搜索精准度。

### Step 4：结构化记录资讯

将检索结果整理为标准 JSON 格式（参见 `scripts/generate_report.py --template`）：

```json
{
  "company": "企业名称",
  "date": "YYYY-MM-DD",
  "summary": "一句话摘要（不超过50字）",
  "detail": "详细描述（100-200字）",
  "dimension": "data | model | application",
  "app_category": "应用子类（仅 application 维度填写）",
  "credibility": 3,
  "source": "来源链接或出处"
}
```

应用子类选项（来自 `references/research_dimensions.md`）：
- 智能运维与巡检
- 电力调度与预测
- 安全生产
- 客服与用户服务
- 知识管理与办公辅助
- 工程设计
- 碳管理与绿色发展
- 市场交易

### Step 5：生成报告

**方式一：使用脚本（适合有结构化数据时）**
```bash
# 将收集的资讯保存为 news.json
python3 scripts/generate_report.py --input news.json --period "2024年4月" --output report.md
```

**方式二：直接使用模板（适合即时生成）**
参考 `assets/report_template.md` 模板结构，直接填写内容输出报告。

报告采用双维度结构：
- **Part A 企业登记表**：按企业维度列举所有动态
- **Part B 主题分类**：按数据建设/行业模型/应用落地分类展示
- **趋势洞察**：基于本期动态归纳 2-3 个行业趋势

### Step 6：归档（可选）

如需持久化存档，将报告文件和原始 JSON 数据保存至用户指定目录，文件命名规范：
- 报告：`energy-llm-report-YYYY-MM.md`
- 原始数据：`energy-llm-news-YYYY-MM.json`

---

## 参考资源

| 文件 | 用途 |
|------|------|
| `references/energy_companies.md` | 重点企业名单、信息来源列表、搜索关键词组合 |
| `references/research_dimensions.md` | 调研维度框架、应用子类说明、报告结构规范 |
| `scripts/fetch_energy_news.py` | 生成搜索查询指引 |
| `scripts/generate_report.py` | 从 JSON 数据生成结构化 Markdown 报告 |
| `assets/report_template.md` | 报告 Markdown 模板 |
