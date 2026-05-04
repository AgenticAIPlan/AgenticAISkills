#!/usr/bin/env python3
"""
模块三：方案内容逐章生成。
在 Ghost Deck 确认后，逐章展开内容。
禁止区机制：敏感信息自动替换为占位符。
"""

import sys
import os

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CAUTION_BLOCK = """
> [!CAUTION]
> **禁止区规则（生成内容时严格遵守）：**
> - 不编造资质证书、认证编号、业绩案例 → 用 **【待补充】** 占位
> - 不虚构技术参数、性能指标、测试数据 → 用 **【待核实】** 占位
> - 不编造报价、成本数字、合同金额 → 用 **【待填】** 占位
> - 不捏造具体客户名称/联系人 → 用 **【参考客户名称】** 占位
> - 所有统计数字必须注明来源或加【待核实】
"""


def build_proposal_prompt(
    ghost_deck: str,
    client_type: str,
    client_profile: str,
    chapter_id: str,
    chapter_title: str,
    mode: str = "standard",
) -> str:
    depth_map = {
        "quick": "简洁版（每章200-400字，重点突出）",
        "standard": "标准版（每章400-800字，逻辑完整）",
        "tender": "完整版（每章800-1500字，覆盖全部评分点）",
    }
    depth = depth_map.get(mode, "标准版（每章400-800字）")

    return f"""# 方案内容生成任务

## 当前任务
展开方案第 **{chapter_id}** 章：**{chapter_title}**

## 方案整体目录（Ghost Deck）
{ghost_deck}

## 客户信息摘要
{client_profile}

## 内容深度要求
{depth}

{CAUTION_BLOCK}

## 生成规范

1. **开头一句话**：点明本章与客户痛点的直接关联（不要废话铺垫）
2. **核心内容**：直接响应客户关注点，数字、事实优先于描述
3. **结尾衔接**：最后一句自然引出下一章

## Action Title 验证
本章 Action Title 为：**{chapter_title}**
生成内容必须支撑并实现这个标题的承诺。

## 禁止行为

- ❌ 不写"总的来说""综上所述"等空话收尾
- ❌ 不写"引领行业""开创先河"等营销口号
- ❌ 不在没有数据支撑时使用绝对数字
- ❌ 不贬低任何竞争对手

现在开始生成第 {chapter_id} 章内容：
"""


def build_full_review_prompt(proposal_text: str) -> str:
    """生成内容自检 Prompt，检查内容与需求的一致性。"""
    return f"""# 方案内容自检任务

请对以下方案全文进行自检，输出检查报告：

## 检查项

1. **叙事逻辑检查**：各章节是否形成完整的"问题→方案→证明→行动"链条
2. **需求响应检查**：是否每个已收集的客户痛点都有对应章节或段落响应
3. **Action Title 验证**：每章的内容是否实现了 Action Title 的承诺
4. **占位符清单**：列出所有【待填】【待补充】【待核实】的位置和上下文
5. **数字一致性**：前后出现的同一数字是否一致
6. **章节重复检查**：不同章节是否有实质性重复内容

## 方案全文

{proposal_text}

## 输出格式

```
## 自检报告

### ✅ 通过项
...

### ⚠️ 待改进项
...

### 📋 占位符待填清单（共X处）
1. 第X页/章：【待填】 - 上下文：...
...

### 建议修改
...
```
"""


def main():
    print("方案生成器 - Prompt 模板工具")
    print("此脚本由 SKILL.md 指导 Claude 调用，生成逐章展开的 Prompt。")
    print()

    # 演示模式
    demo_prompt = build_proposal_prompt(
        ghost_deck="[Ghost Deck 内容]",
        client_type="government",
        client_profile="XX市大数据局，信创压力，审批效率低",
        chapter_id="01",
        chapter_title="飞桨政务AI平台通过全部信创认证，数据安全等级达到等保三级，为XX市采购提供零合规风险保障",
        mode="standard",
    )
    print(demo_prompt)


if __name__ == "__main__":
    main()
