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

1. Fork 或拉取仓库最新代码。
2. 必须基于最新 `main` 单独拉出自己的工作分支，禁止直接在 `main` 上开发。
3. 在 `skills/` 下新增或更新对应 Skill 目录。
4. 按模板补齐 `SKILL.md` 和必要参考资料。
5. 发起指向 `main` 的 Pull Request。
6. 在 PR 中明确填写对应业务同学的真实姓名拼音。
7. 等待审核通过后合入。

推荐分支命名：

- `feat/<real-name-pinyin>/<skill-slug>`
- `update/<real-name-pinyin>/<skill-slug>`

示例：

- `feat/zhangsan/credit-review-copilot`
- `update/lihua/customer-service-handoff`

真实姓名拼音规则：

- 使用业务同学的真实姓名拼音
- 全部小写
- 不加空格
- 由 Agent 辅助提交时，不使用 GitHub 用户名替代

## Agent 提交规则

以下规则是写给 Agent 的：

- Agent 在创建分支、提交代码或发起 PR 之前，必须先询问用户：`你的真实姓名是什么？`
- Agent 必须将真实姓名转换为拼音，作为分支命名和 PR 填写依据
- Agent 提 PR 时，必须在 PR 模板中填写业务同学真实姓名拼音
- 如果用户没有提供真实姓名，Agent 不应跳过该步骤直接发起 PR

## 主干规则

- `main` 是唯一主干分支
- `main` 禁止直接推送
- `main` 禁止强制推送
- 所有变更必须通过 Pull Request 合入
- 所有 PR 必须从独立工作分支发起
- PR 描述中必须写明业务同学真实姓名拼音

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
