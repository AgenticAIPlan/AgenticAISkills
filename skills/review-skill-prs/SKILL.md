---
name: review-skill-prs
description: 审核 AgenticAISkills 仓库中新增或修改 Skill 的 Pull Request。Use when acting as the course TA or reviewer to scan open PRs targeting `dev`, find PRs that have not yet received a `【Code X Agent 自动评论｜自动扫描】` comment, inspect changes under `skills/<skill-slug>/`, judge repository compliance and skill quality with a slightly lenient but still high-standard rubric, and leave a GitHub comment.
---

# Review Skill PRs

## 执行流程

1. 运行 `python3 scripts/find_unreviewed_skill_prs.py` 获取待审核 PR。
2. 对每个候选 PR 执行 `gh pr view <number> --json title,body,files,comments,reviews,url,headRefName,baseRefName,author`，再执行 `gh pr diff <number>` 查看具体改动。
3. 只聚焦 `skills/<skill-slug>/` 内的变更，同时核对仓库级规范：
   - 目标分支应为 `dev`
   - 分支名应符合 `feat/<真实姓名拼音>/<skill-slug>` 或 `update/<真实姓名拼音>/<skill-slug>`
   - 业务同学 PR 应只改一个 Skill 目录
   - 不应直接修改 `skills/_template/` 或 `skills/README.md`
4. 按 [references/review-rubric.md](references/review-rubric.md) 判断质量。
5. 使用 `gh pr comment <number> --body-file <file>` 留言。评论首行必须以 `【Code X Agent 自动评论｜自动扫描】` 开头。
6. 评论后继续处理下一条 PR，直到没有未评论的 Skill PR。

## 审核原则

- 保持“略宽松，但整体质量要求高”。
- 仅在缺少必需结构、工作流不可执行、触发条件不清晰、明显违反仓库规则、或存在误导性指令时给出“必须修改”。
- 不要把可选项当成硬性要求，例如 `references/`、`assets/`、脚本、`agents/openai.yaml` 都不应被机械地要求必须出现。
- 优先指出 1 到 3 个最影响可用性的点，不要把评论写成长清单。
- 先认可优点，再给修改建议；如果整体可用，明确写出“修小问题后可合入”或同等结论。

## 失败处理

- 遇到 `gh` 未登录、仓库不可访问、PR 已关闭、或无法读取 diff 时，立即停止并向用户报告。
- 对已带有 `Code X Agent 自动评论` 标记的 PR 默认跳过，除非用户明确要求复查。
