#!/usr/bin/env python3
"""
模块六：异议处理准备。
从 objection_database.yaml 加载异议库，
按客户类型和已知顾虑，生成 TOP5 异议预案 + 三层话术 + 红线提示。
"""

import sys
import os
import yaml

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_objections(client_type: str) -> list:
    path = os.path.join(SKILL_DIR, "config", "objection_database.yaml")
    with open(path, "r", encoding="utf-8") as f:
        db = yaml.safe_load(f)
    return db.get(client_type, [])


def match_objections(objections: list, known_concerns: list, top_n: int = 5) -> list:
    """根据已知顾虑匹配最相关的异议，未匹配的用默认高频异议补全。"""
    scored = []
    for obj in objections:
        score = 0
        for concern in known_concerns:
            for kw in obj.get("trigger_keywords", []):
                if kw in concern:
                    score += 2
                    break
        scored.append((score, obj))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [obj for _, obj in scored[:top_n]]


def build_objections_prompt(
    client_type: str,
    known_concerns: list = None,
    competitor_info: str = "",
    our_weaknesses: list = None,
) -> str:
    objections = load_objections(client_type)
    known_concerns = known_concerns or []
    our_weaknesses = our_weaknesses or []

    top_objections = match_objections(objections, known_concerns, top_n=5)

    objection_cards = ""
    for i, obj in enumerate(top_objections, 1):
        obj_id = obj.get("id", f"OBJ-{i:03d}")
        triggers = "、".join(obj.get("trigger_keywords", [])[:3])
        concern = obj.get("underlying_concern", "")
        l1 = obj.get("response_layer_1", "")
        l2 = obj.get("response_layer_2", "")
        l3 = obj.get("response_layer_3", "")
        red_lines = " / ".join(obj.get("red_lines", []))

        objection_cards += f"""
### {i}. [{obj_id}] 触发词：{triggers}

**背后真实顾虑**：{concern}

**第一层 — 共情**：{l1}

**第二层 — 重框架**：{l2}

**第三层 — 证据**：{l3}

> ❌ **红线（绝对不说）**：{red_lines}
"""

    weakness_section = ""
    if our_weaknesses:
        weakness_list = "\n".join(f"- {w}" for w in our_weaknesses)
        weakness_section = f"""
## 我方已知弱点的防御性应对

以下是您标注的我方方案弱点，请为每一项准备防御话术：

{weakness_list}

对每个弱点，请输出：
- **最可能的客户质疑**：...
- **主动防御话术**（先于客户提出，抢占主动权）：...
"""

    competitor_section = ""
    if competitor_info:
        competitor_section = f"""
## 竞品应对策略

客户正在评估的竞品信息：{competitor_info}

**竞品应对原则**：
1. 不评价竞品优劣（避免负面背书）
2. 承认竞品的优势（显示客观性，赢得信任）
3. 聚焦我方独特场景优势（而非全面对比）

话术结构：
"[竞品]在[领域A]确实很强，我们认可。对于贵司这个项目，核心需求是[具体需求]，在这个场景下，我们的差异在于[具体差异]，这可以通过[具体验证方式]来确认。"

请针对客户提到的竞品，输出3条具体的差异化话术。
"""

    return f"""# 异议处理准备

## 客户类型：{client_type}

## 已知客户顾虑

{chr(10).join(f"- {c}" for c in known_concerns) if known_concerns else "（未提供，使用该客户类型的高频异议）"}

## TOP {len(top_objections)} 异议预案

{objection_cards}

{weakness_section}

{competitor_section}

## 使用建议

- 熟记每个异议的**背后顾虑**，而非死记话术（顾虑抓对了，话术可以变）
- 第一层共情最重要：让客户感到被理解，才会打开听你说
- 会前用5分钟过一遍 TOP3 异议，想清楚自己的应对逻辑
- 遇到红线诱惑（客户主动给台阶）：坚守，一旦踩线对方会立刻失去信任
"""


def main():
    client_type = sys.argv[1] if len(sys.argv) > 1 else "government"
    known_concerns = sys.argv[2].split(",") if len(sys.argv) > 2 else []

    prompt = build_objections_prompt(
        client_type=client_type,
        known_concerns=known_concerns,
    )
    print(prompt)


if __name__ == "__main__":
    main()
