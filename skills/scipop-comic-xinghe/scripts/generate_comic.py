#!/usr/bin/env python3
"""
科普连环画自动生成脚本

使用方法:
    python generate_comic.py --article "科普文章内容" --output ./output/

依赖:
    pip install openai Pillow
"""

import os
import sys
import json
import base64
import argparse
import time
from io import BytesIO
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("请安装 openai: pip install openai")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请安装 Pillow: pip install Pillow")
    sys.exit(1)


class SciPopComicGenerator:
    """科普连环画生成器 - 使用 OpenAI SDK"""

    BASE_URL = "https://aistudio.baidu.com/llm/lmapi/v3"
    ANALYSIS_MODEL = "ernie-5.0-thinking-preview"
    IMAGE_MODEL = "ernie-image-turbo"

    # 支持的图像尺寸
    SUPPORTED_SIZES = ["1024x1024", "1376x768", "1264x848", "1200x896", "896x1200", "848x1264", "768x1376"]

    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL
        )

    def _call_chat_api(self, messages: list, stream: bool = True, web_search: bool = False, max_retries: int = 3) -> dict:
        """调用文本/多模态API，支持重试和流式响应

        Args:
            messages: 消息列表
            stream: 是否使用流式响应
            web_search: 是否启用联网搜索增强
            max_retries: 最大重试次数

        Returns:
            {"content": "完整响应内容", "reasoning": "思考过程(可选)"}
        """
        extra_body = {}
        if web_search:
            extra_body["web_search"] = {"enable": True}

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.ANALYSIS_MODEL,
                    messages=messages,
                    stream=stream,
                    max_completion_tokens=65536,
                    extra_body=extra_body if extra_body else None
                )

                if stream:
                    # 解析流式响应 - 分别收集思考过程和最终回答
                    full_content = ""
                    reasoning_content = ""
                    for chunk in response:
                        if not chunk.choices or len(chunk.choices) == 0:
                            continue
                        delta = chunk.choices[0].delta
                        # 处理思考过程（reasoning_content）
                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            reasoning_content += delta.reasoning_content
                            # 可选：打印思考进度
                            # print(delta.reasoning_content, end="", flush=True)
                        # 处理最终回答（content）
                        if hasattr(delta, 'content') and delta.content:
                            full_content += delta.content
                    return {"content": full_content, "reasoning": reasoning_content}
                else:
                    result = {"content": response.choices[0].message.content}
                    if hasattr(response.choices[0].message, "reasoning_content"):
                        result["reasoning"] = response.choices[0].message.reasoning_content
                    return result

            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    raise Exception("API Key 无效或过期")
                elif "402" in error_msg or "insufficient" in error_msg.lower():
                    raise Exception("账户余额不足，请充值")
                elif "429" in error_msg or "rate" in error_msg.lower():
                    wait_time = (attempt + 1) ** 2
                    print(f"请求频繁，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    wait_time = (attempt + 1) ** 2
                    print(f"请求错误: {error_msg}，{wait_time}秒后重试...")
                    time.sleep(wait_time)

        raise Exception(f"API调用失败，已重试{max_retries}次")

    def _add_caption_to_image(self, image_bytes: bytes, caption: str) -> bytes:
        """在图像底部居中添加科普旁白

        Args:
            image_bytes: 原始图像字节
            caption: 科普旁白文字（20字以内）

        Returns:
            添加旁白后的图像字节
        """
        if not caption:
            return image_bytes

        # 打开图像
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size

        # 创建绘图对象
        draw = ImageDraw.Draw(image)

        # 尝试加载中文字体，依次尝试常用字体
        font_size = 36
        font = None
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS 备选
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
            "C:\Windows\Fonts\msyh.ttc",  # Windows 微软雅黑
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except Exception:
                    continue

        # 如果没有找到中文字体，使用默认字体
        if font is None:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

        # 计算文字尺寸
        bbox = draw.textbbox((0, 0), caption, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 底部留白区域高度
        padding = 20
        text_area_height = text_height + padding * 2

        # 计算文字位置（底部居中）
        x = (width - text_width) // 2
        y = height - text_area_height + padding

        # 绘制半透明背景矩形（提高文字可读性）
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # 背景矩形：圆角效果，半透明黑色
        bg_margin = 10
        bg_x1 = x - bg_margin
        bg_y1 = y - bg_margin
        bg_x2 = x + text_width + bg_margin
        bg_y2 = y + text_height + bg_margin

        # 绘制圆角矩形背景
        corner_radius = 8
        overlay_draw.rounded_rectangle(
            [bg_x1, bg_y1, bg_x2, bg_y2],
            radius=corner_radius,
            fill=(0, 0, 0, 180)  # 黑色，70% 不透明度
        )

        # 合并背景层
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay)

        # 重新创建绘图对象（在合并后的图像上）
        draw = ImageDraw.Draw(image)

        # 绘制文字（白色，带轻微描边效果）
        # 描边
        outline_color = (0, 0, 0, 255)
        for adj_x in [-1, 0, 1]:
            for adj_y in [-1, 0, 1]:
                if adj_x != 0 or adj_y != 0:
                    draw.text((x + adj_x, y + adj_y), caption, font=font, fill=outline_color)

        # 主文字（白色）
        draw.text((x, y), caption, font=font, fill=(255, 255, 255, 255))

        # 转回 RGB 模式（如果需要 PNG 格式）
        output = BytesIO()
        image_rgb = Image.new('RGB', image.size, (255, 255, 255))
        image_rgb.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else None)
        image_rgb.save(output, format='PNG')

        return output.getvalue()

    def _generate_image(self, prompt: str, size: str = "1024x1024", max_retries: int = 3) -> bytes:
        """生成图像，返回图像字节"""
        for attempt in range(max_retries):
            try:
                response = self.client.images.generate(
                    model=self.IMAGE_MODEL,
                    prompt=prompt,
                    n=1,
                    response_format="b64_json",
                    size=size,
                    extra_body={
                        "use_pe": True,
                        "num_inference_steps": 8,
                        "guidance_scale": 1.0
                    }
                )

                # 解码 base64 图像
                image_b64 = response.data[0].b64_json
                return base64.b64decode(image_b64)

            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    raise Exception("API Key 无效或过期")
                elif "402" in error_msg or "insufficient" in error_msg.lower():
                    raise Exception("账户余额不足，请充值")
                elif "429" in error_msg or "rate" in error_msg.lower():
                    wait_time = (attempt + 1) ** 2
                    print(f"请求频繁，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    wait_time = (attempt + 1) ** 2
                    print(f"图像生成错误: {error_msg}，{wait_time}秒后重试...")
                    time.sleep(wait_time)

        raise Exception(f"图像生成失败，已重试{max_retries}次")

    def phase1_analyze(self, article: str) -> dict:
        """Phase 1: 文章解析与Prompt建模"""
        print("=" * 50)
        print("Phase 1: 文章解析中...")

        system_prompt = """你是一位科普连环画脚本编写专家。分析文章并根据内容的丰富程度和结构确定最合适的 Panel 数量（4-6个）。输出一个 JSON 对象，包含四个字段："recommended_panels"（整数，4-6），"recommendation_reason"（一句话中文解释为什么这个 Panel 数量适合该文章），"style_seed"（简短的中文风格描述，在所有 Panel 中复用），"panels"（与推荐数量匹配的对象数组，每个对象包含 "id"、"scene" 中文场景描述、"caption" 中文科普旁白（20字以内，简洁有力）、"image_prompt" 中文图像生成提示）。仅输出原始 JSON，不要使用 markdown 代码块。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": article}
        ]

        result = self._call_chat_api(messages, stream=True)
        content = result["content"]

        if isinstance(content, str):
            data = json.loads(content)
        else:
            data = content

        print(f"推荐 Panel 数量: {data['recommended_panels']}")
        print(f"推荐理由: {data['recommendation_reason']}")
        print(f"风格种子: {data['style_seed']}")
        print(f"\n各 Panel 旁白:")
        for panel in data['panels']:
            caption = panel.get('caption', '（无旁白）')
            print(f"  Panel {panel['id']}: {caption}")

        return data

    def phase2_generate_panel(self, image_prompt: str, style_seed: str, panel_id: int) -> bytes:
        """Phase 2: 生成单个Panel图像"""
        full_prompt = f"{image_prompt}，{style_seed}，高质量，连环画"

        print(f"  生成 Panel {panel_id}...")

        return self._generate_image(full_prompt, size="1024x1024")

    def phase2_generate_all(self, phase1_result: dict, output_dir: Path) -> tuple:
        """Phase 2: 生成所有Panel

        Returns:
            (panel_paths, final_prompts): 图像路径列表和最终使用的prompt字典
        """
        print("=" * 50)
        print("Phase 2: 生成Panel图像...")

        style_seed = phase1_result["style_seed"]
        panels = phase1_result["panels"]
        panel_paths = []
        captions = {}
        final_prompts = {}  # 记录每个 Panel 最终使用的 prompt（用于 Phase 3）

        for panel in panels:
            panel_id = panel["id"]
            image_prompt = panel["image_prompt"]
            caption = panel.get("caption", "")

            # 构建完整 prompt（包含 style_seed）
            full_prompt = f"{image_prompt}，{style_seed}，高质量，连环画"

            # 保存旁白
            captions[panel_id] = caption

            # 保存最终 prompt（用于 Phase 3 全局合成）
            final_prompts[panel_id] = full_prompt

            print(f"  生成 Panel {panel_id}: {caption}")

            image_bytes = self.phase2_generate_panel(image_prompt, style_seed, panel_id)

            # 在图像底部居中添加科普旁白
            if caption:
                image_bytes = self._add_caption_to_image(image_bytes, caption)

            # 保存图像
            panel_path = output_dir / f"panel_{panel_id:02d}.png"
            panel_path.write_bytes(image_bytes)
            panel_paths.append(str(panel_path))
            print(f"    已保存: {panel_path}")

            # 避免请求过快
            time.sleep(1)

        # 保存所有旁白到文件
        captions_path = output_dir / "captions.json"
        captions_path.write_text(json.dumps(captions, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  旁白已保存: {captions_path}")

        # 保存最终 prompts（用于 Phase 3）
        prompts_path = output_dir / "final_prompts.json"
        prompts_path.write_text(json.dumps(final_prompts, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  最终 Prompts 已保存: {prompts_path}")

        return panel_paths, final_prompts

    def phase3_generate_global(self, style_seed: str, final_prompts: dict, layout: str, output_dir: Path) -> str:
        """Phase 3: 生成全局大图

        Args:
            style_seed: 风格种子
            final_prompts: Panel ID -> 最终 image_prompt 的映射（来自 Phase 2 迭代后的满意结果）
            layout: 布局（如 2x2, 2x3）
            output_dir: 输出目录

        Returns:
            全局大图路径
        """
        print("=" * 50)
        print("Phase 3: 生成全局大图...")

        num_panels = len(final_prompts)

        # 使用 Phase 2 迭代后的最终 Prompt 构建全局 Prompt
        panel_descriptions = "\n".join([
            f"第{panel_id}格：{final_prompts[panel_id]}"
            for panel_id in sorted(final_prompts.keys())
        ])

        global_prompt = f"""{layout} 格连环画，共 {num_panels} 格，{style_seed}，
每格之间用粗黑边框清晰分隔，按阅读顺序排列：
{panel_descriptions}"""

        print(f"  使用 {num_panels} 个最终 Prompt 合并生成全局图...")

        # 注意：ernie-image-turbo 最大支持 1376x768，这里用最大的横向尺寸
        image_bytes = self._generate_image(global_prompt, size="1376x768")

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

    # Phase 2: 生成所有 Panel，返回图像路径和最终 prompts
    panel_paths, final_prompts = generator.phase2_generate_all(phase1_result, output_dir)

    # Phase 3: 使用最终 prompts 生成全局大图
    style_seed = phase1_result["style_seed"]
    global_path = generator.phase3_generate_global(style_seed, final_prompts, layout, output_dir)

    print("\n" + "=" * 50)
    print("✅ 连环画生成完成!")
    print(f"   Panel 图像: {len(panel_paths)} 张")
    print(f"   全局大图: {global_path}")


if __name__ == "__main__":
    main()