---
name: scipop-comic-xinghe
description: |
  科普连环画自动生成工具 - 基于百度星河社区 API 的三阶段闭环创作系统。

  TRIGGER when: 用户想要将科普文章/科学内容转化为连环画、漫画、视觉叙事；
  用户提到"连环画"、"科普漫画"、"可视化科普"、"科学故事画"；
  用户有科普内容需要视觉化呈现；用户提到"星河API"或"Ernie-image"生图。

  不要触发: 用户只是想生成单张图片（非连环画）、用户要处理非科普类内容。
---

# SciPop Comic Orchestrator（科普连环画编排器）

基于百度星河社区 API 的自动化科普连环画生成工具，实现多模态解析 × 单 Panel 精修 × N×N 全局合成的三阶段闭环创作。

---

## 环境配置

> 📖 详细 API 文档参见 [references/api_reference.md](references/api_reference.md)

### 必需条件

| 项目 | 要求 |
|------|------|
| **API Key** | 星河社区 API Key，环境变量 `AISTUDIO_API_KEY` |
| **API 端点** | `https://aistudio.baidu.com/llm/lmapi/v3` |
| **SDK** | `pip install openai Pillow` |
| **分析模型** | `ernie-5.0-thinking-preview`（原生全模态大模型） |
| **生图模型** | `ernie-image-turbo`（图像生成 API） |

### 配置验证

```bash
# 设置 API Key
export AISTUDIO_API_KEY="your-key"

# 安装依赖
pip install openai Pillow

# 验证连通性（Python）
python -c "
from openai import OpenAI
client = OpenAI(
    api_key='$AISTUDIO_API_KEY',
    base_url='https://aistudio.baidu.com/llm/lmapi/v3'
)
response = client.chat.completions.create(
    model='ernie-5.0-thinking-preview',
    messages=[{'role': 'user', 'content': 'ping'}],
    max_completion_tokens=10
)
print('API 连接成功:', response.choices[0].message.content[:20])
"
```

---

## 参考文档

| 文档 | 用途 |
|------|------|
| [references/api_reference.md](references/api_reference.md) | 星河社区 API 详细参考 |
| [references/article_analysis_prompts.md](references/article_analysis_prompts.md) | 文章解析提示词模板 |
| [references/ernie_image_prompt_guide.md](references/ernie_image_prompt_guide.md) | ERNIE-Image 提示词撰写指南 |
| [references/style_guide.md](references/style_guide.md) | 连环画风格设计指南 |

---

## 工作流程

### Phase 1: 文章解析与 Prompt 建模

**目标**: 将科普文章拆解为 4-6 个视觉场景，生成风格一致的图像 Prompt。

> 📖 详细规范参见 [references/article_analysis_prompts.md](references/article_analysis_prompts.md)

#### 提示词结构规范

**系统提示词模板**:

```
你是一位科普连环画脚本编写专家。分析文章并根据内容的丰富程度和结构确定最合适的 Panel 数量（4-6个）。输出一个 JSON 对象，包含四个字段："recommended_panels"（整数，4-6），"recommendation_reason"（一句话中文解释为什么这个 Panel 数量适合该文章），"style_seed"（简短的中文风格描述，在所有 Panel 中复用），"panels"（与推荐数量匹配的对象数组，每个对象包含 "id"、"scene" 中文场景描述、"caption" 中文科普旁白（20字以内，简洁有力）、"image_prompt" 中文图像生成提示、"fact_check" 本画面涉及的关键事实）。仅输出原始 JSON，不要使用 markdown 代码块。

⚠️ 关键信息保留要求：
1. 必须保留文章中的关键数字（年份、数量、百分比等）
2. 必须准确使用人物姓名和身份，不可张冠李戴
3. 必须保留专有名词和科学术语的原文
4. 时间、地点必须与文章记载一致
```

