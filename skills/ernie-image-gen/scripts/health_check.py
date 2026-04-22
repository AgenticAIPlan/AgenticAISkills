#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from common import check_health, load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="执行 ERNIE Image 服务健康检查")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径")
    args = parser.parse_args()

    config = load_config(args.config)
    payload = check_health(config)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
