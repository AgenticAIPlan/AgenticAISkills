# 贡献指南

## 提交前请确认

- Skill 放在 `skills/` 目录下
- Skill 目录名使用 `kebab-case`
- 每个 Skill 目录都包含 `SKILL.md`
- `SKILL.md` 中写清楚使用场景、输入条件、执行步骤和输出要求
- 如 Skill 依赖外部资料，请放入 `references/`
- 如 Skill 依赖图片、样例或附件，请放入 `assets/`

## 推荐提交流程

1. 从 `main` 拉出功能分支。
2. 新建或修改 `skills/<skill-slug>/`。
3. 对照 `skills/_template/SKILL.md` 完成内容。
4. 自查语义是否清晰、边界是否明确、输出要求是否可执行。
5. 提交 Pull Request，等待审核。

## Skill 编写建议

- 名称聚焦业务动作或业务场景
- 描述要说明触发条件，而不是泛泛介绍
- 流程步骤尽量具体，减少模糊表达
- 输出要求要可检查，避免“自行发挥”
- 参考资料只保留真正需要的上下文
