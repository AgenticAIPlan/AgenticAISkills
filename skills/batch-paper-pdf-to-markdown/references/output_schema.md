# PaddleOCR 文档解析返回结构说明

本文档记录 `scripts/lib.py` 和 `scripts/pdf_to_markdown.py` 实际依赖的返回结构，以及脚本输出的 JSON 摘要格式，便于排查接口字段变更。

## `parse_document()` 返回结构

成功时：

```json
{
  "ok": true,
  "text": "Extracted text from all pages",
  "result": { "...": "raw provider response" },
  "error": null
}
```

失败时：

```json
{
  "ok": false,
  "text": "",
  "result": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

## 错误码

| Code | Description |
|------|-------------|
| `INPUT_ERROR` | 输入缺失、文件不存在或格式不支持 |
| `CONFIG_ERROR` | 接口地址或 token 未配置 |
| `API_ERROR` | 接口鉴权失败、超时、限流或返回结构异常 |

## 原始接口结果关键字段

`parse_document()` 会把 PaddleOCR 原始返回包在 `result` 字段里，当前 Skill 依赖的结构如下：

```json
{
  "logId": "request-uuid",
  "errorCode": 0,
  "errorMsg": "Success",
  "result": {
    "layoutParsingResults": [
      {
        "markdown": {
          "text": "Full page content in markdown/HTML format",
          "images": {
            "imgs/example.jpg": "https://..."
          }
        }
      }
    ]
  }
}
```

## 当前脚本实际使用的字段

- `result.layoutParsingResults`
  用于遍历每一页解析结果。
- `result.layoutParsingResults[n].markdown.text`
  用于拼接最终 Markdown 正文。
- `result.layoutParsingResults[n].markdown.images`
  用于下载图片，并将文档中的相对图片路径改写为 `paper/...` 形式。

## 输出文件关系

对于输入 `/path/to/paper.pdf`，脚本最终输出：

- `/path/to/paper.md`
- `/path/to/paper/`
- `/path/to/paper/imgs/...`

Markdown 中的图片引用会被统一改写为相对路径，例如：

```md
![figure](paper/imgs/example.jpg)
```

## 脚本输出摘要

`scripts/pdf_to_markdown.py` 会向 stdout 输出 JSON 摘要。单文件输入时 `mode` 为 `single`，批量输入时 `mode` 为 `batch`。

预检时：

```json
{
  "ok": true,
  "mode": "batch",
  "dry_run": true,
  "total": 2,
  "succeeded": 0,
  "failed": 0,
  "planned_outputs": [
    {
      "source_pdf": "/path/to/paper.pdf",
      "markdown_path": "/path/to/paper.md",
      "image_dir": "/path/to/paper",
      "markdown_exists": false,
      "image_dir_exists": false
    }
  ],
  "results": [],
  "errors": []
}
```

成功时：

```json
{
  "ok": true,
  "mode": "batch",
  "dry_run": false,
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "results": [
    {
      "ok": true,
      "source_pdf": "/path/to/paper.pdf",
      "markdown_path": "/path/to/paper.md",
      "image_dir": "/path/to/paper",
      "image_count": 3,
      "pages": 12
    }
  ],
  "errors": []
}
```

失败或部分失败时：

```json
{
  "ok": false,
  "mode": "batch",
  "dry_run": false,
  "total": 2,
  "succeeded": 1,
  "failed": 1,
  "results": [],
  "errors": [
    {
      "ok": false,
      "source_pdf": "/path/to/bad.pdf",
      "error": "CONFIG_ERROR: PADDLEOCR_ACCESS_TOKEN not configured"
    }
  ]
}
```
