---
name: worldcup2026-parallel-universe
description: |
  2026世界杯赛后平行宇宙叙事引擎 - 将比赛事实转化为诗意的微小说创作。

  当用户想要：创建世界杯/足球相关的微小说叙事、基于比赛事件创作文学内容、使用三元组(entity, event_type, emotion_intensity)生成体育故事、制作世界杯主题的多模态内容（图文结合）时，必须使用此skill。

  触发场景：用户提到"世界杯微小说"、"足球叙事"、"平行宇宙故事"、"绝杀进球故事"、"点球大战叙事"、"球员故事创作"等；用户提供(entity, event_type, emotion_intensity)三元组格式；用户想要将体育赛事转化为创意文学内容。
---

## ⚠️ 前置检查

**执行本 Skill 前必须检查环境变量 `AISTUDIO_API_KEY` 是否已配置。**

### 检查流程

```
Step 1: 检查 AISTUDIO_API_KEY 环境变量
   ↓
未配置 → Step 2: 引导用户获取并告知 API Key
   ↓
Step 3: 自动为用户配置 AISTUDIO_API_KEY
   ↓
已配置 → Step 4: 开始执行创作任务
```

### 未配置时的处理

如果 `AISTUDIO_API_KEY` 未配置或为空，**必须停止执行并引导用户**：

