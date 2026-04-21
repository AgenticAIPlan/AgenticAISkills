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

### ⚠️ 情绪方向判断（重要）

**同一事件，不同视角的情绪方向完全相反**。例如：
- "姆巴佩帽子戏法" → 法国球迷（正向/喜悦）vs 对手球迷（负向/绝望）
- "绝杀进球" → 进球方球迷（正向/狂喜）vs 被进球方球迷（负向/心碎）

**判断流程**：
1. 用户明确说明视角 → 直接采用
2. 用户未明确视角 → **必须询问用户站在哪一方视角**
3. 拆解三元组后 → **必须让用户确认情绪方向**

**情绪方向定义**：

| 方向 | 说明 | 适用场景 |
|------|------|----------|
| `positive` | 正向情绪 | 喜悦、胜利、庆祝、骄傲、感动 |
| `negative` | 负向情绪 | 悲伤、失落、遗憾、愤怒、绝望 |

**常见事件的情绪方向参考**：

| 事件类型 | 正向视角（entity方） | 负向视角（对手方） |
|----------|---------------------|-------------------|
| 绝杀进球 | 胜利狂欢 | 心碎绝望 |
| 帽子戏法 | 英雄礼赞 | 无力回天 |
| 夺冠时刻 | 巅峰荣耀 | 遗憾落败 |
| 点球大战获胜 | 惊险晋级 | 梦碎十二码 |
| 红牌退场 | -（通常为负向） | 获得优势 |
| 小组赛出局 | -（负向） | 竞争对手淘汰 |

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
│  Step 2 │ Config_Manager   │ 锁定体裁契约 (300-500字微小说)     │
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
│  Step 5 │ Creative_Writer  │ 高质微小说创作 (300-500字)        │
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

解析三元组，提取 `conflict_archetype`（叙事冲突原型）、`psyche_mode`（心理模式）与 `emotion_direction`（情绪方向）。

#### 1.1 情绪方向判断

**⚠️ 必须首先判断情绪方向**

根据用户输入判断用户站在哪一方视角：

| 判断依据 | 示例 | 情绪方向 |
|----------|------|----------|
| 用户明确表达支持方 | "我们赢了！"、"法国队帽子戏法太牛了" | 正向 |
| 用户明确表达对立面 | "被绝杀了，心碎"、"我们的点球输了" | 负向 |
| 用户使用第一人称关联 entity | "梅西的绝杀"（用户是梅西球迷） | 正向 |
| 用户未明确视角 | "姆巴佩帽子戏法写个故事" | **需询问** |

**询问用户示例**：

> 您提到「姆巴佩帽子戏法」，请问您是站在哪一方视角来创作？
>
> 1. **法国队/姆巴佩球迷视角** → 正向情绪（英雄礼赞、胜利狂欢）
> 2. **对手球队球迷视角** → 负向情绪（无力回天、绝望心碎）
>
> 请告诉我您的视角，我将为您创作相应的叙事。

#### 1.2 冲突原型与心理模式提取

**模型调用**：`ernie-5.0-thinking-preview`

**冲突原型类型**（需结合情绪方向）：

| 情绪方向 | 正向冲突原型 | 负向冲突原型 |
|----------|-------------|-------------|
| positive | `hero_rises`（英雄崛起） | - |
| positive | `last_stand`（最后一战·胜利） | - |
| positive | `underdog_rises`（黑马崛起） | - |
| negative | - | `hero_falls`（英雄迟暮） |
| negative | - | `bitter_betrayal`（苦涩背叛） |
| negative | - | `silent_defeat`（无声落败） |
| 双向 | `silent_redemption`（无声救赎） | `silent_redemption`（无声救赎） |

**心理模式类型**（需结合情绪方向）：

| 情绪方向 | 正向心理模式 | 负向心理模式 |
|----------|-------------|-------------|
| positive | `volcanic`（火山爆发式） | - |
| positive | `triumphant`（凯旋式） | - |
| positive | `transcendent`（超然升华式） | - |
| negative | - | `melancholic`（忧郁沉思式） |
| negative | - | `numb`（麻木疏离式） |
| negative | - | `defiant`（抗争不屈式） |

#### 1.3 用户确认

**⚠️ 拆解三元组后，必须让用户确认**

**确认内容展示**：

