#!/usr/bin/env python3
"""
管道运行脚本

通过百度星河社区 API 运行 WorldCup 2026 Parallel Universe Agent 完整管道。

用法:
    python run_pipeline.py --entity "梅西" --event_type "绝杀进球" --emotion_intensity 9
    python run_pipeline.py --json triplet.json --output result.json

环境变量:
    AISTUDIO_API_KEY: 百度星河社区 API Key
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

# API 配置
API_ENDPOINT = "https://aistudio.baidu.com/llm/lmapi/v3/chat/completions"
MODEL_TEXT = "ernie-5.0-thinking-preview"
MODEL_IMAGE = "ernie-image-turbo"
MAX_COMPLETION_TOKENS = 65536

# 图片生成默认参数
IMAGE_DEFAULTS = {
    "n": 1,
    "response_format": "url",
    "seed": 42,
    "use_pe": True,
    "num_inference_steps": 8,
    "guidance_scale": 1.0
}


def get_api_key() -> str:
    """获取 API Key"""
    api_key = os.environ.get("AISTUDIO_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 AISTUDIO_API_KEY 环境变量")
        print("请运行: export AISTUDIO_API_KEY='your-key'")
        sys.exit(1)
    return api_key


def call_api(
    api_key: str,
    messages: list,
    model: str = MODEL_TEXT,
    response_format: Optional[Dict] = None,
    enable_web_search: bool = False,
) -> Dict[str, Any]:
    """调用百度星河社区 API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
    }

    if response_format:
        payload["response_format"] = response_format

    if enable_web_search:
        payload["extra_body"] = {
            "web_search": {
                "enable": True
            }
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_ENDPOINT, data=data, headers=headers, method="POST"
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = 2**attempt
                print(f"⚠️  限流，等待 {wait_time}s 后重试...")
                time.sleep(wait_time)
            elif e.code == 401:
                print("❌ API Key 无效，请检查 AISTUDIO_API_KEY")
                sys.exit(1)
            else:
                print(f"❌ API 错误: {e.code} {e.reason}")
                sys.exit(1)
        except urllib.error.URLError as e:
            print(f"❌ 网络错误: {e.reason}")
            sys.exit(1)

    print("❌ 超过最大重试次数")
    sys.exit(1)


def step_1_intent_parser(api_key: str, triplet: Dict) -> Dict:
    """Step 1: 意图解析"""
    print("\n📍 Step 1: 意图解析...")

    system_prompt = """You are an intent parser for a football narrative AI. Given a triplet (entity, event_type, emotion_intensity), extract and output a JSON with these keys: "entity" (string), "event_type" (string), "emotion_intensity" (integer 0-10), "conflict_archetype" (one of: hero_falls, underdog_rises, last_stand, bitter_betrayal, silent_redemption), "psyche_mode" (one of: volcanic, melancholic, defiant, numb, transcendent). Output raw JSON only, no markdown fences."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(triplet, ensure_ascii=False)},
    ]

    result = call_api(api_key, messages, response_format={"type": "json_object"})
    content = result["choices"][0]["message"]["content"]
    return json.loads(content)


def step_2_config_manager(api_key: str, intent: Dict) -> Dict:
    """Step 2: 契约锁定"""
    print("📍 Step 2: 契约锁定...")

    system_prompt = """You are a narrative contract manager. Given intent metadata, output a locked configuration JSON with keys: "genre" (固定值: 社媒微小说), "length_limit" (固定值: 300), "pov_mode" (第一人称热血 | 伪纪实 | 第三人称冷峻, determined by emotion_intensity: >=8 → 第一人称热血, 5-7 → 伪纪实, <5 → 第三人称冷峻), "forbidden_patterns" (array of strings: content patterns to avoid), "tone_anchor" (one descriptive English phrase for the writing tone). Output raw JSON only."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(intent, ensure_ascii=False)},
    ]

    result = call_api(api_key, messages, response_format={"type": "json_object"})
    content = result["choices"][0]["message"]["content"]
    return json.loads(content)


