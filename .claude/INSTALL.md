# 在 Claude 中接入 AgenticAISkills

本仓库参考 `superpowers` 的目录组织方式，为 Claude 预留了说明目录和插件元数据目录。

## 接入依赖

Claude 侧接入依赖以下两个位置：

- `.claude/`：存放说明文档和使用约定
- `.claude-plugin/`：存放插件元数据与 Marketplace 元数据

## 接入原则

1. Skills 内容统一维护在仓库根目录的 `skills/`
2. Claude 侧不单独复制一份 Skills
3. 如果后续接入插件分发或本地安装流程，以 `.claude-plugin/` 作为唯一元数据根目录

## 当前仓库已提供的 Claude 相关文件

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `skills/`

## 维护建议

- 业务 Skill 只放在 `skills/<skill-slug>/`
- Claude 接入说明统一维护在 `.claude/`
- 不要在 `.claude/` 下放业务 Skill 正文，避免与 `skills/` 双写
