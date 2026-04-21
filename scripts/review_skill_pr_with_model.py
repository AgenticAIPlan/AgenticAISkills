#!/usr/bin/env python3

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple


MAX_FILE_BYTES = 200_000
MAX_FILE_CHARS = 18_000
MAX_TOTAL_CHARS = 90_000
MAX_FILES = 40
MAX_REPO_REFERENCE_CHARS = 12_000
MAX_MODEL_PARSE_ATTEMPTS = 2
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".csv",
    ".html",
    ".css",
    ".xml",
}
DIMENSION_KEYS = [
    "trigger_clarity",
    "input_contract",
    "execution_quality",
    "output_contract",
    "boundary_definition",
    "reference_support",
    "repository_fit",
]
REPO_REFERENCE_PATHS = [
    "skills/_template/SKILL.md",
    "CONTRIBUTING.md",
    "README.md",
]

SYSTEM_PROMPT = """你是一个严谨、务实的业务 Skill 仓库 Reviewer，负责评审提交到 Skill 仓库中的单个 Skill PR。

你的目标不是润色文案，而是判断这个 Skill 是否足够清晰、可执行、可复用、适合被仓库长期收录。

请遵守以下审稿原则：
1. 仅依据提供给你的 Skill 目录文本材料做判断，不要假装你执行过脚本、调用过接口或验证过外部依赖。
2. 如果目录里存在脚本、配置或其他辅助文件，要把它们纳入判断；但你只能基于静态内容评估其可理解性、完整性和风险。
3. 如果材料不足以支撑某项能力，请直接指出，不要脑补。
4. 结论要克制，优先指出真正影响复用性、可维护性、触发准确性的缺陷。
5. 评分标准既要参考仓库内 Skill 模板和贡献规范，也要参考高质量指令设计的一般原则。

仓库对高质量 Skill 的核心期待：
- 适用场景明确，触发条件具体，不泛化。
- 输入要求清楚，前置条件和约束清楚。
- 执行步骤可操作，而不是空泛描述。
- 输出要求可检查、可交付。
- 边界和不适用场景明确，能与相邻 Skill 区分。
- 参考资料和附带文件是真正有帮助的，不是噪音。
- 作为业务 Skill 具有可复用性，适合被他人稳定调用。

你必须只输出一个 JSON 对象，不要输出 Markdown，不要输出解释文字，不要使用代码块。

JSON 结构必须满足：
{
  "summary": "字符串，2-4 句话的中文总结",
  "decision": "approve | needs-work | not-ready",
  "overall_score": 0-100 的整数,
  "dimensions": {
    "trigger_clarity": {"score": 1-5, "reason": "中文"},
    "input_contract": {"score": 1-5, "reason": "中文"},
    "execution_quality": {"score": 1-5, "reason": "中文"},
    "output_contract": {"score": 1-5, "reason": "中文"},
    "boundary_definition": {"score": 1-5, "reason": "中文"},
    "reference_support": {"score": 1-5, "reason": "中文"},
    "repository_fit": {"score": 1-5, "reason": "中文"}
  },
  "blocking_issues": ["中文字符串"],
  "non_blocking_suggestions": ["中文字符串"],
  "routing_assessment": {
    "distinctiveness_score": 1-5,
    "reason": "中文",
    "likely_conflicts": ["中文字符串"]
  }
}

输出要求：
- 所有 reason、summary、issues、suggestions 都用中文。
- 如果没有阻塞问题或建议，数组可为空。
- overall_score 要和各维度判断基本一致。
- approve 表示可以合并；needs-work 表示建议修改后再看；not-ready 表示当前质量明显不够。"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--skill-slug", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-bundle", required=True)
    return parser.parse_args()


def looks_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    sample = data[:1024]
    if not sample:
        return False
    non_text = sum(1 for byte in sample if byte < 9 or (13 < byte < 32))
    return non_text / len(sample) > 0.30


def is_probably_text(path: Path, data: bytes) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    if looks_binary(data):
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def file_sort_key(relative_path: str) -> Tuple[int, str]:
    if relative_path == "SKILL.md":
        return (0, relative_path)
    if relative_path.startswith("references/"):
        return (1, relative_path)
    return (2, relative_path)


def collect_skill_bundle(skill_dir: Path) -> Tuple[List[Dict[str, object]], List[Dict[str, str]], List[str]]:
    included: List[Dict[str, object]] = []
    skipped: List[Dict[str, str]] = []
    notes: List[str] = []
    total_chars = 0

    paths = sorted(
        [path for path in skill_dir.rglob("*") if path.is_file()],
        key=lambda path: file_sort_key(path.relative_to(skill_dir).as_posix()),
    )

    if len(paths) > MAX_FILES:
        notes.append(
            f"目录中文件较多，本次最多纳入前 {MAX_FILES} 个更相关的文本文件进行静态审阅。"
        )

    for index, path in enumerate(paths):
        relative_path = path.relative_to(skill_dir).as_posix()

        if index >= MAX_FILES:
            skipped.append({"path": relative_path, "reason": "exceeds-file-limit"})
            continue

        data = path.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            skipped.append({"path": relative_path, "reason": "file-too-large"})
            continue

        if not is_probably_text(path, data):
            skipped.append({"path": relative_path, "reason": "binary-or-unsupported"})
            continue

        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append({"path": relative_path, "reason": "not-utf8"})
            continue
        original_chars = len(content)
        truncated = False

        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS]
            truncated = True

        remaining = MAX_TOTAL_CHARS - total_chars
        if remaining <= 0:
            skipped.append({"path": relative_path, "reason": "exceeds-total-char-budget"})
            continue

        if len(content) > remaining:
            content = content[:remaining]
            truncated = True

        included.append(
            {
                "path": relative_path,
                "chars_included": len(content),
                "chars_original": original_chars,
                "truncated": truncated,
                "content": content,
            }
        )
        total_chars += len(content)

        if total_chars >= MAX_TOTAL_CHARS:
            notes.append("为控制上下文长度，部分文件内容可能被截断或跳过。")

    notes.append("本次评审只基于目录中的静态文本内容进行判断，未实际执行脚本、命令或外部服务调用。")
    return included, skipped, notes


def load_repo_references(repo_root: Path) -> List[Dict[str, object]]:
    references: List[Dict[str, object]] = []
    remaining = MAX_REPO_REFERENCE_CHARS

    for relative_path in REPO_REFERENCE_PATHS:
        path = repo_root / relative_path
        if not path.exists() or not path.is_file() or remaining <= 0:
            continue

        content = path.read_text(encoding="utf-8")
        truncated = False
        if len(content) > remaining:
            content = content[:remaining]
            truncated = True

        references.append(
            {
                "path": relative_path,
                "content": content,
                "truncated": truncated,
            }
        )
        remaining -= len(content)

    return references


def render_bundle(skill_slug: str, included: List[Dict[str, object]], skipped: List[Dict[str, str]], notes: List[str]) -> str:
    lines: List[str] = [
        f"# Skill Review Bundle: {skill_slug}",
        "",
        "## Included Files",
        "",
    ]

    if included:
        for item in included:
            marker = " (truncated)" if item["truncated"] else ""
            lines.append(
                f"- `{item['path']}`: included {item['chars_included']} / {item['chars_original']} chars{marker}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Skipped Files", ""])
    if skipped:
        for item in skipped:
            lines.append(f"- `{item['path']}`: {item['reason']}")
    else:
        lines.append("- none")

    lines.extend(["", "## Notes", ""])
    for note in notes:
        lines.append(f"- {note}")

    for item in included:
        lines.extend(["", f"## File: {item['path']}", ""])
        lines.append("~~~~text")
        lines.append(str(item["content"]))
        lines.append("~~~~")

    return "\n".join(lines).strip() + "\n"


def build_user_prompt(
    skill_slug: str,
    included: List[Dict[str, object]],
    skipped: List[Dict[str, str]],
    notes: List[str],
    repo_references: List[Dict[str, object]],
) -> str:
    lines: List[str] = [
        f"请评审业务 Skill `{skill_slug}`。",
        "",
        "你会看到该 Skill 目录下本次纳入审阅的文本文件内容，以及被跳过文件的摘要。",
        "请基于这些材料给出结构化 JSON 评审结果。",
        "",
        "补充要求：",
        "- 这是业务同学提交到统一 Skill 仓库的候选 Skill。",
        "- 请特别关注是否适合作为可复用、可维护、可稳定触发的业务 Skill 被收录。",
        "- 如果出现脚本、配置、样例等辅助文件，请评估它们是否提升了 Skill 的可理解性和可落地性。",
        "- 但不要假装你执行过这些文件；只能做静态判断。",
        "- 下面还附带了仓库现有模板和贡献规范，请优先以这些仓库内规则作为评审锚点。",
        "",
        "已纳入审阅文件：",
    ]

    for item in included:
        truncated = "，内容已截断" if item["truncated"] else ""
        lines.append(
            f"- {item['path']}（纳入 {item['chars_included']} / 原始 {item['chars_original']} 字符{truncated}）"
        )

    if skipped:
        lines.extend(["", "被跳过文件："])
        for item in skipped:
            lines.append(f"- {item['path']}（{item['reason']}）")

    if notes:
        lines.extend(["", "评审范围备注："])
        for note in notes:
            lines.append(f"- {note}")

    if repo_references:
        lines.extend(["", "仓库参考规范："])
        for item in repo_references:
            truncated = "（内容已截断）" if item["truncated"] else ""
            lines.extend(
                [
                    "",
                    f"===== 仓库参考开始：{item['path']}{truncated} =====",
                    str(item["content"]),
                    f"===== 仓库参考结束：{item['path']} =====",
                ]
            )

    for item in included:
        lines.extend(
            [
                "",
                f"===== 文件开始：{item['path']} =====",
                str(item["content"]),
                f"===== 文件结束：{item['path']} =====",
            ]
        )

    return "\n".join(lines)


def post_chat_completion(model: str, system_prompt: str, user_prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing required environment variable: OPENAI_API_KEY")

    base_url = os.environ.get("OPENAI_API_BASE_URL", "").strip() or "https://api.openai.com/v1"
    base_url = base_url.rstrip("/")
    url = f"{base_url}/chat/completions"

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model API request failed: HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Model API request failed: {exc}") from exc

    payload = json.loads(body)
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("Model API response contained no choices.")

    message = choices[0].get("message") or {}
    content = message.get("content")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_chunks = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_chunks.append(item.get("text", ""))
        if text_chunks:
            return "".join(text_chunks)

    raise RuntimeError("Model API response did not contain text content.")


def strip_code_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    return value


def extract_json_object(text: str) -> str:
    value = strip_code_fence(text)
    start = value.find("{")
    end = value.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("Model output does not contain a JSON object.")
    return value[start : end + 1]


def validate_review(review: Dict[str, object]) -> Dict[str, object]:
    missing = []
    for key in ["summary", "decision", "overall_score", "dimensions", "blocking_issues", "non_blocking_suggestions", "routing_assessment"]:
        if key not in review:
            missing.append(key)
    if missing:
        raise RuntimeError(f"Model review output is missing required keys: {', '.join(missing)}")

    dimensions = review.get("dimensions")
    if not isinstance(dimensions, dict):
        raise RuntimeError("Model review output has invalid 'dimensions'.")
    for key in DIMENSION_KEYS:
        if key not in dimensions:
            raise RuntimeError(f"Model review output is missing dimension '{key}'.")

    decision = str(review.get("decision"))
    if decision not in {"approve", "needs-work", "not-ready"}:
        raise RuntimeError("Model review output has invalid 'decision'.")

    return review


def parse_model_review_output(model_output: str) -> Dict[str, object]:
    return validate_review(json.loads(extract_json_object(model_output)))


def review_with_retry(model: str, user_prompt: str) -> Dict[str, object]:
    last_error: Exception | None = None
    last_output_preview = ""

    for attempt in range(1, MAX_MODEL_PARSE_ATTEMPTS + 1):
        model_output = post_chat_completion(model, SYSTEM_PROMPT, user_prompt)
        try:
            return parse_model_review_output(model_output)
        except (json.JSONDecodeError, RuntimeError) as exc:
            last_error = exc
            last_output_preview = strip_code_fence(model_output).strip().replace("\n", " ")[:500]
            if attempt == MAX_MODEL_PARSE_ATTEMPTS:
                break
            print(
                f"Model review output was not valid on attempt {attempt}/{MAX_MODEL_PARSE_ATTEMPTS}, retrying once...",
                file=sys.stderr,
            )

    detail = str(last_error) if last_error else "unknown error"
    if last_output_preview:
        detail += f" | last_output_preview: {last_output_preview}"
    raise RuntimeError(
        f"Failed to produce a valid structured review after {MAX_MODEL_PARSE_ATTEMPTS} attempts: {detail}"
    )


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    skill_dir = Path(args.skill_dir)
    if not skill_dir.exists():
        raise SystemExit(f"Skill directory does not exist: {skill_dir}")

    included, skipped, notes = collect_skill_bundle(skill_dir)
    repo_references = load_repo_references(repo_root)
    if not included:
        raise SystemExit("No text-like files were found in the target skill directory.")

    bundle_text = render_bundle(args.skill_slug, included, skipped, notes)
    user_prompt = build_user_prompt(
        args.skill_slug,
        included,
        skipped,
        notes,
        repo_references,
    )
    review = review_with_retry(args.model, user_prompt)

    review["review_scope"] = {
        "included_files": [
            {
                "path": item["path"],
                "chars_included": item["chars_included"],
                "chars_original": item["chars_original"],
                "truncated": item["truncated"],
            }
            for item in included
        ],
        "skipped_files": skipped,
        "notes": notes,
    }

    output_json = Path(args.output_json)
    output_bundle = Path(args.output_bundle)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_bundle.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output_bundle.write_text(bundle_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