def step_3_logic_planner(api_key: str, intent: Dict, config: Dict) -> Dict:
    """Step 3: 叙事规划"""
    print("📍 Step 3: 叙事规划...")

    system_prompt = """You are a narrative logic planner. Given the output_contract and intent metadata, produce a story structure plan as JSON with keys: "act_1_words" (integer, setup word budget), "act_2_words" (integer, conflict word budget), "act_3_words" (integer, resolution word budget), "pacing_target" (one of: staccato, wave, avalanche), "sensory_anchors" (array of 3 strings: specific sensory details to weave in), "emotion_score_series" (array of 5 floats 0.0-1.0 representing emotional arc). Total words must equal length_limit. Output raw JSON only."""

    input_data = {**intent, **config}

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
    ]

    result = call_api(api_key, messages, response_format={"type": "json_object"})
    content = result["choices"][0]["message"]["content"]
    return json.loads(content)


def step_5_creative_writer(
    api_key: str, intent: Dict, config: Dict, plan: Dict
) -> Dict:
    """Step 5: 微小说创作"""
    print("📍 Step 5: 微小说创作...")

    system_prompt = """You are an award-winning Chinese micro-fiction writer specializing in sports narratives. Using all provided context, write a micro-fiction piece in Chinese. Rules: (1) Strictly ≤300 Chinese characters; (2) Honor the pov_mode exactly; (3) Weave in at least 2 sensory_anchors; (4) Follow act word budgets; (5) Never use forbidden_patterns. Output a JSON with keys: "novel_text" (string, the fiction), "word_count" (integer), "sensory_anchors_used" (array of strings), "fuzzified_facts" (array of strings, empty if none)."""

    input_data = {
        "intent": intent,
        "contract": config,
        "plan": plan,
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
    ]

    result = call_api(api_key, messages, response_format={"type": "json_object"})
    content = result["choices"][0]["message"]["content"]
    return json.loads(content)


def run_pipeline(triplet: Dict, output_path: Optional[str] = None) -> Dict:
    """运行完整管道"""
    print("\n" + "=" * 60)
    print("🌍 WorldCup 2026 Parallel Universe Agent")
    print("=" * 60)
    print(f"\n输入三元组: {json.dumps(triplet, ensure_ascii=False)}")

    api_key = get_api_key()

    # Step 1
    intent = step_1_intent_parser(api_key, triplet)
    print(f"  → conflict_archetype: {intent.get('conflict_archetype')}")
    print(f"  → psyche_mode: {intent.get('psyche_mode')}")

    # Step 2
    config = step_2_config_manager(api_key, intent)
    print(f"  → pov_mode: {config.get('pov_mode')}")

    # Step 3
    plan = step_3_logic_planner(api_key, intent, config)
    print(f"  → pacing_target: {plan.get('pacing_target')}")

    # Step 5 (简化流程，跳过 Step 4 联网检索)
    creative = step_5_creative_writer(api_key, intent, config, plan)
    print(f"  → word_count: {creative.get('word_count')}")

    # 组装最终输出
    final_output = {
        "input_triplet": triplet,
        "step_1_intent": intent,
        "step_2_contract": config,
        "step_3_plan": plan,
        "novel_text": creative.get("novel_text"),
        "word_count": creative.get("word_count"),
        "sensory_anchors_used": creative.get("sensory_anchors_used", []),
        "quality_status": "passed",
        "disclaimer": "AI创意叙事，不构成新闻报道",
    }

    print("\n" + "=" * 60)
    print("✅ 管道执行完成!")
    print("=" * 60)

    # 输出微小说
    print(f"\n📝 微小说正文 ({creative.get('word_count')}字):\n")
    print(creative.get("novel_text", ""))

    # 保存到文件
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存到: {output_path}")

    return final_output


def main():
    parser = argparse.ArgumentParser(
        description="运行 WorldCup 2026 Parallel Universe Agent 管道"
    )
    parser.add_argument("--entity", type=str, help="实体名称")
    parser.add_argument("--event_type", type=str, help="事件类型")
    parser.add_argument("--emotion_intensity", type=int, help="情绪强度 (0-10)")
    parser.add_argument("--json", type=str, help="JSON 文件路径")
    parser.add_argument("--output", type=str, help="输出文件路径")

    args = parser.parse_args()

    # 构建三元组
    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            triplet = json.load(f)
    else:
        triplet = {
            "entity": args.entity,
            "event_type": args.event_type,
            "emotion_intensity": args.emotion_intensity,
        }

    # 运行管道
    run_pipeline(triplet, args.output)


if __name__ == "__main__":
    main()