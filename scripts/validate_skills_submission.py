#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


SKILLS_ROOT = "skills"
TEMPLATE_DIR = "skills/_template"
SKILLS_README = "skills/README.md"
BRANCH_RE = re.compile(r"^(feat|update)/([a-z]+)/([a-z0-9-]+)$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
PINYIN_RE = re.compile(r"^[a-z]+$")


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def changed_files(base_ref: str) -> List[str]:
    diff = git("diff", "--name-only", f"{base_ref}...HEAD")
    return [line for line in diff.splitlines() if line.strip()]


def parse_template_fields(body: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def is_yes(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"y", "yes", "true", "1", "是", "已", "已询问", "已确认"} or normalized.startswith("是") or normalized.startswith("已")


def load_pr_context() -> Tuple[str, str]:
    body = ""
    head_ref = os.getenv("GITHUB_HEAD_REF", "")

    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        payload = json.loads(Path(event_path).read_text())
        pull_request = payload.get("pull_request", {})
        body = pull_request.get("body") or ""
        head_ref = pull_request.get("head", {}).get("ref") or head_ref

    return body, head_ref


def is_skill_submission(files: List[str], branch: str) -> bool:
    if BRANCH_RE.match(branch):
        return True

    return any(
        path.startswith(f"{SKILLS_ROOT}/")
        and path != SKILLS_README
        and not path.startswith(f"{TEMPLATE_DIR}/")
        for path in files
    )


def validate_branch(branch: str, errors: List[str]) -> Tuple[Optional[str], Optional[str]]:
    match = BRANCH_RE.match(branch)
    if not match:
        errors.append(
            "分支名不符合规范。请使用 `feat/<真实姓名拼音>/<skill-slug>` 或 `update/<真实姓名拼音>/<skill-slug>`。"
        )
        return None, None

    pinyin = match.group(2)
    skill_slug = match.group(3)
    return pinyin, skill_slug


def validate_changed_files(
    files: List[str], expected_skill_slug: Optional[str], errors: List[str]
) -> None:
    if not files:
        errors.append("没有检测到任何改动。")
        return

    changed_skill_dirs: Set[str] = set()
    disallowed_paths: List[str] = []
    guidance_paths: List[str] = []

    for path in files:
        if path == SKILLS_README or path.startswith(f"{TEMPLATE_DIR}/"):
            guidance_paths.append(path)
            continue

        if path.startswith(f"{SKILLS_ROOT}/"):
            parts = path.split("/")
            if len(parts) < 3:
                disallowed_paths.append(path)
                continue
            changed_skill_dirs.add(parts[1])
            continue

        disallowed_paths.append(path)

    if guidance_paths:
        errors.append(
            "请不要直接修改 `skills/README.md` 或 `skills/_template/`。提交业务 Skill 时，应在 `skills/<skill-slug>/` 下新增或更新自己的 Skill 目录。"
        )

    if not changed_skill_dirs:
        errors.append(
            "没有检测到有效的 Skill 目录改动。请在 `skills/<skill-slug>/` 下新增或更新文件。"
        )
        return

    if len(changed_skill_dirs) > 1:
        errors.append(
            f"一次 PR 只允许提交一个 Skill 目录，当前检测到多个目录：{', '.join(sorted(changed_skill_dirs))}。"
        )
        return

    skill_dir = next(iter(changed_skill_dirs))

    if not SLUG_RE.match(skill_dir):
        errors.append(
            f"`skills/{skill_dir}/` 目录名不符合 `kebab-case` 规范。"
        )

    if expected_skill_slug and skill_dir != expected_skill_slug:
        errors.append(
            f"分支中的 skill slug 与目录不一致。当前分支要求 `skills/{expected_skill_slug}/`，实际改动目录为 `skills/{skill_dir}/`。"
        )

    if disallowed_paths:
        errors.append(
            "Skill 提交 PR 只允许修改一个 `skills/<skill-slug>/` 目录。以下路径不符合规范："
            + " "
            + ", ".join(disallowed_paths)
        )

    skill_md = Path(SKILLS_ROOT) / skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(
            f"缺少 `{skill_md.as_posix()}`。每个 Skill 目录都必须包含 `SKILL.md`。"
        )


def validate_pr_body(
    body: str, branch: str, expected_pinyin: Optional[str], errors: List[str]
) -> None:
    fields = parse_template_fields(body)
    required = [
        "业务同学真实姓名",
        "业务同学真实姓名拼音",
        "分支名",
        "本次是否由 Agent 辅助提交",
        "Agent 是否已先询问用户真实姓名",
    ]

    for field in required:
        if not fields.get(field):
            errors.append(f"PR 模板字段 `{field}` 不能为空。")

    pinyin = fields.get("业务同学真实姓名拼音", "")
    if pinyin and not PINYIN_RE.match(pinyin):
        errors.append("`业务同学真实姓名拼音` 必须是连续小写字母，不允许空格、中文或 GitHub 用户名。")

    if pinyin and expected_pinyin and pinyin != expected_pinyin:
        errors.append(
            f"PR 中填写的姓名拼音 `{pinyin}` 与分支中的姓名拼音 `{expected_pinyin}` 不一致。"
        )

    branch_name = fields.get("分支名", "")
    if branch_name and branch_name != branch:
        errors.append(
            f"PR 模板中的 `分支名` 与当前分支不一致。当前分支是 `{branch}`。"
        )

    agent_used = fields.get("本次是否由 Agent 辅助提交", "")
    asked_name = fields.get("Agent 是否已先询问用户真实姓名", "")
    if is_yes(agent_used) and not is_yes(asked_name):
        errors.append("检测到本次由 Agent 辅助提交，但 `Agent 是否已先询问用户真实姓名` 未填写为“是”。")


def run_local(base_ref: str) -> int:
    branch = git("branch", "--show-current")
    files = changed_files(base_ref)

    if not is_skill_submission(files, branch):
        print("未检测到业务 Skill 提交改动，跳过严格校验。")
        return 0

    errors: List[str] = []
    expected_pinyin, expected_skill_slug = validate_branch(branch, errors)
    validate_changed_files(files, expected_skill_slug, errors)

    if errors:
        print("本地提交校验失败：")
        for error in errors:
            print(f"- {error}")
        print("请先修正后再推送。PR 模板中的真实姓名拼音校验会在 GitHub PR 检查中继续执行。")
        return 1

    print("本地提交校验通过。")
    return 0


def run_pr(base_ref: str) -> int:
    body, branch = load_pr_context()
    base = f"origin/{base_ref}"
    files = changed_files(base)

    if not is_skill_submission(files, branch):
        print("未检测到业务 Skill 提交改动，跳过严格校验。")
        return 0

    errors: List[str] = []
    expected_pinyin, expected_skill_slug = validate_branch(branch, errors)
    validate_changed_files(files, expected_skill_slug, errors)
    validate_pr_body(body, branch, expected_pinyin, errors)

    if errors:
        print("PR 校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PR 校验通过。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)

    local_parser = subparsers.add_parser("local")
    local_parser.add_argument("--base-ref", default="origin/main")

    pr_parser = subparsers.add_parser("pr")
    pr_parser.add_argument("--base-ref", default=os.getenv("GITHUB_BASE_REF", "main"))

    args = parser.parse_args()

    try:
        if args.mode == "local":
            return run_local(args.base_ref)
        return run_pr(args.base_ref)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
