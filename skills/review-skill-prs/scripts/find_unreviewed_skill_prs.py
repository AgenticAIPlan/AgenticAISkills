#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any, Dict, List


DEFAULT_BASE = "dev"
DEFAULT_LIMIT = 50
DEFAULT_MARKER = "Code X Agent 自动评论"
SKILLS_ROOT = "skills/"
SKILLS_README = "skills/README.md"
TEMPLATE_ROOT = "skills/_template/"


def run_gh(args: List[str], repo: str | None = None) -> str:
    command = ["gh"]
    if repo:
        command.extend(["--repo", repo])
    command.extend(args)

    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "gh command failed"
        raise RuntimeError(message)
    return completed.stdout


def ensure_gh(repo: str | None) -> None:
    if not shutil.which("gh"):
        raise RuntimeError("未找到 gh CLI，请先安装 GitHub CLI。")
    run_gh(["auth", "status"], repo=repo)


def extract_skill_paths(files: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    skill_dirs: List[str] = []
    guidance_paths: List[str] = []
    other_paths: List[str] = []

    for file_info in files:
        path = file_info.get("path", "")
        if path == SKILLS_README or path.startswith(TEMPLATE_ROOT):
            guidance_paths.append(path)
            continue

        if path.startswith(SKILLS_ROOT):
            parts = path.split("/")
            if len(parts) >= 3:
                skill_dirs.append(parts[1])
            else:
                other_paths.append(path)
            continue

        other_paths.append(path)

    return {
        "skill_dirs": sorted(set(skill_dirs)),
        "guidance_paths": sorted(set(guidance_paths)),
        "other_paths": sorted(set(other_paths)),
    }


def has_marker(items: List[Dict[str, Any]], marker: str) -> bool:
    for item in items:
        body = item.get("body") or ""
        if marker in body:
            return True
    return False


def load_open_prs(base: str, limit: int, repo: str | None) -> List[Dict[str, Any]]:
    raw = run_gh(
        [
            "pr",
            "list",
            "--state",
            "open",
            "--base",
            base,
            "--limit",
            str(limit),
            "--json",
            "number,title,url,headRefName,baseRefName,author",
        ],
        repo=repo,
    )
    return json.loads(raw)


def load_pr_details(number: int, repo: str | None) -> Dict[str, Any]:
    raw = run_gh(
        [
            "pr",
            "view",
            str(number),
            "--json",
            "number,title,url,headRefName,baseRefName,author,comments,reviews,files",
        ],
        repo=repo,
    )
    return json.loads(raw)


def collect_candidates(
    base: str,
    limit: int,
    marker: str,
    include_reviewed: bool,
    repo: str | None,
    single_pr: int | None,
) -> List[Dict[str, Any]]:
    source_prs = (
        [load_pr_details(single_pr, repo=repo)]
        if single_pr is not None
        else [load_pr_details(pr["number"], repo=repo) for pr in load_open_prs(base, limit, repo=repo)]
    )

    candidates: List[Dict[str, Any]] = []
    for pr in source_prs:
        path_info = extract_skill_paths(pr.get("files", []))
        is_skill_pr = bool(path_info["skill_dirs"] or path_info["guidance_paths"])
        already_reviewed = has_marker(pr.get("comments", []), marker) or has_marker(pr.get("reviews", []), marker)

        candidate = {
            "number": pr["number"],
            "title": pr["title"],
            "url": pr["url"],
            "author": (pr.get("author") or {}).get("login", ""),
            "head_ref": pr.get("headRefName", ""),
            "base_ref": pr.get("baseRefName", ""),
            "skill_dirs": path_info["skill_dirs"],
            "guidance_paths": path_info["guidance_paths"],
            "other_paths": path_info["other_paths"],
            "already_reviewed": already_reviewed,
            "is_skill_pr": is_skill_pr,
        }

        if not is_skill_pr:
            continue
        if already_reviewed and not include_reviewed:
            continue
        candidates.append(candidate)

    return candidates


def print_text(candidates: List[Dict[str, Any]], include_reviewed: bool) -> None:
    pending = sum(1 for item in candidates if not item["already_reviewed"])
    print(f"skill PRs: {len(candidates)}")
    print(f"pending review: {pending}")
    if include_reviewed:
        reviewed = sum(1 for item in candidates if item["already_reviewed"])
        print(f"already reviewed: {reviewed}")

    for item in candidates:
        status = "reviewed" if item["already_reviewed"] else "pending"
        skill_dirs = ", ".join(item["skill_dirs"]) or "(no concrete skill dir)"
        print(f"- #{item['number']} [{status}] {item['title']}")
        print(f"  url: {item['url']}")
        print(f"  branch: {item['head_ref']} -> {item['base_ref']}")
        print(f"  author: {item['author']}")
        print(f"  skill dirs: {skill_dirs}")
        if item["guidance_paths"]:
            print(f"  touched guidance paths: {', '.join(item['guidance_paths'])}")
        if item["other_paths"]:
            print(f"  touched non-skill paths: {', '.join(item['other_paths'])}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List open skill PRs that have not yet received the Code X Agent auto-review comment."
    )
    parser.add_argument("--base", default=DEFAULT_BASE, help="Base branch to scan. Default: dev")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Maximum number of open PRs to scan.")
    parser.add_argument("--marker", default=DEFAULT_MARKER, help="Comment marker used to detect prior auto reviews.")
    parser.add_argument("--repo", help="Optional GitHub repo in OWNER/REPO form.")
    parser.add_argument("--pr", type=int, help="Inspect a single PR instead of scanning the open list.")
    parser.add_argument(
        "--include-reviewed",
        action="store_true",
        help="Include PRs that already contain the marker comment.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        ensure_gh(args.repo)
        candidates = collect_candidates(
            base=args.base,
            limit=args.limit,
            marker=args.marker,
            include_reviewed=args.include_reviewed,
            repo=args.repo,
            single_pr=args.pr,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(candidates, ensure_ascii=False, indent=2))
    else:
        print_text(candidates, include_reviewed=args.include_reviewed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