> ❌ **API Key 未配置**
>
> 本 Skill 需要百度星河社区 API Key 才能运行。
>
> 请按以下步骤操作：
> 1. 访问 [百度星河社区](https://aistudio.baidu.com/) 注册账号
> 2. 在个人中心获取 API Key
> 3. 告知我您的 API Key，我将为您自动配置
>
> **注意**：您无需在终端手动设置环境变量，直接告诉我 API Key 即可。

### 用户告知 API Key 后的处理

用户告知 API Key 后，**自动为其配置环境变量**：

```bash
export AISTUDIO_API_KEY="用户提供的key"
```

配置完成后确认：

> ✅ API Key 已配置成功，开始执行创作任务...

---

# WorldCup 2026 Parallel Universe Agent (WP26_PUA)

> 三元组意图驱动 × 实时联网检索 × 深度创意写作 × 多模态长图渲染
> 赛后一小时内完成从事实到诗意的全链路自动化创作

---

## 核心理念

本Agent将世界杯比赛事件转化为"平行宇宙"式的文学叙事——基于真实赛况事实，但以诗意、文学化的方式重新诠释，创造出既有事实根基又富有艺术想象力的微小说作品。

**关键原则**：
- 所有低置信度事实必须"模糊化"处理，确保叙事不会误导读者
- 产出明确标注为"AI创意叙事，不构成新闻报道"
- 尊重球员形象，禁止负面人身攻击

---

## 环境要求

### API 配置

使用本 skill 需要百度星河社区 API Key。

**获取 API Key**：访问 [百度星河社区](https://aistudio.baidu.com/) 注册并获取 API Key

> 💡 **提示**：执行 Skill 时会自动检查 API Key，如未配置会引导您设置。

### API 端点

| 配置项 | 值 |
|--------|-----|
| **API Base URL** | `https://aistudio.baidu.com/llm/lmapi/v3` |
| **创作模型** | `ernie-5.0-thinking-preview`（原生全模态大模型） |
| **目标生图模型** | `ernie-image-turbo`（通过星河社区调用） |
| **最大输出Token** | `65536` |

### API 调用示例 (OpenAI SDK)

**文本生成 API**：
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://aistudio.baidu.com/llm/lmapi/v3",
)

# 流式调用
chat_completion = client.chat.completions.create(
    model="ernie-5.0-thinking-preview",
    messages=[{"role": "user", "content": "你的问题"}],
    stream=True,
    extra_body={"web_search": {"enable": True}},
    max_completion_tokens=65536
)

for chunk in chat_completion:
    if not chunk.choices or len(chunk.choices) == 0:
        continue
    # 处理推理内容 (thinking)
    if hasattr(chunk.choices[0].delta, "reasoning_content") and chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
    else:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

**关键参数说明**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | string | 模型名称：`ernie-5.0-thinking-preview` |
| `messages` | array | 对话消息列表 |
| `stream` | boolean | 是否流式输出，推荐 `true` |
| `extra_body.web_search.enable` | boolean | 是否启用联网搜索 |
| `max_completion_tokens` | integer | 最大输出Token数，默认 `65536` |

### 依赖

```bash
pip install openai
```

### 依赖 Skills

| Skill | 用途 |
|-------|------|
| `web-access` | 执行联网检索，获取赛况事实和在地文化信息 |

---

## 三元组意图协议

所有请求必须包含三元组 `(entity, event_type, emotion_intensity)`，这是驱动整条流水线的唯一入口契约。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `entity` | string | 核心角色/球队/球员 | `"梅西"` / `"巴西队"` / `"姆巴佩"` |
| `event_type` | string | 赛事事件类型 | `"绝杀进球"` / `"点球大战失利"` / `"退场红牌"` |
| `emotion_intensity` | integer 0–10 | 情绪强度，驱动叙事视角路由 | `9` |

**情绪强度路由规则**：

| emotion_intensity | 叙事视角 | 文风 |
|-------------------|---------|------|
| ≥ 8 | 第一人称热血 | 内心独白，高密度感官意象 |
| 5–7 | 伪纪实 | 第三人称限知，新闻笔法夹叙事 |
| < 5 | 纯第三人称冷峻 | 疏离感，白描，克制 |

---

## 10步执行工作流

### 模型调用总览

| 步骤 | 模型 | 说明 |
|------|------|------|
| Step 1-9 | `ernie-5.0-thinking-preview` | 创作模型（原生全模态大模型） |
| Step 10 | `ernie-image-turbo` | 目标生图模型 |

```
┌──────────────────────────────────────────────────────────────┐
│  Phase 1 · 意图解构与契约锁定                                 │
│  Step 1 │ Intent_Parser    │ 解析三元组 → conflict_archetype  │
│  Step 2 │ Config_Manager   │ 锁定体裁契约 (300字微小说)        │
│         │ 📍 模型: ernie-5.0-thinking-preview                    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 2 · 逻辑规划与实时搜索                                 │
│  Step 3 │ Logic_Planner    │ 路由叙事视角，配置 pacing_target  │
│         │ 📍 模型: ernie-5.0-thinking-preview                    │
│  Step 4 │ Web_Search       │ 双路检索：赛况事实 + 在地文化      │
│         │ 📍 使用 web-access skill                           │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 3 · 创意生产与多重审计                                 │
│  Step 5 │ Creative_Writer  │ 高质微小说创作 (≤300字)           │
│  Step 6 │ Safety_Guard     │ 合规审查 + 事实置信度核查          │
│  Step 7 │ Reflexion_Critic │ 自评闭环 (σ>0.3 触发局部重写)     │
│         │                  │ 上限3次 → 失败则熔断降级           │
│         │ 📍 模型: ernie-5.0-thinking-preview                    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 4 · 审美映射与多模态交付                               │
│  Step 8 │ Aesthetic_Mapper │ 色彩/字体/间距映射 + CLIP校准     │
│  Step 9 │ LongImage_Renderer│ 生成图片提示词 (1:1 & 9:16)      │
│         │ 📍 模型: ernie-5.0-thinking-preview                    │
│  Step 10│ MultiModal_Publisher│ 调用生图API生成最终图片        │
│         │ 📍 模型: ernie-image-turbo (目标生图模型)           │
└──────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 意图解构与契约锁定

### Step 1 — 意图深度解析 (Intent_Parser)

解析三元组，提取 `conflict_archetype`（叙事冲突原型）与 `psyche_mode`（心理模式）。

**模型调用**：`ernie-5.0-thinking-preview`

**冲突原型类型**：
- `hero_falls` - 英雄迟暮
- `underdog_rises` - 黑马崛起
- `last_stand` - 最后一战
- `bitter_betrayal` - 苦涩背叛
- `silent_redemption` - 无声救赎

**心理模式类型**：
- `volcanic` - 火山爆发式
- `melancholic` - 忧郁沉思式
- `defiant` - 抗争不屈式
- `numb` - 麻木疏离式
- `transcendent` - 超然升华式

**输出格式**：
```json
{
  "entity": "球员/球队名",
  "event_type": "事件类型",
  "emotion_intensity": 0-10,
  "conflict_archetype": "冲突原型",
  "psyche_mode": "心理模式"
}
```

### Step 2 — 体裁契约锁定 (Config_Manager)

确认输出契约：体裁为社媒微小说，严格限300字，锁定叙事约束参数。

**模型调用**：`ernie-5.0-thinking-preview`

**输出格式**：
```json
{
  "genre": "社媒微小说",
  "length_limit": 300,
  "pov_mode": "视角模式",
  "forbidden_patterns": ["禁止模式列表"],
  "tone_anchor": "英文基调描述短语"
}
```

**禁止模式**：
- 政治敏感表述
- 真实球员负面人身攻击
- 未经证实的伤情细节

---

## Phase 2: 逻辑规划与实时搜索

### Step 3 — 叙事逻辑规划 (Logic_Planner)

根据 `pov_mode` 配置叙事节奏目标 `pacing_target`，确定三幕结构分配。

**模型调用**：`ernie-5.0-thinking-preview`

**节奏类型**：
- `staccato` - 断奏式（短促有力）
- `wave` - 波浪式（起伏有致）
- `avalanche` - 雪崩式（递进爆发）

**输出格式**：
```json
{
  "act_1_words": 开篇字数,
  "act_2_words": 冲突字数,
  "act_3_words": 结局字数,
  "pacing_target": "节奏类型",
  "sensory_anchors": ["感官锚点1", "感官锚点2", "感官锚点3"],
  "emotion_score_series": [0.3, 0.5, 0.8, 1.0, 0.9]
}
```

### Step 4 — 双路联网检索 (Web_Search)

**重要**：两路检索必须独立执行，保持事实溯源可追踪。

**使用 web-access skill 执行检索**

**Query-A：赛况事实检索**

搜索关键词：`{年份}世界杯 {entity} {event_type} 赛况比分 场馆`

需要获取：
- `match_score` - 比分
- `minute_of_event` - 事件发生分钟数
- `venue` - 场馆名称
- `attendance` - 观众人数
- `key_facts` - 关键事实（最多5条）
- `confidence_scores` - 每条事实的置信度（0.0-1.0）

**Query-B：在地文化细节检索**

搜索关键词：`{年份}世界杯 举办城市 本地文化 球迷氛围 地标`

需要获取：
- `city_name` - 城市名
- `local_atmosphere` - 本地氛围描述
- `cultural_symbols` - 文化符号（3个）
- `crowd_chant_fragment` - 球迷口号片段

---

## Phase 3: 创意生产与多重审计

### Step 5 — 微小说高质创作 (Creative_Writer)

将 Steps 1–4 所有输出作为上下文，生成 ≤300 字微小说正文。

**模型调用**：`ernie-5.0-thinking-preview`

**创作规则**：
1. 严格控制在300字以内
2. 精确遵循 pov_mode 视角
3. 至少嵌入2个 sensory_anchors
4. confidence_score < 0.6 的事实必须模糊化处理
5. 遵守三幕字数分配
6. 绝不使用 forbidden_patterns

**事实模糊化规则**：

| confidence_score | 处理方式 | 示例转换 |
|-----------------|---------|---------|
| ≥ 0.80 | 直接使用 | "第89分钟" |
| 0.60–0.79 | 轻度模糊 | "比赛尾声" |
| < 0.60 | 强制虚化 | "某个注定的瞬间" |

**输出格式**：
```json
{
  "novel_text": "微小说正文",
  "word_count": 字数,
  "sensory_anchors_used": ["使用的感官锚点"],
  "fuzzified_facts": ["模糊化处理的事实"]
}
```

### Step 6 — 安全与置信度审计 (Safety_Guard)

并行执行内容合规审查与事实置信度核查。

**模型调用**：`ernie-5.0-thinking-preview`

**审计维度**：
- `compliance_pass` - 合规是否通过
- `fact_confidence_pass` - 事实置信度是否通过
- `overall_pass` - 整体是否通过

**输出格式**：
```json
{
  "compliance_pass": true/false,
  "compliance_issues": ["问题列表"],
  "fact_confidence_pass": true/false,
  "unfuzzified_risks": ["未模糊化风险"],
  "overall_pass": true/false,
  "audit_note": "审计摘要"
}
```

### Step 7 — Reflexion 闭环自评 (Reflexion_Critic)

对小说进行三维自评，任一维度不通过则回流 Step 5。

**模型调用**：`ernie-5.0-thinking-preview`

**评估维度**：

| 维度 | 阈值 | 不通过处理 |
|------|------|-----------|
| 人设漂移 σ | ≤ 0.30 | 变异 tone_anchor 后回流 |
| 情绪弧线拟合度 | ≥ 0.70 | 调整三幕字数后回流 |
| 字数达标 | ≤ 300字 | 压缩后回流 |

**熔断规则**：最多重试3次，超限则标记 `quality_status: "degraded"` 直通 Step 8。

**输出格式**：
```json
{
  "persona_drift_sigma": 0.0-1.0,
  "emotion_arc_fit": 0.0-1.0,
  "word_count_ok": true/false,
  "overall_pass": true/false,
  "rewrite_instructions": "重写指令或null",
  "iteration": 当前迭代次数
}
```

---

## Phase 4: 审美映射与多模态交付

### Step 8 — 视觉参数计算 (Aesthetic_Mapper)

将情绪评分序列映射为色彩、字体、间距参数。

**模型调用**：`ernie-5.0-thinking-preview`

**输出格式**：
```json
{
  "dominant_color_hex": "#主色调",
  "secondary_color_hex": "#辅助色",
  "font_weight": "light/regular/bold/heavy",
  "line_spacing_multiplier": 1.0-2.0,
  "landscape_base": "英文视觉背景描述",
  "clip_cosine_score": 0.0-1.0,
  "recalibration_note": "校准说明或null"
}
```

**CLIP校准**：`cos θ < 0.72` 时必须输出 `recalibration_note` 并重新映射。

### Step 9 — 长图渲染 (LongImage_Renderer)

生成双版面图片提示词，用于后续调用生图API。

**模型调用**：`ernie-5.0-thinking-preview`（生成图片提示词）

**1:1 方图 (1024×1024)**：
- 社媒方图，朋友圈/Instagram
- 文字占据70%画布
- 背景纹理作为辅助

**9:16 竖版长图 (1024×1820)**：
- 微博/小红书/Story
- 充足行间距
- 底部元数据标注

**图片生成提示词结构**：
```
A [aspect_ratio] poster, [dominant_color] background, [secondary_color] accent,
[font_weight] Chinese typography as the dominant visual element,
[landscape_base] as subtle background texture,
minimalist layout, high contrast, editorial quality,
2026 FIFA World Cup atmosphere
```

### Step 10 — 最终多模态交付 (MultiModal_Publisher)

聚合所有步骤输出，调用生图API生成最终图片，组装结构化交付包。

**模型调用**：`ernie-image-turbo`（目标生图模型）

**API 调用方式 (OpenAI SDK)**：
```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://aistudio.baidu.com/llm/lmapi/v3",
)

