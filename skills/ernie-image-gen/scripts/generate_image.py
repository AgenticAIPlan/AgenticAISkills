#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from common import generate_image, load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="通过 ERNIE Image 服务生成图片并归档")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径")
    parser.add_argument("--prompt", required=True, help="生成提示词")
    parser.add_argument(
        "--text-verbatim",
        action="append",
        default=[],
        help="图中文字逐字内容，可重复传入多次",
    )
    parser.add_argument("--width", type=int, help="覆盖默认宽度")
    parser.add_argument("--height", type=int, help="覆盖默认高度")
    parser.add_argument("--steps", type=int, help="覆盖 num_inference_steps")
    parser.add_argument("--guidance-scale", type=float, help="覆盖 guidance_scale")
    parser.add_argument("--seed", type=int, help="固定随机种子")
    parser.add_argument(
        "--response-format",
        choices=["b64_json", "url"],
        help="覆盖默认 response_format",
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="跳过 health 检查（不推荐）",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    result = generate_image(
        config,
        args.prompt,
        text_verbatim=args.text_verbatim,
        width=args.width,
        height=args.height,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance_scale,
        seed=args.seed,
        response_format=args.response_format,
        skip_health_check=args.skip_health_check,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
