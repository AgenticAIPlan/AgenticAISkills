#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
import sys
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


SKILLS_ROOT = "skills"
TEMPLATE_DIR = "skills/_template"
SKILLS_README = "skills/README.md"
FEATURE_BRANCH_RE = re.compile(r"^(feat|update)/([a-z0-9-]+)$")
MAINTENANCE_BRANCH_RE = re.compile(r"^(chore|fix|feat|docs|refactor)/[a-z0-9][a-z0-9/-]*$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
LOCAL_SKIP_BRANCHES = {"main", "dev"}


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


def load_pr_payload() -> Dict[str, Any]:
    raw_event = (os.getenv("GITHUB_EVENT_PATH") or "").strip()
    raw_event_path = Path(raw_event) if raw_event else None

    if raw_event_path and raw_event_path.exists():
        return json.loads(raw_event_path.read_text())

    return {}


def parse_template_fields(body: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        fields[key.strip()] = normalize_template_value(value)
    return fields


def normalize(value: str) -> str:
    return value.strip().lower()


def normalize_template_value(value: str) -> str:
    normalized = value.strip()

    # Accept common Markdown inline-code formatting in PR templates,
    # e.g. `dev` or ``skills/my-skill``.
    while len(normalized) >= 2 and normalized[0] == normalized[-1] == "`":
        normalized = normalized[1:-1].strip()

    return normalized


def load_pr_context(payload: Optional[Dict[str, Any]] = None) -> Tuple[str, str, str]:
    body = ""
    head_ref = ""
    base_ref = ""

    if payload:
        pull_request = payload.get("pull_request", {})
        body = pull_request.get("body") or ""
        head_ref = pull_request.get("head", {}).get("ref") or ""
        base_ref = pull_request.get("base", {}).get("ref") or ""

    if not head_ref:
        head_ref = (os.getenv("GITHUB_HEAD_REF") or "").strip()
    if not base_ref:
        base_ref = (os.getenv("GITHUB_BASE_REF") or "").strip()

    return body, head_ref, base_ref


def github_api_get_json(url: str, token: str) -> Any:
    request = urllib_request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "skills-pr-guard",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urllib_request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed ({exc.code}) for {url}: {body}") from exc


def list_pr_files(owner: str, repo: str, pull_number: int, token: str) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    page = 1

    while True:
        url = (
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"
            f"?per_page=100&page={page}"
        )
        page_items = github_api_get_json(url, token)
        if not isinstance(page_items, list):
            raise RuntimeError("Unexpected GitHub API response while listing pull request files.")

        files.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1

    return files


def list_same_repo_pr_files(payload: Dict[str, Any], token: str) -> List[Dict[str, Any]]:
    repository = payload.get("repository", {})
    pull_request = payload.get("pull_request", {})

    owner = repository.get("owner", {}).get("login") or ""
    repo = repository.get("name") or ""
    pull_number = pull_request.get("number") or payload.get("number")

    if not owner or not repo or not pull_number:
        raise RuntimeError("缺少 Pull Request 仓库上下文，无法读取当前 PR 的变更文件。")

    return list_pr_files(owner, repo, int(pull_number), token)


def is_diff_graph_error(exc: subprocess.CalledProcessError) -> bool:
    details = "\n".join(filter(None, [exc.stderr, exc.stdout])).lower()
    return "no merge base" in details or "bad revision" in details


def path_exists_in_repo(owner: str, repo: str, path: str, ref: str, token: str) -> bool:
    encoded_path = urllib_parse.quote(path, safe="/")
    encoded_ref = urllib_parse.quote(ref, safe="")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}?ref={encoded_ref}"

    request = urllib_request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "skills-pr-guard",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urllib_request.urlopen(request):
            return True
    except urllib_error.HTTPError as exc:
        exc.read()
        if exc.code == 404:
            return False
        raise RuntimeError(f"GitHub API request failed ({exc.code}) for {url}") from exc


def split_repo_full_name(full_name: str) -> Tuple[str, str]:
    if "/" not in full_name:
        raise RuntimeError(f"Invalid repository full name: {full_name}")
    owner, repo = full_name.split("/", 1)
    return owner, repo


def skill_file_exists_after_pr(
    skill_md_path: str,
    pr_files: List[Dict[str, Any]],
    *,
    base_exists: bool,
    head_exists: bool,
) -> bool:
    for item in pr_files:
        filename = item.get("filename")
        previous_filename = item.get("previous_filename")
        status = item.get("status")

        if filename == skill_md_path:
            return status != "removed"

        if previous_filename == skill_md_path:
            return False

    return base_exists or head_exists


def touches_business_skill(files: List[str]) -> bool:
    return any(
        path.startswith(f"{SKILLS_ROOT}/")
        and path != SKILLS_README
        and not path.startswith(f"{TEMPLATE_DIR}/")
        for path in files
    )


def validate_feature_branch(branch: str, errors: List[str]) -> Optional[str]:
    match = FEATURE_BRANCH_RE.match(branch)
    if not match:
        errors.append(
            "分支名不符合规范。业务同学提交请使用 `feat/<skill-slug>` 或 `update/<skill-slug>`。"
        )
        return None

    return match.group(2)


def validate_maintenance_branch(branch: str, errors: List[str]) -> None:
    if not MAINTENANCE_BRANCH_RE.match(branch):
        errors.append(
            "仓库维护分支名不符合规范。请使用 `chore/...`、`fix/...`、`feat/...`、`docs/...` 或 `refactor/...`。"
        )


def validate_changed_skill_files(
    files: List[str],
    expected_skill_slug: Optional[str],
    errors: List[str],
    skill_md_exists: Optional[bool] = None,
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
            f"分支中的 skill slug 与目录不一致。当前分支要求 `skills/{expected_skill_slug}/`，实际改动目录为 `skills/{skill_dir}`。"
        )

    if disallowed_paths:
        errors.append(
            "业务 Skill 提交 PR 只允许修改一个 `skills/<skill-slug>/` 目录。以下路径不符合规范： "
            + ", ".join(disallowed_paths)
        )

    skill_md = Path(SKILLS_ROOT) / skill_dir / "SKILL.md"
    has_skill_md = skill_md_exists if skill_md_exists is not None else skill_md.exists()
    if not has_skill_md:
        errors.append(
            f"缺少 `{skill_md.as_posix()}`。每个 Skill 目录都必须包含 `SKILL.md`。"
        )

    return skill_dir


def require_fields(fields: Dict[str, str], names: List[str], errors: List[str]) -> None:
    for field in names:
        if not fields.get(field):
            errors.append(f"PR 模板字段 `{field}` 不能为空。")


def validate_contributor_pr(
    body: str,
    branch: str,
    base_ref: str,
    files: List[str],
    errors: List[str],
    skill_md_exists: Optional[bool] = None,
) -> None:
    if base_ref != "dev":
        errors.append("业务同学的 Skill PR 必须提交到 `dev`，不能直接提到 `main`。")

    expected_skill_slug = validate_feature_branch(branch, errors)
    changed_skill_dir = validate_changed_skill_files(
        files, expected_skill_slug, errors, skill_md_exists=skill_md_exists
    )

    fields = parse_template_fields(body)
    require_fields(
        fields,
        [
            "PR 类型",
            "目标分支",
            "源分支",
            "Skill 名称",
            "Skill 路径",
            "业务场景",
            "分支名",
            "本次是否由 Agent 辅助提交",
        ],
        errors,
    )

    pr_type = normalize(fields.get("PR 类型", ""))
    if pr_type and "维护" in pr_type:
        errors.append("业务 Skill PR 的 `PR 类型` 不能填写为仓库维护。")
    if pr_type and "dev" not in pr_type:
        errors.append("业务同学 PR 的 `PR 类型` 应明确标注为提交到 `dev`。")

    if fields.get("目标分支") and normalize(fields["目标分支"]) != "dev":
        errors.append("业务同学 PR 的 `目标分支` 必须填写为 `dev`。")

    if fields.get("源分支") and fields["源分支"] != branch:
        errors.append(f"`源分支` 必须与当前分支一致，当前分支是 `{branch}`。")

    if fields.get("分支名") and fields["分支名"] != branch:
        errors.append(f"`分支名` 必须与当前分支一致，当前分支是 `{branch}`。")

    skill_path = fields.get("Skill 路径", "")
    if changed_skill_dir and skill_path and skill_path.rstrip("/") != f"skills/{changed_skill_dir}":
        errors.append(f"`Skill 路径` 必须填写为 `skills/{changed_skill_dir}`。")


def validate_maintenance_pr(
    body: str, branch: str, base_ref: str, files: List[str], errors: List[str]
) -> None:
    if base_ref != "dev":
        errors.append("仓库维护 PR 必须提交到 `dev`。")

    if not files:
        errors.append("没有检测到任何改动。")

    if touches_business_skill(files):
        errors.append("仓库维护 PR 不应混入业务 Skill 目录改动，请拆分提交。")

    validate_maintenance_branch(branch, errors)

    fields = parse_template_fields(body)
    require_fields(fields, ["PR 类型", "目标分支", "源分支", "分支名"], errors)

    pr_type = normalize(fields.get("PR 类型", ""))
    if pr_type and not ("维护" in pr_type or "maintenance" in pr_type):
        errors.append("仓库维护 PR 的 `PR 类型` 应明确标注为仓库维护提交到 `dev`。")

    if fields.get("目标分支") and normalize(fields["目标分支"]) != "dev":
        errors.append("仓库维护 PR 的 `目标分支` 必须填写为 `dev`。")

    if fields.get("源分支") and fields["源分支"] != branch:
        errors.append(f"`源分支` 必须与当前分支一致，当前分支是 `{branch}`。")

    if fields.get("分支名") and fields["分支名"] != branch:
        errors.append(f"`分支名` 必须与当前分支一致，当前分支是 `{branch}`。")


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
            "涉及 Skill 列表",
        ],
        errors,
    )

    if fields.get("PR 类型") and "main" not in fields["PR 类型"].lower():
        errors.append("发布 PR 的 `PR 类型` 应明确标注为从 `dev` 合并到 `main`。")

    if fields.get("目标分支") and normalize(fields["目标分支"]) != "main":
        errors.append("发布 PR 的 `目标分支` 必须填写为 `main`。")

    if fields.get("源分支") and normalize(fields["源分支"]) != "dev":
        errors.append("发布 PR 的 `源分支` 必须填写为 `dev`。")

    skill_list = fields.get("涉及 Skill 列表", "")
    if skill_list and not re.fullmatch(r"[a-z0-9, /-]+", skill_list):
        errors.append("`涉及 Skill 列表` 只能包含 skill slug、数字、逗号、空格、斜杠或连字符。")