> 📖 详细的关键信息保留规范参见 [references/article_analysis_prompts.md](references/article_analysis_prompts.md#关键信息保留与事实核对)

**image_prompt 撰写规范**（详见 [references/ernie_image_prompt_guide.md](references/ernie_image_prompt_guide.md)）：

```
{主体特征}，{动作姿态}，{环境背景}，{细节元素}，{风格关键词}，{质量标签}
```

**示例**：
```
一位戴眼镜的女科学家，穿着白色实验服，正激动地指着屏幕，现代实验室背景有显微镜和电脑，屏幕上显示橙红色的黑洞光环图像，扁平插画风格，清晰轮廓，科学配色，高质量，连环画
```

#### Panel 数量决策规则

| Panel数 | 适用场景 |
|--------|---------|
| 4 | 内容简洁，结构清晰，有明确的起承转合 |
| 5 | 内容适中，需要一个过渡或高潮格 |
| 6 | 内容丰富，知识点多，需要完整叙事链 |

#### 风格种子设计规范

> 📖 详细规范参见 [references/style_guide.md](references/style_guide.md)

**格式**: `{画风}，{色调}，{线条/质感}，{氛围}`

| 主题类型 | 推荐风格种子 |
|---------|-------------|
| 天文/物理 | 扁平插画风格，深邃太空蓝配色，清晰轮廓，科学严谨氛围 |
| 生物/医学 | 可爱卡通风，柔和粉彩配色，圆润造型，温馨友好 |
| 环境/生态 | 水彩手绘风，清新自然色调，柔和笔触，生态感 |
| 科技/AI | 赛博朋克风格，霓虹光效，高科技质感，未来感 |
| 科学史 | 复古连环画风，怀旧暖色调，经典漫画风格 |

**步骤**:
1. 接收用户提供的科普文章全文
2. 调用 `ernie-5.0-thinking-preview` 进行解析
3. 向用户展示推荐的 Panel 数量及理由，获取确认

**API 调用模板**:

> 💡 **思考模型特性**: `ernie-5.0-thinking-preview` 会先输出思考过程（`reasoning_content`），再输出最终回答（`content`）。

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://aistudio.baidu.com/llm/lmapi/v3"
)

response = client.chat.completions.create(
    model="ernie-5.0-thinking-preview",
    messages=[
        {
            "role": "system",
            "content": "你是一位科普连环画脚本编写专家。分析文章并根据内容的丰富程度和结构确定最合适的 Panel 数量（4-6个）。输出一个 JSON 对象，包含四个字段："recommended_panels"（整数，4-6），"recommendation_reason"（一句话中文解释为什么这个 Panel 数量适合该文章），"style_seed"（简短的中文风格描述，在所有 Panel 中复用），"panels"（与推荐数量匹配的对象数组，每个对象包含 "id"、"scene" 中文场景描述、"caption" 中文科普旁白（20字以内，简洁有力）、"image_prompt" 中文图像生成提示）。仅输出原始 JSON，不要使用 markdown 代码块。"
        },
        {
            "role": "user",
            "content": "【科普文章全文】"
        }
    ],
    stream=True,
    extra_body={
        "web_search": {"enable": True}  # 可选：启用联网搜索增强
    },
    max_completion_tokens=65536
)

# 解析流式响应 - 分别处理思考过程和最终回答
for chunk in response:
    if not chunk.choices or len(chunk.choices) == 0:
        continue
    # 思考过程（可选打印）
    if hasattr(chunk.choices[0].delta, "reasoning_content") and chunk.choices[0].delta.reasoning_content:
        pass  # print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
    # 最终回答
    if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

**返回结构**:

```json
{
  "recommended_panels": 5,
  "recommendation_reason": "文章涵盖五个层次，5格可完整呈现叙事弧线。",
  "style_seed": "扁平插画风格，柔和粉彩配色，清晰轮廓，2D矢量艺术",
  "key_facts": {
    "key_numbers": ["关键数字列表，如年份、数量、百分比"],
    "key_names": ["关键人物/机构名称列表"],
    "key_locations": ["关键地点列表"],
    "key_dates": ["关键时间列表"],
    "key_terms": ["关键术语列表"]
  },
  "panels": [
    {
      "id": 1,
      "scene": "场景描述",
      "caption": "科普旁白，20字以内",
      "image_prompt": "中文图像生成提示，描述画面内容、风格、构图等",
      "fact_check": "本画面涉及的关键事实，用于核对准确性"
    }
  ]
}
```

