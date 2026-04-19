---
name: llm-data-research
description: |
  大模型数据动态定期洞察 Skill。用于自动从小红书、微信公众号、百度、行业媒体采集最新数据，**重点监控头部厂商和外部数商的"招募动态"**（数据标注任务招募、专家招募画像），推断下一代模型发力方向，生成 Excel 报告和市场洞察。

  关键原则：凡是用户问到大模型数据相关市场动态，不能仅凭训练知识回答——必须启动此 Skill 进行实时信息采集，因为这个领域变化极快，训练知识几乎肯定已过时。

  以下场景请务必触发此 Skill（即使你认为自己能直接回答）：
  - 询问大模型数据标注、训练数据、数据服务市场的"最新动态"、"最近情况"、"现在格局"
  - 询问字节/百度/阿里/腾讯/DeepSeek 在数据层面的发力方向或合作情况
  - 询问数据服务商（数据堂、海天瑞声、倍赛科技、博登智能、Talents AI、一面千识等）的新进展、融资、中标
  - 要求搜集/整理/调研大模型专家标注、预训练数据、RLHF数据、SFT数据相关内容
  - 要求监控"数据标注任务招募"、"专家招募画像"，反推模型发力方向
  - 要求评估外部数商（Talents AI、一面千识等）的生产能力和专家储备质量
  - 要求调研 OpenAI/Google/Meta/Apple/Microsoft 等海外大厂的数据动态
  - 要求生成大模型数据市场报告或 Excel 汇总表
  - 要求设置定时调研任务
  - 说"开始调研"、"帮我调研"、"llm data research"、"数据标注市场分析"、"招募监控"

  判断标准：如果用户的问题需要2024-2025年的具体数字、融资动态、合作线索、中标公告、招募信号等实时信息，就一定要触发此 Skill，而不是凭知识作答。
---

# 大模型数据动态定期洞察 Skill

本 Skill 自动执行完整的大模型数据市场调研流程，涵盖数据采集、Excel 整理、合作线索关联、市场洞察报告输出、定时任务设置、**Word 报告生成**共六个步骤。

**新增核心能力**：监控头部厂商和外部数商的**招募动态**（数据标注任务招募、专家招募画像），通过招募信号反推：
- 头部大厂下一代模型的发力方向（招募什么样的专家 → 在训练哪个能力方向）
- 外部数商（Talents AI、一面千识等）的生产能力和专家储备质量
- 海外大厂（OpenAI、Google、Meta 等）的数据战略动向

---

## 环境前置检查

在开始前确认以下环境就绪：

```bash
# 1. 确认 CDP Proxy 运行（web-access skill 依赖）
curl -s http://localhost:3456/targets | python3.11 -c "import json,sys; t=json.load(sys.stdin); print(f'CDP就绪，{len(t)}个Tab')"

# 2. 确认 Python 版本（openpyxl 安装在 python3.11）
python3.11 -c "import openpyxl; print('openpyxl', openpyxl.__version__)"
```

若 CDP Proxy 未启动，运行：`node ~/.claude/skills/web-access/scripts/check-deps.mjs`

**关键约束**：
- 所有浏览器操作**必须在主线程用 Bash 直接执行**，不得启动子 Agent 执行网络操作（子 Agent 无法继承工具权限）
- Excel 生成使用 `python3.11`（不是 python3 或 python）
- 小红书详情页需登录才能看正文，搜索结果列表页关闭弹窗后可读取卡片信息

### 工具受限时的降级策略

如果 Bash/Write 工具被拒绝，**不要停止，切换到「知识合成 + 内联输出」模式继续执行所有6步**：

1. 继续完成所有6步，文件输出改为内联 Markdown 输出，并在每步开头注明：`> ⚠️ 工具受限：以下为内联输出，建议手动保存`
2. Step 1：列出将执行的具体搜索关键词，从训练知识中综合近期信息（明确标注「来源：训练知识，截止至 XXXX 年」）
3. Step 2 Excel：输出各 Sheet 的列名 + 至少5条真实数据行（Markdown 表格格式）
4. Step 4 报告：完整输出所有8节内容，各节有实质分析，不留空节
5. Step 6 Word：输出完整 `/tmp/llm_report_data.json` JSON 内容（代码块包裹），提示用户可手动运行 `node scripts/generate_report.js --data /tmp/llm_report_data.json`

