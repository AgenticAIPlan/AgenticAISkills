---
name: ai-hardware-ecosystem-monitor
description: 监控 AI 相关多硬件生态新闻、产业动态与风险信号。用于 GPU、NPU、ASIC、服务器、存储、网络、液冷、电源、光模块、晶圆、先进封装、HBM、ODM/OEM、云厂商、数据中心和大模型厂商相关任务，包括：(1) 跟踪 AI 硬件上下游、算力基础设施和模型厂商新闻，(2) 识别产能、交付、价格、路线图、合作伙伴、部署、兼容与政策等核心议题，(3) 挖掘媒体、分析师、工程师、渠道商、企业客户和关键机构，(4) 监控大模型厂商、云厂商与硬件供应商之间的竞合关系，(5) 生成监测计划、生态情报报告、预警清单和行动建议。触发词包括：AI硬件生态、算力生态监控、AI产业链新闻、GPU产业链、HBM动态、服务器生态、模型厂商动态、云厂商采购、AI基础设施情报、AI供应链预警。
---

# AI 硬件生态监控

## 用途

用这个 Skill 监控 AI 相关多硬件生态新闻、产业动态和风险信号。它的重点不是单一硬件产品口碑，而是围绕 AI 产业链观察上游、中游、下游以及大模型厂商之间的联动关系。

监测重点覆盖：晶圆、先进封装、HBM、GPU / NPU / ASIC、服务器整机、机柜与液冷、网络与光模块、云厂商、数据中心、企业部署，以及 OpenAI、Anthropic、Google、Meta、xAI、DeepSeek、阿里、百度、腾讯、字节、智谱等模型厂商。

不要编造新闻、合作、产能、价格、交付、情绪或风险等级。遇到来源不足、时间不明、引用链条断裂、价格未核验或爆料未证实时，必须明确披露。

## 适用场景

在以下场景优先使用本 Skill：

- 跟踪 AI 硬件上下游新闻和产业链变化
- 观察 GPU、NPU、ASIC、HBM、服务器、液冷、网络等关键环节动态
- 监控大模型厂商、云厂商和硬件供应商的合作、采购、部署和替代关系
- 跟踪新产品发布、路线图、交付、扩产、价格、制裁和政策变化
- 输出日报、周报、专题复盘、竞争态势分析和风险预警

## 监测对象

按以下层级组织监测对象：

1. **上游**：晶圆、先进封装、HBM / DRAM、基板、互连、散热、电源、交换芯片、光模块
2. **中游**：GPU、NPU、ASIC、加速卡、服务器整机、AI 一体机、机柜、液冷系统、ODM / OEM
3. **下游**：云厂商、数据中心、企业客户、行业解决方案商、开发者生态
4. **模型厂商**：OpenAI、Anthropic、Google、Meta、xAI、DeepSeek 及国内外大模型厂商
5. **外部环境**：政策、制裁、出口管制、资本开支、融资、并购、行业标准

## 工作流

### 步骤 1：明确监测范围

先补齐以下信息：

- **监测主体**：品牌、厂商、机构或产业链环节
- **重点对象**：产品线、技术环节、供应链节点、模型厂商、云厂商
- **时间范围**：默认近 7 天；重大事件建议 24 小时或 72 小时滚动监控
- **重点议题**：产能、交付、价格、路线图、合作、部署、兼容、政策、资本开支
- **竞品范围**：明确主要对手、替代方案和对比对象
- **模块范围**：`news`、`supply-chain`、`model-vendor`、`competitor`、`kol`、`risk`、`all`

如果用户没有给全，优先补足“监测主体、重点对象、时间范围、重点议题、竞品范围”五项。

### 步骤 2：组织关键词包

至少准备 6 组关键词：

- **核心词**：品牌名、产品名、型号、SKU、代号
- **上游词**：wafer、CoWoS、HBM、substrate、封装、良率、光模块、电源、散热
- **中游词**：GPU、NPU、ASIC、server、rack、liquid cooling、interconnect、NIC
- **下游词**：cloud、datacenter、inference、deployment、enterprise、cluster、capex
- **模型厂商词**：OpenAI、Anthropic、Google、Meta、xAI、DeepSeek 等
- **风险词**：缺货、跳票、断供、制裁、出口管制、过热、兼容问题、价格波动、砍单

优先覆盖中英文、简称、代号、旧型号和行业常用说法。

### 步骤 3：规划采集路径

至少覆盖 4 类来源：

- **行业媒体 / 科技媒体**：Tom's Hardware、AnandTech、ServeTheHome、SemiAnalysis、36氪、量子位、机器之心
- **官方与合作伙伴页面**：厂商博客、产品页、驱动更新日志、伙伴新闻稿、客户案例
- **社区与开发者站点**：Reddit、GitHub Issues、Hacker News、Chiphell、V2EX
- **模型厂商与云厂商信息源**：OpenAI、Google、Meta、Anthropic、阿里云、AWS、Azure、GCP 等博客或公告
- **社交与视频平台**：微博、小红书、B站、抖音、X、LinkedIn
- **资本与政策信息源**：财报摘要、监管公告、政策网站、行业协会与研究机构

优先复用这些采集能力：