**字段说明**:

| 字段 | 说明 |
|-----|------|
| `id` | Panel 编号（从 1 开始） |
| `scene` | 场景描述，用于理解上下文 |
| `caption` | **科普旁白**，中文，20字以内，简洁有力，用于展示在图像中或作为配文 |
| `image_prompt` | 图像生成提示词 |
| `fact_check` | **关键事实核对**，记录本画面涉及的数字、人物、时间等关键信息，确保准确性 |
| `key_facts` | **全局关键信息**，汇总文章中的关键数字、名称、地点等，用于整体核对 |

**用户确认**: 展示 `recommended_panels` 与 `recommendation_reason`，询问用户是否采用。若不同意，询问期望数量（4-6），调整 `panels` 数组。

---

### Phase 2: 单 Panel 图像生成与迭代

**目标**: 为每个 Panel 生成图像，支持用户反馈迭代优化。

> 📖 详细规范参见 [references/ernie_image_prompt_guide.md](references/ernie_image_prompt_guide.md)

#### 提示词撰写核心原则

1. **中文优先**: `ernie-image-turbo` 对中文 Prompt 效果最佳
2. **结构化描述**: 采用 `主体 → 动作 → 环境 → 风格` 的顺序
3. **具体胜于抽象**: 明确描述细节，避免模糊表述

#### Phase 2a: 图像生成

**关键规则**: 将 `style_seed` 追加到每个 `image_prompt` 末尾，保证风格一致。

```
{panel_image_prompt}，{style_seed}，高质量，连环画
```

**提示词长度建议**: 单 Panel 以 80-150 中文字符为宜

**API 调用模板**:

> 📖 详细 API 参数参见 [references/api_reference.md](references/api_reference.md#图像生成-api)

**推荐方式：使用 OpenAI SDK**

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://aistudio.baidu.com/llm/lmapi/v3"
)

# 生成图像
response = client.images.generate(
    model="ernie-image-turbo",
    prompt="【拼接后的完整Prompt】",
    n=1,
    response_format="b64_json",  # 或 "url"
    size="1024x1024",
    extra_body={
        "seed": 42,
        "use_pe": True,
        "num_inference_steps": 8,
        "guidance_scale": 1.0
    }
)

# 保存图像
image_bytes = base64.b64decode(response.data[0].b64_json)
with open("panel_01.png", "wb") as f:
    f.write(image_bytes)
```

**支持尺寸**:

| 尺寸 | 适用场景 |
|-----|---------|
| `1024x1024` | 单个 Panel（正方形） |
| `1376x768` | 全局大图（横向长条） |
| `768x1376` | 全局大图（竖向长条） |
| `1264x848`, `1200x896`, `896x1200`, `848x1264` | 其他比例 |

#### 科普旁白渲染

> ⚠️ **重要说明**：输出给用户确认的单 Panel 图像是**已渲染科普旁白**后的图像，而非模型直接生成的原始图像。流程为：模型生成图像 → Pillow 渲染旁白 → 展示给用户确认。这样确保用户看到的图像就是最终的成品效果。

**位置规范**: 科普旁白统一渲染在单 Panel 图像**底部居中**位置。

**渲染参数**:
- 字体大小：36px
- 文字颜色：白色（#FFFFFF）
- 背景样式：半透明黑色圆角矩形（70% 不透明度）
- 描边效果：黑色 1px 描边，增强可读性

**实现方式**（使用 Pillow）:

```python
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def add_caption(image_bytes: bytes, caption: str) -> bytes:
    """在图像底部居中添加科普旁白"""
    if not caption:
        return image_bytes

    image = Image.open(BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)

    # 加载中文字体
    font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)

    # 计算文字位置（底部居中）
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_width = bbox[2] - bbox[0]
    x = (image.width - text_width) // 2
    y = image.height - 60  # 底部留白

    # 绘制半透明背景 + 文字
    # ... 详见 scripts/generate_comic.py

    output = BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()
