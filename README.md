# AgenticAISkills

`AgenticAISkills` 是本次培养计划统一的业务 Skills 仓库，用于集中沉淀和维护所有同学提交的业务型 Agent Skills。

本仓库参考 [obra/superpowers](https://github.com/obra/superpowers) 的组织方式，保留 Agent 侧入口目录和统一的 `skills/` 技能目录，但内容定位切换为 BMO 培养计划的业务 Skills 资产库。

## 仓库定位

- 统一收集本次培养计划中产出的业务 Skills
- 沉淀可复用的业务场景提示词与执行规范
- 支持 Codex、Claude 等 Agent 工具按统一结构接入
- 通过 Pull Request 管理新增、修改和迭代

## 目录结构

```text
.
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── .claude/
│   ├── INSTALL.md
│   └── README.md
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .codex/
│   └── INSTALL.md
├── .codex-plugin/
│   └── plugin.json
├── .opencode/
│   ├── INSTALL.md
│   └── plugins/
│       └── agentic-ai-skills.js
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md
├── skills/
│   ├── README.md
│   └── _template/
│       ├── SKILL.md
│       └── references/
│           └── README.md
├── CONTRIBUTING.md
└── .gitignore
```

## Skills 目录规范

所有业务 Skill 都必须放在 `skills/` 目录下，按如下结构组织：

```text
skills/<skill-slug>/
├── SKILL.md
├── references/
└── assets/
```

要求如下：

- `skill-slug` 使用 `kebab-case`
- 一个目录只放一个 Skill
- `SKILL.md` 为必需文件
- `references/` 和 `assets/` 为可选目录
- 命名应优先体现业务场景，而不是个人名称

示例：

```text
skills/credit-review-copilot/
skills/customer-service-handoff/
skills/marketing-content-auditor/
```

## 提交流程

本仓库当前有三类提交流程：

- 业务同学提交：`feature branch -> dev`
- 仓库维护者提交：`maintenance branch -> dev`
- 助教发布提交：`dev -> main`

业务同学提交流程：

1. Fork 或拉取仓库最新代码。
2. 先同步最新 `dev`，必须基于 `dev` 单独拉出自己的工作分支，禁止直接在 `dev` 或 `main` 上开发。
3. 在 `skills/` 下新增或更新对应 Skill 目录。
4. 按模板补齐 `SKILL.md` 和必要参考资料。
5. 发起指向 `dev` 的 Pull Request。
6. 在 PR 中明确填写 `Skill 名称`、`Skill 路径` 和业务场景摘要。
7. 等待助教审核并合入 `dev`。

助教发布流程：

1. 助教在 `dev` 完成审核与汇总。
2. 助教发起 `dev -> main` 的 Pull Request。
3. 完成最终审核后，将 `dev` 合入 `main`。

仓库维护者提交流程：

1. 先同步最新 `dev`，并基于 `dev` 拉出独立维护分支。
2. 在 `.github/`、`scripts/`、文档或其他仓库级目录中完成维护性修改。
3. 发起指向 `dev` 的仓库维护 Pull Request。

业务同学推荐分支命名：

- `feat/<skill-slug>`
- `update/<skill-slug>`

示例：

- `feat/credit-review-copilot`
- `update/customer-service-handoff`

## Agent 提交规则

以下规则是写给 Agent 的：

- Agent 为业务同学创建分支时，必须从 `dev` 拉分支，而不是从 `main` 拉分支
- Agent 为业务同学提 PR 时，目标分支必须是 `dev`
- Agent 提 PR 时，必须在 PR 模板中填写 `Skill 名称`、`Skill 路径` 和业务场景摘要
- 公开仓库中不得在分支名、PR 描述或 Skill 内容里提交任何个人身份信息
- 只有助教或仓库维护者才应发起 `dev -> main` 的发布 PR

## 自动校验

本仓库提供两层校验：

- 本地 `git hook`：在推送前检查分支命名和 Skill 目录结构
- GitHub Action：在 PR 上区分并校验业务 Skill PR、仓库维护 PR 和发布 PR

本地安装命令：

```bash
bash scripts/install-hooks.sh
```

自动校验会重点检查：

- 业务同学 PR 是否提交到 `dev`
- 仓库维护 PR 是否提交到 `dev`
- `main` 的 PR 是否来自 `dev`
- 是否从独立分支发起变更
- 分支名是否符合 `feat/<skill-slug>` 或 `update/<skill-slug>`
- PR 中是否填写 `Skill 名称`、`Skill 路径` 和业务场景摘要
- Skill 改动是否真正落在 `skills/<skill-slug>/` 下
- 是否错误修改了 `skills/_template/` 或 `skills/README.md`
- 仓库维护 PR 是否混入业务 Skill 目录改动
- 是否在公开仓库中提交了个人身份信息

对于业务 Skill PR，维护者还可以手动触发 `Skill PR AI Eval`，生成一条 AI 辅助审阅评论。

如果不符合规范，push 前的本地 hook 会直接报错，PR 上的 GitHub Action 也会失败并阻止合入。

## 主干规则

- `dev` 是业务同学提交 Skill 的集成分支
- `main` 是最终发布主干
- `dev` 禁止直接推送
- `main` 禁止直接推送
- `dev` 和 `main` 都禁止强制推送
- 业务同学所有变更必须通过 Pull Request 合入 `dev`
- 助教发布必须通过 `dev -> main` 的 Pull Request 完成
- 业务同学 PR 描述中必须写明 `Skill 名称`、`Skill 路径` 和业务场景摘要

## Agent 接入说明

- Codex 侧安装说明见 [`.codex/INSTALL.md`](./.codex/INSTALL.md)
- Claude 侧安装说明见 [`.claude/INSTALL.md`](./.claude/INSTALL.md)
- Claude 侧插件元数据见 [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json)
- Claude 侧仓库说明见 [`.claude/README.md`](./.claude/README.md)
- OpenCode 侧安装说明见 [`.opencode/INSTALL.md`](./.opencode/INSTALL.md)

## 适用范围

本仓库适合收录以下类型的业务 Skills：

- 面向具体业务流程的执行 Skill
- 面向特定岗位的分析或协作 Skill
- 面向某类文档、工单、流程的处理 Skill
- 在培养计划中验证过、具备复用价值的业务能力模块
