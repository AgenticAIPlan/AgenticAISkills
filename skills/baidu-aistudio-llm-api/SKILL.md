---
name: baidu-aistudio-llm-api
description: The Baidu 「AI Studio」 LLM API Assistant helps developers quickly connect to large model API services and access capabilities from models such as ERNIE and DeepSeek. Powered by the Baidu Intelligent Cloud Qianfan Platform, this service is compatible with the OpenAI Python SDK, allowing developers to integrate directly using the native openai-python SDK. It also provides guidance on model invocation, integration workflows, and related usage questions.✨ Bonus: Sign up and receive 1 million free tokens!
---

# baidu-aistudio-llm-api / 百度 AI Studio 星河社区大模型API调用

**Official Skill from Baidu 「AI Studio」: Baidu AI Studio LLM API Access**

## 概述

星河大模型API是为开发者提供的一套基础大模型服务，背靠百度智能云千帆平台，提供文心(ERNIE)、DeepSeek等大模型能力。该服务**完全兼容OpenAI Python SDK**，开发者可直接使用原生openai-python SDK调用。

**福利：注册即送100万免费Tokens额度！**

The Baidu 「AI Studio」 LLM API Assistant helps developers quickly connect to large model API services and access capabilities from models such as ERNIE and DeepSeek. Powered by the Baidu Intelligent Cloud Qianfan Platform, this service is compatible with the OpenAI Python SDK, allowing developers to integrate directly using the native openai-python SDK. It also provides guidance on model invocation, integration workflows, and related usage questions.✨ Bonus: Sign up and receive 1 million free tokens!

## 快速开始

### Step 1: 获取API Key

检查用户是否已设置环境变量 `AI_STUDIO_API_KEY`：

```bash
# 检查环境变量
echo $AI_STUDIO_API_KEY
```

**如果没有设置，提醒用户：**

> 请访问 https://aistudio.baidu.com/account/accessToken 获取您的访问令牌(Access Token)，然后设置环境变量：
>
> ```bash
> # macOS/Linux
> export AI_STUDIO_API_KEY="您的访问令牌"
>
> # Windows PowerShell
> $env:AI_STUDIO_API_KEY="您的访问令牌"
>
> # 或使用 .env 文件
> echo 'AI_STUDIO_API_KEY="您的访问令牌"' >> .env
> ```

### Step 2: 安装依赖

```bash
pip install openai
```

### Step 3: 基本调用

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("AI_STUDIO_API_KEY"),
    base_url="https://aistudio.baidu.com/llm/lmapi/v3",
)

response = client.chat.completions.create(
    model="ernie-5.0-thinking-preview",
    messages=[
        {"role": "system", "content": "你是一个有帮助的AI助手。"},
        {"role": "user", "content": "你好！"}
    ]
)

print(response.choices[0].message.content)
```

## 模型选择指南

根据用户需求推荐合适的模型：

| 使用场景 | 推荐模型 | 说明 |
|---------|---------|------|
| 深度思考 | `ernie-5.0-thinking-preview` | 最新ERNIE 5.0，思维链推理 |
| 代码生成 | `deepseek-v3` / `qwen3-coder` | 代码能力强 |
| 复杂推理 | `deepseek-r1` | 思维链推理，复杂问题 |
| 通用对话 | `kimi-k2-instruct` | Moonshot开源模型 |
| 长文本处理 | `ernie-4.5-turbo-128k-preview` | 128K上下文 |
| 多模态 | `ernie-4.5-turbo-vl` | 支持图像、视频理解 |
| 快速响应 | `ernie-speed-8k` | 速度快 |

**完整模型列表请查看：** [references/models.md](references/models.md)

## 常用功能示例

### 流式输出

```python
completion = client.chat.completions.create(
    model="ernie-5.0-thinking-preview",
    messages=[{"role": "user", "content": "讲个故事"}],
    stream=True,
)

for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### 多轮对话

```python
messages = [
    {"role": "system", "content": "你是AI助手。"}
]

# 添加用户消息
messages.append({"role": "user", "content": "你好"})

# 获取回复
response = client.chat.completions.create(
    model="kimi-k2-instruct",
    messages=messages
)

# 保存到历史
messages.append({
    "role": "assistant",
    "content": response.choices[0].message.content
})
```

### 联网搜索（搜索增强）

```python
completion = client.chat.completions.create(
    model="ernie-5.0-thinking-preview",
    messages=[{"role": "user", "content": "今天北京天气"}],
    extra_body={
        "web_search": {
            "enable": True,
            "enable_trace": True
        }
    }
)
```

**支持联网搜索的模型：** ernie-5.0, ernie-4.5, deepseek-r1, deepseek-v3

### Function Calling

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名"}
            },
            "required": ["city"]
        }
    }
}]

response = client.chat.completions.create(
    model="deepseek-v3",
    messages=[{"role": "user", "content": "北京今天天气"}],
    tools=tools,
    tool_choice="auto"
)
```

**支持Function Call的模型：** ernie-5.0-thinking-preview, ernie-x1-turbo, deepseek-r1, deepseek-v3

### 结构化输出（JSON）

```python
response = client.chat.completions.create(
    model="ernie-4.5-turbo-128k-preview",
    messages=[{"role": "user", "content": "列出三个水果"}],
    response_format={"type": "json_object"}
)
```

### 深度思考模型（思维链）

```python
response = client.chat.completions.create(
    model="deepseek-r1",
    messages=[{"role": "user", "content": "请解释相对论"}]
)

# 思维链内容
print(response.choices[0].message.reasoning_content)
# 最终回答
print(response.choices[0].message.content)
```

### 多模态（图像理解）

```python
response = client.chat.completions.create(
    model="ernie-4.5-turbo-vl",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这张图片"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
    }]
)
```

### 文生图

```python
images = client.images.generate(
    prompt="一只可爱的白猫，戴着红帽子",
    model="Stable-Diffusion-XL",
    response_format="url"
)
print(images.data[0].url)
```

### 文本向量化

```python
embeddings = client.embeddings.create(
    model="embedding-v1",
    input=["你好世界", "机器学习"]
)
print(embeddings.data[0].embedding)
```

## 高级功能

详细的API参数说明和更多功能，请查看：
- **完整模型列表：** [references/models.md](references/models.md)
- **API参数详解：** [references/api_params.md](references/api_params.md)

## 常见错误处理

| 错误码 | 说明 | 解决方案 |
|-------|------|---------|
| 401 | 认证失败 | 检查API Key是否正确 |
| 429 | 请求限流 | 降低请求频率或等待 |
| 400 | 参数错误 | 检查messages格式和参数 |
| 403 | 内容安全 | 修改输入内容 |

## 官方资源

- 安装教程：[《在OpenClaw中安装星河社区 Skills》](https://dcn8t60z51f3.feishu.cn/wiki/DiiFwvRMoiQe1MkYqLacwsuWnZb)
- API文档：https://ai.baidu.com/ai-doc/AISTUDIO/rm344erns
- 获取Token：https://aistudio.baidu.com/account/accessToken
- 使用明细：登录星河社区后查看

## Resources

### scripts/
- `test_connection.py` - 测试API连接
- `list_models.py` - 查询可用模型列表

### references/
- `models.md` - 完整模型列表和能力说明
- `api_params.md` - API参数详细说明