> **三元组拆解结果确认**
>
> | 字段 | 值 |
> |------|-----|
> | 核心角色 | 姆巴佩 |
> | 事件类型 | 帽子戏法 |
> | 情绪强度 | 8 |
> | 情绪方向 | 正向（法国队球迷视角） |
> | 冲突原型 | hero_rises（英雄崛起） |
> | 心理模式 | volcanic（火山爆发式） |
>
> 请确认以上拆解是否正确？
> - 确认 → 继续执行
> - 需要调整 → 请告诉我需要修改的内容

#### 1.4 输出格式

```json
{
  "entity": "球员/球队名",
  "event_type": "事件类型",
  "emotion_intensity": 0-10,
  "emotion_direction": "positive/negative",
  "conflict_archetype": "冲突原型",
  "psyche_mode": "心理模式",
  "user_perspective": "用户视角说明"
}
```

### Step 2 — 体裁契约锁定 (Config_Manager)

确认输出契约：体裁为社媒微小说，篇幅300-500字，锁定叙事约束参数。

**模型调用**：`ernie-5.0-thinking-preview`

**输出格式**：
```json
{
  "genre": "社媒微小说",
  "length_limit": {"min": 300, "max": 500},
  "pov_mode": "视角模式",
  "forbidden_patterns": ["禁止模式列表"],
  "tone_anchor": "英文基调描述短语"
}
```

**禁止模式**：
- 政治敏感表述、可能引起争议的政治或宗教相关意象
- 真实球员负面人身攻击
- 未经证实的伤情细节
- 低俗、违法或不符合公序良俗的内容
- 近现代名人肖像（已确认出现在微小说正文中的球员除外）

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
1. 严格控制在300-500字
2. 精确遵循 pov_mode 视角
3. **必须体现 `emotion_direction`（正向/负向情绪）**
4. 至少嵌入2个 sensory_anchors
5. confidence_score < 0.6 的事实必须模糊化处理
6. 遵守三幕字数分配
7. 绝不使用 forbidden_patterns
8. **严禁使用以下内容**：
   - 可能引起争议的政治、宗教相关意象
   - 低俗、违法或不符合公序良俗的内容
   - 近现代名人肖像（三元组中确认的球员除外）

#### 微小说高质方法论

创作时必须遵循以下8项高质标准，确保微小说品质：

**1. 叙事创新性**
- 在经典叙事模式下有新颖变量或独特视角
- 避免套路化表达，如"他是传奇"等空洞描述
- **正向示例**："这不是一个进球——这是一个时代的加冕"（将进球升华为时代符号）
- **负向示例**："他踢进了一个漂亮的球，大家都为他欢呼"（平淡无奇）

**2. 剧情紧凑度**
- 无冗余铺垫，每句话都推动叙事
- 起承转合完整：开篇抛出钩子 → 冲突直接爆发 → 无断层推进 → 结尾留余韵
- **正向示例**：开篇即入高潮情境，结尾留有回味的金句
- **负向示例**：大段背景介绍，结尾仓促收场

**3. 核心主题明确**
- 主题清晰（如：英雄迟暮、绝地反击、悲情救赎、荣耀加冕等）
- 情感内核有共鸣点，传递普世价值
- **正向示例**：39岁最后一战 → 主题"传奇的完整句号"
- **负向示例**：只有事件描述，没有情感内核

**4. 情感浓度**
- 有精心设计的情感爆发点
- 情绪张弛有度，非单一情绪曲线
- **正向示例**：从紧张 → 爆发 → 释放 → 余韵，情绪有层次
- **负向示例**：全篇同一种情绪，无起伏

**5. 悬念与张力**
- 开篇设置悬念钩子或结尾留有反转
- 冲突合乎逻辑，真实自然
- **正向示例**："我听见自己的心跳"（制造紧张感）→ 结尾"这是活着的味道"（反转升华）
- **负向示例**：平铺直叙，无悬念设计

**6. 人物辨识度**
- 核心人物性格鲜明，无模糊感
- 人物行为符合人设和现实常理
- **正向示例**：通过细节动作展现人物（"跪倒在草地上"展现疲惫与释然）
- **负向示例**：人物行为突兀，为推进剧情而降智

**7. 语言精炼度**
- 台词/叙述直白精炼，冲击力强
- 无冗余长句、无过度形容词
- 有"金句"潜质的句子，利于传播
- **正向示例**："十二码的距离，却隔着整整一个时代"（精炼有张力）
- **负向示例**："这是一个非常非常重要的时刻，他的心情非常复杂..."（冗余无力）

