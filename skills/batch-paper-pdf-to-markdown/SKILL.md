---
name: batch-paper-pdf-to-markdown
description: 当用户提供本地论文 PDF 文件、PDF 目录或 PDF 路径清单，并希望批量解析为 Markdown 与同名图片目录时使用本 Skill。适合科研论文阅读、知识库入库和批量预处理；不负责论文摘要、翻译、引用元数据抽取、远程 URL 下载或非 PDF 文档处理。
---

# 批量论文 PDF 转 Markdown

## 适用场景

当用户需要把一个或多个**本地论文 PDF** 转成可编辑 Markdown，并保留版面中的图片资源时，使用本 Skill。

适用于以下场景：

- 批量将论文导入知识库或笔记系统
- 为后续摘要、问答或标签整理做预处理
- 在保留图片引用的前提下，把 PDF 内容转成可编辑文本
- 将版面复杂、包含图片和结构化内容的学术论文先转成更适合编辑、检索和复用的中间格式

本 Skill 基于 PaddleOCR 文档解析能力完成 PDF 内容提取和图片整理，并在脚本侧补充整篇文档输出、图片资源落盘、相对路径改写、覆盖保护、超时控制和错误返回约束，减少手工摘录、手工改路径和重复整理成本。

## 不适用场景与边界

- 不处理远程 URL、网页、DOCX、PPT、图片文件或压缩包；用户需先提供本地 `.pdf` 文件。
- 不做论文摘要、翻译、主题分类、引用格式解析、BibTeX 生成或文献综述。
- 不保证复刻 PDF 原版排版；目标是生成可编辑 Markdown 和可引用的本地图片资源。
- 不替用户申请、保存或提交 PaddleOCR token；密钥只能通过运行环境变量提供。
- 不在输出已存在时自动覆盖；只有用户明确允许覆盖时才使用 `--force`。
- 单次运行总时间上限为 300 秒；大批量论文应拆成多批处理。

## 输入要求

- 输入三选一：
  - `--file-path`：单个本地 PDF 文件
  - `--input-dir`：包含 PDF 的本地目录，可配合 `--recursive`
  - `--file-list`：逐行列出 PDF 路径的 UTF-8 文本文件，空行和 `#` 开头的注释行会被忽略
- 当前目录应为本 Skill 目录，或命令中的 `scripts/pdf_to_markdown.py` 路径应写成可执行的相对/绝对路径。
- 运行环境需有 Python 3、`httpx` 和可用的 PaddleOCR 文档解析接口。
- 已配置以下环境变量：
  - `PADDLEOCR_DOC_PARSING_API_URL`
  - `PADDLEOCR_ACCESS_TOKEN`
  - 可选：`PADDLEOCR_DOC_PARSING_TIMEOUT`

不要把 token、`.env` 或其他密钥文件放进 Skill 目录或仓库提交内容。

## 执行步骤

1. 先确认输入路径存在，PDF 输出可以写回原目录，并确认是否允许覆盖已有结果。
2. 如缺少依赖，先在当前 Skill 目录下执行 `python -m pip install -r scripts/requirements.txt`。
3. 对批量任务先执行 `--dry-run`，确认将处理的 PDF 列表和目标输出路径。
4. 根据输入类型选择正式命令：
   - 单个 PDF：使用 `--file-path`
   - 目录批量：使用 `--input-dir`，需要包含子目录时追加 `--recursive`
   - 路径清单：使用 `--file-list`
5. 以可轮询的异步方式等待脚本完成，总超时时间不得超过 300 秒；预计超过时先拆批。
6. 如果目标 `paper.md` 或 `paper/` 已存在，只有在明确允许覆盖时才追加 `--force`。
7. 批量任务默认遇到首个错误即失败停止；如果用户明确希望尽量处理完其余 PDF，追加 `--continue-on-error`。
8. 如果脚本非零退出，直接返回原始报错和 JSON 摘要，不要改用其他 OCR 或手工解析流程。

## 输出要求

- 对每个 PDF，在同目录生成一个同名 Markdown 文件，例如 `paper.md`
- 对每个 PDF，在同目录生成一个同名图片目录，例如 `paper/`
- Markdown 中的图片引用应改写为相对路径，例如 `paper/imgs/example.jpg`
- 脚本输出 JSON 摘要，单文件和批量结果都需要明确：
  - Markdown 路径
  - 图片目录路径
  - 图片数量
  - 页数
- 批量任务还需要明确总数、成功数、失败数和失败明细
- 失败时直接暴露脚本返回的错误信息，不能静默忽略

## 质量自查

任务完成后检查：

- JSON 摘要中的 `ok`、`total`、`succeeded`、`failed` 与实际处理结果一致。
- 每条成功记录都包含 `source_pdf`、`markdown_path`、`image_dir`、`image_count`、`pages`。
- `markdown_path` 指向的 Markdown 文件存在且非空。
- `image_dir` 指向的目录存在；如 `image_count > 0`，目录下应有对应图片文件。
- 若存在失败项，输出中必须列出失败 PDF 路径和错误原因。

## 命令示例

单个 PDF：

```bash
python scripts/pdf_to_markdown.py --file-path "/absolute/path/to/paper.pdf"
```

覆盖已有结果：

```bash
python scripts/pdf_to_markdown.py --file-path "/absolute/path/to/paper.pdf" --force
```

批量预检，不调用 OCR：

```bash
python scripts/pdf_to_markdown.py --input-dir "/absolute/path/to/papers" --dry-run
```

目录批量：

```bash
python scripts/pdf_to_markdown.py --input-dir "/absolute/path/to/papers"
```

递归解析目录中的 PDF，并尽量继续处理其余文件：

```bash
python scripts/pdf_to_markdown.py --input-dir "/absolute/path/to/papers" --recursive --continue-on-error
```

按路径清单批量解析：

```bash
python scripts/pdf_to_markdown.py --file-list "/absolute/path/to/papers.txt"
```

## 参考资料

- `references/output_schema.md`：PaddleOCR 返回结构中本 Skill 实际依赖的字段说明
- `references/batch_workflow.md`：批量输入模式、覆盖策略和结果检查说明
- `references/error_handling.md`：常见失败类型、脚本行为和用户反馈要求
- `references/paddleocr_context.md`：PaddleOCR 能力来源和接口依赖说明
- `scripts/lib.py`：PaddleOCR API 包装逻辑
- `scripts/pdf_to_markdown.py`：Markdown 拼装和图片下载逻辑
