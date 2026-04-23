# API参数详解

## 基础配置

```python
from openai import OpenAI

client = OpenAI(
    api_key="您的Access Token",  # 或 os.environ.get("AI_STUDIO_API_KEY")
    base_url="https://aistudio.baidu.com/llm/lmapi/v3"
)
```

## Chat Completion 参数

### 必填参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| `model` | string | 模型ID，如 `ernie-5.0-thinking-preview` |
| `messages` | List[dict] | 对话消息列表 |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `stream` | bool | False | 是否流式返回 |
| `temperature` | float | 0.95 | 随机性 (0, 1.0] |
| `top_p` | float | 0.7 | 多样性 [0, 1.0] |
| `max_completion_tokens` | int | - | 最大输出token数 |
| `response_format` | dict | - | 输出格式 `{"type": "json_object"}` |
| `seed` | int | - | 随机种子 |
| `stop` | List[str] | - | 停止词 |
| `frequency_penalty` | float | - | 频率惩罚 [-2.0, 2.0] |
| `presence_penalty` | float | - | 存在惩罚 [-2.0, 2.0] |
| `tools` | List[dict] | - | Function calling 工具定义 |
| `tool_choice` | str/dict | - | 工具选择策略 |

### 星河特有参数（extra_body）

| 参数 | 类型 | 说明 |
|-----|------|------|
| `penalty_score` | float | 重复惩罚 [1.0, 2.0] |
| `web_search` | dict | 联网搜索配置 |

## Messages 格式

### 基本格式

```python
messages = [
    {"role": "system", "content": "系统提示词"},
    {"role": "user", "content": "用户消息"},
    {"role": "assistant", "content": "助手回复"}
]
```

### 多模态消息

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "描述这张图片"},
        {"type": "image_url", "image_url": {"url": "图片URL或base64"}}
    ]
}]
```

### 视频理解

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "描述视频内容"},
        {"type": "video_url", "video_url": {"url": "视频URL", "fps": 1}}
    ]
}]
```

## 联网搜索参数

```python
extra_body={
    "web_search": {
        "enable": True,           # 开启搜索
        "enable_citation": True,  # 返回角标
        "enable_trace": True,     # 返回溯源
        "enable_status": True,    # 返回搜索状态
        "search_num": 10,         # 检索数量
        "reference_num": 5        # 参考数量
    }
}
```

## Function Calling

### 工具定义

```python
tools = [{
    "type": "function",
    "function": {
        "name": "函数名",
        "description": "函数描述",
        "parameters": {
            "type": "object",
            "properties": {
                "参数名": {
                    "type": "string",
                    "description": "参数描述"
                }
            },
            "required": ["必需参数"]
        }
    }
}]
```

### 工具选择

```python
tool_choice = "auto"      # 自动决定
tool_choice = "none"      # 不调用函数
tool_choice = "required"  # 必须调用函数
tool_choice = {"type": "function", "function": {"name": "指定函数名"}}
```

## 响应格式

### 响应结构

```python
response = {
    "id": "请求ID",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "ernie-5.0-thinking-preview",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "回复内容",
            "tool_calls": [],  # Function call时
            "reasoning_content": ""  # 思维链模型时
        },
        "finish_reason": "normal"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    }
}
```

### finish_reason 说明

| 值 | 说明 |
|---|------|
| `normal` | 正常完成 |
| `stop` | 遇到停止词 |
| `length` | 达到最大长度 |
| `content_filter` | 内容被过滤 |
| `function_call` | 调用函数 |

## 流式响应

```python
for chunk in completion:
    # 内容
    content = chunk.choices[0].delta.content

    # 思维链（DeepSeek-R1）
    reasoning = chunk.choices[0].delta.reasoning_content

    # 搜索结果
    if hasattr(chunk, 'search_results'):
        results = chunk.search_results
```

## 错误码

| HTTP状态码 | 类型 | 说明 |
|-----------|------|------|
| 400 | invalid_request_error | 请求参数错误 |
| 401 | access_denied | 认证失败，检查API Key |
| 403 | unsafe_request | 内容安全问题 |
| 404 | no_such_model | 模型不存在 |
| 429 | rate_limit_exceeded | 请求限流 |
| 500 | internal_error | 服务器内部错误 |

## 文生图参数

```python
client.images.generate(
    model="Stable-Diffusion-XL",
    prompt="描述词",              # 必填
    negative_prompt="反向描述",   # 可选
    response_format="url",        # url 或 b64_json
    size="1024x1024",            # 图片尺寸
    n=1,                          # 生成数量 1-4
    style="Base",                 # 风格
    steps=20,                     # 迭代轮次
    cfg_scale=5,                  # 提示词相关性
    seed=None                     # 随机种子
)
```

## Embedding 参数

```python
client.embeddings.create(
    model="embedding-v1",
    input=["文本1", "文本2"]  # 最多16个文本
)
```

## 异步调用

```python
from openai import AsyncOpenAI
import asyncio

client = AsyncOpenAI(
    api_key=os.environ.get("AI_STUDIO_API_KEY"),
    base_url="https://aistudio.baidu.com/llm/lmapi/v3"
)

async def main():
    response = await client.chat.completions.create(
        model="ernie-5.0-thinking-preview",
        messages=[{"role": "user", "content": "你好"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```
