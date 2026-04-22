#!/usr/bin/env python3
"""
Pipeline Runner - Complete 10-Step Pipeline

Usage:
    python run_pipeline.py --entity "Messi" --event_type "goal" --emotion_intensity 9
    python run_pipeline.py --json triplet.json --output result.json

Environment:
    AISTUDIO_API_KEY: Baidu Xinghe API Key

Dependencies:
    pip install openai
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, Any, Optional, List
import base64

# OpenAI SDK for both text and image generation
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Error: openai package not installed. Run: pip install openai")

# API Configuration
BASE_URL = "https://aistudio.baidu.com/llm/lmapi/v3"
MODEL_TEXT = "ernie-5.0-thinking-preview"
MODEL_IMAGE = "ernie-image-turbo"
MAX_COMPLETION_TOKENS = 65536

# Supported image sizes
IMAGE_SIZES = ["1024x1024", "1376x768", "1264x848", "1200x896", "896x1200", "848x1264", "768x1376", "1024x1820"]

# Image generation defaults
IMAGE_DEFAULTS = {
    "n": 1,
    "response_format": "url",
    "seed": 42,
    "use_pe": True,
    "num_inference_steps": 8,
    "guidance_scale": 1.0
}

# Reflexion config
REFLEXION_MAX_ITERATIONS = 3
PERSONA_DRIFT_THRESHOLD = 0.30
EMOTION_ARC_FIT_THRESHOLD = 0.70


def get_api_key() -> str:
    api_key = os.environ.get("AISTUDIO_API_KEY")
    if not api_key:
        print("Error: AISTUDIO_API_KEY not set")
        sys.exit(1)
    return api_key


def get_client(api_key: str) -> "OpenAI":
    """Get OpenAI client instance"""
    if not HAS_OPENAI:
        print("Error: openai package not installed. Run: pip install openai")
        sys.exit(1)
    return OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
    )


def call_api(api_key: str, messages: list, model: str = MODEL_TEXT,
             response_format: Optional[Dict] = None,
             enable_web_search: bool = False) -> Dict[str, Any]:
    """Call text generation API using OpenAI SDK"""
    client = get_client(api_key)

    # Build extra_body
    extra_body = {}
    if enable_web_search:
        extra_body["web_search"] = {"enable": True}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Use stream=False for non-streaming response
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                extra_body=extra_body if extra_body else None,
            )

            # Extract content
            content = response.choices[0].message.content

            # Return in expected format
            return {
                "choices": [{
                    "message": {
                        "content": content,
                        "role": "assistant"
                    }
                }]
            }

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                wait_time = 2 ** attempt
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            elif "401" in error_str or "unauthorized" in error_str.lower():
                print("Invalid API Key")
                sys.exit(1)
            else:
                print(f"API Error: {e}")
                if attempt == max_retries - 1:
                    sys.exit(1)
                time.sleep(1)

    print("Max retries exceeded")
    sys.exit(1)


def call_api_stream(api_key: str, messages: list, model: str = MODEL_TEXT,
                    enable_web_search: bool = False, verbose: bool = False):
    """Call text generation API with streaming (for debugging)"""
    client = get_client(api_key)

    extra_body = {}
    if enable_web_search:
        extra_body["web_search"] = {"enable": True}

    chat_completion = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        extra_body=extra_body if extra_body else None,
        max_completion_tokens=MAX_COMPLETION_TOKENS
    )

    full_content = ""
    for chunk in chat_completion:
        if not chunk.choices or len(chunk.choices) == 0:
            continue
        if hasattr(chunk.choices[0].delta, "reasoning_content") and chunk.choices[0].delta.reasoning_content:
            if verbose:
                print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
        else:
            content = chunk.choices[0].delta.content or ""
            full_content += content
            if verbose:
                print(content, end="", flush=True)

    if verbose:
        print()  # newline

    return {
        "choices": [{
            "message": {
                "content": full_content,
                "role": "assistant"
            }
        }]
    }


def call_image_api(api_key: str, prompt: str, size: str = "1024x1024") -> Dict:
    """Call image generation API using OpenAI SDK"""
    client = get_client(api_key)

    try:
        response = client.images.generate(
            model=MODEL_IMAGE,
            prompt=prompt,
            n=IMAGE_DEFAULTS["n"],
            response_format=IMAGE_DEFAULTS["response_format"],
            size=size,
            extra_body={
                "seed": IMAGE_DEFAULTS["seed"],
                "use_pe": IMAGE_DEFAULTS["use_pe"],
                "num_inference_steps": IMAGE_DEFAULTS["num_inference_steps"],
                "guidance_scale": IMAGE_DEFAULTS["guidance_scale"],
            }
        )

        # Return in consistent format
        if response.data and len(response.data) > 0:
            img_data = response.data[0]
            result = {
                "data": [{
                    "url": getattr(img_data, 'url', None),
                }]
            }
            # If b64_json format, decode and save
            if hasattr(img_data, 'b64_json') and img_data.b64_json:
                result["data"][0]["b64_json"] = img_data.b64_json
            return result
        return {"error": "No image generated"}

    except Exception as e:
        print(f"Image API Error: {e}")
        return {"error": str(e)}


# ============== Step Functions ==============

def step_1_intent_parser(api_key: str, triplet: Dict) -> Dict:
    print("\n[Step 1] Intent Parser...")
    system_prompt = """You are an intent parser for a football narrative AI. Given a triplet (entity, event_type, emotion_intensity), extract and output a JSON with: entity, event_type, emotion_intensity, conflict_archetype (hero_falls|underdog_rises|last_stand|bitter_betrayal|silent_redemption), psyche_mode (volcanic|melancholic|defiant|numb|transcendent). Output raw JSON only."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(triplet, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"})
    return json.loads(result["choices"][0]["message"]["content"])


