# 星河社区 API 参考

## 端点

### 文本/多模态模型
```
https://aistudio.baidu.com/llm/lmapi/v3/chat/completions
```

### 图像生成模型
```
https://aistudio.baidu.com/llm/lmapi/v3/images/generations
```

## 认证

使用 Bearer Token 认证：

```bash
Authorization: Bearer $AISTUDIO_API_KEY
```

## 模型列表

| 模型名称 | 用途 | 特点 |
|---------|------|------|
| `ernie-5.0-thinking-preview` | 多模态分析 | 原生全模态大模型，支持深度思考 |
| `ernie-image-turbo` | 图像生成 | 中文Prompt效果最佳 |

---

## 文本/多模态模型 API

### 请求格式

```json
{
  "model": "ernie-5.0-thinking-preview",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "stream": true,
  "response_format": {"type": "json_object"},
  "max_completion_tokens": 65536,
  "extra_body": {
    "web_search": {
      "enable": true
    }
  }
}
```

**关键参数说明**：

| 参数 | 说明 |
|-----|------|
| `stream` | 是否流式返回，默认 `true` |
| `max_completion_tokens` | 最大输出token数，支持高达 65536 |
| `extra_body.web_search.enable` | 是否启用联网搜索增强 |

### 多模态请求（图片+文本）

```json
{
  "model": "ernie-5.0-thinking-preview",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {"url": "data:image/png;base64,..."}
        },
        {
          "type": "text",
          "text": "分析这张图片..."
        }
      ]
    }
  ],
  "stream": true,
  "max_completion_tokens": 65536
}
```

### 返回格式

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "返回的文本内容或JSON"
    }
  }]
}
```

---

## 图像生成 API

### 请求格式

```bash
curl --location 'https://aistudio.baidu.com/llm/lmapi/v3/images/generations' \n    --header 'Authorization: Bearer $AISTUDIO_API_KEY' \n    --header 'Content-Type: application/json' \n    --data '{
        "model": "ernie-image-turbo",
        "prompt": "一只可爱的猫咪坐在窗台上",
        "n": 1,
        "response_format": "url",
        "size": "1024x1024",
        "seed": 42,
        "use_pe": true,
        "num_inference_steps": 8,
        "guidance_scale": 1.0
    }'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `model` | string | 是 | 模型名称：`ernie-image-turbo` |
| `prompt` | string | 是 | 中文图像描述，支持中文 Prompt |
| `n` | integer | 否 | 生成图片数量，默认 1 |
| `response_format` | string | 否 | 返回格式：`url`（图片URL）或 `b64_json`（base64） |
| `size` | string | 否 | 图片尺寸，默认 `1024x1024` |
| `seed` | integer | 否 | 随机种子，用于复现结果 |
| `use_pe` | boolean | 否 | 是否使用优先增强，默认 `true` |
| `num_inference_steps` | integer | 否 | 推理步数，默认 8，范围 1-50 |
| `guidance_scale` | float | 否 | 引导比例，默认 1.0，范围 0-20 |

### 返回格式

**URL 格式** (`response_format: "url"`)：

```json
{
  "created": 1234567890,
  "data": [{
    "url": "https://xxx.bcebos.com/xxx.png"
  }]
}
```

**Base64 格式** (`response_format: "b64_json"`)：

```json
{
  "created": 1234567890,
  "data": [{
    "b64_json": "iVBORw0KGgoAAAANSUhEUgA..."
  }]
}
```

### 尺寸参数

| 尺寸 | 用途 |
|-----|------|
| `1024x1024` | 单个 Panel |
| `2048x2048` | 全局大图 |

---

## 错误码

| 状态码 | 含义 | 处理方式 |
|-------|------|---------|
| 401 | 认证失败 | 检查API Key |
| 402 | 余额不足 | 充值 |
| 429 | 请求频繁 | 指数退避重试 |
| 5xx | 服务端错误 | 重试 |

## 官方文档

- [星河社区控制台](https://aistudio.baidu.com)
- [API文档](https://aistudio.baidu.com/docs)