#!/usr/bin/env python3
"""
科普连环画自动生成脚本

使用方法:
    python generate_comic.py --article "科普文章内容" --output ./output/

依赖:
    pip install requests
"""

import os
import sys
import json
import base64
import argparse
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    sys.exit(1)


class SciPopComicGenerator:
    """科普连环画生成器"""

    CHAT_ENDPOINT = "https://aistudio.baidu.com/llm/lmapi/v3/chat/completions"
    IMAGE_ENDPOINT = "https://aistudio.baidu.com/llm/lmapi/v3/images/generations"
    ANALYSIS_MODEL = "ernie-5.0-thinking-preview"
    IMAGE_MODEL = "ernie-image-turbo"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def _call_chat_api(self, payload: dict, max_retries: int = 3) -> dict:
        """调用文本/多模态API，支持重试"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.CHAT_ENDPOINT,
                    headers=self.headers,
                    json=payload,
                    timeout=120
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise Exception("API Key 无效或过期")
                elif response.status_code == 402:
                    raise Exception("账户余额不足，请充值")
                elif response.status_code == 429:
                    wait_time = (attempt + 1) ** 2
                    print(f"请求频繁，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    wait_time = (attempt + 1) ** 2
                    print(f"HTTP {response.status_code}，{wait_time}秒后重试...")
                    time.sleep(wait_time)
            except requests.exceptions.Timeout:
                print(f"请求超时，重试 {attempt + 1}/{max_retries}")
                time.sleep(2)

        raise Exception(f"API调用失败，已重试{max_retries}次")

    def _call_image_api(self, payload: dict, max_retries: int = 3) -> dict:
        """调用图像生成API，支持重试"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.IMAGE_ENDPOINT,
                    headers=self.headers,
                    json=payload,
                    timeout=120
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise Exception("API Key 无效或过期")
                elif response.status_code == 402:
                    raise Exception("账户余额不足，请充值")
                elif response.status_code == 429:
                    wait_time = (attempt + 1) ** 2
                    print(f"请求频繁，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    wait_time = (attempt + 1) ** 2
                    print(f"HTTP {response.status_code}，{wait_time}秒后重试...")
                    time.sleep(wait_time)
            except requests.exceptions.Timeout:
                print(f"请求超时，重试 {attempt + 1}/{max_retries}")
                time.sleep(2)

        raise Exception(f"图像API调用失败，已重试{max_retries}次")

    def phase1_analyze(self, article: str) -> dict:
        """Phase 1: 文章解析与Prompt建模"""
        print("=" * 50)
        print("Phase 1: 文章解析中...")

        system_prompt = """你是一位科普连环画脚本编写专家。分析文章并根据内容的丰富程度和结构确定最合适的 Panel 数量（4-6个）。输出一个 JSON 对象，包含四个字段："recommended_panels"（整数，4-6），"recommendation_reason"（一句话中文解释为什么这个 Panel 数量适合该文章），"style_seed"（简短的中文风格描述，在所有 Panel 中复用），"panels"（与推荐数量匹配的对象数组，每个对象包含 "id"、"scene" 中文场景描述、"image_prompt" 中文图像生成提示）。仅输出原始 JSON，不要使用 markdown 代码块。"""

        payload = {
            "model": self.ANALYSIS_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": article}
            ],
            "stream": True,
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 65536
        }

        result = self._call_chat_api(payload)
        content = result["choices"][0]["message"]["content"]

        if isinstance(content, str):
            data = json.loads(content)
        else:
            data = content

        print(f"推荐 Panel 数量: {data['recommended_panels']}")
        print(f"推荐理由: {data['recommendation_reason']}")
        print(f"风格种子: {data['style_seed']}")

        return data

    def phase2_generate_panel(self, image_prompt: str, style_seed: str, panel_id: int) -> bytes:
        """Phase 2: 生成单个Panel图像"""
        full_prompt = f"{image_prompt}，{style_seed}，高质量，连环画"

        print(f"  生成 Panel {panel_id}...")

        payload = {
            "model": self.IMAGE_MODEL,
            "prompt": full_prompt,
            "n": 1,
            "response_format": "b64_json",
            "size": "1024x1024",
            "use_pe": True,
            "num_inference_steps": 8,
            "guidance_scale": 1.0
        }

        result = self._call_image_api(payload)
        image_data = result["data"][0]["b64_json"]

        return base64.b64decode(image_data)

    def phase2_generate_all(self, phase1_result: dict, output_dir: Path) -> list:
        """Phase 2: 生成所有Panel"""
        print("=" * 50)
        print("Phase 2: 生成Panel图像...")

        style_seed = phase1_result["style_seed"]
        panels = phase1_result["panels"]
        panel_paths = []

        for panel in panels:
            panel_id = panel["id"]
            image_prompt = panel["image_prompt"]

            image_bytes = self.phase2_generate_panel(image_prompt, style_seed, panel_id)

            # 保存图像
            panel_path = output_dir / f"panel_{panel_id:02d}.png"
            panel_path.write_bytes(image_bytes)
            panel_paths.append(str(panel_path))
            print(f"  已保存: {panel_path}")

            # 避免请求过快
            time.sleep(1)

        return panel_paths

    def phase3_generate_global(self, phase1_result: dict, layout: str, output_dir: Path) -> str:
        """Phase 3: 生成全局大图"""
        print("=" * 50)
        print("Phase 3: 生成全局大图...")

        style_seed = phase1_result["style_seed"]
        panels = phase1_result["panels"]
        num_panels = len(panels)

        # 构建全局Prompt
        panel_descriptions = "\n".join([
            f"第{p['id']}格：{p['image_prompt']}"
            for p in panels
        ])

        global_prompt = f"""{layout} 格连环画，共 {num_panels} 格，{style_seed}，
每格之间用粗黑边框清晰分隔，按阅读顺序排列：
{panel_descriptions}"""

        payload = {
            "model": self.IMAGE_MODEL,
            "prompt": global_prompt,
            "n": 1,
            "response_format": "b64_json",
            "size": "2048x2048",
            "use_pe": True,
            "num_inference_steps": 8,
            "guidance_scale": 1.0
        }

        result = self._call_image_api(payload)
        image_data = result["data"][0]["b64_json"]

        image_bytes = base64.b64decode(image_data)

        # 保存大图
        global_path = output_dir / "global_comic.png"
        global_path.write_bytes(image_bytes)
        print(f"已保存全局大图: {global_path}")

        return str(global_path)