response = client.images.generate(
    model="ernie-image-turbo",
    prompt="图片描述提示词",
    n=1,
    response_format="url",  # 或 "b64_json"
    size="1024x1024",
    extra_body={
        "seed": 42,
        "use_pe": True,
        "num_inference_steps": 8,
        "guidance_scale": 1.0
    }
)

# 获取图片 URL
image_url = response.data[0].url

# 或保存 base64 图片
if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
    image_bytes = base64.b64decode(response.data[0].b64_json)
    with open("output.png", "wb") as f:
        f.write(image_bytes)
```

**图片生成参数说明**：

| 参数 | 类型 | 说明 | 推荐值 |
|------|------|------|--------|
| `model` | string | 模型名称 | `ernie-image-turbo` |
| `prompt` | string | 图片描述提示词 | 来自 Step 9 的提示词 |
| `n` | integer | 生成图片数量 (1-4) | `1` |
| `response_format` | string | 返回格式 | `url` 或 `b64_json` |
| `size` | string | 图片尺寸 | 见下方支持列表 |
| `seed` | integer | 随机种子 | `42` |
| `use_pe` | boolean | 使用 Prompt Enhancement | `true` |
| `num_inference_steps` | integer | 推理步数 | `8` |
| `guidance_scale` | float | 引导系数 | `1.0` |

**支持的图片尺寸**：
- `1024x1024` - 方图 (1:1)
- `1376x768` - 横版 (16:9)
- `1264x848` - 横版 (3:2)
- `1200x896` - 横版 (4:3)
- `896x1200` - 竖版 (3:4)
- `848x1264` - 竖版 (2:3)
- `768x1376` - 竖版 (9:16)
- `1024x1820` - 长图 (9:16)

**最终输出格式**：
```json
{
  "novel_text": "微小说正文",
  "word_count": 字数,
  "image_1x1_url_or_base64": "方图URL或Base64",
  "image_9x16_url_or_base64": "长图URL或Base64",
  "provenance_metadata": {
    "match_source": "事实来源",
    "retrieval_timestamp": "检索时间戳",
    "confidence_summary": "置信度摘要"
  },
  "quality_status": "passed/degraded",
  "pipeline_summary": {
    "persona_drift_sigma": 值,
    "emotion_arc_fit": 值,
    "audit_pass": true/false,
    "total_iterations": 迭代次数
  }
}
```

---

## 质量控制机制

### Reflexion 闭环

| 评估维度 | 阈值 | 不通过处理 |
|---------|------|-----------|
| 人设漂移 σ | ≤ 0.30 | 变异 `tone_anchor` 参数后回流 Step 5 |
| 情绪弧线拟合度 | ≥ 0.70 | 调整三幕字数分配后回流 Step 5 |
| 字数达标 | ≤ 300字 | 压缩 Act 2 后回流 Step 5 |
| **最大重试次数** | **3次** | 超限触发熔断，`quality_status: "degraded"` |

### 错误处理

| HTTP状态码 | 含义 | 处理策略 |
|------------|------|---------|
| `401` | API Key 无效 | 中止，提示检查密钥 |
| `429` | 限流 | 指数退避重试：1s → 4s → 16s，最多3次 |
| `5xx` | 服务端错误 | 指数退避重试3次，失败后降级 |

---

## 输出规范

| 产物 | 规格 | 用途 |
|------|------|------|
| 微小说正文 | ≤300字中文 | 社媒文案 |
| 1:1 方图 | 1024×1024 | 朋友圈 / Instagram |
| 9:16 竖版长图 | 1024×1820 | 微博 / 小红书 / Story |
| 溯源元数据 | JSON | 内容审核 / 存档 |
| 质量状态标记 | `passed` / `degraded` | 发布决策参考 |

---

## 使用示例

**用户输入**：
```
为梅西在2026世界杯的绝杀进球写一个平行宇宙故事，情绪强度9
```

**三元组解析**：
```json
{
  "entity": "梅西",
  "event_type": "绝杀进球",
  "emotion_intensity": 9
}
```

**执行流程**：
1. 解析三元组 → conflict_archetype: `silent_redemption`, psyche_mode: `transcendent`
2. 锁定契约 → pov_mode: `第一人称热血`, tone_anchor: `breathless, luminous, time-suspended`
3. 规划叙事 → pacing_target: `avalanche`, 三幕结构 80/140/80 字
4. 联网检索 → 获取赛况事实 + 达拉斯在地文化
5. 创作微小说 → 嵌入感官锚点，模糊低置信事实
6. 安全审计 → 合规检查 + 事实置信度核查
7. Reflexion自评 → σ=0.18, arc_fit=0.91, 通过
8. 视觉映射 → 深紫主色调 + 金色点缀
9. 长图渲染 → 生成方图 + 竖版长图
10. 交付成品 → 文本 + 图片 + 元数据

---

## 注意事项

1. **事实模糊化**：所有 confidence < 0.6 的事实必须虚化处理，确保输出为"有据可依的平行宇宙叙事"
2. **合规底线**：禁止政治敏感、人身攻击内容
3. **免责声明**：所有生成内容需标注"AI创意叙事，不构成新闻报道"
4. **API依赖**：需要配置 `AISTUDIO_API_KEY` 环境变量
5. **联网检索**：使用 web-access skill 执行网络搜索操作

---

> 本工具仅供创意写作与体育人文传播用途。
> 所有生成内容均为 AI 创意叙事，不构成新闻报道，请勿作为事实依据传播。