```

> 💡 **注意**: 旁白文字在生成图像**后**通过 Pillow 渲染，不是由图像生成模型直接生成。

#### Phase 2b: 多模态反馈迭代

> ⚠️ **注意**: 用户反馈迭代时看到的图像是**已渲染科普旁白**后的图像。若用户对旁白样式不满意，可调整渲染参数；若对图像内容不满意，则需修改 `image_prompt` 重新生成。

若用户不满意，将图像 base64 + 用户反馈文字传入多模态模型获取改进建议。

**常见问题改进策略**（详见 [references/ernie_image_prompt_guide.md](references/ernie_image_prompt_guide.md#常见问题与解决方案)）：

| 问题类型 | 改进策略 |
|---------|---------|
| 风格不一致 | 强化 style_seed 关键词，添加"保持风格统一"指令 |
| 细节缺失 | 添加具体细节描述，如"带有XX标识"、"背景显示XX" |
| 角色变形 | 添加"比例协调"、"人体结构正确"等约束 |
| 色彩偏差 | 明确色调描述，如"主色调为深蓝色" |
| 构图混乱 | 添加构图指令，如"居中构图"、"三分法构图" |

```bash
IMAGE_B64=$(base64 -i panel_01.png | tr -d '\n')

curl -s https://aistudio.baidu.com/llm/lmapi/v3/chat/completions \n  -H "Content-Type: application/json" \n  -H "Authorization: Bearer $AISTUDIO_API_KEY" \n  -d "{
    "model": "ernie-5.0-thinking-preview",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,${IMAGE_B64}"}},
        {"type": "text", "text": "用户反馈：【用户反馈】\n\n分析图像与反馈之间的差距，仅返回改进后的中文图像生成提示，不需要解释，不要使用 markdown。"}
      ]
    }],
    "stream": true,
    "max_completion_tokens": 65536
  }"
```

**迭代循环**: 用改进后的 Prompt 重新执行 Phase 2a，直至用户满意。

> ⚠️ **重要**: 保留用户满意的最终 Prompt，用于 Phase 3 全局合成。

---

### Phase 3: N×N 全局合成

**目标**: 将所有 Panel 合成为一张完整连环画长图。

> 📖 详细规范参见 [references/style_guide.md](references/style_guide.md)

#### Phase 3a: 布局确认

根据 Panel 数量推荐布局：

| Panel 数 | 推荐布局 | 说明 |
|---------|---------|------|
| 4 | `2×2` | 正方形，视觉均衡 |
| 5 | `2×3`（空出右下角）| 横向阅读，留白收尾 |
| 6 | `2×3` | 标准竖向长图 |

**阅读顺序**: 中文连环画采用从左到右、从上到下的阅读顺序。

向用户展示推荐布局，获取确认或自定义布局。

**布局合法性**: `行数 × 列数 ≥ Panel数`

#### Phase 3b: 全局 Prompt 构建

> ⚠️ **关键**: 使用 **Phase 2b 迭代后用户满意的最终 Prompt**，而非 Phase 1 原始 Prompt。

**合并规则**:
1. 收集所有 Panel 用户满意的最终 `image_prompt`
2. 添加连环画结构指令：`{grid} 格连环画，共 {num_panels} 格`
3. 添加风格种子：`{style_seed}`
4. 添加分隔要求：`每格之间用粗黑边框清晰分隔，按阅读顺序排列`
5. 按顺序排列各 Panel 的最终 prompt

**提示词长度建议**: 全局合成以 200-400 中文字符为宜。

```
{grid} 格连环画，共 {num_panels} 格，{style_seed}，
每格之间用粗黑边框清晰分隔，按阅读顺序排列：
第1格：{panel_1_final_image_prompt}
第2格：{panel_2_final_image_prompt}
...
第N格：{panel_N_final_image_prompt}
```

若有空余格，末尾追加"剩余格子留白"。

**示例**（假设 Panel 1 经过迭代优化后）:

```
# 原始 Prompt (Phase 1):
一位科学家在实验室中，扁平插画风格

