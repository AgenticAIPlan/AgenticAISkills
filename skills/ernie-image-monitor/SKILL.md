---
name: ernie-image-monitor
description: 当用户需要对 ERNIE-Image（百度文心图像生成模型）进行舆情监测时使用本 Skill。覆盖知乎、小红书、微信公众号、百度搜索四个平台，自动采集账号名称、内容摘要、发布时间，由 Claude 进行语义情感判断（正面/负面/中性），并将结构化报告以表格格式上传至飞书文档。依赖 OpenCLI（~/.local/bin/opencli）和 lark-cli（~/.local/bin/lark-cli）。
---

# ERNIE-Image 舆情监测

对 ERNIE-Image 相关讨论进行多平台采集、语义情感分析，并生成结构化飞书报告。

每次运行结果上传到飞书时，必须创建一份**新文档**，不覆盖历史记录。

## 适用场景

- 用户想了解 ERNIE-Image 在各平台的讨论热度与口碑
- 用户需要汇总某段时间内的舆情，并以表格方式归档到飞书
- 用户需要追踪某次发布（如开源发布、版本更新）后的市场反应

> **监测范围限定：** 仅采集与 ERNIE-Image 直接相关的内容，其他图像生成模型（Midjourney、Qwen-Image、Stable Diffusion 等）的讨论不纳入监测，即使在同一篇文章中被提及。

## 内容过滤规则

### 相关性过滤

仅保留标题或内容摘要中包含以下关键词之一的条目：

| 关键词 | 说明 |
|--------|------|
| `ERNIE-Image` / `ERNIE Image` | 模型英文名 |
| `ERNIE-ViLG` | 前代模型名 |
| `文心图像` / `文心文生图` / `文心生图` | 中文相关表述 |
| `文心一格` | 百度文心图像生成产品名 |

不包含上述关键词的条目一律过滤，不进入报告。

### 日期过滤

ERNIE-Image 正式发布日期为 **2026-04-14**，仅保留发布时间 **≥ 2026-04-14** 的内容。

- 发布时间明确早于 2026-04-14 的条目直接丢弃
- 发布时间无法解析的条目默认保留，交由 Claude 在情感判断时二次核查

## 前置条件

运行前确认以下依赖已就绪：

```bash
# 检查 OpenCLI 连通性
~/.local/bin/opencli doctor

# 如未安装 OpenCLI
npm install -g @jackwener/opencli --prefix ~/.local

# 检查 lark-cli
~/.local/bin/lark-cli --version
```

OpenCLI 需要 Chrome 浏览器扩展以访问需要 Cookie 的平台（知乎、小红书）。
扩展加载路径：`~/.local/lib/node_modules/@jackwener/opencli/extension/`

## 输入要求

- 监测关键词（默认：`ERNIE-Image` / `文心图像` / `百度文心图像生成`）
- 各平台抓取条数限制（默认每平台 20 条）
- 目标平台列表（默认全部）
- 飞书文档标题（默认含抓取时间戳自动生成）

## 执行步骤

### 第一步：运行采集脚本

```bash
# 全平台采集（推荐）
python3 skills/ernie-image-monitor/scripts/monitor.py --limit 20 --save

# 指定平台
python3 skills/ernie-image-monitor/scripts/monitor.py --platforms zhihu xhs --limit 20
python3 skills/ernie-image-monitor/scripts/monitor.py --platforms weixin baidu --limit 10
```

脚本输出 JSON 文件（`ernie_image_monitor_<YYYYMMDD_HHMM>.json`），`sentiment` 字段为空，由 Claude 填写。

### 第二步：Claude 语义情感判断

脚本不做情感分析。Claude 读取每条数据的 `title` + `content_snippet`，进行语义判断：

| 情感 | 判断标准 |
|------|----------|
| 正面 ✅ | 赞扬、推荐、使用满意、积极体验、技术肯定 |
| 负面 ❌ | 批评、抱怨、失望、不满、质疑真实性 |
| 中性 ➖ | 客观介绍、新闻报道、教程、无明显倾向的讨论 |

**不得使用关键词匹配**，必须根据语义上下文综合判断。

### 第三步：生成表格格式报告

报告结构：

1. **概况汇总表**：总条数、各情感分布、各平台条数

2. **各平台详情表**（按发布时间倒序排列）：

   | # | 账号名称 | 标题 | 发布时间 | 情感 | 来源 |
   |:-:|----------|------|:--------:|:----:|:----:|
   | 1 | 账号A | 标题内容… | 2026-04-16 | 正面 ✅ | [查看](url) |

每个平台独立分节，小节标题注明条数和情感分布概况。

### 第四步：上传飞书文档（每次必须）

```bash
# 将报告写入文件
# feishu_report.md 包含完整 Markdown 表格内容

# 必须从 ~ 目录执行，使用相对路径
cd ~ && ~/.local/bin/lark-cli docs +create \
  --title "ERNIE-Image 舆情监测报告 <YYYY-MM-DD HH:MM>" \
  --markdown @feishu_report.md
```

- 每次运行必须创建新文档（`+create`），**不覆盖已有文档**
- 文档标题必须包含本次抓取时间戳
- 执行成功后，将返回的飞书文档 URL 告知用户

## 输出要求

- 输出为结构化 Markdown 表格，每条数据占一行
- **仅输出与 ERNIE-Image 直接相关、发布时间 ≥ 2026-04-14 的条目**
- 情感判断字段必须有值（不得为空）
- 发布时间无法获取时显示 `—`，不得省略该列
- 最终飞书文档 URL 必须返回给用户
- 明确指出哪些平台因超时或权限问题数据不完整

## 平台覆盖说明

| 平台 | 采集方式 | 需要登录 |
|------|----------|----------|
| 知乎 | `opencli zhihu search` | 是（Cookie） |
| 小红书 | `opencli xiaohongshu search` | 是（Cookie） |
| 微信公众号 | Google `site:mp.weixin.qq.com` | 否 |
| 百度搜索 | Google `site:baidu.com` 系列 | 否 |

## 默认搜索关键词

- `ERNIE-Image`
- `文心图像`
- `百度文心图像生成`

如需修改，编辑 `scripts/monitor.py` 中的 `SEARCH_KEYWORDS` 列表。

## 参考资料

- [references/opencli_commands.md](references/opencli_commands.md) — OpenCLI 完整命令参考
- [references/feishu_upload_guide.md](references/feishu_upload_guide.md) — lark-cli 飞书上传操作说明
