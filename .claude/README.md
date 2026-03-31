# Claude 接入说明

本目录用于承接 Claude 侧的仓库说明和安装说明，而不是存放业务 Skill 正文。

## 当前目录职责

- `.claude/INSTALL.md`：Claude 侧接入和落地说明
- `.claude-plugin/plugin.json`：插件元数据
- `.claude-plugin/marketplace.json`：Marketplace 元数据

## 使用原则

- Claude 相关的业务 Skill 内容统一放在仓库根目录的 `skills/`
- `.claude/` 只承接说明文档，不重复存放 Skills
- `.claude-plugin/` 作为 Claude 侧元数据入口，后续接入时直接复用

## 维护约束

- 新增业务 Skill 时，只改 `skills/` 目录
- 修改 Claude 接入方式时，优先更新 `.claude/INSTALL.md`
- 修改插件信息时，更新 `.claude-plugin/plugin.json` 与 `.claude-plugin/marketplace.json`