**用户真正需要的是分析质量**，不只是文件存在。在工具受限时，高质量的内联分析报告比「无法执行」更有价值。

---

## Step 1：多平台信息采集

### 1.1 小红书采集

小红书有反爬机制，必须通过 CDP 操作：

```bash
# 打开搜索页
XHS_ID=$(curl -s "http://localhost:3456/new?url=https://www.xiaohongshu.com/search_result?keyword=大模型专家标注招募" | python3.11 -c "import json,sys; print(json.load(sys.stdin)['targetId'])")
sleep 4

# 关闭登录弹窗（弹窗选择器）
curl -s -X POST "http://localhost:3456/click?target=$XHS_ID" -d '.close-icon' > /dev/null
sleep 1

# 提取搜索结果卡片
curl -s -X POST "http://localhost:3456/eval?target=$XHS_ID" -d '
JSON.stringify(Array.from(document.querySelectorAll("section.note-item, [class*=\"note-item\"]")).map(el => {
  const title = el.querySelector("a[class*=\"title\"] span, [class*=\"title\"] span")?.innerText?.trim() || "";
  const author = el.querySelector("[class*=\"author\"] span")?.innerText?.trim() || "";
  const time_text = el.innerText?.match(/\d{4}-\d{2}-\d{2}|\d+天前|\d+小时前|[0-9]{2}-[0-9]{2}/)?.[0] || "";
  const href = el.querySelector("a[href*=\"explore\"]")?.href || "";
  return {title, author, time_text, url: href};
}).filter(x=>x.title).slice(0,20))
'
```

**搜索关键词**（依次搜索，每次导航到新关键词）：

招募监控类（优先采集）：
1. `大模型专家标注招募`
2. `AI数据标注兼职招募`
3. `Talents AI 招募`
4. `一面千识 标注任务`
5. `数据标注专家 画像`

市场动态类：
6. `大模型数据服务`
7. `大模型训练数据`

每组关键词提取 15-20 条卡片信息（标题、作者、时间、URL）。对于招募类帖子，**重点提取**：发布主体、任务类型描述、专家要求（学历/专业/经验）、薪酬信号。

### 1.2 微信公众号采集

