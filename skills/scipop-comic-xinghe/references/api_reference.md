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

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://aistudio.baidu.com/llm/lmapi/v3"
)

response = client.chat.completions.create(
    model="ernie-5.0-thinking-preview",
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    stream=True,
    extra_body={
        "web_search": {
            "enable": True
        }
    },
    max_completion_tokens=65536
)
```

**关键参数说明**：

| 参数 | 说明 |
|-----|------|
| `stream` | 是否流式返回，默认 `true`（推荐） |
| `max_completion_tokens` | 最大输出token数，支持高达 65536 |
| `extra_body.web_search.enable` | 是否启用联网搜索增强 |

### 多模态请求（图片+文本）

```python
response = client.chat.completions.create(
    model="ernie-5.0-thinking-preview",
    messages=[
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
    stream=True,
    max_completion_tokens=65536
)
```

### 流式响应解析

> ⚠️ **思考模型特性**: `ernie-5.0-thinking-preview` 会先输出思考过程，再输出最终回答。

```python
for chunk in response:
    if not chunk.choices or len(chunk.choices) == 0:
        continue
    # 思考过程（reasoning_content）
    if hasattr(chunk.choices[0].delta, "reasoning_content") and chunk.choices[0].delta.reasoning_content:
        # 可选：打印思考过程
        print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
    # 最终回答（content）
    if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
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

### 推荐方式：使用 OpenAI SDK

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://aistudio.baidu.com/llm/lmapi/v3"
)

# 负面提示词（避免常见图像生成问题）
negative_prompt = "重复文字，多余的手，第三只手，变形的手指，人体结构错误，比例失调，模糊不清，风格混乱"

# 生成图像
response = client.images.generate(
    model="ernie-image-turbo",
    prompt="一只可爱的猫咪坐在窗台上",
    n=1,                            # 可选：1、2、3、4
    response_format="b64_json",     # 可选：b64_json、url
    size="1024x1024",               # 见下方支持尺寸列表
    extra_body={
        "seed": 42,
        "use_pe": True,
        "num_inference_steps": 8,
        "guidance_scale": 1.0,
        "negative_prompt": negative_prompt  # 负面提示词
    }
)

# 保存图像（b64_json 格式）
image_bytes = base64.b64decode(response.data[0].b64_json)
with open("output.png", "wb") as f:
    f.write(image_bytes)

# 或获取 URL（url 格式）
# image_url = response.data[0].url
```

### 方式二：使用 cURL

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
        "guidance_scale": 1.0,
        "negative_prompt": "重复文字，模糊不清，风格混乱"
    }'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `model` | string | 是 | 模型名称：`ernie-image-turbo` |
| `prompt` | string | 是 | 中文图像描述，支持中文 Prompt |
| `n` | integer | 否 | 生成图片数量，默认 1，支持 1-4 |
| `response_format` | string | 否 | 返回格式：`url`（图片URL）或 `b64_json`（base64） |
| `size` | string | 否 | 图片尺寸，见下方尺寸列表 |
| `seed` | integer | 否 | 随机种子，用于复现结果 |
| `use_pe` | boolean | 否 | 是否使用优先增强，默认 `true` |
| `num_inference_steps` | integer | 否 | 推理步数，默认 8，范围 1-50 |
| `guidance_scale` | float | 否 | 引导比例，默认 1.0，范围 0-20 |
| `negative_prompt` | string | 否 | **负面提示词**，避免生成不需要的内容，如"重复文字，多余的手，变形" |

### 负面提示词推荐

> ⚠️ **重要**: 为避免模型生成重复文字、多余肢体等问题，建议在每次调用时添加负面提示词。

**推荐负面提示词**：

```
重复文字，多余的手，第三只手，变形的手指，人体结构错误，比例失调，模糊不清，风格混乱
```

**按场景定制**：

| 场景 | 推荐负面提示词 |
|-----|--------------|
| 人物场景 | 多余的手，第三只手，变形的手指，人体结构错误，比例失调 |
| 文字场景 | 重复文字，文字重叠，文字模糊 |
| 通用场景 | 模糊不清，风格混乱，低质量 |

### 支持尺寸

| 尺寸 | 适用场景 |
|-----|---------|
| `1024x1024` | 单个 Panel（正方形） |
| `1376x768` | 全局大图（横向长条） |
| `768x1376` | 全局大图（竖向长条） |
| `1264x848` | 横向矩形 |
| `1200x896` | 横向矩形 |
| `896x1200` | 竖向矩形 |
| `848x1264` | 竖向矩形 |

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