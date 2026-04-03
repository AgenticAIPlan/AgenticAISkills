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
FEATURE_BRANCH_RE = re.compile(r"^(feat|update)/([a-z]+)/([a-z0-9-]+)$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
PINYIN_RE = re.compile(r"^[a-z]+$")
LOCAL_SKIP_BRANCHES = {"main", "dev"}
ADMIN_GITHUB_LOGINS = {"lemonteeeeaa"}


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


def normalize(value: str) -> str:
    return value.strip().lower()


def is_yes(value: str) -> bool:
    normalized = normalize(value)
    return normalized in {"y", "yes", "true", "1", "是", "已", "已询问", "已确认"} or normalized.startswith("是") or normalized.startswith("已")


def load_pr_context() -> Tuple[str, str, str]:
    body = ""
    head_ref = os.getenv("GITHUB_HEAD_REF", "")
    base_ref = os.getenv("GITHUB_BASE_REF", "")

    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        payload = json.loads(Path(event_path).read_text())
        pull_request = payload.get("pull_request", {})
        body = pull_request.get("body") or ""
        head_ref = pull_request.get("head", {}).get("ref") or head_ref
        base_ref = pull_request.get("base", {}).get("ref") or base_ref

    return body, head_ref, base_ref


def current_github_login() -> str:
    for key in ("GITHUB_ACTOR", "GH_USER", "GITHUB_USER"):
        value = os.getenv(key, "").strip()
        if value:
            return value

    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        payload = json.loads(Path(event_path).read_text())
        for login in (
            payload.get("sender", {}).get("login", ""),
            payload.get("pull_request", {}).get("user", {}).get("login", ""),
        ):
            if login:
                return login

    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def admin_bypass_login() -> Optional[str]:
    login = current_github_login()
    if login in ADMIN_GITHUB_LOGINS:
        return login
    return None


def touches_business_skill(files: List[str]) -> bool:
    return any(
        path.startswith(f"{SKILLS_ROOT}/")
        and path != SKILLS_README
        and not path.startswith(f"{TEMPLATE_DIR}/")
        for path in files
    )


def validate_feature_branch(branch: str, errors: List[str]) -> Tuple[Optional[str], Optional[str]]:
    match = FEATURE_BRANCH_RE.match(branch)
    if not match:
        errors.append(
            "分支名不符合规范。业务同学提交请使用 `feat/<真实姓名拼音>/<skill-slug>` 或 `update/<真实姓名拼音>/<skill-slug>`。"
        )
        return None, None

    return match.group(2), match.group(3)


def validate_changed_skill_files(
    files: List[str], expected_skill_slug: Optional[str], errors: List[str]
) -> Optional[str]:
    if not files:
        errors.append("没有检测到任何改动。")
        return None

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
            "请不要直接修改 `skills/README.md` 或 `skills/_template/`。业务 Skill 提交必须在 `skills/<skill-slug>/` 下新增或更新目录。"
        )

    if not changed_skill_dirs:
        errors.append(
            "没有检测到有效的 Skill 目录改动。请在 `skills/<skill-slug>/` 下新增或更新文件。"
        )
        return None

    if len(changed_skill_dirs) > 1:
        errors.append(
            f"一次业务 PR 只允许提交一个 Skill 目录，当前检测到多个目录：{', '.join(sorted(changed_skill_dirs))}。"
        )
        return None

    skill_dir = next(iter(changed_skill_dirs))

    if not SLUG_RE.match(skill_dir):
        errors.append(f"`skills/{skill_dir}/` 目录名不符合 `kebab-case` 规范。")

    if expected_skill_slug and skill_dir != expected_skill_slug:
        errors.append(
            f"分支中的 skill slug 与目录不一致。当前分支要求 `skills/{expected_skill_slug}/`，实际改动目录为 `skills/{skill_dir}/`。"
        )

    if disallowed_paths:
        errors.append(
            "业务 Skill 提交 PR 只允许修改一个 `skills/<skill-slug>/` 目录。以下路径不符合规范： "
            + ", ".join(disallowed_paths)
        )

    skill_md = Path(SKILLS_ROOT) / skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(
            f"缺少 `{skill_md.as_posix()}`。每个 Skill 目录都必须包含 `SKILL.md`。"
        )

    return skill_dir


def require_fields(fields: Dict[str, str], names: List[str], errors: List[str]) -> None:
    for field in names:
        if not fields.get(field):
            errors.append(f"PR 模板字段 `{field}` 不能为空。")


