#!/usr/bin/env python3
"""
星河 AI 生图脚本 — 单张/多张图片生成
通过百度 AIStudio ERNIE-Image-Turbo API 生成图片

用法：
  python3 generate.py --prompt "提示词" --size 1264x848 --output out.png

依赖：
  pip install openai
"""

import argparse
import base64
import os
import sys
from pathlib import Path

# ── 常量 ─────────────────────────────────────────────────────────
BASE_URL = "https://aistudio.baidu.com/llm/lmapi/v3"
MODEL    = "ernie-image-turbo"  # ⚠️ 全小写，大写会报 HTTP 400

VALID_SIZES = {
    "1024x1024", "848x1264", "768x1376",
    "896x1200",  "1264x848", "1376x768", "1200x896",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="星河 AI 生图脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 generate.py --prompt "科技感封面图" --size 1376x768 --output cover.png
  python3 generate.py -p "小红书卡片" -s 848x1264 -o card.png --steps 50 --no-pe
  python3 generate.py -p "信息图" -s 1264x848 -o info.png --n 2 --seed 42
        """,
    )
    parser.add_argument("-p", "--prompt",  required=True,           help="生图提示词（推荐中文）")
    parser.add_argument("-s", "--size",    default="1024x1024",     help="图片尺寸，如 1264x848（默认 1024x1024）")
    parser.add_argument("-o", "--output",  required=True,           help="输出文件路径，.png 格式")
    parser.add_argument("--n",             type=int, default=1,     help="生成张数 1-4（默认 1）")
    parser.add_argument("--steps",         type=int, default=8,     help="推理步数：8=Turbo 快速，50=高质量（默认 8）")
    parser.add_argument("--guidance",      type=float, default=1.0, help="引导强度 guidance_scale（默认 1.0）")
    parser.add_argument("--no-pe",         action="store_true",     help="禁用提示词增强 PE（默认开启）")
    parser.add_argument("--seed",          type=int, default=-1,    help="随机种子，-1 为随机（默认 -1）")
    parser.add_argument("--api-key",       default=None,            help="临时覆盖 AISTUDIO_API_KEY 环境变量")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── API Key ───────────────────────────────────────────────────
    api_key = args.api_key or os.environ.get("AISTUDIO_API_KEY", "")
    if not api_key:
        print("错误: 未找到 API Key。请设置 AISTUDIO_API_KEY 环境变量，或使用 --api-key 参数传入。", file=sys.stderr)
        sys.exit(1)

    # ── 尺寸校验 ─────────────────────────────────────────────────
    if args.size not in VALID_SIZES:
        print(f"错误: 不合法的尺寸 '{args.size}'。合法尺寸：{', '.join(sorted(VALID_SIZES))}", file=sys.stderr)
        sys.exit(1)

    # ── 张数校验 ─────────────────────────────────────────────────
    if not 1 <= args.n <= 4:
        print("错误: --n 必须在 1~4 之间。", file=sys.stderr)
        sys.exit(1)

    # ── 导入 openai ──────────────────────────────────────────────
    try:
        from openai import OpenAI
    except ImportError:
        print("错误: 未找到 openai 库。请运行：pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    # ── 构造 extra_body ──────────────────────────────────────────
    extra: dict = {
        "use_pe": not args.no_pe,
        "num_inference_steps": args.steps,
        "guidance_scale": args.guidance,
    }
    if args.seed != -1:
        extra["seed"] = args.seed

    # ── 调用 API ─────────────────────────────────────────────────
    try:
        resp = client.images.generate(
            model=MODEL,
            prompt=args.prompt,
            n=args.n,
            response_format="b64_json",
            size=args.size,          # type: ignore[arg-type]
            extra_body=extra,
        )
    except Exception as e:
        print(f"错误: API 调用失败 — {e}", file=sys.stderr)
        sys.exit(1)

    # ── 保存图片 ─────────────────────────────────────────────────
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = resp.data or []
    if not data:
        print("错误: API 返回空数据。", file=sys.stderr)
        sys.exit(1)

    saved: list[str] = []
    for i, item in enumerate(data):
        raw = item.b64_json or ""
        if not raw:
            print(f"警告: 第 {i+1} 张图片数据为空，跳过。", file=sys.stderr)
            continue

        if args.n == 1:
            dest = out_path
        else:
            dest = out_path.with_stem(f"{out_path.stem}_{i+1:02d}")

        dest.write_bytes(base64.b64decode(raw))
        saved.append(str(dest))
        print(f"✓ 已保存: {dest}")
        print(f"OUTPUT: {dest}")

    if not saved:
        print("错误: 没有图片被成功保存。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
