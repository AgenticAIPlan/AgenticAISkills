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


def get_chinese_font(size: int = 36) -> ImageFont.FreeTypeFont:
    """获取中文字体，支持跨平台

    Args:
        size: 字体大小

    Returns:
        Pillow ImageFont 对象
    """
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",  # macOS 备选
        "C:/Windows/Fonts/msyh.ttc",  # Windows 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

    # 如果没有找到中文字体，尝试使用默认字体
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


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

        # 加载中文字体（复用跨平台字体加载函数）
        font = get_chinese_font(size=36)

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

    def _generate_image(self, prompt: str, size: str = "1024x1024", max_retries: int = 3, negative_prompt: str = None) -> bytes:
        """生成图像，返回图像字节

        Args:
            prompt: 图像生成提示词
            size: 图像尺寸
            max_retries: 最大重试次数
            negative_prompt: 负面提示词（避免重复文字、多余肢体等问题）
        """
        # 默认负面提示词（避免常见图像生成问题）
        if negative_prompt is None:
            negative_prompt = "重复文字，多余的手，第三只手，变形的手指，人体结构错误，比例失调，模糊不清，风格混乱"

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
                        "guidance_scale": 1.0,
                        "negative_prompt": negative_prompt  # 负面提示词
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

        system_prompt = """你是一位科普连环画脚本编写专家。分析文章并根据内容的丰富程度和结构确定最合适的 Panel 数量（4-6个）。输出一个 JSON 对象，包含以下字段：
- "recommended_panels"（整数，4-6）
- "recommendation_reason"（一句话中文解释为什么这个 Panel 数量适合该文章）
- "style_seed"（简短的中文风格描述，在所有 Panel 中复用）
- "key_facts"（对象，包含：key_numbers 关键数字列表、key_names 关键人物/机构名称列表、key_locations 关键地点列表、key_dates 关键时间列表、key_terms 关键术语列表）
- "panels"（数组，每个对象包含 "id"、"scene" 场景描述、"caption" 科普旁白20字以内、"image_prompt" 图像生成提示、"fact_check" 本画面关键事实）

⚠️ 关键信息保留要求：
1. 必须保留文章中的关键数字（年份、数量、百分比等）
2. 必须准确使用人物姓名和身份，不可张冠李戴
3. 必须保留专有名词和科学术语的原文
4. 时间、地点必须与文章记载一致

仅输出原始 JSON，不要使用 markdown 代码块。"""

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

        # 显示关键信息
        key_facts = data.get('key_facts', {})
        if key_facts:
            print(f"\n关键信息提取:")
            if key_facts.get('key_numbers'):
                print(f"  关键数字: {', '.join(key_facts['key_numbers'][:5])}")
            if key_facts.get('key_names'):
                print(f"  关键人物/机构: {', '.join(key_facts['key_names'][:5])}")
            if key_facts.get('key_locations'):
                print(f"  关键地点: {', '.join(key_facts['key_locations'][:5])}")
            if key_facts.get('key_dates'):
                print(f"  关键时间: {', '.join(key_facts['key_dates'][:3])}")

        print(f"\n各 Panel 旁白与事实核对:")
        for panel in data['panels']:
            caption = panel.get('caption', '（无旁白）')
            fact_check = panel.get('fact_check', '（无）')
            print(f"  Panel {panel['id']}: {caption}")
            print(f"    事实: {fact_check}")

        return data

    def phase1b_validate_script(self, script: dict) -> dict:
        """Phase 1b: 脚本内容校验

        对生成的脚本进行质量校验，确保有吸引力、清晰、优质。

        Args:
            script: Phase 1 生成的脚本数据

        Returns:
            校验结果字典，包含 is_valid 和 validation_report
        """
        print("=" * 50)
        print("Phase 1b: 脚本内容校验中...")

        panels = script.get('panels', [])

        # 1. 字段完整性校验
        required_fields = ['id', 'scene', 'caption', 'image_prompt', 'fact_check']
        missing_fields = []

        for panel in panels:
            panel_id = panel.get('id', 'unknown')
            for field in required_fields:
                if field not in panel or not panel[field]:
                    missing_fields.append(f"Panel {panel_id} 缺少字段: {field}")

        if missing_fields:
            print("❌ 字段完整性校验失败:")
            for msg in missing_fields:
                print(f"  - {msg}")
            return {"is_valid": False, "validation_report": {"error": "字段完整性校验失败"}}

        print("✓ 字段完整性校验通过")

        # 2. 调用 API 进行方法论评估
        validation_prompt = """请对以下连环画脚本进行质量评估，从以下五个维度打分：
1. 叙事吸引力（25%）：开篇是否抓人？叙事是否有起伏？黄金开篇、悬念留白、情绪起伏、认知反差
2. 逻辑层次感（25%）：起承转合？因果链条？信息递进？无缝过渡？
3. 内容准确性（20%）：关键信息保留？科学事实准确？术语正确？
4. 画面可绘性（20%）：场景明确？主体清晰？动作可绘？
5. 风格一致性（10%）：画风统一？比例协调？

请输出一个 JSON 对象，包含以下结构：
{
  "overall_score": "<优秀/良好/一般/较差>",
  "dimension_scores": {
    "narrative_attractiveness": {"score": "<评级>", "issues": ["问题列表"]},
    "logical_hierarchy": {"score": "<评级>", "issues": ["问题列表"]},
    "content_accuracy": {"score": "<评级>", "issues": ["问题列表"]},
    "visual_feasibility": {"score": "<评级>", "issues": ["问题列表"]},
    "style_consistency": {"score": "<评级>", "issues": ["问题列表"]}
  },
  "summary": "整体评价摘要",
  "improvement_suggestions": ["改进建议列表"]
}

仅输出原始 JSON，不要使用 markdown 代码块。以下是需要评估的脚本：
""" + json.dumps(script, ensure_ascii=False, indent=2)

        messages = [
            {"role": "system", "content": "你是一位专业的连环画脚本质量评估专家。"},
            {"role": "user", "content": validation_prompt}
        ]

        result = self._call_chat_api(messages, stream=True)
        content = result["content"]

        try:
            if isinstance(content, str):
                validation = json.loads(content)
            else:
                validation = content
        except json.JSONDecodeError:
            print("⚠️ 校验结果解析失败，跳过详细校验")
            return {"is_valid": True, "validation_report": {"summary": "校验跳过"}}

        # 输出校验结果
        print(f"\n整体评价: {validation.get('overall_score', '未知')}")
        print(f"摘要: {validation.get('summary', '')}")

        dimension_scores = validation.get('dimension_scores', {})
        for dim_name, dim_data in dimension_scores.items():
            score = dim_data.get('score', '未知')
            issues = dim_data.get('issues', [])
            print(f"\n{dim_name}: {score}")
            if issues:
                for issue in issues:
                    print(f"  - {issue}")

        suggestions = validation.get('improvement_suggestions', [])
        if suggestions:
            print(f"\n改进建议:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")

        # 根据评分决定是否通过
        overall_score = validation.get('overall_score', '')
        is_valid = overall_score in ['优秀', '良好']

        if is_valid:
            print("\n✓ 脚本校验通过")
        else:
            print("\n⚠️ 脚本质量需要改进（当前为" + overall_score + "）")

        return {
            "is_valid": is_valid,
            "validation_report": validation
        }

    def phase2_generate_panel(self, image_prompt: str, style_seed: str, panel_id: int) -> bytes:
        """Phase 2: 生成单个Panel图像

        Args:
            image_prompt: 图像生成提示词
            style_seed: 风格种子
            panel_id: Panel 编号
        """
        # 构建完整 prompt（包含质量保障关键词）
        full_prompt = f"{image_prompt}，{style_seed}，高质量，连环画，画面清晰，人体结构正确"

        print(f"  生成 Panel {panel_id}...")

        return self._generate_image(full_prompt, size="1024x1024")

    def phase2_generate_all(self, phase1_result: dict, output_dir: Path) -> tuple:
        """Phase 2: 生成所有Panel

        Returns:
            (panel_paths, final_prompts, captions): 图像路径列表、最终使用的prompt字典、旁白字典
        """
        print("=" * 50)
        print("Phase 2: 生成Panel图像...")

        style_seed = phase1_result["style_seed"]
        panels = phase1_result["panels"]
        panel_paths = []
        captions = {}
        final_prompts = {}  # 记录每个 Panel 最终使用的 prompt（用于 Phase 3）
        fact_checks = {}  # 记录每个 Panel 的关键事实

        for panel in panels:
            panel_id = panel["id"]
            image_prompt = panel["image_prompt"]
            caption = panel.get("caption", "")
            fact_check = panel.get("fact_check", "")

            # 构建完整 prompt（包含 style_seed 和质量保障关键词）
            full_prompt = f"{image_prompt}，{style_seed}，高质量，连环画，画面清晰，人体结构正确"

            # 保存旁白
            captions[panel_id] = caption

            # 保存事实核对信息
            fact_checks[panel_id] = fact_check

            # 保存最终 prompt（用于 Phase 3 全局合成）
            final_prompts[panel_id] = full_prompt

            print(f"  生成 Panel {panel_id}: {caption}")
            if fact_check:
                print(f"    事实核对: {fact_check}")

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

        # 保存事实核对信息
        if fact_checks:
            fact_checks_path = output_dir / "fact_checks.json"
            fact_checks_path.write_text(json.dumps(fact_checks, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  事实核对信息已保存: {fact_checks_path}")

        # 保存最终 prompts（用于 Phase 3）
        prompts_path = output_dir / "final_prompts.json"
        prompts_path.write_text(json.dumps(final_prompts, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  最终 Prompts 已保存: {prompts_path}")

        return panel_paths, final_prompts, captions

    def _add_captions_to_global_comic(self, image_bytes: bytes, captions: dict, layout: str) -> bytes:
        """在全局大图的每个格子底部居中添加科普旁白

        Args:
            image_bytes: 原始全局大图字节
            captions: Panel ID -> 旁白文字 的映射
            layout: 布局（如 "2x2", "2x3"）

        Returns:
            添加旁白后的图像字节
        """
        # 打开图像
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size

        # 解析布局
        rows, cols = map(int, layout.lower().split('x'))
        cell_width = width // cols
        cell_height = height // rows

        # 转换为 RGBA 模式以支持半透明
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # 根据格子大小调整字体（字体大小约为格子高度的 8%）
        font_size = max(16, min(32, int(cell_height * 0.08)))

        # 加载中文字体（复用跨平台字体加载函数）
        font = get_chinese_font(size=font_size)

        # 创建绘图对象
        draw = ImageDraw.Draw(image)

        # 按阅读顺序处理每个格子（从左到右、从上到下）
        for panel_id in sorted(captions.keys()):
            caption = captions[panel_id]
            if not caption:
                continue

            # 计算格子位置（panel_id 从 1 开始）
            idx = panel_id - 1
            row = idx // cols
            col = idx % cols

            # 格子边界
            cell_x1 = col * cell_width
            cell_y1 = row * cell_height
            cell_x2 = cell_x1 + cell_width
            cell_y2 = cell_y1 + cell_height

            # 计算文字尺寸
            bbox = draw.textbbox((0, 0), caption, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 文字位置（格子底部居中）
            padding = 8
            text_x = cell_x1 + (cell_width - text_width) // 2
            text_y = cell_y2 - text_height - padding - 5

            # 绘制半透明背景
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            bg_margin = 5
            bg_x1 = text_x - bg_margin
            bg_y1 = text_y - bg_margin
            bg_x2 = text_x + text_width + bg_margin
            bg_y2 = text_y + text_height + bg_margin

            # 圆角矩形背景
            corner_radius = 4
            overlay_draw.rounded_rectangle(
                [bg_x1, bg_y1, bg_x2, bg_y2],
                radius=corner_radius,
                fill=(0, 0, 0, 180)
            )

            # 合并背景
            image = Image.alpha_composite(image, overlay)
            draw = ImageDraw.Draw(image)

            # 描边
            outline_color = (0, 0, 0, 255)
            for adj_x in [-1, 0, 1]:
                for adj_y in [-1, 0, 1]:
                    if adj_x != 0 or adj_y != 0:
                        draw.text((text_x + adj_x, text_y + adj_y), caption, font=font, fill=outline_color)

            # 主文字（白色）
            draw.text((text_x, text_y), caption, font=font, fill=(255, 255, 255, 255))

        # 转回 RGB 并保存
        output = BytesIO()
        image_rgb = Image.new('RGB', image.size, (255, 255, 255))
        image_rgb.paste(image, mask=image.split()[3])
        image_rgb.save(output, format='PNG')

        return output.getvalue()

    @staticmethod
    def create_comic_grid(panel_paths: list, layout: str, border_width: int = 4) -> Image.Image:
        """使用 Pillow 拼接 Panel 图像为连环画大图

        Args:
            panel_paths: Panel 图像路径列表（按 panel_id 排序）
            layout: 布局（如 "2x2", "2x3"）
            border_width: 边框宽度，默认 4px

        Returns:
            拼接后的图像
        """
        # 解析布局
        rows, cols = map(int, layout.lower().split('x'))

        # 按 panel_id 排序（确保面板按顺序排列）
        sorted_paths = sorted(panel_paths, key=lambda p: int(Path(p).stem.split('_')[-1]))

        # 加载所有图像
        images = [Image.open(p) for p in sorted_paths]

        # 假设所有图像尺寸相同（均为 1024x1024）
        img_size = images[0].size  # (width, height)

        # 计算总尺寸（包括边框）
        total_width = cols * img_size[0] + (cols + 1) * border_width
        total_height = rows * img_size[1] + (rows + 1) * border_width

        # 创建新画布（白色背景）
        canvas = Image.new('RGB', (total_width, total_height), color='white')

        # 绘制黑色边框（整个画布边缘）
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([(0, 0), (total_width - 1, total_height - 1)], outline='black', width=border_width)

        # 依次粘贴图像
        for idx, img in enumerate(images):
            row = idx // cols
            col = idx % cols

            # 计算粘贴位置（包含边框）
            x = border_width + col * (img_size[0] + border_width)
            y = border_width + row * (img_size[1] + border_width)

            canvas.paste(img, (x, y))

            # 绘制格子边框（右侧和下侧）
            if col < cols - 1:  # 右侧边框
                border_x = x + img_size[0]
                draw.rectangle([(border_x, y), (border_x + border_width - 1, y + img_size[1] - 1)], fill='black')
            if row < rows - 1:  # 下侧边框
                border_y = y + img_size[1]
                draw.rectangle([(x, border_y), (x + img_size[0] - 1, border_y + border_width - 1)], fill='black')

        return canvas

    def phase3_generate_global(self, panel_paths: list, layout: str, output_dir: Path) -> str:
        """Phase 3: 生成全局大图（使用 Pillow 拼接）

        Args:
            panel_paths: Panel 图像路径列表
            layout: 布局（如 2x2, 2x3）
            output_dir: 输出目录

        Returns:
            全局大图路径
        """
        print("=" * 50)
        print("Phase 3: 生成全局大图（拼接Panel图像）...")

        num_panels = len(panel_paths)

        print(f"  使用 {num_panels} 个 Panel 拼接生成全局图...")

        # 使用拼接函数生成全局大图
        global_image = self.create_comic_grid(panel_paths, layout, border_width=4)

        # 保存大图
        global_path = output_dir / "global_comic.png"
        global_image.save(global_path)
        print(f"已保存全局大图: {global_path}")

        return str(global_path)


def main():
    parser = argparse.ArgumentParser(description="科普连环画自动生成工具")
    parser.add_argument("--article", "-a", required=True, help="科普文章内容")
    parser.add_argument("--output", "-o", default="./output/", help="输出目录")
    parser.add_argument("--layout", "-l", default=None, help="布局（如 2x2, 2x3）")
    parser.add_argument("--phase1-only", action="store_true", help="仅执行Phase 1")
    parser.add_argument("--skip-validation", action="store_true", help="跳过Phase 1b校验")
    parser.add_argument("--max-validation-retries", type=int, default=2, help="校验不通过时的最大重试次数")

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

    # 单独保存关键信息，便于核对
    key_facts = phase1_result.get('key_facts', {})
    if key_facts:
        key_facts_path = output_dir / "key_facts.json"
        key_facts_path.write_text(json.dumps(key_facts, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"关键信息已保存: {key_facts_path}")

    if args.phase1_only:
        print("\n仅执行Phase 1模式，完成。")
        return

    # Phase 1b: 脚本内容校验
    if not args.skip_validation:
        validation_result = generator.phase1b_validate_script(phase1_result)

        # 保存校验结果
        validation_path = output_dir / "phase1b_validation.json"
        validation_path.write_text(json.dumps(validation_result.get('validation_report', {}), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Phase 1b 校验结果已保存: {validation_path}")

        # 如果校验不通过，询问用户是否继续
        if not validation_result.get('is_valid', True):
            print("\n⚠️ 脚本校验未通过，建议优化脚本后重新生成。")
            print("当前脚本已保存，如需继续生成，请使用 --skip-validation 参数。")
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

    # Phase 2: 生成所有 Panel，返回图像路径、最终 prompts 和旁白
    panel_paths, final_prompts, captions = generator.phase2_generate_all(phase1_result, output_dir)

    # Phase 3: 使用 Panel 图像拼接生成全局大图（不再使用模型生成）
    global_path = generator.phase3_generate_global(panel_paths, layout, output_dir)

    print("\n" + "=" * 50)
    print("✅ 连环画生成完成!")
    print(f"   Panel 图像: {len(panel_paths)} 张")
    print(f"   全局大图: {global_path}")


if __name__ == "__main__":
    main()