**8. 真实感与共情**
- 对话/叙述真实自然，符合人物身份
- 能触发读者共通情绪，产生"他/她就是我"的代入感
- **正向示例**："眼泪流进嘴里。咸的。"（感官细节触发共情）
- **负向示例**：生硬说教、脱离现实的台词

**情绪方向创作指南**：

| 情绪方向 | 叙事基调 | 感官锚点示例 | 关键词 |
|----------|---------|-------------|--------|
| positive（正向） | 胜利、喜悦、荣耀、骄傲 | 金色光芒、欢呼声、香槟味道 | 狂喜、巅峰、永恒、传奇 |
| negative（负向） | 失落、遗憾、悲壮、心碎 | 雨滴、沉默、灰色天空 | 沉默、离别、最后一眼、遗憾 |

**正向情绪示例**：
> "金色雨从天而降，我听见九万人的咆哮化成一首歌。这不是一个进球——这是一个时代的加冕..."

**负向情绪示例**：
> "雨还在下。我听见自己的心跳，和看台上那片沉默融为一体。十二码的距离，却隔着整整一个时代..."

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
  "fuzzified_facts": ["模糊化处理的事实"],
  "quality_checklist": {
    "narrative_innovation": true/false,
    "plot_compactness": true/false,
    "theme_clarity": true/false,
    "emotional_intensity": true/false,
    "suspension_tension": true/false,
    "character_distinctiveness": true/false,
    "language_precision": true/false,
    "empathy_realism": true/false
  }
}
```

### Step 6 — 安全与置信度审计 (Safety_Guard)

并行执行内容合规审查与事实置信度核查。

**模型调用**：`ernie-5.0-thinking-preview`

**审计维度**：
- `compliance_pass` - 合规是否通过
- `forbidden_content_check` - 禁止内容检查（政治/宗教争议意象、低俗违法内容、近现代名人肖像）
- `fact_confidence_pass` - 事实置信度是否通过
- `overall_pass` - 整体是否通过

**输出格式**：
```json
{
  "compliance_pass": true/false,
  "compliance_issues": ["问题列表"],
  "forbidden_content_check": true/false,
  "forbidden_content_found": ["发现的禁止内容"],
  "fact_confidence_pass": true/false,
  "unfuzzified_risks": ["未模糊化风险"],
  "overall_pass": true/false,
  "audit_note": "审计摘要"
}
```

### Step 7 — Reflexion 闭环自评 (Reflexion_Critic)

对小说进行多维自评，任一核心维度不通过则回流 Step 5。

**模型调用**：`ernie-5.0-thinking-preview`

**硬性门槛**（必须通过，不纳入评分）：
- 字数达标：300-500字，不通过则调整后回流

**高质方法论校验维度**（按重要性权重）：

| 维度 | 权重 | 评分标准 | 不通过处理 |
|------|------|---------|-----------|
| 叙事创新性 | 15% | 是否有新颖变量或独特视角，避免套路化 | 提示创新方向后回流 |
| 剧情紧凑度 | 20% | 是否无冗余铺垫，起承转合完整 | 删减冗余后回流 |
| 核心主题明确 | 15% | 主题是否清晰，情感内核是否有共鸣 | 明确主题后回流 |
| 情感层次 | 15% | 情绪弧线是否完整，情感浓度是否足够，有无层次起伏 | 调整情绪曲线后回流 |
| 悬念与张力 | 10% | 开篇/结尾是否有悬念设计，冲突是否合乎逻辑 | 增加悬念钩子后回流 |
| 人物一致性 | 15% | 人物性格是否鲜明，行为是否符合人设，无突兀反转 | 调整人物细节后回流 |
| 语言精炼度 | 5% | 是否有金句，是否无冗余长句 | 精简语言后回流 |
| 真实感与共情 | 5% | 是否真实自然，能否触发共情 | 增加感官细节后回流 |

**高质评分计算**：
```
quality_score = Σ (维度评分 × 权重)
```
- `quality_score ≥ 0.75` → 通过
- `0.60 ≤ quality_score < 0.75` → 需改进后回流
- `quality_score < 0.60` → 熔断，标记 `quality_status: "degraded"`

**熔断规则**：最多重试3次，超限则标记 `quality_status: "degraded"` 直通 Step 8。

**输出格式**：
```json
{
  "word_count_ok": true/false,
  "quality_score": 0.0-1.0,
  "quality_breakdown": {
    "narrative_innovation": 0.0-1.0,
    "plot_compactness": 0.0-1.0,
    "theme_clarity": 0.0-1.0,
    "emotional_depth": 0.0-1.0,
    "suspension_tension": 0.0-1.0,
    "character_consistency": 0.0-1.0,
    "language_precision": 0.0-1.0,
    "empathy_realism": 0.0-1.0
  },
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

**重要提示**：
- `ernie-image-turbo` 对中文理解能力更强，**所有图片提示词必须使用中文撰写**
- 图片必须**能体现出核心事件**（如"绝杀进球"、"点球大战失利"、"帽子戏法"等），通过视觉元素传达事件性质
- ⚠️ **文生图模型无法精确渲染文字**，微小说原文文字将在 Step 10 通过代码叠加到图片上

**参考文档**：撰写提示词时请参考 [image_prompt_guide.md](references/image_prompt_guide.md)，确保提示词清晰、优质、符合文生图最佳实践。

#### 图片高质方法论

生成图片提示词时必须遵循以下6项高质标准：

**1. 场景辨识度**
- 每个核心场景具备独特的视觉基调，能让观众在3秒内识别场景功能
- 场景布局打破陈规，在常规场景中加入具有设计感的视觉锚点
- **正向示例**：深紫色渐变背景+金色光芒洒落（独特视觉基调）
- **负向示例**：普通体育场照片（缺乏辨识度）

**2. 场景叙事功能**
- 场景设计不仅是背景，需具备推动叙事的功能或暗示人物处境
- 通过空间结构传达情绪氛围
- **正向示例**：空旷球门+孤独背影暗示失利与孤独
- **负向示例**：场景与事件/情绪无关联

**3. 视觉构图简洁**
- 画面构图简洁有力，剔除干扰剧情表达的冗余元素
- 核心信息始终处于视觉焦点
- **正向示例**：画面中央呈现球员剪影，背景虚化
- **负向示例**：画面元素过多，视觉焦点分散

**4. 情绪色彩统一**
- 全图色调风格保持高度统一，通过色相传达情感倾向
- 主色调与情绪方向匹配（正向→暖色/金色，负向→冷色/灰暗）
- **正向示例**：正向情绪用深红/金色，负向情绪用灰蓝/银白
- **负向示例**：色彩与情绪方向冲突

**5. 视觉钩子设计**
- 图片具有冲击力的视觉元素，形成强烈的视觉留存
- 包含利于传播的"高光时刻"或名场面
- **正向示例**：金色光芒喷涌、球员剪影双臂张开
- **负向示例**：平淡无奇，无记忆点

**6. 光影层次丰富**
- 利用明暗对比塑造氛围或烘托情绪
- 关键区域光影设计合理，增强画面张力
- **正向示例**：聚光灯效果突出主体，背景渐暗
- **负向示例**：画面平面化，无光影层次

#### 核心事件与情绪方向视觉化

图片必须体现三元组中的 `event_type` 和 `emotion_direction`，通过视觉元素传达事件性质和情绪方向：

**正向情绪（positive）视觉元素**：

| 核心事件 | 视觉元素 | 色彩基调 |
|----------|---------|----------|
| 绝杀进球（进球方） | 球员剪影、金色光芒、胜利姿态、欢腾人群 | 深红/金色 |
| 帽子戏法（进球方） | 三颗足球、庆祝动作、聚光灯、金色数字"3" | 深紫/金色 |
| 夺冠时刻 | 举起奖杯、金色雨、国旗飘扬、烟火 | 金色/翠绿 |
| 点球大战获胜 | 拥抱庆祝、晋级横幅、惊险逃生后的狂喜 | 蓝色/金色 |

**负向情绪（negative）视觉元素**：

| 核心事件 | 视觉元素 | 色彩基调 |
|----------|---------|----------|
| 绝杀进球（被进球方） | 孤独背影、沉默的球场、黯淡灯光 | 灰蓝/暗色 |
| 帽子戏法（对手方） | 无力回天、空旷球门、绝望眼神 | 灰色/暗紫 |
| 点球大战失利 | 孤独背影、空旷球门、雨滴、点球点 | 灰蓝/银白 |
| 红牌退场 | 红色卡片、离场背影、孤独通道 | 灰色/暗红 |
| 小组赛出局 | 低头沉默、更衣室背影、空荡球场 | 灰蓝/暗色 |

**⚠️ 重要**：同一事件根据 `emotion_direction` 选择完全不同的视觉元素和色彩基调。

#### 1:1 方图 (1024×1024)
- 社媒方图，朋友圈/Instagram
- **必须体现核心事件**（通过主体意象、视觉元素）
- 背景纹理与核心事件呼应，传达情绪氛围
- 纯视觉呈现，无文字

#### 9:16 竖版长图 (1024×1820)
- 微博/小红书/Story
- **生成纯背景图片**，为后续文字叠加预留空间
- **背景需体现核心事件**（通过视觉元素暗示事件性质）
- 背景设计要求：
  - 顶部留有适当空间（便于叠加标题）
  - 中央区域相对简洁（便于叠加正文）
  - 底部保留空间标注元数据
  - 整体色调与文字形成对比（确保叠加后文字清晰可读）

**图片生成提示词结构（中文）**：

**方图提示词**：
```
一张方形海报，
[主色调]渐变背景，[辅助色]光晕点缀，
画面中央呈现[核心事件的视觉表现]，
[背景描述]，
[风格关键词]，[情绪关键词]，[核心事件关键词]，
高清，编辑品质，2026年世界杯主题
```

**长图提示词**（纯背景，不含文字）：
```
一张竖版长图海报，
[主色调]背景，[辅助色]点缀，
画面呈现[核心事件的视觉表现]作为背景，
顶部和中央区域留有简洁空间，
[背景描述]作为微妙的纹理，
[风格关键词]，[情绪关键词]，[核心事件关键词]，
高清，编辑品质，2026年世界杯主题
```

**提示词撰写要点**：
1. **核心事件视觉化**：必须包含能体现事件性质的视觉元素
2. 明确描述画面主体和背景
3. 指定色彩基调（主色、辅助色）
4. 情绪关键词（如"热血"、"诗意"、"疏离"）
5. 风格关键词（如"极简"、"editorial"、"电影感"）
6. **长图不要求嵌入文字**，文字将在 Step 10 通过代码叠加
7. **严禁使用以下内容**：
   - 可能引起争议的政治、宗教相关意象
   - 低俗、违法或不符合公序良俗的内容
   - 近现代名人肖像（三元组中确认的球员除外）

### Step 10 — 最终多模态交付 (MultiModal_Publisher)

聚合所有步骤输出，调用生图API生成图片，**叠加微小说文字**，组装结构化交付包。

**⚠️ 执行流程（必须按顺序完成）**：

```
Step 10.1: 生成方图 (1:1) ──────────────────────→ 获取 image_1x1_url
                    │
                    ▼
Step 10.1: 生成长图背景 (9:16) ─────────────────→ 获取 image_9x16_url (纯背景)
                    │
                    ▼
Step 10.2: ⚠️ 叠加文字到长图 (必须执行!) ───────→ 获取最终长图 (已叠加文字)
                    │                                    ↓
                    │                           image_9x16_final_path
                    ▼
Step 10.3: 组装最终输出 ────────────────────────→ 返回完整 JSON
```

**⚠️ 关键提醒**：
- **Step 10.2 不可跳过**：长图生成后必须执行文字叠加，否则长图只是纯背景图，不完整
- **文字颜色必须正确**：根据 Step 8 的 `dominant_color_hex` 自动判断使用白色或黑色文字
- **验证输出**：确认最终长图文件存在且文字清晰可读

#### 10.1 图片生成

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
```

#### 10.2 文字叠加（长图专用）⚠️ 必须执行

**⚠️ 此步骤不可遗漏！长图必须叠加文字才算完成。**

文生图模型无法精确渲染文字，需通过代码在生成的图片上叠加微小说原文。

**执行检查清单**（执行前必须确认）：
- [ ] 已获取长图背景图片 URL
- [ ] 已准备好微小说原文（`novel_text`）
- [ ] 已确定背景主色调（来自 Step 8 的 `dominant_color_hex`）
- [ ] 已选择与背景形成高对比的文字颜色

**文字颜色选择规则**（根据背景色调自动判断）：

| 背景主色调 | 文字颜色 | RGB 值 | 判断逻辑 |
|-----------|---------|--------|---------|
| 深色（深红、深紫、深蓝、灰蓝等） | 白色 | `(255, 255, 255)` | 背景亮度 < 128 |
| 浅色（白、淡黄、淡蓝等） | 黑色 | `(0, 0, 0)` | 背景亮度 ≥ 128 |
| 不确定时 | 白色带描边 | 白色文字 + 黑色描边 | 确保可读性 |

**完整代码示例（直接执行）**：

```python
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap

def calculate_brightness(hex_color: str) -> float:
    """计算颜色亮度（0-255）"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (r * 299 + g * 587 + b * 114) / 1000

def overlay_text_on_image(
    image_url: str,
    novel_text: str,
    dominant_color_hex: str,
    output_path: str = "/tmp/final_9x16.png"
) -> str:
    """
    在生成的长图上叠加微小说文字

    ⚠️ 此函数必须执行，不可跳过

    Args:
        image_url: 生成的背景图片URL
        novel_text: 微小说原文（300-500字）
        dominant_color_hex: 背景主色调（来自Step 8，如 "#1a1a2e"）
        output_path: 输出图片路径

    Returns:
        输出图片路径
    """
    # 1. 下载背景图片
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(img)

    # 2. 根据背景亮度自动选择文字颜色
    brightness = calculate_brightness(dominant_color_hex)
    text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)

    # 3. 字体设置（优先使用系统可用字体）
    font_size = 24
    line_height = int(font_size * 1.8)  # 行间距
    margin = 50

    # 尝试多种中文字体路径
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",  # macOS 备选
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux 备选
        "/Windows/Fonts/msyh.ttc",  # Windows 微软雅黑
        "NotoSansSC-Regular.otf",  # 当前目录
    ]

    font = None
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except:
            continue

    if font is None:
        # 降级使用默认字体
        font = ImageFont.load_default()
        print("警告：未找到中文字体，使用默认字体")

    # 4. 自动换行处理（每行约25个中文字符）
    chars_per_line = 25
    lines = textwrap.wrap(novel_text, width=chars_per_line)

    # 5. 绘制文字
    y_position = margin
    for line in lines:
        draw.text((margin, y_position), line, font=font, fill=text_color)
        y_position += line_height

    # 6. 保存结果
    img.save(output_path)
    print(f"✅ 文字叠加完成，已保存至: {output_path}")
    print(f"   - 背景亮度: {brightness:.1f}")
    print(f"   - 文字颜色: {'白色' if text_color == (255, 255, 255) else '黑色'}")
    print(f"   - 总行数: {len(lines)}")

    return output_path

# 执行示例
# final_image_path = overlay_text_on_image(
#     image_url="生成的图片URL",
#     novel_text="微小说正文...",
#     dominant_color_hex="#1a1a2e"  # 来自 Step 8
# )
```

**执行后验证**：
- [ ] 检查输出文件是否存在
- [ ] 确认文字清晰可读
- [ ] 确认文字颜色与背景形成足够对比
- [ ] 确认排版整齐，无文字溢出

**常见问题修复**：

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 文字不可见 | 颜色与背景相近 | 切换文字颜色（白↔黑）或添加描边 |
| 文字溢出 | 字号过大或行数过多 | 减小字号至 20px 或增加每行字符数 |
| 字体缺失 | 系统无指定字体 | 使用上述代码中的字体路径列表 |
| 排版混乱 | 未正确换行 | 使用 `textwrap.wrap()` 确保自动换行 |

**文字叠加参数标准值**：

| 参数 | 标准值 | 说明 |
|------|--------|------|
| 字体 | 思源黑体 / PingFang SC | 清晰易读的中文字体 |
| 字号 | 24px | 300-500字篇幅最佳 |
| 行间距 | 1.8倍字号 | 阅读舒适 |
| 文字颜色 | 自动判断 | 根据背景亮度选择白/黑 |
| 边距 | 50px | 四周留白 |
| 每行字符 | 25个中文字 | 确保排版整齐 |

#### 10.3 最终输出

**⚠️ 输出前必须确认**：
- [ ] 方图（1:1）已生成（纯视觉，无文字）
- [ ] 长图（9:16）**已完成文字叠加**（不是纯背景图！）
- [ ] 文字叠加文件路径已记录

**最终输出格式**：
```json
{
  "novel_text": "微小说正文",
  "word_count": 字数,
  "image_1x1_url": "方图URL（纯视觉）",
  "image_9x16_url": "长图背景URL（生成原始图）",
  "image_9x16_final_path": "长图最终路径（已叠加文字，如 /tmp/final_9x16.png）",
  "text_overlay_completed": true,
  "text_color_used": "white/black",
  "provenance_metadata": {
    "match_source": "事实来源",
    "retrieval_timestamp": "检索时间戳",
    "confidence_summary": "置信度摘要"
  },
  "quality_status": "passed/degraded",
  "disclaimer": "AI创意叙事，不构成新闻报道"
}
```

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
| 字数达标 | 300-500字 | 调整字数后回流 Step 5 |
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
| 微小说正文 | 300-500字中文 | 社媒文案 |
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