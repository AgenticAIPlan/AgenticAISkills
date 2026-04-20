#!/usr/bin/env python3
"""
三元组验证脚本

验证用户输入的三元组是否符合 WorldCup 2026 Parallel Universe Agent 的格式要求。

用法:
    python validate_triplet.py --entity "梅西" --event_type "绝杀进球" --emotion_intensity 9
    python validate_triplet.py --json '{"entity": "梅西", "event_type": "绝杀进球", "emotion_intensity": 9}'
"""

import argparse
import json
import sys
from typing import Dict, Any, List, Tuple


# 支持的事件类型
VALID_EVENT_TYPES = [
    "绝杀进球",
    "点球大战失利",
    "帽子戏法",
    "红牌退场",
    "关键助攻",
    "失误导致丢球",
    "夺冠时刻",
    "告别演出",
    "淘汰晋级",
    "小组赛出局",
]

# 支持的实体类型示例
ENTITY_EXAMPLES = [
    "梅西", "C罗", "姆巴佩", "哈兰德", "凯恩", "贝林厄姆",
    "巴西队", "阿根廷队", "法国队", "德国队", "西班牙队", "英格兰队",
]


def validate_entity(entity: str) -> Tuple[bool, str]:
    """验证实体名称"""
    if not entity or not entity.strip():
        return False, "entity 不能为空"
    if len(entity) > 50:
        return False, f"entity 长度超过限制 (当前: {len(entity)}, 最大: 50)"
    return True, "OK"


def validate_event_type(event_type: str) -> Tuple[bool, str]:
    """验证事件类型"""
    if not event_type or not event_type.strip():
        return False, "event_type 不能为空"
    if event_type not in VALID_EVENT_TYPES:
        return False, f"不支持的事件类型 '{event_type}'，支持的事件类型: {', '.join(VALID_EVENT_TYPES)}"
    return True, "OK"


def validate_emotion_intensity(intensity: int) -> Tuple[bool, str]:
    """验证情绪强度"""
    if not isinstance(intensity, int):
        return False, f"emotion_intensity 必须是整数 (当前类型: {type(intensity).__name__})"
    if intensity < 0 or intensity > 10:
        return False, f"emotion_intensity 必须在 0-10 范围内 (当前: {intensity})"
    return True, "OK"


def get_pov_mode(intensity: int) -> str:
    """根据情绪强度获取视角模式"""
    if intensity >= 8:
        return "第一人称热血"
    elif intensity >= 5:
        return "伪纪实"
    else:
        return "第三人称冷峻"


def validate_triplet(triplet: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证完整的三元组

    返回包含验证结果和建议的字典
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": {},
    }

    # 验证 entity
    entity_valid, entity_msg = validate_entity(triplet.get("entity", ""))
    if not entity_valid:
        results["errors"].append(f"entity: {entity_msg}")
        results["valid"] = False

    # 验证 event_type
    event_valid, event_msg = validate_event_type(triplet.get("event_type", ""))
    if not event_valid:
        results["errors"].append(f"event_type: {event_msg}")
        results["valid"] = False

    # 验证 emotion_intensity
    intensity = triplet.get("emotion_intensity")
    if intensity is None:
        results["errors"].append("emotion_intensity: 缺失必填字段")
        results["valid"] = False
    else:
        intensity_valid, intensity_msg = validate_emotion_intensity(intensity)
        if not intensity_valid:
            results["errors"].append(f"emotion_intensity: {intensity_msg}")
            results["valid"] = False

    # 生成建议
    if results["valid"]:
        results["suggestions"] = {
            "pov_mode": get_pov_mode(intensity),
            "recommended_conflict_archetype": suggest_conflict_archetype(
                triplet.get("event_type", "")
            ),
        }

    return results


def suggest_conflict_archetype(event_type: str) -> str:
    """根据事件类型建议冲突原型"""
    mapping = {
        "绝杀进球": "last_stand / silent_redemption",
        "点球大战失利": "bitter_betrayal",
        "帽子戏法": "last_stand",
        "红牌退场": "hero_falls / bitter_betrayal",
        "关键助攻": "silent_redemption",
        "失误导致丢球": "bitter_betrayal",
        "夺冠时刻": "last_stand / underdog_rises",
        "告别演出": "hero_falls",
        "淘汰晋级": "underdog_rises",
        "小组赛出局": "hero_falls",
    }
    return mapping.get(event_type, "根据情境选择")


def main():
    parser = argparse.ArgumentParser(
        description="验证 WorldCup 2026 Parallel Universe Agent 三元组"
    )
    parser.add_argument("--entity", type=str, help="实体名称 (球员/球队)")
    parser.add_argument("--event_type", type=str, help="事件类型")
    parser.add_argument("--emotion_intensity", type=int, help="情绪强度 (0-10)")
    parser.add_argument("--json", type=str, help="JSON 格式的三元组")

    args = parser.parse_args()

    # 从 JSON 或单独参数构建三元组
    if args.json:
        try:
            triplet = json.loads(args.json)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析错误: {e}")
            sys.exit(1)
    else:
        triplet = {
            "entity": args.entity,
            "event_type": args.event_type,
            "emotion_intensity": args.emotion_intensity,
        }

    # 执行验证
    results = validate_triplet(triplet)

    # 输出结果
    print("\n" + "=" * 60)
    print("三元组验证结果")
    print("=" * 60)
    print(f"\n输入: {json.dumps(triplet, ensure_ascii=False)}")

    if results["valid"]:
        print("\n✅ 验证通过!")
        print(f"\n建议视角: {results['suggestions']['pov_mode']}")
        print(f"建议冲突原型: {results['suggestions']['recommended_conflict_archetype']}")
    else:
        print("\n❌ 验证失败!")
        for error in results["errors"]:
            print(f"  - {error}")

    if results["warnings"]:
        print("\n⚠️  警告:")
        for warning in results["warnings"]:
            print(f"  - {warning}")

    print("\n" + "=" * 60)

    sys.exit(0 if results["valid"] else 1)


if __name__ == "__main__":
    main()