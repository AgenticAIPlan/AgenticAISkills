#!/usr/bin/env python3
"""
获取小红书笔记详情及评论，用于深入分析特定 ERNIE-Image 笔记
"""

import subprocess
import json
import sys
from pathlib import Path

OPENCLI = str(Path.home() / ".local/bin/opencli")


def get_note_detail(note_id: str) -> dict:
    """获取小红书笔记正文和互动数据"""
    cmd = [OPENCLI, "xiaohongshu", "note", note_id, "-f", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[错误] {result.stderr}", file=sys.stderr)
            return {}
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        return {}


def get_note_comments(note_id: str, limit: int = 20) -> list:
    """获取笔记评论"""
    cmd = [OPENCLI, "xiaohongshu", "comments", note_id, "--limit", str(limit), "-f", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[错误] {result.stderr}", file=sys.stderr)
            return []
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        return []


def extract_note_id(url: str) -> str:
    """从小红书 URL 中提取笔记 ID"""
    import re
    m = re.search(r"explore/([a-f0-9]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"/([a-f0-9]{24})", url)
    return m.group(1) if m else url


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="获取小红书笔记详情和评论")
    parser.add_argument("target", help="笔记 ID 或 URL")
    parser.add_argument("--comments", action="store_true", help="同时获取评论")
    parser.add_argument("--limit", type=int, default=20, help="评论数量")
    args = parser.parse_args()

    note_id = extract_note_id(args.target)
    detail = get_note_detail(note_id)
    print("=== 笔记详情 ===")
    print(json.dumps(detail, ensure_ascii=False, indent=2))

    if args.comments:
        comments = get_note_comments(note_id, args.limit)
        print("\n=== 评论列表 ===")
        print(json.dumps(comments, ensure_ascii=False, indent=2))
