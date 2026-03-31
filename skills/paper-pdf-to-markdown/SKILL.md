---
name: paper-pdf-to-markdown
description: 用于将本地论文 PDF 解析为 Markdown 和图片目录，适合论文阅读、知识库入库和后续结构化整理场景。
---

# 论文 PDF 转 Markdown

## 适用场景

当用户需要把本地论文 PDF 转成可编辑的 Markdown，并保留版面中的图片资源时，使用本 Skill。

适用于以下场景：

- 将论文导入知识库或笔记系统
- 为后续摘要、问答或标签整理做预处理
- 在保留图片引用的前提下，把 PDF 内容转成可编辑文本

## 输入要求

- 一个本地 PDF 文件路径
- 可用的 PaddleOCR 文档解析接口
- 已在运行环境中配置以下环境变量：
  - `PADDLEOCR_DOC_PARSING_API_URL`
  - `PADDLEOCR_ACCESS_TOKEN`
  - 可选：`PADDLEOCR_DOC_PARSING_TIMEOUT`

不要把 token、`.env` 或其他密钥文件放进 Skill 目录或仓库提交内容。

## 执行步骤

1. 先确认输入路径存在、是 PDF 文件，且本次允许在原目录写出结果。
2. 运行 `python scripts/pdf_to_markdown.py --file-path "/absolute/path/to/paper.pdf"`。
3. 以可轮询的异步方式等待脚本完成，总超时时间不得超过 300 秒。
4. 如果目标 `paper.md` 或 `paper/` 已存在，只有在明确允许覆盖时才追加 `--force`。
5. 如果脚本非零退出，直接返回原始报错，不要改用其他 OCR 或手工解析流程。

## 输出要求

- 在 PDF 同目录生成一个同名 Markdown 文件，例如 `paper.md`
- 在 PDF 同目录生成一个同名图片目录，例如 `paper/`
- Markdown 中的图片引用应改写为相对路径，例如 `paper/imgs/example.jpg`
- 输出中需要明确：
  - Markdown 路径
  - 图片目录路径
  - 图片数量
  - 页数
- 失败时直接暴露脚本返回的错误信息，不能静默忽略

## 命令示例

```bash
python scripts/pdf_to_markdown.py --file-path "/absolute/path/to/paper.pdf"
```

```bash
python scripts/pdf_to_markdown.py --file-path "/absolute/path/to/paper.pdf" --force
```

## 参考资料

- `references/output_schema.md`：PaddleOCR 返回结构中本 Skill 实际依赖的字段说明
- `scripts/lib.py`：PaddleOCR API 包装逻辑
- `scripts/pdf_to_markdown.py`：Markdown 拼装和图片下载逻辑
