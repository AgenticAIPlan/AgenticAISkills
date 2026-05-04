#!/usr/bin/env python3
"""
模块二：Ghost Deck 生成器。
借鉴 mbb-decks 的 Ghost Deck First 工作流：
先生成每页 Action Title（目录），用户确认叙事逻辑后再展开内容。

Action Title 规范：
- 主谓宾完整，有具体数字或因果关系，10-15词
- ✅ "三层数据架构消除孤岛，历史数据迁移周期缩短60%"
- ❌ 禁止标签式/问句式
"""

import sys
import os
import yaml

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_pain_point_map() -> dict:
    path = os.path.join(SKILL_DIR, "config", "pain_point_map.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_client_profiles() -> dict:
    path = os.path.join(SKILL_DIR, "config", "client_profiles.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 三类客户的基础框架章节
BASE_FRAMEWORKS = {
    "government": [
        {"id": "cover", "title_hint": "封面：项目名称要有政治高度，如'XX市政务智能化升级项目'"},
        {"id": "exec_summary", "title_hint": "执行摘要：核心价值主张（1页，供领导单独阅读）"},
        {"id": "policy_alignment", "title_hint": "政策对齐：与国家/省/市数字政府政策的呼应关系"},
        {"id": "current_situation", "title_hint": "现状诊断：用客户自己的语言描述当前问题（量化损失）"},
        {"id": "solution", "title_hint": "解决方案：功能模块与业务场景一一对应（标注国产化标签）"},
        {"id": "benchmark_cases", "title_hint": "标杆案例：同级别政府单位的成功案例（必须有具体数字）"},
        {"id": "implementation", "title_hint": "实施计划：里程碑与采购周期/汇报节点对齐"},
        {"id": "roi", "title_hint": "投入产出：TCO分析 + 预算来源建议"},
    ],
    "enterprise": [
        {"id": "cover", "title_hint": "封面：突出行业标签和战略定位"},
        {"id": "industry_trend", "title_hint": "行业趋势：AI应用成熟度 + 竞争对手动向（用权威数据）"},
        {"id": "business_scenarios", "title_hint": "业务场景价值：精选2-3个最高ROI的场景（每个场景含ROI测算）"},
        {"id": "solution", "title_hint": "技术方案：与现有IT架构的集成方案（必须有架构图）"},
        {"id": "ecosystem", "title_hint": "生态合作：联合创新/行业标准共建机会"},
        {"id": "roadmap", "title_hint": "实施路线：分阶段（快赢+长期）+ KPI与业务考核挂钩"},
        {"id": "roi", "title_hint": "投资回报：ROI测算方法论 + 投资回收期"},
    ],
    "tech": [
        {"id": "tech_diagnosis", "title_hint": "技术现状评估：精准诊断当前技术瓶颈（基于摸底信息）"},
        {"id": "solution", "title_hint": "技术方案：模型选型 + API/SDK接入方案 + 性能参数"},
        {"id": "benchmark", "title_hint": "性能基准：在客户关键指标上的Benchmark对比数据"},
        {"id": "poc_plan", "title_hint": "PoC验证方案：用客户自己的数据跑benchmark（赢得信任的关键）"},
        {"id": "migration", "title_hint": "迁移支持：从当前技术栈迁移的具体工作量和支持方案"},
        {"id": "developer_support", "title_hint": "开发者支持：文档质量 + 社区 + 专属技术支持SLA"},
    ],
}

# 动态注入章节（根据痛点触发）
DYNAMIC_SECTIONS = {
    "policy_alignment": {"title": "政策符合性论证", "client_types": ["government"]},
    "security_cert": {"title": "信创认证与安全合规证明", "client_types": ["government", "tech"]},
    "infosec_architecture": {"title": "信息安全架构设计", "client_types": ["government"]},
    "data_localization": {"title": "数据本地化部署方案", "client_types": ["government", "tech"]},
    "tco_analysis": {"title": "全生命周期成本(TCO)分析", "client_types": ["government", "enterprise"]},
    "phased_implementation": {"title": "分阶段实施路线（适配预算节奏）", "client_types": ["government"]},
    "budget_source_suggestion": {"title": "可用专项资金申请路径建议", "client_types": ["government"]},
    "roi_calculation": {"title": "ROI量化测算与回收期预测", "client_types": ["enterprise"]},
    "kpi_framework": {"title": "KPI指标体系设计", "client_types": ["enterprise"]},
    "integration_architecture": {"title": "与现有系统集成架构详解", "client_types": ["enterprise"]},
    "api_spec": {"title": "API接口规范与集成示例", "client_types": ["enterprise", "tech"]},
    "competitive_analysis": {"title": "竞争格局与差异化优势矩阵", "client_types": ["enterprise"]},
    "benchmark_data": {"title": "性能Benchmark对比数据", "client_types": ["tech"]},
    "poc_plan": {"title": "PoC验证方案设计", "client_types": ["tech", "enterprise"]},
    "compatibility_guide": {"title": "与现有框架兼容性说明及迁移工具", "client_types": ["tech"]},
    "cost_optimization": {"title": "推理/训练成本优化方案", "client_types": ["tech"]},
    "data_compliance": {"title": "数据合规与私有化部署架构", "client_types": ["tech"]},
}


def get_triggered_sections(pain_points: list, client_type: str) -> list:
    """根据痛点列表，返回需要动态注入的章节ID列表。"""
    pain_map = load_pain_point_map()
    client_map = pain_map.get(client_type, {})

    triggered = set()
    for category, category_data in client_map.items():
        keywords = category_data.get("keywords", [])
        for pain in pain_points:
            for kw in keywords:
                if kw in pain:
                    for section_id in category_data.get("inject_sections", []):
                        triggered.add(section_id)
                    break

    return [sid for sid in triggered if sid in DYNAMIC_SECTIONS]


def build_ghost_deck_prompt(
    client_type: str,
    pain_points: list,
    product_scope: str,
    meeting_goal: str,
    mode: str = "standard",
) -> str:
    """
    构建 Ghost Deck 生成的 Claude Prompt。
    """
    profiles = load_client_profiles()
    profile = profiles.get(client_type, {})

    base_sections = BASE_FRAMEWORKS.get(client_type, [])
    triggered_sections = get_triggered_sections(pain_points, client_type)

    # 根据三档模式决定页数
    page_limits = {"quick": "5-8页", "standard": "12-18页", "tender": "25-40页"}
    page_limit = page_limits.get(mode, "12-18页")

    pain_str = "\n".join(f"- {p}" for p in pain_points)
    triggered_str = "\n".join(
        f"- **{DYNAMIC_SECTIONS[sid]['title']}**（由痛点触发）"
        for sid in triggered_sections
        if sid in DYNAMIC_SECTIONS
    )

    prompt = f"""# Ghost Deck 生成任务

## 任务说明

你是一位资深售前工程师，现在需要为以下客户生成方案 PPT 的 Ghost Deck（目录+Action Title）。

**重要：只生成每页的 Action Title，不展开内容。用户确认叙事逻辑后，再逐章展开。**

## 客户信息

- **客户类型**：{profile.get('label', client_type)}
- **核心痛点**：
{pain_str}
- **我方产品/方案范围**：{product_scope}
- **本次拜访目标**：{meeting_goal}
- **方案模式**：{mode}（目标页数：{page_limit}）

## Action Title 规范（每页标题必须符合）

✅ **正确示例**：
- "三层数据中台架构消除跨部门孤岛，数据查询时间从3天缩短至实时"
- "飞桨自动化审批模型将证照审核周期从5天压缩至1小时，年节省人力成本【待核实】万元"
- "基于LoRA的轻量微调方案，A100单卡2小时完成行业模型适配，训练成本降低90%"

❌ **禁止**：
- 纯名词标题："产品架构介绍"
- 问句标题："如何解决数据孤岛问题？"
- 无因果/无数字的口号："引领行业AI转型"

## 基础框架章节（必选）

{chr(10).join(f"- {s['title_hint']}" for s in base_sections)}

## 动态注入章节（基于痛点触发，按需选取）

{triggered_str if triggered_str else "（当前痛点未触发额外章节）"}

## 你的输出格式

请按以下格式输出 Ghost Deck：

```
# Ghost Deck：[项目名称]
## 叙事主线：[一句话描述整个方案的逻辑主线]

| 页码 | 章节类型 | Action Title |
|------|---------|-------------|
| 封面 | 封面 | [项目名称，体现客户诉求] |
| 01 | 执行摘要 | [Action Title] |
| 02 | ... | [Action Title] |
...
```

**完成后**，请提问：
"以上是方案的叙事目录，您看整体逻辑是否流畅？有哪些章节需要调整顺序、删除或增加？确认后我将逐章展开内容。"

## 注意事项

- 所有数字如无真实数据支撑，使用"【待核实】"占位，不要编造
- 页数控制在{page_limit}以内
- 确保叙事逻辑：问题→方案→证明→行动，客户读完应感到"这就是我的问题，这是解法，这是证据，我该怎么做"
"""
    return prompt


def main():
    # 命令行简单测试模式
    import json
    test_input = {
        "client_type": sys.argv[1] if len(sys.argv) > 1 else "government",
        "pain_points": ["信创合规压力", "审批效率低", "预算有限"],
        "product_scope": "飞桨政务AI解决方案",
        "meeting_goal": "首次汇报，建立信任，确认需求",
        "mode": "standard",
    }
    prompt = build_ghost_deck_prompt(**test_input)
    print(prompt)


if __name__ == "__main__":
    main()