def step_2_config_manager(api_key: str, intent: Dict) -> Dict:
    print("[Step 2] Config Manager...")
    system_prompt = """You are a narrative contract manager. Output JSON with: genre (社媒微小说), length_limit (300), pov_mode (emotion>=8: 第一人称热血, 5-7: 伪纪实, <5: 第三人称冷峻), forbidden_patterns (array), tone_anchor (English phrase)."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(intent, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"})
    return json.loads(result["choices"][0]["message"]["content"])


def step_3_logic_planner(api_key: str, intent: Dict, config: Dict) -> Dict:
    print("[Step 3] Logic Planner...")
    system_prompt = """You are a narrative logic planner. Output JSON with: act_1_words, act_2_words, act_3_words (total=300), pacing_target (staccato|wave|avalanche), sensory_anchors (3 items), emotion_score_series (5 floats 0-1)."""
    input_data = {**intent, **config}
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"})
    return json.loads(result["choices"][0]["message"]["content"])


def step_4_web_search(api_key: str, intent: Dict) -> Dict:
    print("[Step 4] Web Search...")
    system_prompt = """You are a sports research assistant. Search for match facts and cultural context. Output JSON with: match_facts (match_score, minute_of_event, venue, key_facts, confidence_scores), cultural_details (city_name, local_atmosphere, cultural_symbols). Use web search."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(intent, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"}, enable_web_search=True)
    return json.loads(result["choices"][0]["message"]["content"])


def step_5_creative_writer(api_key: str, intent: Dict, config: Dict, plan: Dict, web_data: Dict) -> Dict:
    print("[Step 5] Creative Writer...")
    system_prompt = """You are an award-winning Chinese micro-fiction writer. Write a micro-fiction in Chinese (<=300 chars). Rules: honor pov_mode, use 2+ sensory_anchors, follow act budgets, avoid forbidden_patterns. Output JSON: novel_text, word_count, sensory_anchors_used, fuzzified_facts."""
    input_data = {"intent": intent, "contract": config, "plan": plan, "web_data": web_data}
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"})
    return json.loads(result["choices"][0]["message"]["content"])


