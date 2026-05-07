#!/usr/bin/env python3
"""
获取知乎问题详情及回答，用于深入分析特定 ERNIE-Image 讨论帖
"""

import subprocess
import json
import sys
from pathlib import Path

OPENCLI = str(Path.home() / ".local/bin/opencli")


def get_question_detail(question_id: str, limit: int = 10) -> dict:
    """获取知乎问题详情和回答列表"""
    cmd = [OPENCLI, "zhihu", "question", question_id, "--limit", str(limit), "-f", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[错误] {result.stderr}", file=sys.stderr)
            return {}
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        return {}


def extract_question_id(url: str) -> str:
    """从知乎 URL 中提取问题 ID"""
    import re
    m = re.search(r"question/(\d+)", url)
    return m.group(1) if m else url


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="获取知乎问题详情")
    parser.add_argument("target", help="知乎问题 ID 或 URL")
    parser.add_argument("--limit", type=int, default=10, help="获取回答数量")
    args = parser.parse_args()

    qid = extract_question_id(args.target)
    data = get_question_detail(qid, args.limit)
    print(json.dumps(data, ensure_ascii=False, indent=2))
