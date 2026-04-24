---
name: ai-overseas-daily
description: 每日自动生成海外 AI/LLM 情报日报。从 8 个数据源聚合情报，经 LLM 生成三板块结构化报告（商业化与竞争格局、数据工程与模型能力突破、应用创新与工程前沿），分发到飞书知识库和如流群。当用户提到"海外AI日报""海外大模型情报""AI市场简报""生成日报""配置日报""海外AI竞争""模型商业化""数据工程突破""应用创新"时触发，也适用于需要定时生成海外 AI 行业情报的场景。
---

# 海外大模型每日情报观察

## 适用场景

- 需要每日自动生成海外 AI/LLM 领域结构化情报报告的运营或管理团队
- 需要跟踪海外模型厂商商业化动态、数据工程前沿、应用创新趋势的决策者
- 需要将 AI 行业情报自动分发到飞书知识库和如流群的团队协作场景
- 需要定时（如每日工作日早晨）执行情报采集和分析的自动化需求

## 输入要求

### 环境配置（首次使用必须完成）

在项目根目录创建 `.env` 文件，以 `assets/.env.example` 为模板，填入以下配置：

**必填项：**

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `RAPIDAPI_KEY` | RapidAPI 密钥（Twitter、Reddit、Product Hunt 数据抓取） | 注册 rapidapi.com，订阅 twitter-api45、reddit34、product-hunt-scraper-api |
| `LLM_API_KEY` | 报告生成 LLM 的 API Key | OpenAI 兼容 LLM 提供商 |
| `LLM_BASE_URL` | LLM 接口 Base URL | LLM 提供商的 API 端点 |
| `LLM_MODEL` | 模型名称 | 如 `gpt-4o`、`ernie-5.0-thinking-latest` |
| `FEISHU_APP_ID` | 飞书应用 App ID | 飞书开放平台 |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret | 飞书开放平台 |
| `FEISHU_WIKI_SPACE_ID` | 飞书知识库空间 ID | 知识库页面 URL |
| `RULIU_WEBHOOK_URL` | 如流群 Webhook URL | 如流群设置 |
| `RULIU_GROUP_ID` | 如流群 ID（数字） | 如流群设置 |

**选填项：**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BOCHA_API_KEY` | 博查搜索 API Key | 未配置则跳过雷达6 |
| `X_LIST_URL` | Twitter/X 精选 List URL | 未配置则跳过雷达1 |
| `FEISHU_WIKI_PARENT_NODE_TOKEN` | 飞书知识库父节点 | 空（空间根目录） |
| `FEISHU_BASE_URL` | 飞书 API 域名 | `https://open.feishu.cn` |
| `FEISHU_WIKI_DOMAIN` | 飞书知识库页面域名 | `bytedance.feishu.cn` |
| `http_proxy` / `https_proxy` | 代理地址（支持 PAC 自动解析） | 无代理 |

### 依赖安装

```bash
pip install -r scripts/requirements.txt
```

## 执行步骤

### 步骤1：确认配置就绪

检查项目根目录是否存在 `.env` 文件且必填项已配置。若未配置，引导用户按上方配置表填写。检查 Python 依赖是否已安装。

### 步骤2：运行情报管线

```bash
# 完整运行（采集 + 生成报告 + 分发）
python3 scripts/daily_report.py

# 仅生成报告，不分发（测试用）
python3 scripts/daily_report.py --no-distribute
```

管线自动执行以下流程：

1. **8 雷达数据采集**：依次从 Twitter List、Twitter 全网搜索、Hacker News、Reddit、Product Hunt、博查搜索、ArXiv、HuggingFace Papers 采集数据
2. **跨源数据清洗**：去重、去过期、去空内容，合并为统一情报流
3. **LLM 情报加工**：将清洗后的情报流送入 LLM，按 `references/system_prompt.md` 中的 prompt 生成三板块结构化报告
4. **自动分发**：飞书知识库（完整报告）→ 如流群（精简摘要 + 飞书链接）

### 步骤3：验证输出

- 检查脚本输出中各雷达的采集结果（条数）
- 确认报告文件已生成（`YYYY-MM-DD-Overseas-LLM-Insight.md`）
- 若启用了分发，确认飞书知识库页面和如流群消息发送成功

### 步骤4（可选）：设置定时调度

```bash
# crontab 示例：工作日 9:03 AM 自动执行
3 9 * * 1-5 cd /path/to/project && python3 scripts/daily_report.py >> /path/to/project/cron.log 2>&1
```

## 输出要求

### 完整日报（Markdown 文件）

生成 `YYYY-MM-DD-Overseas-LLM-Insight.md`，包含三板块：

**板块一：海外商业化与竞争格局**
- 聚焦模型厂商如何赚钱、如何竞争
- 每条必须有商业机制信息（定价、营收、市场份额），纯投资/纯技术发布不收录
- 格式：**标题** + 子弹句 + 商业拆解 + 来源

**板块二：数据工程与模型能力突破**
- 聚焦数据策略如何驱动模型能力提升
- 每条必须论证先进性（对比已有方法的突破点），成熟技术重述不收录
- 格式：**标题** + 子弹句 + 先进性说明 + 来源

**板块三：应用创新与工程前沿**
- 聚焦 AI 原生应用创新与模型落地工程方法
- 每条必须说明创新性（解决什么新问题/开创什么新模式/达到什么新指标）
- 格式：**标题** + 子弹句 + 入选理由 + 来源

### 如流群精简摘要

- 每条新闻：**加粗标题** + 不加粗子弹句
- 不含趋势总结、入选理由、详细分析
- 末尾附飞书知识库完整报告链接
- 字符上限 2000（超长自动降级纯文本）

### 飞书知识库页面

- 完整报告发布为飞书文档
- Markdown 自动转为飞书 Block（标题、加粗、列表、引用等）

## 代理配置

管线自动处理被墙站点的代理（ArXiv、HuggingFace），对不需要代理的站点直连。支持：
- PAC URL（如 `http://pac.internal.company.com/proxy.pac`）— 自动解析为实际代理地址
- 直连代理（如 `http://proxy-host:port`）
- 所有站点均可直连时无需配置

## 自定义指引

| 自定义项 | 操作位置 | 说明 |
|----------|----------|------|
| 更换 Twitter List | `.env` 中的 `X_LIST_URL` | 设置自己的 X List URL，建议添加 AI 研究者、模型厂商、VC 分析师 |
| 修改报告 prompt | `references/system_prompt.md` | 调整板块定义、选题门控、语言风格、红线规则 |
| 调整搜索关键词 | `scripts/daily_report.py` 中的 `fetch_twitter_global_data()` 和 `fetch_bocha_data()` | 修改 `query` 字符串或 `queries` 列表 |
| 增减分发渠道 | `scripts/distribute.py` 中的 `distribute_report()` | 新增发布函数并在其中调用 |
| 适配国际版飞书 | `.env` 中设置 `FEISHU_BASE_URL=https://open.larksuite.com` 和 `FEISHU_WIKI_DOMAIN=yourorg.larksuite.com` | 国际版 Lark 兼容 |

## 参考资料

- `references/system_prompt.md`：LLM 报告生成的完整 prompt，控制板块定义、选题门控标准、输出格式、语言风格和红线规则
- `assets/.env.example`：环境配置模板，含各配置项的详细注释和获取方式
