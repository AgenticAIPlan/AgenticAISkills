#!/usr/bin/env python3
"""
模块五：演讲要点生成。
根据方案大纲、参会角色、会议时长，生成分段演讲要点。
支持主线 + 分支话术（针对不同角色）。
"""

import sys
import os
import yaml

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 角色关注点映射
ROLE_FOCUS = {
    "政府领导/一把手": "政治安全 + 成果可汇报 + 风险规避",
    "信息化局长/IT负责人": "技术合规 + 运维难度 + 国产化",
    "业务科室主任": "好不好用 + 是否影响现有工作",
    "财务/采购负责人": "价格合理性 + 采购合规",
    "企业CEO/总裁": "战略价值 + ROI + 竞争影响",
    "企业CTO/CIO": "架构合理性 + 集成可行性 + 技术债",
    "业务VP/部门总监": "业务效率 + 快速见效 + 可量化",
    "CFO/财务总监": "ROI + 投资回收期 + TCO",
    "AI/ML工程师": "技术深度 + API质量 + 迁移成本",
    "产品经理": "功能边界 + 使用门槛 + 集成工作量",
}

THREE_THREE_FRAMEWORK = """
**"三个三"演讲框架**

开场三步：
① 建立共鸣（"我们了解到贵单位正在面临X挑战..."）
② 亮出价值（"今天带来一个经过XX家同类机构验证的解决方案..."）
③ 设定期待（"接下来45分钟，我希望跟大家确认三件事..."）

主体三层：
① 痛点共鸣（让客户说"是的，这就是我们的问题"）
② 方案展示（让客户觉得"这个方案是专门为我们设计的"）
③ 证据支撑（让客户感到"有人已经成功了，我们可以放心"）

收尾三步：
① 总结核心价值（一句话重申最大卖点）
② 主动提出可能的异议并回应
③ 明确下一步（提出具体行动建议，不让会议在模糊中结束）
"""


def build_talking_points_prompt(
    ghost_deck: str,
    attendees: list,
    duration_minutes: int,
    meeting_goal: str,
    client_type: str,
) -> str:
    # 时间分配
    open_time = int(duration_minutes * 0.1)
    qa_time = int(duration_minutes * 0.2)
    close_time = int(duration_minutes * 0.1)
    body_time = duration_minutes - open_time - qa_time - close_time

    attendee_str = "\n".join(f"- {a}" for a in attendees)
    roles_focus = "\n".join(
        f"- **{role}**：{focus}"
        for role, focus in ROLE_FOCUS.items()
        if any(role in a for a in attendees)
    )
    if not roles_focus:
        roles_focus = "（请根据实际参会角色参考上方角色关注点表）"

    return f"""# 演讲要点生成任务

## 会议信息

- **参会人员**：
{attendee_str}
- **会议时长**：{duration_minutes}分钟
- **会议目标**：{meeting_goal}
- **客户类型**：{client_type}

## 时间分配建议

| 环节 | 时长 |
|------|------|
| 开场 | {open_time}分钟 |
| 主体内容 | {body_time}分钟 |
| Q&A互动 | {qa_time}分钟 |
| 收尾/下一步 | {close_time}分钟 |

## 参会角色关注点

{roles_focus}

## 方案目录（Ghost Deck）

{ghost_deck}

{THREE_THREE_FRAMEWORK}

## 你的输出任务

请生成以下内容：

### 1. 开场话术（完整文本，可直接使用）

针对参会人员角色，写出完整的开场白（{open_time}分钟内）。
注意：要让最高级别的决策者在第30秒内就感受到"这个方案是为我们准备的"。

### 2. 各章演讲要点

对每个章节，输出：
- **PPT上写的**：精简文字（不超过20字/条）
- **嘴上说的**：展开表达（2-4句话，包含语气词和过渡）
- **数据插入点**：这里需要什么数字/案例（用【待核实】标注）
- **时间建议**：这章建议讲多久

### 3. 角色差异化补充

当特定角色深度介入时的额外话术：
- 当技术负责人追问技术细节时 → 分支话术A
- 当财务/领导关注成本时 → 分支话术B
- 当对方提到竞品时 → 切换应对

### 4. 收尾话术（含下一步行动引导）

让会议不以"好的，回去研究研究"结束的具体话术。

### 5. 弹性应对

- 如果时间不够（提前10分钟）：可跳过哪些章节 + 快速收尾话术
- 如果客户反应冷淡：转换策略
- 如果某个问题答不上来：标准应对公式

## 注意事项

- 区分"PPT上写的文字"和"演讲时说的话"——这是最关键的价值
- 所有数字用【待核实】占位，由用户填入真实数据
- 口语化，有温度，不要像在读PPT
"""


def main():
    client_type = sys.argv[1] if len(sys.argv) > 1 else "government"
    prompt = build_talking_points_prompt(
        ghost_deck="[Ghost Deck 内容]",
        attendees=["分管副市长", "信息化局长", "业务科室主任"],
        duration_minutes=45,
        meeting_goal="首次汇报，获得领导支持",
        client_type=client_type,
    )
    print(prompt)


if __name__ == "__main__":
    main()
