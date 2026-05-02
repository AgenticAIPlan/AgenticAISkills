# 飞书文档上传操作说明

使用 `lark-cli`（`~/.local/bin/lark-cli`）将 Markdown 报告上传到飞书，每次监测运行后自动创建新文档。

---

## 基本用法

```bash
# 必须从 ~ 目录执行，使用相对路径 @feishu_report.md
cd ~ && ~/.local/bin/lark-cli docs +create \
  --title "ERNIE-Image 舆情监测报告 2026-04-16 21:10" \
  --markdown @feishu_report.md
```

成功响应示例：

```json
{
  "ok": true,
  "data": {
    "doc_id": "XxxxxxxxxxxxxxxxxxxxxxxX",
    "doc_url": "https://www.feishu.cn/docx/XxxxxxxxxxxxxxxxxxxxxxxX"
  }
}
```

---

## 关键注意事项

| 要点 | 说明 |
|------|------|
| 必须 `cd ~` | lark-cli 从当前目录解析 `@file` 路径，不支持绝对路径 |
| 每次用 `+create` | 每次监测必须创建新文档，**不要**覆盖已有文档 |
| 标题含时间戳 | 格式：`ERNIE-Image 舆情监测报告 YYYY-MM-DD HH:MM` |
| 返回 URL | 执行成功后将 `doc_url` 告知用户 |

---

## 报告文件写入

在上传前，将完整 Markdown 内容写入 `~/feishu_report.md`：

```python
with open(os.path.expanduser("~/feishu_report.md"), "w") as f:
    f.write(markdown_content)
```

---

## 常见问题

**Q: 上传后飞书文档格式乱了？**
A: 确保 Markdown 中的表格每行有对应的 `|` 分隔，避免单元格内换行。

**Q: lark-cli 报认证错误？**
A: 运行 `~/.local/bin/lark-cli auth` 重新登录飞书账号。

**Q: 文件路径找不到？**
A: 确认已 `cd ~`，且 `feishu_report.md` 确实存在于 `~` 目录下。
