---
name: business-archives-full
description: This skill should be used when the user wants to create a comprehensive company profile archive following a structured 7-section workflow. Triggers include phrases like "帮我制作企业档案", "生成完整企业档案", "制作【公司名称】的企业档案". The skill follows a detailed SOP to generate a company profile with: basic info (from web search), main products, founder info, product introduction, AI scenarios, benchmark customers, company development history, and enterprise news.
---

# 企业档案制作 Skill（完整版）

This skill generates a comprehensive company profile following the 7-section SOP workflow.

## Workflow Overview

When the user provides a company name, execute the following steps in order:

### Step 1: Search Basic Information (工商信息搜索)

Search for company basic info using web search. Query patterns:
- `{公司名称} 工商信息 注册资本 法定代表人`
- `{公司名称} 企查查 爱企查 基本信息`
- `{公司名称} 参保人数 员工规模`

Collect: 企业名称、注册资本、注册地、股权信息、社保人数、成立时间、荣誉资质、知识产权数量

### Step 2: Generate Main Products (主营产品)

Use the prompt from `references/01_main_products.md`:
- Replace `{公司名称}` with actual company name
- Generate concise product introduction

### Step 3: Generate Founder Information (创始人信息)

Use the prompt from `references/02_founder_info.md`:
- Replace `{公司名称}` with actual company name
- Follow the reference format for consistent output

### Step 4: Generate Product Introduction (产品介绍)

Use the prompt from `references/03_product_intro.md`:
- Replace `{公司名称}` with actual company name
- Focus on AI/artificial intelligence related products
- Use numbered list format

### Step 5: Generate AI Scenarios (AI场景与需求)

Use the prompt from `references/04_ai_scenarios.md`:
- Replace `{公司名称}` with actual company name
- Focus on AI-related business scenarios

### Step 6: Generate Benchmark Customers (标杆客户)

Use the prompt from `references/05_benchmark_customers.md`:
- Replace `{公司名称}` with actual company name
- Organize by industry categories
- Include cooperation descriptions

### Step 7: Generate Company Development History (企业发展)

Use the prompt from `references/06_company_development.md`:
- Replace `{公司名称}` with actual company name
- Timeline format in chronological order

### Step 8: Generate Enterprise News (企业新闻)

Use the prompt from `references/07_enterprise_news.md`:
- Replace `{公司名称}` with actual company name
- Prioritize cooperation-related news
- Reverse chronological order (newest first)

## Output Format

Generate a complete Markdown document with the following structure:

```markdown
# 【公司名称】企业档案

## 一、基本信息
| 字段 | 内容 |
|------|------|
| 企业名称 | XXX |
| 注册资本 | XXX |
| 注册地 | XXX |
| 成立时间 | XXX |
| 经营状态 | XXX |
| 社保人数 | XXX |
| 知识产权 | XXX |

## 二、主营产品
[AI生成内容]

## 三、创始人信息
[AI生成内容]

## 四、产品介绍
[AI生成内容]

## 五、AI场景与需求
[AI生成内容]

## 六、标杆客户
[AI生成内容]

## 七、企业发展
[AI生成内容]

## 八、企业新闻
[AI生成内容]

---
*档案生成时间: YYYY-MM-DD*
*数据来源: 爱企查、企查查、企业官网等公开渠道*
```

## Notes

- Execute web searches in parallel when possible to speed up the process
- If exact data cannot be found, use "公开渠道暂未披露" or "未知"
- Always maintain the non-table format requirement as specified in each section's prompt
- Save the final document to the workspace with filename: `{公司名称}_企业档案.md`
