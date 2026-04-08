import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_pr_submission
from scripts.validate_pr_submission import (
    parse_template_fields,
    run_pr_target,
    skill_file_exists_after_pr,
    validate_contributor_pr,
)


class ValidatePrSubmissionTests(unittest.TestCase):
    def make_fork_pr_payload(self, *, body: str, head_ref: str, base_ref: str = "dev") -> dict:
        return {
            "number": 12,
            "repository": {
                "name": "AgenticAISkills",
                "full_name": "AgenticAIPlan/AgenticAISkills",
                "owner": {"login": "AgenticAIPlan"},
            },
            "pull_request": {
                "number": 12,
                "body": body,
                "head": {
                    "ref": head_ref,
                    "sha": "abc123",
                    "repo": {"full_name": "student/AgenticAISkills"},
                },
                "base": {"ref": base_ref},
            },
        }

    def run_pr_target_with_payload(
        self,
        payload: dict,
        pr_files: list[dict],
        *,
        base_skill_md_exists: bool = False,
        head_skill_md_exists: bool = False,
    ) -> int:
        with tempfile.TemporaryDirectory() as temp_dir:
            event_path = Path(temp_dir) / "event.json"
            event_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            original_cwd = Path.cwd()

            if base_skill_md_exists:
                skill_dir = Path(temp_dir) / "skills" / payload["pull_request"]["head"]["ref"].split("/", 1)[1]
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / "SKILL.md").write_text("# base skill\n", encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "GITHUB_EVENT_PATH": str(event_path),
                    "GITHUB_TOKEN": "test-token",
                },
                clear=False,
            ):
                with patch.object(
                    validate_pr_submission,
                    "list_pr_files",
                    return_value=pr_files,
                ), patch.object(
                    validate_pr_submission,
                    "path_exists_in_repo",
                    return_value=head_skill_md_exists,
                ):
                    os.chdir(temp_dir)
                    try:
                        with patch("sys.stdout", new=io.StringIO()):
                            return run_pr_target()
                    finally:
                        os.chdir(original_cwd)

    def test_parse_template_fields_strips_markdown_code_ticks(self) -> None:
        body = """
- 目标分支: `dev`
- 源分支: `feat/agent-boundary-design`
- Skill 路径: `skills/agent-boundary-design`
"""

        fields = parse_template_fields(body)

        self.assertEqual(fields["目标分支"], "dev")
        self.assertEqual(fields["源分支"], "feat/agent-boundary-design")
        self.assertEqual(fields["Skill 路径"], "skills/agent-boundary-design")

    def test_validate_contributor_pr_accepts_inline_code_template_values(self) -> None:
        body = """
- PR 类型: `业务同学提交到 dev`
- 目标分支: `dev`
- 源分支: `feat/agent-boundary-design`
- Skill 名称: `agent-boundary-design`
- Skill 路径: `skills/agent-boundary-design`
- 业务场景: `用于在业务 Agent 设计阶段明确职责边界`
- 分支名: `feat/agent-boundary-design`
- 本次是否由 Agent 辅助提交: `是`
"""
        errors = []
        original_cwd = Path.cwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            skill_dir = temp_path / "skills" / "agent-boundary-design"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# test\n", encoding="utf-8")
            os.chdir(temp_path)

            try:
                validate_contributor_pr(
                    body=body,
                    branch="feat/agent-boundary-design",
                    base_ref="dev",
                    files=["skills/agent-boundary-design/SKILL.md"],
                    errors=errors,
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(errors, [])

    def test_run_pr_target_accepts_valid_fork_business_skill_pr(self) -> None:
        payload = self.make_fork_pr_payload(
            body="""
- PR 类型: `业务同学提交到 dev`
- 目标分支: `dev`
- 源分支: `feat/credit-review-copilot`
- Skill 名称: `credit-review-copilot`
- Skill 路径: `skills/credit-review-copilot`
- 业务场景: `授信审核辅助`
- 分支名: `feat/credit-review-copilot`
- 本次是否由 Agent 辅助提交: `是`
""",
            head_ref="feat/credit-review-copilot",
        )

        exit_code = self.run_pr_target_with_payload(
            payload,
            [
                {
                    "filename": "skills/credit-review-copilot/SKILL.md",
                    "status": "added",
                }
            ],
        )

        self.assertEqual(exit_code, 0)

    def test_run_pr_target_accepts_existing_skill_without_skill_md_change(self) -> None:
        payload = self.make_fork_pr_payload(
            body="""
- PR 类型: `业务同学提交到 dev`
- 目标分支: `dev`
- 源分支: `update/credit-review-copilot`
- Skill 名称: `credit-review-copilot`
- Skill 路径: `skills/credit-review-copilot`
- 业务场景: `补充授信审核辅助参考资料`
- 分支名: `update/credit-review-copilot`
- 本次是否由 Agent 辅助提交: `否`
""",
            head_ref="update/credit-review-copilot",
        )

        exit_code = self.run_pr_target_with_payload(
            payload,
            [
                {
                    "filename": "skills/credit-review-copilot/references/README.md",
                    "status": "modified",
                }
            ],
            head_skill_md_exists=True,
        )

        self.assertEqual(exit_code, 0)

    def test_run_pr_target_accepts_stale_fork_when_base_already_has_skill_md(self) -> None:
        payload = self.make_fork_pr_payload(
            body="""
- PR 类型: `业务同学提交到 dev`
- 目标分支: `dev`
- 源分支: `update/existing-skill`
- Skill 名称: `existing-skill`
- Skill 路径: `skills/existing-skill`
- 业务场景: `补充已有 Skill 的参考资料`
- 分支名: `update/existing-skill`
- 本次是否由 Agent 辅助提交: `否`
""",
            head_ref="update/existing-skill",
        )

        exit_code = self.run_pr_target_with_payload(
            payload,
            [
                {
                    "filename": "skills/existing-skill/references/README.md",
                    "status": "modified",
                }
            ],
            base_skill_md_exists=True,
            head_skill_md_exists=False,
        )

        self.assertEqual(exit_code, 0)

    def test_run_pr_target_rejects_fork_maintenance_pr(self) -> None:
        payload = self.make_fork_pr_payload(
            body="""
- PR 类型: `仓库维护提交到 dev`
- 目标分支: `dev`
- 源分支: `docs/update-readme`
- 分支名: `docs/update-readme`
""",
            head_ref="docs/update-readme",
        )

        exit_code = self.run_pr_target_with_payload(
            payload,
            [{"filename": "README.md", "status": "modified"}],
        )

        self.assertEqual(exit_code, 1)

    def test_skill_file_exists_after_pr_rejects_removed_skill_md_even_if_base_has_it(self) -> None:
        self.assertFalse(
            skill_file_exists_after_pr(
                "skills/example-skill/SKILL.md",
                [
                    {
                        "filename": "skills/example-skill/SKILL.md",
                        "status": "removed",
                    }
                ],
                base_exists=True,
                head_exists=False,
            )
        )

    def test_run_pr_target_rejects_skill_pr_with_non_skill_files(self) -> None:
        payload = self.make_fork_pr_payload(
            body="""
- PR 类型: `业务同学提交到 dev`
- 目标分支: `dev`
- 源分支: `feat/bad-skill`
- Skill 名称: `bad-skill`
- Skill 路径: `skills/bad-skill`
- 业务场景: `测试非法改动`
- 分支名: `feat/bad-skill`
- 本次是否由 Agent 辅助提交: `否`
""",
            head_ref="feat/bad-skill",
        )

        exit_code = self.run_pr_target_with_payload(
            payload,
            [
                {"filename": "skills/bad-skill/SKILL.md", "status": "added"},
                {"filename": "README.md", "status": "modified"},
            ],
        )

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