def validate_contributor_pr(body: str, branch: str, base_ref: str, files: List[str], errors: List[str]) -> None:
    if base_ref != "dev":
        errors.append("业务同学的 Skill PR 必须提交到 `dev`，不能直接提到 `main`。")

    expected_pinyin, expected_skill_slug = validate_feature_branch(branch, errors)
    changed_skill_dir = validate_changed_skill_files(files, expected_skill_slug, errors)

    fields = parse_template_fields(body)
    require_fields(
        fields,
        [
            "PR 类型",
            "目标分支",
            "源分支",
            "业务同学真实姓名",
            "业务同学真实姓名拼音",
            "Skill 名称",
            "Skill 路径",
            "分支名",
            "本次是否由 Agent 辅助提交",
            "Agent 是否已先询问用户真实姓名",
        ],
        errors,
    )

    if fields.get("PR 类型") and "dev" not in fields["PR 类型"].lower():
        errors.append("业务同学 PR 的 `PR 类型` 应明确标注为提交到 `dev`。")

    if fields.get("目标分支") and normalize(fields["目标分支"]) != "dev":
        errors.append("业务同学 PR 的 `目标分支` 必须填写为 `dev`。")

    if fields.get("源分支") and fields["源分支"] != branch:
        errors.append(f"`源分支` 必须与当前分支一致，当前分支是 `{branch}`。")

    if fields.get("分支名") and fields["分支名"] != branch:
        errors.append(f"`分支名` 必须与当前分支一致，当前分支是 `{branch}`。")

    pinyin = fields.get("业务同学真实姓名拼音", "")
    if pinyin and not PINYIN_RE.match(pinyin):
        errors.append("`业务同学真实姓名拼音` 必须是连续小写字母，不允许空格、中文或 GitHub 用户名。")

    if pinyin and expected_pinyin and pinyin != expected_pinyin:
        errors.append(
            f"PR 中填写的姓名拼音 `{pinyin}` 与分支中的姓名拼音 `{expected_pinyin}` 不一致。"
        )

    skill_path = fields.get("Skill 路径", "")
    if changed_skill_dir and skill_path and skill_path.rstrip("/") != f"skills/{changed_skill_dir}":
        errors.append(f"`Skill 路径` 必须填写为 `skills/{changed_skill_dir}`。")

    agent_used = fields.get("本次是否由 Agent 辅助提交", "")
    asked_name = fields.get("Agent 是否已先询问用户真实姓名", "")
    if is_yes(agent_used) and not is_yes(asked_name):
        errors.append("检测到本次由 Agent 辅助提交，但 `Agent 是否已先询问用户真实姓名` 未填写为“是”。")


def validate_release_pr(body: str, branch: str, base_ref: str, errors: List[str]) -> None:
    if base_ref != "main":
        errors.append("发布 PR 必须以 `main` 为目标分支。")

    if branch != "dev":
        errors.append("只允许从 `dev` 发起到 `main` 的发布 PR。")

    fields = parse_template_fields(body)
    require_fields(
        fields,
        [
            "PR 类型",
            "目标分支",
            "源分支",
            "涉及业务同学真实姓名拼音列表",
        ],
        errors,
    )

    if fields.get("PR 类型") and "main" not in fields["PR 类型"].lower():
        errors.append("发布 PR 的 `PR 类型` 应明确标注为从 `dev` 合并到 `main`。")

    if fields.get("目标分支") and normalize(fields["目标分支"]) != "main":
        errors.append("发布 PR 的 `目标分支` 必须填写为 `main`。")

    if fields.get("源分支") and normalize(fields["源分支"]) != "dev":
        errors.append("发布 PR 的 `源分支` 必须填写为 `dev`。")

    pinyin_list = fields.get("涉及业务同学真实姓名拼音列表", "")
    if pinyin_list and not re.fullmatch(r"[a-z, /-]+", pinyin_list):
        errors.append("`涉及业务同学真实姓名拼音列表` 只能包含小写拼音、逗号、空格、斜杠或连字符。")


def run_local(base_ref: str) -> int:
    branch = git("branch", "--show-current")
    files = changed_files(base_ref)

    admin_login = admin_bypass_login()
    if admin_login:
        print(f"检测到管理员账号 `{admin_login}`，跳过校验。")
        return 0

    if branch in LOCAL_SKIP_BRANCHES:
        print(f"当前分支 `{branch}` 跳过本地业务提交校验。")
        return 0

    if not touches_business_skill(files) and not FEATURE_BRANCH_RE.match(branch):
        print("未检测到业务 Skill 提交改动，跳过严格校验。")
        return 0

    errors: List[str] = []
    _, expected_skill_slug = validate_feature_branch(branch, errors)
    validate_changed_skill_files(files, expected_skill_slug, errors)

    if errors:
        print("本地提交校验失败：")
        for error in errors:
            print(f"- {error}")
        print("请先修正后再推送。PR 模板与目标分支校验会在 GitHub PR 检查中继续执行。")
        return 1

    print("本地提交校验通过。")
    return 0


def run_pr() -> int:
    body, branch, base_ref = load_pr_context()

    admin_login = admin_bypass_login()
    if admin_login:
        print(f"检测到管理员账号 `{admin_login}`，跳过校验。")
        return 0

    try:
        git("fetch", "origin", base_ref, "--depth=1")
    except subprocess.CalledProcessError:
        pass

    files = changed_files("origin/{}".format(base_ref))
    errors: List[str] = []

    if base_ref == "dev":
        validate_contributor_pr(body, branch, base_ref, files, errors)
    elif base_ref == "main":
        validate_release_pr(body, branch, base_ref, errors)
    else:
        errors.append("只允许发起指向 `dev` 或 `main` 的 Pull Request。")

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
    local_parser.add_argument("--base-ref", default="origin/dev")

    subparsers.add_parser("pr")

    args = parser.parse_args()

    try:
        if args.mode == "local":
            return run_local(args.base_ref)
        return run_pr()
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
