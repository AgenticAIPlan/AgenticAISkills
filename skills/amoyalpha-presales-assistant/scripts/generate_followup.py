#!/usr/bin/env python3
"""
模块八：跟进行动计划生成。
会后快速生成结构化跟进计划 + 会议纪要草稿。
防止商机因跟进不及时而流失。
"""

import sys
import os

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_followup_prompt(
    meeting_notes: str,
    client_reaction: str,
    decision_timeline: str,
    next_step_agreed: str = "",
) -> str:
    reaction_guide = {
        "热情": "立刻跟进，48小时内发出会议纪要和补充材料，主动提出PoC或高层拜访",
        "中性": "按时跟进，重点在会后材料中强化一个核心卖点，等待反馈",
        "保留": "温和跟进，优先解决会上提出的顾虑，不催促",
        "冷淡": "轻触跟进，评估商机质量，考虑是否投入更多资源",
    }
    strategy = reaction_guide.get(client_reaction, "按时跟进")

    return f"""# 会后跟进行动计划

## 会议信息摘要

**会议要点**：
{meeting_notes}

**客户反应**：{client_reaction}（跟进策略：{strategy}）

**预计决策周期**：{decision_timeline}

**会上已约定的下一步**：{next_step_agreed if next_step_agreed else "（未明确约定）"}

## 你的输出任务

### 1. 机会健康度评估

基于客户反应和会议情况，给出：
- 机会健康度：[红/黄/绿]
- 风险信号：（会上出现的负面信号，如客户提到竞品名称、没有确定下一步等）
- 推荐的跟进力度：[积极推进 / 保持联系 / 重新评估]

### 2. 24小时行动清单

请列出24小时内必须完成的任务（含格式模板）：

| 优先级 | 任务 | 截止时间 | 格式/模板 |
|--------|------|---------|---------|
| P0 | 发送会议纪要 | 今天下班前 | 见下方 |
| P1 | ... | ... | ... |

### 3. 会议纪要草稿（可直接发给客户的版本）

```
主题：[会议主题]
时间：[日期]
参与方：[我方] / [客户方参会人员]

一、本次会议主要内容
1. ...
2. ...

二、双方达成的共识
1. ...

三、待确认事项
- [客户方] 负责：...（预计回复时间：）
- [我方] 负责：...（预计完成时间：）

四、下一步行动
- 下次沟通时间：[待定 / 具体日期]
- 下次沟通议题：...
```

### 4. 分阶段跟进计划

根据「{decision_timeline}」决策周期，制定触达计划：

| 时间节点 | 触达方式 | 触达内容（要给客户带去价值，不只是催进度） |
|---------|---------|----------------------------------------|
| 会后24h | 邮件 | 发送会议纪要 + 一页纸执行摘要 |
| 第3天 | ... | ... |
| ... | ... | ... |

### 5. 一页纸执行摘要（供客户向上汇报用）

> **重要**：政府/企业客户的中层联系人往往需要向上级汇报，
> 给他们一份可以直接用的一页纸总结，能大幅提升推进效率。

请基于会议内容生成：

```
[项目名称] — 核心要点（供内部汇报）

背景：...（1句话）
方案核心价值：...（1-2句话）
关键数据：...（1-2个最有说服力的数字，用【待核实】占位）
建议下一步：...（1句话，明确且可操作）
```
"""


def main():
    meeting_notes = sys.argv[1] if len(sys.argv) > 1 else "请输入会议要点"
    client_reaction = sys.argv[2] if len(sys.argv) > 2 else "中性"
    timeline = sys.argv[3] if len(sys.argv) > 3 else "1-3个月"

    prompt = build_followup_prompt(
        meeting_notes=meeting_notes,
        client_reaction=client_reaction,
        decision_timeline=timeline,
    )
    print(prompt)


if __name__ == "__main__":
    main()