- `web-research`：行业媒体、论坛、官网、伙伴页面调研
- `chrome-devtools`、`playwright-mcp`：复杂页面、动态页面、价格页、评论页抓取
- `daily-hot-news`：微博 / 知乎 / B站 / 抖音热点观察
- `wechat-article-to-markdown`：公众号文章抓取
- `xiaohongshu`：消费级硬件与装机内容搜索
- `arxiv-search`：论文、研究资料、技术趋势检索

重大风险样本必须尽量保留原始链接、发布时间、作者、机构、关键引用和二次来源链路。

### 步骤 4：生成监测计划或加载样本

支持两种模式：

1. **监测计划模式**：先输出关键词包、平台优先级、采集路由、关注对象和执行提示
2. **样本分析模式**：已有 JSON / JSONL / CSV 时，直接运行脚本分析

生成监测计划：

```bash
python3 scripts/ai_hardware_ecosystem_monitor.py       --brand "NVIDIA"       --products "B200,GB200,HGX"       --competitors "AMD,Intel,Google"       --model-vendors "OpenAI,Anthropic,DeepSeek"       --period week       --topic "HBM 供给与模型厂商采购"       --module all       --plan-only
```

### 步骤 5：运行分析脚本

当你已经有结构化样本时，优先执行：

```bash
python3 scripts/ai_hardware_ecosystem_monitor.py       --input records.json       --brand "NVIDIA"       --products "B200,GB200,HGX"       --competitors "AMD,Intel,Google"       --model-vendors "OpenAI,Anthropic,DeepSeek"       --start 2026-04-01       --end 2026-04-07       --module all       --risk-level high       --alert       --output report.md
```

脚本支持：

- `--period day|week|month`：按周期生成时间范围
- `--topic`：指定专项监测议题
- `--model-vendors`：指定需要重点跟踪的大模型厂商
- `--module news|supply-chain|model-vendor|competitor|kol|risk|all`：按模块执行
- `--plan-only`：只输出监测计划
- `--risk-level low|medium|high|critical`：筛选风险等级
- `--alert`：对达到阈值的风险打印预警
- Markdown / JSON / CSV 输出

### 步骤 6：人工复核

把脚本结果视作初筛，不要直接照抄结论。交付前至少检查：

- 新闻是否来自可靠原始来源，是否存在转载失真
- 供给、交付、扩产、价格、资本开支信息是否有二次证据
- 模型厂商与硬件厂商之间的关系是实质合作、测试验证，还是市场猜测
- 风险等级是否需要因客户类型、区域范围、政策背景上调
- 竞品提及是否代表真实替代趋势，而非普通对比讨论

## 数据要求

优先使用 `references/data_schema.md` 的字段结构。最小字段集：

- `platform`
- `title`
- `content`
- `author`
- `url`
- `published_at`
- `likes`
- `comments`
- `shares`
- `views`
- `followers`

对产业链样本，尽量补充 `entity_layer`、`company_type`、`model_vendor`、`component_type`、`region` 等字段。

## 输出要求

默认输出一份 Markdown 报告，至少包含：

1. **监测策略**：模块、关键词包、平台优先级、覆盖限制
2. **生态总览**：时间范围、样本量、渠道分布、主题分布、环节分布
3. **关键新闻**：高热度、高价值、高影响样本及链接
4. **上下游动态**：上游、中游、下游的重要变化
5. **模型厂商动态**：模型厂商与硬件、云、部署相关动态
6. **风险看板**：风险类型、等级、影响范围、建议动作
7. **关键机构 / KOL**：媒体、分析师、工程师、渠道与企业客户名单
8. **竞品与行业变化**：竞品动作、替代趋势、行业结构变化
9. **行动建议**：24 小时动作、本周动作、中期建议

使用 `assets/report_template.md` 作为结构模板。

## 可复用能力

| 能力 | 典型用途 |
|------|----------|
| `web-research` | 行业媒体、论坛、官网、伙伴页面调研 |
| `chrome-devtools` | 复杂页面与无公开 API 页面抓取 |
| `playwright-mcp` | 动态页面、价格页、评论页自动化采集 |
| `daily-hot-news` | 微博 / 知乎 / B站 / 抖音热点观察 |
| `wechat-article-to-markdown` | 公众号文章抓取 |
| `xiaohongshu` | 消费级硬件与装机内容搜索 |
| `arxiv-search` | 论文、研究资料、技术趋势检索 |

## 参考资料

按需加载这些文件，不要一次性全部塞进上下文：

- `references/monitoring_guide.md`：AI 硬件生态监测总指南
- `references/source_integration.md`：采集路由与站点优先级
- `references/taxonomy.md`：生态环节、主题与信号分类
- `references/data_schema.md`：输入数据字段规范
- `references/sentiment_analysis.md`：情绪与影响判断方法
- `references/kol_framework.md`：关键机构与 KOL 识别框架
- `references/risk_assessment.md`：风险判定标准与响应要求

## 验证清单

提交前确认：

- [ ] 已写明监测主体、重点对象、时间范围和样本来源
- [ ] 至少覆盖 4 类来源，或明确说明受限原因
- [ ] 报告包含关键新闻、上下游动态、模型厂商动态和风险项
- [ ] 风险项有等级、触发原因、影响范围与建议动作
- [ ] 已写明使用了哪些采集能力，哪些平台未覆盖以及原因
- [ ] 所有关键结论都能追溯到原始链接或原始记录
- [ ] 已披露数据缺口、样本偏差与无法验证项
