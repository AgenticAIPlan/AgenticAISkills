# AI 硬件生态采集路由与站点优先级

## 用途

用这份文档统一采集路径、站点优先级和证据保留要求。采集时既要看新闻本身，也要看它处于产业链的哪个环节，以及会影响哪些模型厂商、云厂商或部署场景。

## 渠道与工具映射

| 渠道类型 | 典型来源 | 优先工具 | 重点观察 |
|----------|----------|----------|----------|
| 行业媒体 / 科技媒体 | Tom's Hardware、AnandTech、ServeTheHome、SemiAnalysis、36氪 | `web-research` | 发布、评测、行业结构变化 |
| 厂商官网 / 伙伴页面 | 产品页、新闻稿、路线图、案例页 | `web-research` / `chrome-devtools` | 合作、认证、交付、路线图 |
| 模型厂商 / 云厂商公告 | OpenAI、Anthropic、Google、AWS、Azure、GCP 等博客 | `web-research` / `chrome-devtools` | 采购、部署、替代、云算力布局 |
| 社区与开发者站点 | Reddit、GitHub Issues、Hacker News、V2EX、Chiphell | `web-research` | 驱动、SDK、兼容性、部署反馈 |
| 社交与视频平台 | 微博、X、LinkedIn、小红书、B站、抖音 | `daily-hot-news` / `xiaohongshu` / `playwright-mcp` | 热点扩散、评论区信号、KOL 观点 |
| 资本 / 政策信息源 | 财报问答、政策公告、监管页面 | `web-research` | 资本开支、政策变化、合规风险 |

## 关键词包组织方式

建议拆成 6 组：

1. **核心词**：品牌、机构、产品线、型号、代号
2. **上游词**：HBM、CoWoS、wafer、substrate、光模块、电源、良率
3. **中游词**：GPU、NPU、ASIC、server、rack、liquid cooling、interconnect
4. **下游词**：cloud、datacenter、inference、enterprise、cluster、capex
5. **模型厂商词**：OpenAI、Anthropic、Google、Meta、xAI、DeepSeek 等
6. **风险词**：缺货、跳票、断供、制裁、兼容问题、价格波动、砍单、过热

## 站点优先级

### P1：日常必看

- 行业媒体、厂商博客、伙伴新闻稿、云厂商与模型厂商公告
- GitHub Issues、Reddit、Hacker News
- 关键产品页、SDK / 驱动更新日志

### P2：发布期或争议期重点看

- 微博、X、LinkedIn、小红书、B站、知乎、抖音
- 渠道到货页、价格页、电商评论区
- V2EX、贴吧、Discord 等社区

### P3：事件触发式补充

- 财报摘要、监管公告、政策站点
- 漏洞披露站点、研究报告摘要
- 供应链爆料与行业传闻渠道

## 证据保留要求

采集完成后至少确认：

- 对转载稿回溯原始来源
- 对价格、产能、交付、资本开支信息标明核验状态
- 对模型厂商与硬件厂商关系区分“确认合作”“测试验证”“市场猜测”
- 对高风险样本保留原始链接、时间、机构、关键引用和二次来源链路
