# Claude 接入说明

本仓库为 Claude 预留了与 `superpowers` 相似的插件元数据结构。

相关文件位于：

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

其中：

- `plugin.json` 描述当前 Skills 插件本身
- `marketplace.json` 描述本地或仓库级 Marketplace 元数据

如果后续需要接入 Claude 侧分发或安装流程，请以 `.claude-plugin/` 目录作为统一元数据入口，不要将 Skills 内容散落到其他目录。
