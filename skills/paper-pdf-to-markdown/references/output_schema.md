# PaddleOCR 文档解析返回结构说明

本文档记录 `scripts/lib.py` 和 `scripts/pdf_to_markdown.py` 实际依赖的返回结构，便于排查接口字段变更。

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
