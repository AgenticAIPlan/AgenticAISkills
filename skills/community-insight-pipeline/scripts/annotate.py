#!/usr/bin/env python3
"""
AI 标注辅助脚本 - 独立可运行版本

用法：
  python3 annotate.py --batch [--limit 40] [--platform reddit]
  python3 annotate.py --save annotations.json
  python3 annotate.py --stats

数据库路径通过环境变量 DISCUSSION_DB_PATH 指定，默认 discussions.db
（需与 fetch_batch.py 使用同一数据库）
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.getenv("DISCUSSION_DB_PATH", "discussions.db")


def get_conn() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        print(f"Error: database not found: {DB_PATH}")
        print("Run fetch_batch.py first to create the database.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def cmd_batch(limit: int, platform: str):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT d.platform_id, d.content_type, d.title, d.content,
               d.post_title, d.parent_content, d.image_urls,
               d.depth, d.search_keywords
        FROM discussions d
        LEFT JOIN annotations a ON d.platform_id = a.platform_id
        WHERE a.platform_id IS NULL
          AND d.platform = ?
        ORDER BY d.fetched_at ASC
        LIMIT ?
        """,
        (platform, limit),
    ).fetchall()
    conn.close()

    if not rows:
        print(json.dumps({"status": "done", "message": "All rows annotated", "rows": []}))
        return

    output = {
        "status": "pending",
        "count": len(rows),
        "rows": [dict(r) for r in rows],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_save(json_file: str):
    path = Path(json_file)
    if not path.exists():
        print(f"Error: file not found: {json_file}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    annotations = data if isinstance(data, list) else data.get("annotations", [])
    model = data.get("model", "unknown") if isinstance(data, dict) else "unknown"

    if not annotations:
        print("Error: no annotations found in JSON", file=sys.stderr)
        sys.exit(1)

    conn = get_conn()
    now = datetime.utcnow().isoformat()
    for ann in annotations:
        conn.execute(
            """
            INSERT OR REPLACE INTO annotations
              (platform_id, is_relevant, summary, advantages, disadvantages,
               tendency, model, annotated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ann["platform_id"],
                1 if ann.get("is_relevant") else 0,
                ann.get("summary", ""),
                ann.get("advantages", ""),
                ann.get("disadvantages", ""),
                ann.get("tendency", ""),
                model,
                now,
            ),
        )
    conn.commit()
    conn.close()
    print(f"Saved {len(annotations)} annotations")


def cmd_stats():
    conn = get_conn()
    total      = conn.execute("SELECT COUNT(*) FROM discussions").fetchone()[0]
    annotated  = conn.execute("SELECT COUNT(*) FROM annotations").fetchone()[0]
    relevant   = conn.execute("SELECT COUNT(*) FROM annotations WHERE is_relevant=1").fetchone()[0]
    irrelevant = conn.execute("SELECT COUNT(*) FROM annotations WHERE is_relevant=0").fetchone()[0]
    conn.close()

    pct = f"{annotated / total * 100:.1f}%" if total else "0%"
    print(f"Progress: {annotated}/{total} ({pct})")
    print(f"  Relevant: {relevant}  Irrelevant: {irrelevant}  Pending: {total - annotated}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI annotation helper - community-insight-pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--batch",  action="store_true", help="Get unannotated batch (JSON output)")
    group.add_argument("--save",   metavar="FILE",      help="Save annotations from JSON file")
    group.add_argument("--stats",  action="store_true", help="Show annotation progress")
    parser.add_argument("--limit",    type=int, default=40,      help="Batch size (default: 40)")
    parser.add_argument("--platform", type=str, default="reddit", help="Platform filter (default: reddit)")
    args = parser.parse_args()

    if args.batch:
        cmd_batch(args.limit, args.platform)
    elif args.save:
        cmd_save(args.save)
    elif args.stats:
        cmd_stats()
