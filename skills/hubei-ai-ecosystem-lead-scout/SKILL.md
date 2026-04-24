---
name: hubei-ai-ecosystem-lead-scout
description: Use this skill when the task is to discover, analyze, classify, or structure Hubei or Wuhan enterprise leads for AI ecosystem cooperation. Apply it for enterprise clue collection, AI demand judgment, partner prioritization, lead-table normalization, or SOP-driven screening tied to Baidu PaddlePaddle, regional AI enablement, technical exchange, training, or ecosystem partnership building.
---

# Hubei AI Ecosystem Lead Scout

## Overview

This skill standardizes how to collect and judge enterprise leads in Hubei for AI ecosystem cooperation. It is built for regional ecosystem operations rather than pure sales prospecting, so the core output is a judgment on AI demand, scene fit, and partnership potential.

Use this skill when you need to:
- find Hubei or Wuhan enterprises worth researching
- analyze whether an enterprise has AI application scenarios
- judge whether an enterprise is a potential ecosystem partner
- classify leads as key account, ecosystem partner, technical case, or hold
- turn messy research notes into a consistent lead sheet or SOP output

If the user provides a raw enterprise list and wants a standard template quickly, use `scripts/build_lead_template.py`.

## Workflow

1. Confirm the task target.
Determine whether the user needs enterprise discovery, lead analysis, table cleanup, partner classification, or SOP generation.

2. Gather only the minimum enterprise facts first.
Start with enterprise name, city, industry, core products or business, enterprise scale, and technical or R&D capability if available.

3. Focus on AI-scene evidence, not broad company profiling.
Check recent public signals such as official news,公众号内容, activity participation, product updates, partner introductions, hiring, and digital transformation messaging.

4. Judge partnership value using the two hard gates.
An enterprise is a strong candidate only if both are broadly true:
- it has a plausible AI application scenario
- it has a technical team or technical carrying capacity

If the scenario is good but the technical team is unclear, do not discard it immediately. Mark it as observation or light-touch communication.

5. Classify the enterprise.
Use exactly one primary classification:
- `大客户`: large scale, strong regional influence, demo effect, and clear AI cooperation scenes
- `生态伙伴`: has AI demand or cooperation basis and can join project, technology, training, activity, or ecosystem collaboration
- `技术案例`: an outstanding ecosystem partner with representative AI scenarios and external storytelling value
- `暂不跟进`: no clear AI scene, weak technical basis, insufficient information, unclear timing, or poor fit

6. Produce a structured result.
When possible, output in a lead-table-ready format using the standard field set below.

7. Normalize raw enterprise lists when needed.
If the input is only a company-name list, run `python3 scripts/build_lead_template.py --input <file> --output-dir <dir>`. The script creates both CSV and XLSX templates with the standard columns.

## Standard Fields

Use these columns when building or normalizing a lead sheet:

| 字段 | 用途 |
| --- | --- |
| 企业名称 | 唯一识别对象 |
| 所在城市 | 武汉或湖北其他地市 |
| 行业 | 行业赛道判断 |
| 核心产品/业务 | 识别业务场景 |
| 企业规模 | 判断大客户潜力与影响力 |
| 技术/研发情况 | 判断是否具备技术承接能力 |
| 近期动态 | 提取公开信号来源 |
| AI需求判断 | 明确是否存在明确需求、潜在需求、待观察 |
| 潜在应用场景 | 例如质检、客服、知识库、培训、数据分析 |
| 线索来源 | 政府名单、官网、公众号、活动名单、伙伴推荐等 |
| 分类结果 | 大客户、生态伙伴、技术案例、暂不跟进 |
| 跟进建议 | 建议观察、交流、邀约活动、技术交流等 |
| 当前状态 | 新增、观察中、已分析、待沟通等 |
| 更新时间 | 便于周度更新 |

## Classification Details

### 大客户

Use when the enterprise is large, influential, often group-like or leading in its region or industry, has demonstration value, and also shows clear AI cooperation scenes.

### 生态伙伴

Use when the enterprise has AI demand or cooperation willingness, has technical cooperation potential, and can participate in project, technical, training, activity, or ecosystem collaboration.