def main():
    parser = argparse.ArgumentParser(description="科普连环画自动生成工具")
    parser.add_argument("--article", "-a", required=True, help="科普文章内容")
    parser.add_argument("--output", "-o", default="./output/", help="输出目录")
    parser.add_argument("--layout", "-l", default=None, help="布局（如 2x2, 2x3）")
    parser.add_argument("--phase1-only", action="store_true", help="仅执行Phase 1")

    args = parser.parse_args()

    # 检查API Key
    api_key = os.environ.get("AISTUDIO_API_KEY")
    if not api_key:
        print("错误: 请设置环境变量 AISTUDIO_API_KEY")
        sys.exit(1)

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 初始化生成器
    generator = SciPopComicGenerator(api_key)

    # Phase 1
    phase1_result = generator.phase1_analyze(args.article)

    # 保存Phase 1结果
    phase1_path = output_dir / "phase1_result.json"
    phase1_path.write_text(json.dumps(phase1_result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Phase 1 结果已保存: {phase1_path}")

    if args.phase1_only:
        print("\n仅执行Phase 1模式，完成。")
        return

    # 推荐布局
    num_panels = phase1_result["recommended_panels"]
    layout_recommendations = {
        4: "2x2",
        5: "2x3",
        6: "2x3"
    }
    layout = args.layout or layout_recommendations.get(num_panels, "2x3")
    print(f"\n使用布局: {layout}")

    # Phase 2
    panel_paths = generator.phase2_generate_all(phase1_result, output_dir)

    # Phase 3
    global_path = generator.phase3_generate_global(phase1_result, layout, output_dir)

    print("\n" + "=" * 50)
    print("✅ 连环画生成完成!")
    print(f"   Panel 图像: {len(panel_paths)} 张")
    print(f"   全局大图: {global_path}")


if __name__ == "__main__":
    main()