def step_6_safety_guard(api_key: str, creative: Dict, config: Dict) -> Dict:
    print("[Step 6] Safety Guard...")
    system_prompt = """You are a content safety auditor. Check for: compliance issues, forbidden patterns, fact confidence. Output JSON: compliance_pass (bool), compliance_issues (array), fact_confidence_pass (bool), unfuzzified_risks (array), overall_pass (bool), audit_note."""
    input_data = {"creative": creative, "forbidden_patterns": config.get("forbidden_patterns", [])}
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"})
    return json.loads(result["choices"][0]["message"]["content"])


def step_7_reflexion_critic(api_key: str, creative: Dict, intent: Dict, plan: Dict) -> Dict:
    print("[Step 7] Reflexion Critic...")
    system_prompt = """You are a narrative quality critic. Evaluate: persona_drift_sigma (0-1, threshold 0.30), emotion_arc_fit (0-1, threshold 0.70), word_count_ok (bool). Output JSON: persona_drift_sigma, emotion_arc_fit, word_count_ok, overall_pass (bool), rewrite_instructions (null if pass), iteration."""
    input_data = {"creative": creative, "intent": intent, "plan": plan}
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"})
    return json.loads(result["choices"][0]["message"]["content"])


def step_8_aesthetic_mapper(api_key: str, creative: Dict, intent: Dict) -> Dict:
    print("[Step 8] Aesthetic Mapper...")
    system_prompt = """You are a visual aesthetic mapper. Map emotions to colors and typography. Output JSON: dominant_color_hex, secondary_color_hex, font_weight (bold|regular), line_spacing_multiplier (1.2-2.0), landscape_base (English description), clip_cosine_score (0-1)."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps({"creative": creative, "intent": intent}, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"})
    return json.loads(result["choices"][0]["message"]["content"])


def step_9_image_renderer(api_key: str, aesthetic: Dict, creative: Dict) -> Dict:
    print("[Step 9] Image Renderer...")
    system_prompt = """You are an image prompt engineer. Generate image prompts for 1:1 and 9:16 formats. Output JSON: image_1x1_prompt (English, detailed), image_9x16_prompt (English, detailed)."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps({"aesthetic": aesthetic, "novel_text": creative.get("novel_text", "")}, ensure_ascii=False)},
    ]
    result = call_api(api_key, messages, response_format={"type": "json_object"})
    return json.loads(result["choices"][0]["message"]["content"])


def step_10_multimodal_publisher(api_key: str, creative: Dict, image_prompts: Dict, web_data: Dict, quality: Dict) -> Dict:
    print("[Step 10] MultiModal Publisher...")
    # Generate images
    image_1x1 = call_image_api(api_key, image_prompts.get("image_1x1_prompt", ""), "1024x1024")
    image_9x16 = call_image_api(api_key, image_prompts.get("image_9x16_prompt", ""), "1024x1820")
    
    return {
        "novel_text": creative.get("novel_text"),
        "word_count": creative.get("word_count"),
        "image_1x1_url": image_1x1.get("data", [{}])[0].get("url") if "data" in image_1x1 else None,
        "image_9x16_url": image_9x16.get("data", [{}])[0].get("url") if "data" in image_9x16 else None,
        "provenance_metadata": {
            "match_source": web_data.get("match_facts", {}).get("key_facts", []),
            "confidence_summary": f"confidence range: {min(web_data.get('match_facts', {}).get('confidence_scores', [0.5])):.2f}-{max(web_data.get('match_facts', {}).get('confidence_scores', [0.5])):.2f}"
        },
        "quality_status": "passed" if quality.get("overall_pass", True) else "degraded",
        "disclaimer": "AI creative narrative, not news report"
    }


# ============== Main Pipeline ==============