微信公众号是头部厂商和数商发布招募任务的重要渠道，使用 [Access_wechat_article](https://github.com/yeximm/Access_wechat_article) 工具或通过搜狗微信搜索（CDP方式）采集：

```bash
# 方式一：通过搜狗微信搜索（推荐，无需额外工具）
WX_ID=$(curl -s "http://localhost:3456/new?url=https://weixin.sogou.com/weixin?type=2&query=大模型专家标注招募&ie=utf8&s_from=input" \
  | python3.11 -c "import json,sys; print(json.load(sys.stdin)['targetId'])")
sleep 4

# 提取搜索结果
curl -s -X POST "http://localhost:3456/eval?target=$WX_ID" -d '
JSON.stringify(Array.from(document.querySelectorAll(".news-box .txt-box")).slice(0,15).map(el => {
  const title = el.querySelector("h3 a")?.innerText?.trim() || "";
  const href  = el.querySelector("h3 a")?.href || "";
  const account = el.querySelector(".account")?.innerText?.trim() || "";
  const time_text = el.querySelector(".s2")?.innerText?.trim() || "";
  const summary = el.querySelector("p")?.innerText?.trim() || "";
  return {title, account, time_text, summary, url: href};
}).filter(x=>x.title))
'
```

**微信公众号搜索关键词**（依次执行，每次修改 URL 中的 query 参数）：
1. `大模型专家标注招募`
2. `Talents AI 招募 数据标注`
3. `一面千识 标注任务招募`
4. `数据标注 专家 招募 大模型 2025`
5. `AI数据 兼职 专家 画像 招募`
6. `字节/百度/阿里 数据标注 招募`（分别搜索三次）
7. `OpenAI data annotation contractor`（可尝试）

对于高价值文章（招募主体明确 + 任务描述详细），通过 CDP 打开详情页读取正文，提取：招募主体、任务类型、人员画像要求、发布时间。


---

## Step 2：生成 Excel 文件

详细实现参见 `scripts/generate_excel.py`。核心结构如下：

### Sheet 配置

```python
SHEETS = {
    "招募动态": {
        "header_color": "E67E22",  # 橙色，突出显示招募核心数据
        "columns": ["序号","招募主体","招募任务类型","招募人员画像","招募发布时间","薪酬/单价信号","来源渠道","来源URL","内容摘要","采集日期"],
        "widths":  [5,     20,        28,             30,             14,             16,             14,         48,        40,         13    ],
    },
    "小红书&微信公众号": {
        "header_color": "C0392B",  # 红色
        "columns": ["序号","标题","作者/公众号","发布时间","命中关键词","内容摘要","分类标签","招募主体","招募任务类型","URL","采集日期"],
        "widths":  [5,     38,    18,            12,         20,         45,         16,         18,         22,            48,    13   ],
    },
    "网页搜索&行业媒体": {
        "header_color": "1A5276",  # 深蓝
        "columns": ["序号","标题","来源平台","发布时间","涉及公司","关键数字","数据类型","内容摘要","URL","采集日期"],
        "widths":  [5,     40,    13,        12,         28,        20,        16,         52,        48,   13   ],
    },
    "厂商合作动态线索": {
        "header_color": "117A65",  # 深绿
        "columns": ["序号","大模型厂商","合作方/数据服务商","合作内容","数据类型","金额/规模","时间","训练阶段","来源","可信度","分析备注"],
        "widths":  [5,     14,          18,                  38,        18,         18,          11,    16,       18,     9,       35     ],
    },
    "汇总分析": {
        "header_color": "4A235A",  # 深紫
        "sections": ["来源分布统计", "数据类型热度", "厂商战略对比矩阵"],
    }
}
```

### 分类标签规则

对采集内容自动打标签，规则：

| 关键词 | 分类标签 |
|--------|----------|
| 招聘/岗位/内推 | 招聘/人才 |
| 单价/薪资/工资/元/小时 | 薪酬/定价 |
| 融资/A轮/B轮/投资 | 融资/资本 |
| 中标/采购/招标 | 政府/企业采购 |
| 合成数据/DataFlow/自动 | 合成数据 |
| 视频/多模态/图文 | 视频/多模态 |
| RLHF/SFT/post-training | Post-Training数据 |
| 预训练/pre-training | 预训练数据 |
| 数据飞轮/飞轮 | 数据飞轮 |
| 架构/团队/组织 | 组织架构 |
| Scale AI/对比/估值 | 行业分析 |
| 其他 | 行业生态 |

### 可信度评级标准

| 评级 | 条件 |
|------|------|
| 高 | 来自官方公告/公开中标/权威媒体，有具体数字 |
| 中 | 来自行业媒体报道/多条来源交叉印证 |
| 低-中 | 仅有单一社区帖文/招聘信息推断 |
| 低 | 仅有传言/未经证实 |

### 文件命名

```
~/Downloads/大模型数据市场调研_YYYY-MM-DD.xlsx
```

其中日期为当天采集日期。若当天文件已存在，追加新内容（不覆盖已有数据）。

---

## Step 3：厂商合作动态线索关联

在 Step 1 采集基础上，额外针对以下厂商进行专项搜索：

### 重点厂商列表

**大模型厂商**（甲方）：
- 百度（文心/千帆/百度智能云）
- 字节跳动（火山引擎/豆包/即梦/Dreamina/Seed团队）
- 阿里巴巴（通义/PAI/阿里云）
- 腾讯（混元/腾讯云）
- 科大讯飞（星火）
- DeepSeek
- 智谱AI（GLM）
- 月之暗面（Kimi）
- 商汤科技、旷视、百川智能

**数据服务商**（乙方）：
- 数据堂、海天瑞声
- 倍赛科技、博登智能
- 云测数据、龙猫数据
- 景联文科技、百川数安
- 勤为科技、库帕思（上海库帕思科技）
- 华胜天成、上海新致
- 墨比数据（杭州墨比数据科技）、熠智科技、砺英数智、整数智能
- 定熵科技、淘丁集团、图虫、北部湾数据
- 中启易联、Cosmos/均兴万时、百行数智
- 中文在线、幂逆、SuperCLUE、知识罐头
- 熵基秩序、景联文、浙江大数据中心、无锡快数
- **Talents AI**（重点监控：任务类型/专家要求/发布频率）
- **一面千识**（重点监控：生产能力/专家储备质量/业务侧重）

**海外大厂**（境外甲方，需英文搜索）：
- OpenAI（ChatGPT/o系列/GPT-5）
- Google DeepMind（Gemini/Veo）
- Meta AI（Llama系列）
- Apple（Apple Intelligence）
- Microsoft（Copilot）
- Amazon（Nova/Q）

### 线索关联规则

将采集到的信息整合到 Sheet3，填写以下关键字段：
- **训练阶段**：Pre-training / Mid-training / Post-training（SFT/RLHF）/ RL
- **合作形式**：自建 / 外包 / 战略合作 / 政府采购 / 生态投资
- **数据类型**：参考 Step 2 分类标签

---

## Step 4：市场洞察报告

完成采集和 Excel 生成后，在对话中输出 Markdown 格式的市场洞察报告。**这是技能的核心价值输出，无论工具是否受限都必须完整输出，不允许留空节或省略任何章节。**

### 报告结构（必须完整输出所有8节）

```markdown
## 大模型数据服务市场洞察报告
**采集日期：YYYY-MM-DD | 数据量：XX条（小红书/微信XX + 网页XX + 招募动态XX + 线索XX）**
**信息来源说明：实时采集 / 训练知识合成（截止 XXXX）**  ← 明确标注数据来源类型

---

### 一、市场规模与增速
| 指标 | 数据 | 来源 |
|------|------|------|
| （填入具体指标，如"中国AI数据服务市场规模"）| （填入具体数字）| （媒体/报告名称 + 日期）|

### 二、招募信号分析 → 下一代模型发力方向推断
**（核心章节，必须有至少5行实质内容）**

| 招募主体 | 招募任务类型 | 专家画像要求 | 推断的模型发力方向 | 信号强度 |
|---------|------------|------------|-----------------|---------|
| 字节跳动 | （填入）| （填入）| （填入）| ★★★★ |

### 三、外部数商能力评估
**Talents AI**：
- 当前主要任务类型：（具体类型，如"深度推理标注、数学CoT验证"）
- 专家储备：（规模估计，如"专家库8000+人，含博士/执业资格"）
- 与大厂绑定程度：（如"已与XX签年度框架合同"）
- 信号来源：（平台 + 时间）

**一面千识**：
（同上格式）

### 四、海外大厂数据战略动向
| 公司 | 最新招募/战略信号 | 战略含义推断 | 来源 |
|------|----------------|------------|------|

### 五、各厂商发力方向推断
每家厂商格式：**[厂商名]** — 方向：X | 数据类型：X | 关键信号：X | 推断逻辑：X

### 六、数据服务商格局
| 服务商 | 定位 | 核心客户 | 能力差异化 |
|--------|------|---------|----------|

### 七、核心洞察（≥5条）
1. **[洞察标题]**：（1-2句判断）。支撑数据：（具体数字）。来源：（平台 YYYY-MM-DD）。可信度：高/中/低
2. （同上格式，每条必须有来源和可信度标注）

### 八、趋势变化
（与上期对比的变化描述，若无历史数据则标注「首次调研，无对比基准」）
```

### 洞察质量要求

- 每条洞察必须有**具体数据支撑**（不写"可能"、"也许"、"预计"等模糊表述）
- 每条洞察必须标注**来源**（来源平台 + 文章标题/日期）
- 区分**高可信度洞察**（基于公开中标/融资公告）和**推断型洞察**（基于招聘信号/社区内容）

---

## Step 5：定时任务设置

完成以上流程后，询问用户是否设置定时任务：

> "是否设置每周五 14:00 自动执行调研流程？（定时任务为会话级，需保持 Claude 会话活跃，3天后自动到期）"

若用户确认，使用 CronCreate 工具设置：

```
cron: "0 14 * * 5"
recurring: true
```

定时触发的 prompt 内容参见 `references/cron_prompt.md`。

---

## Step 6：生成 Word 报告

完成 Step 4 报告输出后，**立即**将报告内容序列化为 JSON，调用 Node.js 脚本生成专业 `.docx`，保存到 `~/Downloads/`。

**重要**：Step 6 是 Step 4 的直接延伸，不要跳到 Step 5 后再回来。顺序是 4 → 6 → 5（定时任务最后询问）。

### 6.1 写出报告 JSON 数据文件

将 Step 4 的报告内容**逐节填入**以下结构，写入 `/tmp/llm_report_data.json`。**不允许留空 rows/items，每节至少填2条真实数据**：

```json
{
  "meta": {
    "report_date": "YYYY-MM-DD",
    "data_summary": "小红书/微信XX条 + 网页XX条 + 招募动态XX条 + 线索XX条"
  },
  "sections": {
    "market_size": {
      "title": "一、市场规模与增速",
      "table": { "headers": ["指标","数据","来源"], "rows": [["<指标>","<数据>","<来源>"]] }
    },
    "recruitment_signals": {
      "title": "二、招募信号分析 → 下一代模型发力方向推断",
      "table": {
        "headers": ["招募主体","招募任务类型","专家画像要求","推断的模型发力方向","信号强度"],
        "rows": [["<主体>","<任务>","<画像>","<推断>","★★★★"]]
      }
    },
    "vendor_assessment": {
      "title": "三、外部数商能力评估",
      "items": [{
        "vendor": "<数商名称>",
        "production_scale": "<月均任务量>",
        "expert_pool": "<专家储备描述>",
        "business_focus": "<业务侧重>",
        "client_binding": "<与大厂绑定程度>",
        "source": "<来源平台 YYYY-MM-DD>"
      }]
    },
    "overseas_strategy": {
      "title": "四、海外大厂数据战略动向",
      "items": [{ "company": "<公司>", "signal": "<信号>", "implication": "<战略含义>", "source": "<来源>" }]
    },
    "vendor_directions": {
      "title": "五、各厂商发力方向推断",
      "items": [{
        "vendor": "<厂商>", "direction": "<战略方向>",
        "core_data_type": "<核心数据类型>", "key_signal": "<关键信号>", "reasoning": "<推断逻辑>"
      }]
    },
    "service_provider_landscape": {
      "title": "六、数据服务商格局",
      "table": { "headers": ["服务商","定位","核心客户","能力差异"], "rows": [["<名称>","<定位>","<客户>","<差异>"]] }
    },
    "key_insights": {
      "title": "七、核心洞察",
      "items": [{ "insight": "<洞察判断>", "support": "<数据支撑>", "source": "<来源>", "confidence": "高|中|低" }]
    },
    "trend_changes": {
      "title": "八、趋势变化",
      "items": ["<趋势描述1>", "<趋势描述2>"]
    }
  }
}
```

### 6.2 调用生成脚本

```bash
NODE_PATH=$(npm root -g) \
  node scripts/generate_report.js \
  --data /tmp/llm_report_data.json \
  --output ~/Downloads
```

脚本输出示例：
```
Word 报告已保存: /Users/<用户名>/Downloads/大模型数据市场洞察报告_2026-04-17.docx
```

### 6.3 环境检查

```bash
NODE_PATH=$(npm root -g) \
  node -e "require('docx'); console.log('docx 就绪')"
# 若报错: npm install -g docx
```

### 6.4 输出文件

```
~/Downloads/大模型数据市场洞察报告_YYYY-MM-DD.docx
```

报告包含：封面页（标题/日期/机密提示）、页眉页脚（含页码）、8个章节（表格+要点列表）。

---

## 清理 Tab

完成采集后，关闭所有由本 Skill 创建的 Tab：

```bash
# 记录所有创建的 Tab ID，最后统一关闭
for ID in $ALL_CREATED_TAB_IDS; do
  curl -s "http://localhost:3456/close?target=$ID" > /dev/null
done
```

---

## 错误处理

| 问题 | 解决方案 |
|------|----------|
| 小红书详情页显示"暂时无法浏览" | 详情页需登录，改为从搜索列表提取卡片信息，提示用户登录后可补采正文 |
| 百度链接跳转失败（ERR_INVALID_REDIRECT） | 直接用 Bash 搜索相关关键词获取新链接，不依赖旧 URL |
| python3.11 找不到 openpyxl | 运行 `pip3.11 install openpyxl` 或确认路径 `/Users/$USER/.pyenv/versions/3.11.*/bin/python3.11` |
| CDP Proxy 未启动 | 运行 `node ~/.claude/skills/web-access/scripts/check-deps.mjs` |
| 采集内容过少（<10条）| 扩展关键词，或提示用户登录小红书以获取完整内容 |
| docx 包缺失 | 运行 `npm install -g docx`，或检查 `NODE_PATH=$(npm root -g)` |

---

## 参考文件

- `references/keywords.md` — 完整关键词列表与搜索策略
- `references/companies.md` — 大模型厂商和数据服务商信息库
- `references/cron_prompt.md` — 定时任务触发 prompt 模板
- `scripts/generate_excel.py` — Excel 生成脚本（可独立运行）
- `scripts/generate_report.js` — Word 报告生成脚本（Node.js，可独立运行）
