#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from common import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="校验 ERNIE Image skill YAML 配置")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径")
    args = parser.parse_args()

    config = load_config(args.config)
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