def run_local(base_ref: str) -> int:
    branch = git("branch", "--show-current")
    files = changed_files(base_ref)

    if branch in LOCAL_SKIP_BRANCHES:
        print(f"当前分支 `{branch}` 跳过本地提交校验。")
        return 0

    errors: List[str] = []

    if touches_business_skill(files):
        expected_skill_slug = validate_feature_branch(branch, errors)
        validate_changed_skill_files(files, expected_skill_slug, errors)
    else:
        validate_maintenance_branch(branch, errors)

    if errors:
        print("本地提交校验失败：")
        for error in errors:
            print(f"- {error}")
        print("请先修正后再推送。PR 模板与目标分支校验会在 GitHub PR 检查中继续执行。")
        return 1

    print("本地提交校验通过。")
    return 0


def run_pr() -> int:
    payload = load_pr_payload()
    body, branch, base_ref = load_pr_context(payload)

    try:
        git("fetch", "origin", base_ref, "--depth=1")
    except subprocess.CalledProcessError:
        pass

    try:
        files = changed_files(f"origin/{base_ref}")
    except subprocess.CalledProcessError as exc:
        if not is_diff_graph_error(exc):
            raise

        token = (os.getenv("GITHUB_TOKEN") or "").strip()
        if not token:
            print("PR 校验失败：")
            print("- Git diff 无法确定 PR 改动，且缺少 `GITHUB_TOKEN` 回退读取当前 PR 文件列表。")
            return 1

        try:
            pr_files = list_same_repo_pr_files(payload, token)
        except RuntimeError as api_exc:
            print("PR 校验失败：")
            print(f"- Git diff 无法确定 PR 改动，且回退读取当前 PR 文件列表失败：{api_exc}")
            return 1

        files = [item.get("filename", "") for item in pr_files if item.get("filename")]

    errors: List[str] = []

    if base_ref == "dev":
        if touches_business_skill(files):
            validate_contributor_pr(body, branch, base_ref, files, errors)
        else:
            validate_maintenance_pr(body, branch, base_ref, files, errors)
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