def run_pipeline(triplet: Dict, output_path: Optional[str] = None, skip_image: bool = False) -> Dict:
    """Run complete 10-step pipeline"""
    print("\n" + "=" * 60)
    print("WorldCup 2026 Parallel Universe Agent")
    print("=" * 60)
    print(f"\nInput triplet: {json.dumps(triplet, ensure_ascii=False)}")
    
    api_key = get_api_key()
    
    # Phase 1: Intent & Contract
    intent = step_1_intent_parser(api_key, triplet)
    print(f"  -> conflict_archetype: {intent.get('conflict_archetype')}")
    print(f"  -> psyche_mode: {intent.get('psyche_mode')}")
    
    config = step_2_config_manager(api_key, intent)
    print(f"  -> pov_mode: {config.get('pov_mode')}")
    
    # Phase 2: Planning & Search
    plan = step_3_logic_planner(api_key, intent, config)
    print(f"  -> pacing_target: {plan.get('pacing_target')}")
    
    web_data = step_4_web_search(api_key, intent)
    print(f"  -> venue: {web_data.get('match_facts', {}).get('venue', 'N/A')}")
    
    # Phase 3: Creative & Audit (with Reflexion loop)
    iteration = 0
    creative = None
    quality = {"overall_pass": False}
    
    while iteration < REFLEXION_MAX_ITERATIONS and not quality.get("overall_pass", False):
        iteration += 1
        print(f"\n  [Iteration {iteration}]")
        
        creative = step_5_creative_writer(api_key, intent, config, plan, web_data)
        print(f"    -> word_count: {creative.get('word_count')}")
        
        safety = step_6_safety_guard(api_key, creative, config)
        print(f"    -> safety_pass: {safety.get('overall_pass')}")
        
        if not safety.get("overall_pass", True):
            print(f"    -> Safety issues: {safety.get('compliance_issues', [])}")
            continue
        
        quality = step_7_reflexion_critic(api_key, creative, intent, plan)
        print(f"    -> persona_drift: {quality.get('persona_drift_sigma', 0):.2f}")
        print(f"    -> emotion_arc_fit: {quality.get('emotion_arc_fit', 0):.2f}")
        
        if quality.get("overall_pass", False):
            print("    -> Quality check PASSED")
        else:
            print(f"    -> Quality check FAILED, retrying...")
    
    # Phase 4: Aesthetic & Publishing
    aesthetic = step_8_aesthetic_mapper(api_key, creative, intent)
    print(f"  -> colors: {aesthetic.get('dominant_color_hex')} / {aesthetic.get('secondary_color_hex')}")
    
    image_prompts = step_9_image_renderer(api_key, aesthetic, creative)
    
    if skip_image:
        final_output = {
            "novel_text": creative.get("novel_text"),
            "word_count": creative.get("word_count"),
            "image_prompts": image_prompts,
            "quality_status": "passed" if quality.get("overall_pass") else "degraded",
            "iterations": iteration,
            "disclaimer": "AI creative narrative, not news report"
        }
    else:
        final_output = step_10_multimodal_publisher(api_key, creative, image_prompts, web_data, quality)
        final_output["iterations"] = iteration
    
    print("\n" + "=" * 60)
    print("Pipeline completed!")
    print("=" * 60)
    
    print(f"\nNovel ({creative.get('word_count')} chars):\n")
    print(creative.get("novel_text", ""))
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
        print(f"\nResult saved to: {output_path}")
    
    return final_output


def main():
    parser = argparse.ArgumentParser(description="WorldCup 2026 Parallel Universe Pipeline")
    parser.add_argument("--entity", type=str, help="Entity name")
    parser.add_argument("--event_type", type=str, help="Event type")
    parser.add_argument("--emotion_intensity", type=int, help="Emotion intensity (0-10)")
    parser.add_argument("--json", type=str, help="JSON file path for triplet")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--skip-image", action="store_true", help="Skip image generation")
    
    args = parser.parse_args()
    
    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            triplet = json.load(f)
    else:
        triplet = {
            "entity": args.entity,
            "event_type": args.event_type,
            "emotion_intensity": args.emotion_intensity,
        }
    
    run_pipeline(triplet, args.output, args.skip_image)


if __name__ == "__main__":
    main()
