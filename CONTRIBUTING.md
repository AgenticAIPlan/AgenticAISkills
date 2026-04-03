# 贡献指南

## 提交前请确认

- Skill 放在 `skills/` 目录下
- Skill 目录名使用 `kebab-case`
- 每个 Skill 目录都包含 `SKILL.md`
- `SKILL.md` 中写清楚使用场景、输入条件、执行步骤和输出要求
- 如 Skill 依赖外部资料，请放入 `references/`
- 如 Skill 依赖图片、样例或附件，请放入 `assets/`

## 推荐提交流程

1. 先同步最新 `dev`，并从 `dev` 拉出功能分支，禁止直接在 `dev` 或 `main` 上开发。
2. 新建或修改 `skills/<skill-slug>/`。
3. 对照 `skills/_template/SKILL.md` 完成内容。
4. 自查语义是否清晰、边界是否明确、输出要求是否可执行。
5. 发起指向 `dev` 的 Pull Request，并按模板填写业务同学真实姓名、真实姓名拼音、Skill 路径和分支信息。
6. 等待助教审核并合入 `dev`。

## Skill 编写建议

- 名称聚焦业务动作或业务场景
- 描述要说明触发条件，而不是泛泛介绍
- 流程步骤尽量具体，减少模糊表达
- 输出要求要可检查，避免“自行发挥”
- 参考资料只保留真正需要的上下文
- 不要把 `README.md`、`CHANGELOG.md` 一类辅助文档塞进单个 Skill 目录
- `references/`、`assets/`、脚本都是可选项，只有在确实能提升复用性时再添加