def run_pr_target() -> int:
    payload = load_pr_payload()
    body, branch, base_ref = load_pr_context(payload)
    pull_request = payload.get("pull_request", {})
    repository = payload.get("repository", {})
    errors: List[str] = []
    head_repo = pull_request.get("head", {}).get("repo") or {}

    owner = repository.get("owner", {}).get("login") or ""
    repo = repository.get("name") or ""
    repo_full_name = repository.get("full_name") or ""
    pull_number = pull_request.get("number") or payload.get("number")
    head_repo_full_name = head_repo.get("full_name") or ""
    head_sha = pull_request.get("head", {}).get("sha") or ""
    token = (os.getenv("GITHUB_TOKEN") or "").strip()

    if not owner or not repo or not repo_full_name or not pull_number:
        errors.append("缺少 Pull Request 仓库上下文，无法执行 Fork PR 校验。")

    if not head_repo_full_name or not head_sha:
        errors.append("缺少 Fork PR 的 head 仓库或提交信息，无法执行校验。")

    if not token:
        errors.append("缺少 `GITHUB_TOKEN`，无法通过 GitHub API 读取 Fork PR 变更。")

    if errors:
        print("PR 校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1

    is_fork = head_repo_full_name != repo_full_name
    if not is_fork:
        print("PR 校验失败：")
        print("- `pr-target` 模式只应用于来自 Fork 的业务 Skill PR。")
        return 1

    try:
        pr_files = list_pr_files(owner, repo, int(pull_number), token)
    except RuntimeError as exc:
        print("PR 校验失败：")
        print(f"- {exc}")
        return 1

    files = [item.get("filename", "") for item in pr_files if item.get("filename")]

    if base_ref != "dev":
        errors.append("来自 Fork 的 PR 只支持业务 Skill 提交到 `dev`。")

    if not touches_business_skill(files):
        errors.append(
            "来自 Fork 的 PR 仅支持业务 Skill 提交；仓库维护或发布 PR 请在主仓库分支中发起。"
        )

    skill_md_exists: Optional[bool] = None
    if not errors:
        preflight_errors: List[str] = []
        expected_skill_slug = validate_feature_branch(branch, preflight_errors)
        changed_skill_dir = validate_changed_skill_files(
            files,
            expected_skill_slug,
            preflight_errors,
            skill_md_exists=True,
        )
        if changed_skill_dir:
            skill_md_path = f"{SKILLS_ROOT}/{changed_skill_dir}/SKILL.md"
            base_skill_md_exists = Path(skill_md_path).exists()
            head_skill_md_exists = False

            try:
                head_owner, head_repo = split_repo_full_name(head_repo_full_name)
                head_skill_md_exists = path_exists_in_repo(
                    head_owner,
                    head_repo,
                    skill_md_path,
                    head_sha,
                    token,
                )
            except RuntimeError as exc:
                errors.append(str(exc))

            if not errors:
                skill_md_exists = skill_file_exists_after_pr(
                    skill_md_path,
                    pr_files,
                    base_exists=base_skill_md_exists,
                    head_exists=head_skill_md_exists,
                )

    if not errors:
        validate_contributor_pr(
            body,
            branch,
            base_ref,
            files,
            errors,
            skill_md_exists=skill_md_exists,
        )

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
    subparsers.add_parser("pr-target")

    args = parser.parse_args()

    try:
        if args.mode == "local":
            return run_local(args.base_ref)
        if args.mode == "pr-target":
            return run_pr_target()
        return run_pr()
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
