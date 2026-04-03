---
name: review-skill-prs
description: 审核 AgenticAISkills 仓库中新增或修改业务 Skill 的 Pull Request。Use when acting as the course TA or reviewer to scan open PRs targeting `dev`, find PRs that have not yet received a `【Code X Agent 自动评论｜自动扫描】` comment, inspect changes under `skills/<skill-slug>/`, evaluate both business usefulness and skill-creation quality, and leave GitHub comments.
---

# Review Skill PRs

## 执行顺序

1. 运行 `python3 scripts/find_unreviewed_skill_prs.py` 获取待审核 PR。
2. 对每个候选 PR 执行 `gh pr view <number> --json title,body,files,comments,reviews,url,headRefName,baseRefName,author`，再执行 `gh pr diff <number>` 查看具体改动。
3. 按下面的顺序评审：
   - 先看业务是否成立
   - 再看这个 Skill 作为 Skill 是否站得住
   - 最后看仓库规范和提交流程
4. 只聚焦 `skills/<skill-slug>/` 内的变更，并按 [references/review-rubric.md](references/review-rubric.md) 判断质量。
5. 使用 `gh pr comment <number> --body-file <file>` 留言。评论首行必须以 `【Code X Agent 自动评论｜自动扫描】` 开头。
6. 评论后继续处理下一条 PR，直到没有未评论的 Skill PR。

## 核心判断

- 不要把“有一个 `SKILL.md`”误判成“已经是合格 Skill”。
- 不要把行数当质量代理。`SKILL.md` 只有几百行并不天然有问题；问题在于它是否真的沉淀了可复用的业务判断、边界、输入约束、输出结构和失败处理。
- 对“业务价值薄、只是把通用提示词换了个业务标题”的 Skill，评价要更直接。
- 对“结构不花哨，但业务场景、步骤、输出和风险都讲清楚了”的 Skill，不要因为缺少可选目录就机械打回。

## 业务视角

先问这几个问题：

- 这个 Skill 对应的是不是一个真实、可复用的业务任务，而不是一句泛化口号。
- 它有没有说清楚使用者是谁、在什么场景触发、为了解决什么业务动作。
- 输入是不是业务上拿得到、补得齐，而不是默认总会有完整上下文。
- 步骤里有没有业务判断、校验、优先级、例外分支，而不是“分析一下”“整理一下”。
- 输出是不是能直接进入下一步动作，例如汇报、审批、交接、建档、决策，而不是只给一段泛泛总结。
- 是否说明了重要风险、假设、红线或需要人工确认的点。

以下情况要提高严重度：

- 看起来什么业务都能套用
- 只有形式要求，没有业务决策逻辑
- 只强调“更专业、更高效”，但没有明确产物和验收标准
- 明显缺少领域约束、失败处理、或关键风险提醒

## Skill Creator 视角

按 `skill-creator` 的标准审，但不要教条：

- frontmatter 只保留 `name` 和 `description`
- `description` 必须同时说明“做什么”和“什么时候触发”，不能只是标题改写
- `SKILL.md` 主文件只放核心工作流、硬约束和选择规则；长篇细节应下沉到 `references/`
- 如果任务需要稳定复用、容易反复重写、或对正确性敏感，应考虑脚本，而不是全部靠自然语言
- 如果核心价值只是常识性写作建议，没有额外流程知识、资源、约束或脚本，说明它更像提示词，不像 Skill
- 步骤必须可执行，输出必须可检查，失败和边界必须能落地

重点看这句：

一个好 Skill 不是“把用户请求重新说一遍”，而是“把另一个 Agent 原本不知道、但完成任务必须知道的流程知识和约束沉淀进去”。

## 评论策略

- 先给一句结论，再给 1 到 2 个亮点。
- 重点写 `必须修改` 或 `建议优化`，不要堆很多碎建议。
- 业务不成立时，更直接，明确指出“建议先补实业务场景再合入”。
- 如果仓库规范没问题、业务也成立，只是还缺一点触发边界、资源拆分或输出颗粒度，就写“小修后可合入”。
- 不要把 `references/`、`assets/`、脚本、`agents/openai.yaml` 当成机械必选项。

## 失败处理

- 遇到 `gh` 未登录、仓库不可访问、PR 已关闭、或无法读取 diff 时，立即停止并向用户报告。
- 对已带有 `Code X Agent 自动评论` 标记的 PR 默认跳过，除非用户明确要求复查。
