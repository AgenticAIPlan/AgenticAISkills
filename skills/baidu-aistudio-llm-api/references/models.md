# 星河社区大模型完整列表

## 文生文模型

### ERNIE 系列（百度文心）

| 模型名称 | model 参数 | 上下文 | 最大输入 | 最大输出 | 特点 |
|---------|-----------|-------|---------|---------|------|
| ERNIE 4.5 | `ernie-4.5-turbo-128k-preview` | 128k | 123k | 2-12k | 最新旗舰，高性能 |
| ERNIE 4.5 | `ernie-4.5-21b-a3b` | 128k | 120k | 2-12k | 开源版本 |
| ERNIE 4.5 | `ernie-4.5-0.3b` | 128k | 120k | 2-12k | 轻量版 |
| ERNIE 4.0 | `ernie-4.0-8k` | 8k | 5k | 2-2k | 通用对话 |
| ERNIE 4.0 Turbo | `ernie-4.0-turbo-128k` | 128k | 124k | 2-4k | 长文本首选 |
| ERNIE 4.0 Turbo | `ernie-4.0-turbo-8k` | 8k | 5k | 2-2k | 性价比高 |
| ERNIE 3.5 | `ernie-3.5-8k` | 8k | 5k | 2-2k | 入门推荐 |
| ERNIE Speed | `ernie-speed-8k` | 8k | 6k | 2-1k | 快速响应 |
| ERNIE Speed | `ernie-speed-128k` | 128k | 124k | 2-4k | 快速+长文本 |
| ERNIE Tiny | `ernie-tiny-8k` | 8k | 6k | 2-1k | 极速轻量 |
| ERNIE Lite | `ernie-lite-8k` | 8k | 6k | 2-1k | 轻量版 |
| ERNIE Character | `ernie-char-8k` | 8k | 7k | 2-1k | 角色扮演 |

### DeepSeek 系列

| 模型名称 | model 参数 | 上下文 | 最大输入 | 最大输出 | 特点 |
|---------|-----------|-------|---------|---------|------|
| DeepSeek-Chat | `deepseek-v3` | 128k | 128k | 2-12k | 代码能力强 |
| DeepSeek-Reasoner | `deepseek-r1` | 96k | 64k | 16k | 深度推理，思维链 |
| DeepSeek-Reasoner | `deepseek-r1-250528` | 96k | 64k | 16k | R1特定版本 |

### 其他开源模型

| 模型名称 | model 参数 | 上下文 | 最大输入 | 最大输出 | 特点 |
|---------|-----------|-------|---------|---------|------|
| Kimi-K2 | `kimi-k2-instruct` | 128k | 128k | 1-32k | Moonshot |
| Qwen3-Coder | `qwen3-coder-30b-a3b-instruct` | 128k | 128k | 1-32k | 代码专用 |

## 深度思考模型（思维链）

| 模型名称 | model 参数 | 上下文 | 最大输入 | 最大输出 | 思维链长度 |
|---------|-----------|-------|---------|---------|-----------|
| ERNIE 5.0 Thinking | `ernie-5.0-thinking-preview` | 128k | 119k | 1-65k | 60k |
| ERNIE 4.5 Thinking | `ernie-4.5-21b-a3b-thinking` | 128k | 96k | 1-32k | 32k |
| ERNIE X1.1 | `ernie-x1.1-preview` | 64k | 55k | 1-65k | 64k |
| ERNIE X1 Turbo | `ernie-x1-turbo-32k` | 32k | 24k | 2-16k | 16k |

## 多模态模型（图像/视频理解）

| 模型名称 | model 参数 | 支持模态 | 上下文 | 最大输入 | 最大输出 |
|---------|-----------|---------|-------|---------|---------|
| ERNIE 4.5 VL Thinking | `ernie-4.5-vl-28b-a3b-thinking` | 文本、图像、视频 | 128k | 123k | 2-12k |
| ERNIE 4.5 Turbo VL | `ernie-4.5-turbo-vl` | 文本、图像、视频 | 128k | 123k | 2-12k |
| ERNIE 4.5 VL | `ernie-4.5-vl-28b-a3b` | 文本、图像、视频 | 128k | 123k | 2-12k |
| ERNIE 4.5 Turbo VL | `ernie-4.5-turbo-vl-32k` | 文本、图像 | 32k | 30k | 1-8k |

## 向量模型

| 模型名称 | model 参数 | 最大文本数 | 每文本长度 |
|---------|-----------|-----------|-----------|
| Embedding-V1 | `embedding-v1` | 1 | 384 tokens |
| bge-large-zh | `bge-large-zh` | 16 | 512 tokens |

## 文生图模型

| 模型名称 | model 参数 | 类型 |
|---------|-----------|------|
| Stable-Diffusion-XL | `Stable-Diffusion-XL` | 文生图 |

## 功能支持矩阵

### 联网搜索（搜索增强）

支持模型：
- ernie-5.0-thinking-preview
- ernie-x1.1-preview
- ernie-x1-turbo
- ernie-4.5 系列
- ernie-4.0 系列
- ernie-3.5
- deepseek-r1
- deepseek-v3

### Function Calling

支持模型：
- ernie-5.0-thinking-preview
- ernie-x1.1-preview
- ernie-x1-turbo
- deepseek-r1
- deepseek-v3

### 结构化输出

支持模型：
- ernie-4.5 系列
- ernie-4.0-turbo
- ernie-3.5

## 模型选择建议

### 按场景选择

| 场景 | 推荐模型 | 理由 |
|-----|---------|------|
| 深度思考 | `ernie-5.0-thinking-preview` | 最新ERNIE 5.0，思维链推理 |
| 代码开发 | `deepseek-v3` / `qwen3-coder` | 代码专长 |
| 复杂推理 | `deepseek-r1` | 思维链能力强 |
| 通用对话 | `kimi-k2-instruct` | Moonshot开源模型 |
| 长文档处理 | `ernie-4.5-turbo-128k-preview` | 128K上下文 |
| 图像理解 | `ernie-4.5-turbo-vl` | 多模态能力 |
| 快速响应 | `ernie-speed-8k` | 速度最快 |

### 按成本选择

| 成本等级 | 推荐模型 |
|---------|---------|
| 低成本 | `ernie-speed-8k`, `ernie-tiny-8k` |
| 中等成本 | `kimi-k2-instruct`, `deepseek-v3` |
| 高性能 | `ernie-5.0-thinking-preview`, `deepseek-r1` |
