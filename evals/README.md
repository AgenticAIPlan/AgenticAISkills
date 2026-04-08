# Skill PR AI Eval

本目录用于承载仓库级的 Skill PR AI 评审说明。

## 触发方式

本仓库绝大多数 Skill PR 来自 fork。

GitHub 默认不会把仓库 secrets 暴露给来自 fork 的 `pull_request` workflow，因此不能安全地直接在普通 PR 检查里调用模型 API。

因此当前方案是：

- 静态结构校验继续自动运行
- AI 评审由维护者手动触发 `Skill PR AI Eval`

## 当前评测方法

当前版本会对 PR 中变更的单个 Skill 目录做静态审阅，优先读取：

- `SKILL.md`
- `references/` 下的资料
- 目录内其他可解码的文本类文件，如代码、配置、样例说明等

默认不会执行 Skill 附带脚本，也不会访问外部服务；当前定位仍是 Reviewer 辅助工具。

模型会输出：

- 总分
- 合并建议
- 各维度评分
- 阻塞问题
- 非阻塞优化建议
- 与相邻 Skill 的冲突风险判断

## 配置项

建议在仓库中配置：

- `OPENAI_API_KEY`
- `OPENAI_API_BASE_URL`（可选，用于 OpenAI-compatible 网关）
- `SKILL_EVAL_MODEL`（可选，作为默认评审模型）

## 当前边界

当前版本不会直接阻塞合并。

- PR 评论中的 AI 结论用于辅助审核
- 不替代维护者最终判断
- 如后续效果稳定，再考虑是否增加更强的门槛或更深的自动化校验
