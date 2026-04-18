# 批量处理工作流

本文档说明批量论文 PDF 解析时的输入模式、预检方式、覆盖策略和交付检查。

## 输入模式

| 模式 | 命令参数 | 适用情况 | 说明 |
|------|----------|----------|------|
| 单文件 | `--file-path /path/to/paper.pdf` | 临时处理一篇论文 | 只处理一个 PDF |
| 目录 | `--input-dir /path/to/papers` | 同一目录下有多篇论文 | 默认只扫描当前目录的 `*.pdf` |
| 递归目录 | `--input-dir /path/to/papers --recursive` | PDF 分散在子目录中 | 递归扫描所有子目录 |
| 路径清单 | `--file-list /path/to/papers.txt` | 需要精确指定处理顺序或跨目录处理 | 文本文件需为 UTF-8，每行一个 PDF 路径 |

`--file-list` 支持空行和注释行：

```text
# papers.txt
/Users/example/papers/a.pdf
relative/path/b.pdf
```

相对路径会按清单文件所在目录解析。

## 预检

正式调用 OCR 前，先运行 `--dry-run`：

```bash
python scripts/pdf_to_markdown.py --input-dir "/path/to/papers" --recursive --dry-run
```

预检只解析输入和目标输出路径，不调用 PaddleOCR，也不会写 Markdown 或图片目录。重点检查：

- `total` 是否符合预期
- `planned_outputs[n].source_pdf` 是否都是目标论文
- `markdown_exists` 或 `image_dir_exists` 是否提示已有输出
- 单次运行是否可能超过 300 秒；如果 PDF 数量多或页数长，应拆成多批

## 覆盖策略

默认不覆盖已有输出。若任一 PDF 对应的 `paper.md` 或 `paper/` 已存在，脚本会失败并提示追加 `--force`。

只有用户明确允许覆盖时才使用：

```bash
python scripts/pdf_to_markdown.py --input-dir "/path/to/papers" --force
```

使用 `--force` 时会删除旧的同名 Markdown 和图片目录，再发布新结果。

## 批量失败策略

默认策略是 fail-fast：遇到第一个失败 PDF 就停止，避免继续消耗接口额度。

如果用户更重视完成率，可以追加：

```bash
python scripts/pdf_to_markdown.py --input-dir "/path/to/papers" --continue-on-error
```

此时脚本会继续处理后续 PDF，并在最终 JSON 的 `errors` 中列出失败项。

## 交付检查

成功项必须满足：

- `markdown_path` 指向的文件存在且非空
- `image_dir` 指向的目录存在
- `pages` 大于 0
- `image_count` 与下载到本地的图片资源数量一致

失败项必须反馈：

- 失败 PDF 路径
- 错误原因
- 是否已经处理了其他 PDF