### 技术案例

Use only for strong ecosystem partners with representative AI application scenes and good external case value.

### 暂不跟进

Use when there is no clear AI scene, no obvious technical basis, insufficient public information, unclear cooperation timing, or weak fit with Baidu AI ecosystem work.

## Quality Threshold

A high-quality lead usually has most of these traits:
- a credible AI application scene
- technical or R&D capacity
- public signals showing intelligent upgrade or innovation direction
- regional or industry influence
- potential fit for Baidu AI ecosystem enablement

## Judgment Rules

Prioritize these signals:
- clear intelligent upgrade, digital transformation, or AI application intent
- industry scenes suitable for AI, such as knowledge Q&A, visual inspection, customer service, data analysis, training, operations support, or model-based efficiency tools
- evidence of technical or R&D capability
- strong regional or industry influence
- ability to become an activity, training, project, or technical cooperation object

Avoid overvaluing:
- company size without a usable AI scene
- generic innovation messaging without concrete business signals
- contact completeness as a proxy for quality

## Output Style

Keep outputs concise and decision-oriented. For each enterprise, prefer:
- one-line enterprise summary
- AI demand judgment
- potential application scenes
- classification result
- short follow-up suggestion

For one enterprise, prefer this compact structure:

```markdown
企业名称：
所在城市：
行业：
核心产品/业务：
技术/研发情况：
近期动态：
AI需求判断：
潜在应用场景：
分类结果：
跟进建议：
```

If the user asks for batch analysis, use a compact table or spreadsheet with the standard fields in this file.

Use `scripts/build_lead_template.py` when:
- the user has a plain-text, CSV, TSV, or JSON enterprise list
- you need to normalize rows before analysis
- you want a reusable lead sheet for batch enrichment by another agent

## Script Notes

`scripts/build_lead_template.py` turns a raw enterprise list into a standard spreadsheet template.

Supported inputs:
- `.txt`: one enterprise name per line
- `.csv` or `.tsv`: first column or a detected `企业名称` or `company` style column
- `.json`: a list of strings or objects containing a company-name field

Outputs:
- `hubei_ai_leads_template.csv`
- `hubei_ai_leads_template.xlsx`

Recommended command:

```bash
python3 scripts/build_lead_template.py --input raw_enterprises.txt --output-dir ./out
```


## Sample Input And Output

Use this section to understand the expected script input, generated spreadsheet shape, and analysis output style before first use.

### Sample input: plain text enterprise list

Create a `.txt` file with one enterprise name per line. Duplicate names are removed while preserving the first occurrence.

```text
武汉示例智能制造有限公司
湖北示例医药科技集团
武汉示例智能制造有限公司
```

Run:

```bash
python3 scripts/build_lead_template.py \
  --input sample_enterprises.txt \
  --output-dir ./out \
  --source-label 政府重点企业名单 \
  --status 新增
```

Generated files:
- `out/hubei_ai_leads_template.csv`
- `out/hubei_ai_leads_template.xlsx`

Sample CSV output preview:

```csv
企业名称,所在城市,行业,核心产品/业务,企业规模,技术/研发情况,近期动态,AI需求判断,潜在应用场景,线索来源,分类结果,跟进建议,当前状态,更新时间
武汉示例智能制造有限公司,,,,,,,,,政府重点企业名单,,,新增,
湖北示例医药科技集团,,,,,,,,,政府重点企业名单,,,新增,
```

Field meaning in this sample:
- `企业名称`: filled from the raw input list
- `线索来源`: filled from `--source-label`
- `当前状态`: filled from `--status`
- other fields: intentionally left blank for a later research or enrichment agent to complete

### Sample input: CSV enterprise list

The script can read a CSV with a company-name column. Supported column names include `企业名称`, `公司名称`, `名称`, `company`, `company_name`, and `name`.

```csv
企业名称,所在城市,行业
武汉示例光电科技股份有限公司,武汉,光电子
宜昌示例化工集团有限公司,宜昌,先进材料
```

Run:

```bash
python3 scripts/build_lead_template.py --input sample_enterprises.csv --output-dir ./out
```

