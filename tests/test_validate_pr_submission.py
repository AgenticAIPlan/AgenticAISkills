import os
import tempfile
import unittest
from pathlib import Path

from scripts.validate_pr_submission import (
    parse_template_fields,
    validate_contributor_pr,
)


class ValidatePrSubmissionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
