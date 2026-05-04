#!/usr/bin/env python3
"""
模块七：商机 Close Readiness 评分。
借鉴 SprintClub 的关单准备度评分机制。
8项指标量化评估，给出推进/暂缓/重新鉴定建议。
"""

import sys
import os
import json

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCORE_ITEMS = [
    {
        "id": 1,
        "name": "需求已明确",
        "description": "客户痛点和需求已被清晰表述，而非模糊意向",
        "gov_weight": 1,
        "ent_weight": 1,
        "tech_weight": 1,
    },
    {
        "id": 2,
        "name": "技术决策人已参与",
        "description": "技术评估方已参与会议，不只是采购/行政部门",
        "gov_weight": 1,
        "ent_weight": 2,
        "tech_weight": 2,
    },
    {
        "id": 3,
        "name": "方案已获技术认可",
        "description": "技术团队对我方方案的可行性无根本性反对",
        "gov_weight": 1,
        "ent_weight": 2,
        "tech_weight": 3,
    },
    {
        "id": 4,
        "name": "预算已确认具体金额",
        "description": "客户已明确预算范围（不是'有预算'而是'多少预算'）",
        "gov_weight": 2,
        "ent_weight": 2,
        "tech_weight": 1,
    },
    {
        "id": 5,
        "name": "竞品已识别并有对策",
        "description": "知道客户在评估哪些竞品，并有针对性的差异化话术",
        "gov_weight": 1,
        "ent_weight": 1,
        "tech_weight": 1,
    },
    {
        "id": 6,
        "name": "评分标准已获取",
        "description": "（投标场景）已获取或推断出评审打分的关键维度",
        "gov_weight": 3,
        "ent_weight": 1,
        "tech_weight": 1,
    },
    {
        "id": 7,
        "name": "关键人无未解决反对意见",
        "description": "决策链上的关键人没有明显未被回应的顾虑",
        "gov_weight": 2,
        "ent_weight": 2,
        "tech_weight": 2,
    },
    {
        "id": 8,
        "name": "下一步行动已被客户接受",
        "description": "会后有明确的下一步节点（POC/高层拜访/技术评审），客户已确认",
        "gov_weight": 1,
        "ent_weight": 1,
        "tech_weight": 1,
    },
]


def build_score_prompt(
    client_type: str,
    situation_description: str,
) -> str:
    items_str = "\n".join(
        f"{item['id']}. **{item['name']}** — {item['description']}"
        for item in SCORE_ITEMS
    )

    return f"""# 商机 Close Readiness 评分

## 当前商机情况

{situation_description}

## 8项评分指标

请对以下每项给出 ✅（已达成）或 ❌（未达成），并附上一句说明：

{items_str}

## 评分规则

- 每项达成得1分，满分8分
- **≥7分**：🟢 可以推进报价/投标
- **4-6分**：🟡 建议继续需求深化，明确薄弱项
- **<4分**：🔴 建议重新鉴定商机，评估是否值得继续投入

## 你的输出格式

```
## 商机评分：X/8

| # | 指标 | 状态 | 说明 |
|---|------|------|------|
| 1 | 需求已明确 | ✅/❌ | ... |
...

**总分：X/8 — [建议]**

**薄弱项分析（❌项的改进方向）：**
1. ...

**下一步优先行动（按紧迫程度）：**
1. [最紧急] ...
2. ...
3. ...

**风险预警：**
- ...
```
"""


def main():
    client_type = sys.argv[1] if len(sys.argv) > 1 else "enterprise"
    situation = sys.argv[2] if len(sys.argv) > 2 else "请描述当前商机的进展情况"

    prompt = build_score_prompt(client_type, situation)
    print(prompt)


if __name__ == "__main__":
    main()
