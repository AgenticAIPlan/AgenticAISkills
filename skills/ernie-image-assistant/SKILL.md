---
name: ernie-image-assistant
description: |
    图片逆向提示词助手。当用户需要从图片反推文生图 prompt、逆向提示词、复现图片、分析图片风格时使用此 skill。
    接收用户粘贴的图片路径，调用文心多模态大模型（ERNIE-4.5）进行深度视觉分析，
    从主体内容、艺术风格、构图、色彩、光影、文字渲染等多个维度拆解图片，
    最终生成适用于 ERNIE-Image 的多版本精准提示词，帮助用户复现或再创作。
    重点擅长动漫、胶片、插画等艺术风格图片的逆向分析。
---

# ERNIE-Image Assistant: Enter Prompt, Auto-Generate

## 使用场景

用户说以下类似内容时触发此 skill：
- "帮我逆向这张图的提示词"
- "分析这张图片，生成文生图 prompt"
- "我想复现这张图，帮我写提示词"
- "反推一下这张图的 prompt"
- "逆向提示词"
- "图片转 prompt"

## 环境要求

- 需要设置星河社区 API Key：`export AISTUDIO_API_KEY="your-key"`
- API 端点：`https://aistudio.baidu.com/llm/lmapi/v3/chat/completions`
- 分析模型：`ernie-4.5-turbo-vl-32k`（支持多模态图片理解）
- 目标生图模型：Ernie-image-turbo（通过星河社区调用）

## 工作流程

### Step 1: 获取图片

确认用户提供的图片来源：
1. 用户粘贴**本地图片路径**（如 `/path/to/image.png`）
2. 如果用户未提供图片，主动询问

**支持格式：** PNG、JPG、JPEG、WebP、BMP

获取图片后，使用 Read 工具读取图片文件以确认图片可访问，然后将其转为 base64 编码用于 API 调用。

```bash
# 将图片转为 base64
base64 -i <图片路径>
```

### Step 2: 多维度视觉分析

调用星河社区 ERNIE-4.5 多模态 API，对图片进行结构化深度分析。

**API 调用方式：**

```bash
curl -s https://aistudio.baidu.com/llm/lmapi/v3/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: bearer $AISTUDIO_API_KEY" \
  -d '{
    "model": "ernie-4.5-turbo-vl-32k",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/<ext>;base64,<BASE64_DATA>"}},
        {"type": "text", "text": "<分析提示词>"}
      ]
    }],
    "temperature": 0.3,
    "max_tokens": 4096
  }'
```

**分析提示词（系统级，写入 text 字段）：**

参见 `references/analysis-prompt.md` 中的完整分析提示词模板。

**分析维度：**

| 维度 | 关注点 |
|------|--------|
| 主体内容 | 画面中的核心对象、人物特征（发型/服装/表情/动作）、场景元素 |
| 艺术风格 | 动漫/胶片/写实/水彩/油画/像素/赛博朋克等风格识别 |
| 构图方式 | 视角（俯拍/仰拍/平视）、构图法则（三分法/对称/引导线）、景深 |
| 色彩基调 | 主色调、配色方案、色温（冷/暖）、饱和度、对比度 |
| 光影效果 | 光源方向、光线类型（自然光/逆光/霓虹灯）、阴影特征 |
| 氛围情绪 | 整体氛围（温馨/忧郁/热血/宁静）、情绪表达 |
| 文字渲染 | 图中出现的文字内容、字体风格、排版位置、文字特效（如果有） |
| 纹理质感 | 画面质感（颗粒感/平滑/磨砂）、特效（光斑/烟雾/雨滴） |

### Step 3: 生成多版本提示词

基于 Step 2 的分析结果，生成 3 个版本的 ERNIE-Image 提示词：

**版本说明：**

| 版本 | 用途 | 特点 |
|------|------|------|
| 精准复现版 | 尽可能还原原图 | 包含全部细节描述，最长最详细 |
| 创意改编版 | 在原图基础上微调 | 保留核心风格，简化部分细节，留出创意空间 |
| 精简核心版 | 快速出图 | 只保留最关键的风格和主体描述 |

**提示词撰写规范：**

参见 `references/prompt-writing-guide.md` 中的 ERNIE-Image 提示词撰写指南。

### Step 4: 输出结果

按以下格式输出完整的逆向分析报告：

```
## 图片逆向分析报告

### 一、视觉分析

#### 主体内容
...

#### 艺术风格
...

#### 构图与视角
...

#### 色彩分析
...

#### 光影效果
...

#### 氛围与情绪
...

#### 文字内容（如有）
...

#### 纹理与质感
...

---

### 二、逆向提示词

#### 版本 A — 精准复现版
> [完整提示词]

#### 版本 B — 创意改编版
> [提示词]

#### 版本 C — 精简核心版
> [提示词]

---

### 三、生图建议
- 推荐尺寸：...
- 推荐风格参数：...
- 注意事项：...
```

### Step 5: 交互优化

输出结果后，询问用户：
1. **直接使用** — 选择某个版本的提示词去生图
2. **微调优化** — 指出需要修改的部分，重新生成
3. **换个侧重点** — 比如更强调文字、更强调色彩等
4. **直接生图** — 如果用户配置了 AISTUDIO_API_KEY，可以直接调用 ERNIE-Image 生成图片

如果用户选择直接生图，调用 ERNIE-Image API：

```bash
curl -s https://aistudio.baidu.com/llm/lmapi/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: bearer $AISTUDIO_API_KEY" \
  -d '{
    "model": "Ernie-image-turbo",
    "prompt": "<用户选择的提示词>",
    "n": 1,
    "response_format": "b64_json",
    "size": "1024x1024",
    "seed": -1
  }'
```
