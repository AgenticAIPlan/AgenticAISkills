#!/usr/bin/env python3
"""
模块四：专家视角自审（GO/NO-GO 机制）。
借鉴 expert-review-panel 的反群体思维设计：
3-4位虚拟专家从不同视角审查方案，输出 GO/NO-GO 裁决。
"""

import sys
import os
import yaml

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_client_profiles() -> dict:
    path = os.path.join(SKILL_DIR, "config", "client_profiles.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 虚拟专家团队（按客户类型动态组队）
EXPERT_PANELS = {
    "government": [
        {
            "name": "老王",
            "role": "有20年经验的政府采购顾问",
            "focus": "采购合规性、政治风险、与上级政策的一致性",
            "bias": "极度谨慎，见过太多项目因合规问题被叫停",
        },
        {
            "name": "李处长",
            "role": "退休的政府信息化处长",
            "focus": "实际业务价值、运维可行性、对基层工作人员的影响",
            "bias": "务实派，不相信PPT上的数字，关心能不能真正用起来",
        },
        {
            "name": "张律师",
            "role": "政府IT采购领域律师",
            "focus": "合同条款、知识产权归属、数据权益、验收标准模糊性",
            "bias": "找漏洞专家，专门看方案里的模糊表述和潜在法律风险",
        },
    ],
    "enterprise": [
        {
            "name": "陈CFO",
            "role": "上市公司前CFO",
            "focus": "ROI测算的合理性、投资回收期、隐性成本",
            "bias": "数字驱动，不信任没有方法论支撑的ROI承诺",
        },
        {
            "name": "技术架构师老赵",
            "role": "有15年经验的企业架构师",
            "focus": "技术方案的可行性、集成复杂度、技术债风险",
            "bias": "见过太多纸面好看但落地惨败的方案，专找技术陷阱",
        },
        {
            "name": "商务谈判专家小林",
            "role": "经验丰富的乙方商务总监",
            "focus": "客户可能的异议点、方案的说服力、竞品对比策略",
            "bias": "站在客户角度找方案的弱点",
        },
    ],
    "tech": [
        {
            "name": "资深ML工程师小李",
            "role": "有10年工业落地经验的ML工程师",
            "focus": "技术细节准确性、Benchmark真实性、迁移成本评估",
            "bias": "技术完美主义，对任何不精确的技术声明都会追问",
        },
        {
            "name": "CTO老林",
            "role": "AI创业公司CTO",
            "focus": "架构合理性、扩展性、供应商依赖风险、make-or-buy决策",
            "bias": "有强烈的技术自主意识，警惕供应商锁定",
        },
        {
            "name": "产品VP阿雯",
            "role": "AI产品副总裁",
            "focus": "方案能否解决商业问题、时间成本、工程师接受度",
            "bias": "只关心能不能帮业务，对技术细节不感兴趣",
        },
    ],
}

ANTI_SYCOPHANCY_RULES = """
## 反谄媚规则（必须遵守）

1. **盲评原则**：每位专家独立评审，不受其他专家影响
2. **Devil's Advocate**：至少一位专家必须提出强烈质疑，即使方案整体不错
3. **一致通过警示**：如果所有专家都给出正面评价，系统自动触发额外质疑轮次
4. **少数意见保护**：即使1位专家有顾虑，必须在报告中完整呈现，不被多数压制
5. **禁止模糊肯定**：不允许"总体不错""有待改进"等空话，必须具体指出
"""


def build_review_prompt(proposal_text: str, client_type: str, proposal_goal: str) -> str:
    profiles = load_client_profiles()
    profile = profiles.get(client_type, {})
    experts = EXPERT_PANELS.get(client_type, EXPERT_PANELS["enterprise"])

    expert_intros = "\n".join(
        f"- **{e['name']}**（{e['role']}）：专注{e['focus']}。偏见/视角：{e['bias']}"
        for e in experts
    )

    return f"""# 方案专家审查任务

## 背景

你需要扮演以下{len(experts)}位独立专家，对一份{profile.get('label', client_type)}客户的售前方案进行审查。

## 评审目标

{proposal_goal}

## 专家团队

{expert_intros}

{ANTI_SYCOPHANCY_RULES}

## 方案全文

{proposal_text}

## 输出格式

对每位专家，分别输出：

---

### [专家姓名]（[角色]）的评审

**总体评分**：[1-10分] | **立场**：[支持 / 中立 / 反对]

**最强支撑点（1-2条）**：
- ...

**最大风险/漏洞（必须至少1条，不允许为空）**：
- ...

**具体修改建议**：
- ...

---

## 综合裁决

| 专家 | 评分 | 立场 |
|------|------|------|
| {experts[0]['name']} | X/10 | ... |
...

**综合评分**：X/10

**GO/NO-GO 裁决**：[GO ✅ / NO-GO ❌ / 条件GO ⚠️]

**NO-GO 或 条件GO 的必要修改项**：
1. ...
2. ...

**提交前必须解决的核心问题**：
...
"""


def main():
    print("方案自审模块 - 专家评审 Prompt 生成工具")
    client_type = sys.argv[1] if len(sys.argv) > 1 else "government"

    demo_prompt = build_review_prompt(
        proposal_text="[方案全文]",
        client_type=client_type,
        proposal_goal="首次汇报，目标是获得高层支持和进入正式采购流程",
    )
    print(demo_prompt)


if __name__ == "__main__":
    main()