# 迭代后最终 Prompt (Phase 2b 满意结果):
一位戴眼镜的女科学家，穿着白色实验服，正激动地指着屏幕，现代实验室背景有显微镜和电脑，屏幕上显示橙红色的黑洞光环图像，扁平插画风格，清晰轮廓，科学配色，高质量

# Phase 3 合并时使用迭代后的最终 Prompt
```

#### Phase 3c: 大图生成

> ⚠️ **尺寸注意**: `ernie-image-turbo` 最大支持 `1376x768`，不支持 `2048x2048`。

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://aistudio.baidu.com/llm/lmapi/v3"
)

response = client.images.generate(
    model="ernie-image-turbo",
    prompt="【全局Prompt】",
    n=1,
    response_format="b64_json",
    size="1376x768",  # 最大横向尺寸
    extra_body={
        "use_pe": True,
        "num_inference_steps": 8,
        "guidance_scale": 1.0
    }
)

image_bytes = base64.b64decode(response.data[0].b64_json)
with open("global_comic.png", "wb") as f:
    f.write(image_bytes)
```

#### Phase 3d: 大图反馈迭代（可选）

若用户对大图有整体调整意见，使用多模态反馈路径重新生成。

#### 全局大图旁白保留

> ⚠️ **重要**: 全局大图生成后，会通过 Pillow 自动为每个格子添加对应的科普旁白，确保与单 Panel 图像一致。

**渲染逻辑**：
1. 根据布局（如 `2x2`、`2x3`）计算每个格子的位置
2. 在每个格子底部居中位置渲染对应的 `caption`
3. 字体大小根据格子尺寸自动调整（约为格子高度的 8%）
4. 使用与单 Panel 相同的样式：白色文字 + 半透明黑色圆角背景 + 黑色描边

---

## Style Seed 一致性机制

`style_seed` 由 Phase 1 生成，在后续所有调用中**保持原文不变**：

```
{panel_image_prompt}，{style_seed}，高质量，连环画
```

Phase 3 全局合成时，`style_seed` 置于 Prompt 首部强调，防止风格漂移。

---

## 错误处理

| HTTP 状态码 | 含义 | 处理策略 |
|------------|------|---------|
| `401` | API Key 无效 | 检查 `AISTUDIO_API_KEY` |
| `402` | 余额不足 | 登录星河社区控制台充值 |
| `429` | 请求频繁 | 指数退避重试：1s → 4s → 16s，最多3次 |
| `5xx` | 服务端错误 | 指数退避重试3次 |

---

## 执行检查清单

创建连环画时，按以下顺序执行：

1. **环境检查**: 确认 `AISTUDIO_API_KEY` 已设置
2. **Phase 1**: 解析文章 → 确认 Panel 数量 → 保存 `style_seed`
3. **Phase 2**: 逐个生成 Panel → 渲染科普旁白 → 展示给用户确认 → 收集反馈 → 迭代优化
4. **Phase 3**: 确认布局 → 构建全局 Prompt → 生成大图 → 渲染旁白 → 可选迭代
5. **交付**: 保存所有 Panel 图像及最终大图（均含渲染后的旁白）

---

## 常见问题

**Q: 多张图像风格不统一？**
检查每次调用是否将 `style_seed` 原文追加至 Prompt 末尾。

**Q: 支持中文 Prompt？**
`ernie-image-turbo` 对中文 Prompt 效果最佳。

**Q: 旁白文字是如何添加的？**
旁白文字不是由图像生成模型直接生成，而是在模型生成图像后，通过 Pillow 库渲染到图像底部居中位置。用户看到的单 Panel 图像和全局大图都是已经渲染旁白后的成品。

**Q: base64 在 Windows 处理？**
PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("panel_01.png"))`