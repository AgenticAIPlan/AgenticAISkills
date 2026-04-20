# 参考资料

本目录存放 Benchmark Model Test Skill 的补充说明和参考资料。

## 文件说明

| 文件 | 说明 |
|------|------|
| `excel-template.md` | Excel 模板详细说明 |
| `model-keywords.md` | 模型关键字匹配规则 |

## 快速参考

### Excel 列定义

- **D 列**：prompt 输入
- **G 列**：附件文件名（多文件用 `/` 分隔）
- **H 列起**：模型名称（表头）→ 响应结果（数据）

### 命令参数

```bash
node scripts/skill.js --file <excel> [--start-row <n>] [--timeout <s>] [--auto]
```

### 支持的附件格式

- 图片：jpg, jpeg, png, gif, webp
- 文档：txt, pdf, doc, docx, csv, xlsx, xls