### Sample output: single enterprise analysis

When an agent enriches one enterprise after public research, use this style. Keep the judgment concise, evidence-based, and decision-oriented.

```markdown
企业名称：武汉示例光电科技股份有限公司
所在城市：武汉
行业：光电子/智能制造
核心产品/业务：光电器件、检测设备、智能产线相关产品
技术/研发情况：公开信息显示企业设有研发团队，并持续发布技术升级和产线改造动态
近期动态：近期企业公众号提到数字化产线升级、工业视觉检测和智能制造示范项目
AI需求判断：存在潜在 AI 需求，重点在工业视觉、质检和生产数据分析
潜在应用场景：视觉缺陷检测、设备预测性维护、工艺参数分析、员工 AI 应用培训
分类结果：生态伙伴
跟进建议：建议邀请参加 AI+制造技术交流，进一步确认研发团队和具体试点场景
```

### Sample output: batch screening table

For batch screening, return a compact table and avoid long company profiles.

| 企业名称 | 所在城市 | 行业 | AI需求判断 | 潜在应用场景 | 分类结果 | 跟进建议 |
| --- | --- | --- | --- | --- | --- | --- |
| 武汉示例光电科技股份有限公司 | 武汉 | 光电子/智能制造 | 存在潜在需求 | 视觉质检、设备运维、数据分析 | 生态伙伴 | 建议技术交流 |
| 湖北示例医药科技集团 | 宜昌 | 医药健康 | 待观察 | 研发知识库、文献分析、培训赋能 | 生态伙伴 | 建议先观察交流 |
| 武汉示例商贸有限公司 | 武汉 | 商贸服务 | 暂未发现明显需求 | 暂无明确场景 | 暂不跟进 | 暂不投入重点资源 |

## Reusable Prompt Templates

Use these prompts when another agent needs to call this skill with stable output expectations.

### Single Enterprise Analysis

```text
Use $hubei-ai-ecosystem-lead-scout to analyze this enterprise for Hubei AI ecosystem cooperation.
Focus on whether it has a credible AI application scenario, whether it has technical or R&D capacity, what cooperation direction is most plausible, and which one classification fits best.
Output with these fields:
企业名称
所在城市
行业
核心产品/业务
技术/研发情况
近期动态
AI需求判断
潜在应用场景
分类结果
跟进建议
```

### Batch Enterprise Screening

```text
Use $hubei-ai-ecosystem-lead-scout to screen this batch of Hubei or Wuhan enterprises for AI ecosystem partnership potential.
For each enterprise, judge AI demand, infer possible application scenes from public signals, and classify it as 大客户、生态伙伴、技术案例、暂不跟进.
Return the result as a compact table using the standard fields in this skill.
```

### Lead Sheet Enrichment

```text
Use $hubei-ai-ecosystem-lead-scout to enrich this enterprise lead sheet.
Do not rewrite the whole table. Fill missing fields where the public information is sufficient, especially:
技术/研发情况
近期动态
AI需求判断
潜在应用场景
分类结果
跟进建议
Keep judgments concise and decision-oriented.
```

### Activity Or Training Target Selection

```text
Use $hubei-ai-ecosystem-lead-scout to identify which enterprises are best suited for AI technical exchange, training, or regional ecosystem activity invitation.
Prioritize enterprises with clear scenarios, technical carrying capacity, and regional influence.
For each recommended enterprise, explain the most suitable cooperation entry point in one sentence.
```

## Collaboration Notes

When this skill is used with other agents or tools:
- use the script first if the input is only a raw company list
- use web research second to gather recent public signals
- apply classification only after checking both AI scene plausibility and technical capacity
- prefer concise judgments over long company profiles
- keep one primary classification per enterprise unless the user explicitly asks for multi-tagging

## Guardrails

- Do not classify a company as high priority based only on size or fame.
- Do not infer strong AI demand without at least one business-scene signal.
- If evidence is weak, mark the lead as observation-oriented rather than overcommitting.
- If the company has strong scenes but unclear technical team, keep it in observation or light-touch communication instead of discarding it.
- For this skill, partnership value matters more than contact completeness.
