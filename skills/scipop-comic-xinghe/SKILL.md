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
| [references/script_writing_guide.md](references/script_writing_guide.md) | 脚本撰写指南（叙事框架与质量校验） |
| [references/ernie_image_prompt_guide.md](references/ernie_image_prompt_guide.md) | ERNIE-Image 提示词撰写指南 |
| [references/style_guide.md](references/style_guide.md) | 连环画风格设计指南 |

---

## ⚠️ 内容安全规范

> **重要**：在生成脚本和图像时，必须严格遵守以下内容安全规范，确保输出内容合法、合规、健康。

### 禁止内容类型

| 禁止类型 | 说明 | 示例 |
|---------|------|------|
| **政治相关意象** | 避免使用可能引起政治争议的符号、场景、人物 | 政治人物形象、政治标语、敏感地图、政治事件场景 |
| **宗教相关意象** | 避免使用宗教符号、宗教人物、宗教场所 | 宗教十字架、佛像、清真寺、宗教仪式场景 |
| **低俗/违法意象** | 严禁使用任何低俗、暴力、违法内容 | 暴力血腥、性暗示、毒品、犯罪行为 |
| **近现代名人肖像** | 不得使用文章中未提及的近现代名人肖像 | 非科普文章主角的当代政治家、明星、企业家肖像 |

### 名人肖像处理规则

```
✅ 允许：
- 文章中明确提及的科学家的肖像（如爱因斯坦、居里夫人等）
- 已故历史人物（如古代科学家、发明家）
- 使用概括性描述代替具体肖像（如"一位科学家"而非特定人物）

❌ 禁止：
- 文章未提及的当代政治人物肖像
- 文章未提及的明星、网红肖像
- 文章未提及的企业家、商业人物肖像
```

### 安全替代方案

| 禁止内容 | 安全替代方案 |
|---------|-------------|
| 政治人物形象 | 使用概括性职业形象（如"一位政府工作人员"） |
| 宗教符号 | 使用科学符号或中性装饰元素 |
| 当代名人肖像 | 使用背影、剪影或虚构角色 |
| 暴力场景 | 使用比喻或抽象表达（如用箭头表示对抗） |

### 违规内容检测

在 Phase 1 解析文章时，系统会自动检测以下违规内容：

1. **image_prompt 违规检测**：检查是否包含禁止词汇
2. **fact_check 合规审查**：确保关键信息不涉及敏感内容
3. **人物身份核实**：确认人物是否在文章中被提及

若检测到违规内容，将拒绝生成并提示用户修改。

---

## 工作流程

### Phase 1: 文章解析与 Prompt 建模

**目标**: 将科普文章拆解为 4-6 个视觉场景，生成风格一致的图像 Prompt。

> 📖 详细规范参见 [references/article_analysis_prompts.md](references/article_analysis_prompts.md)

#### 提示词结构规范

**系统提示词模板**:

```
你是一位科普连环画脚本编写专家。分析文章并根据内容的丰富程度和结构确定最合适的 Panel 数量（4-6个）。

## 输出格式
输出一个 JSON 对象，包含以下字段：
- "recommended_panels"：整数（4-6）
- "recommendation_reason"：一句话中文解释
- "style_seed"：简短的中文风格描述
- "key_facts"：关键信息汇总
- "panels"：Panel 数组

## ⚠️ panels 数组字段要求（每个 Panel 必须包含以下5个字段，缺一不可）

| 字段名 | 类型 | 要求 |
|-------|------|------|
| "id" | 整数 | Panel 编号，从1开始递增 |
| "scene" | 字符串 | 中文场景描述，包含主体、动作、环境、情绪 |
| "caption" | 字符串 | 中文科普旁白，20字以内，简洁有力 |
| "image_prompt" | 字符串 | 中文图像生成提示，100-200字，必须详细描述所有元素 |
| "fact_check" | 字符串 | 本画面涉及的关键事实（人物、时间、地点、数据等） |

## 叙事框架要求（钩子-解释与案例-结论与展望）
- Panel 1（钩子）：必须有视觉吸引力，能引发好奇心
- Panel 2 ~ N-1（解释与案例）：每个 Panel 只承载一个核心概念，逻辑递进
- Panel N（结论与展望）：回应开篇，有情感或价值升华

## ⚠️ image_prompt 撰写核心要求（必须严格遵守）

### 1. 必须严格遵循 scene 字段的场景设计
scene 字段描述了画面的核心内容，image_prompt 必须完整还原 scene 中的所有元素：
- 主体人物：姓名、外貌、服饰、动作
- 环境背景：地点、时间、氛围
- 关键道具：屏幕内容、标语、文件等

### 2. 关键信息必须完整体现在 image_prompt 中

| 信息类型 | 要求 | 示例 |
|---------|------|------|
| **具体数字** | 必须原样写出，不可省略 | "5500万光年"、"一年有期徒刑"、"1000元罚金" |
| **具体文字** | 必须用引号标明，写明"清晰显示XX字样" | 手机屏幕清晰显示"差评"二字 |
| **法条编号** | 必须写出具体编号和内容 | 刑法第221条"损害商业信誉、商品声誉罪" |
| **专有名词** | 必须使用原文，不可意译或简化 | "事件视界望远镜(EHT)" |

### 3. 文字内容显示规范
画面中需要显示文字时，必须明确写出：
- "屏幕/标语/文件上清晰显示'具体文字内容'"
- 重要文字用引号标明，不可模糊描述如"显示XX内容"

### 4. image_prompt 长度要求
- 最少 100 字，最多 200 字
- 每个关键元素都要有详细描述
- 避免模糊表述，使用具体描述

## 关键信息保留检查清单（生成每个 Panel 时必须核对）
□ 是否保留了文章中的关键数字？（年份、数量、金额、刑期等）
□ 是否准确使用了人物姓名和身份？
□ 是否保留了专有名词和科学术语的原文？
□ 时间、地点是否与文章记载一致？
□ scene 中的所有元素是否都在 image_prompt 中体现？
□ 需要显示的文字内容是否明确写出？（如标语、法条、判决结果等）

## 高质方法论检查清单（确保脚本质量）

### 1. 叙事吸引力
□ Panel 1 是否能在"第一眼"抓住注意力？（黄金开篇）
□ Panel 之间是否有悬念或因果驱动？（悬念留白）
□ 叙事节奏是否有起伏变化？（情绪起伏）
□ 是否有打破预期的元素？（认知反差）

### 2. 逻辑层次感
□ Panel 是否按照起承转合的逻辑排列？
□ 每格与前后格是否有明确的因果或递进关系？
□ 信息难度是否逐层深入？
□ Panel 之间过渡是否自然？

### 3. 内容准确性
□ 关键数字是否与原文一致？
□ 专业术语和法条编号是否准确？
□ 人物信息是否与原文一致？

### 4. 画面可绘性
□ image_prompt 是否描述了具体的人物或物体？
□ 动作是否足够具体，可以被画出来？
□ 环境背景是否有足够的细节？
□ 是否有明确可辨识的视觉元素？

### 5. 风格一致性
□ 所有 Panel 是否使用相同的画风描述？
□ 同一人物在不同格中形象是否一致？

仅输出原始 JSON，不要使用 markdown 代码块。
```

> 📖 详细的关键信息保留规范参见 [references/article_analysis_prompts.md](references/article_analysis_prompts.md#关键信息保留与事实核对)

**image_prompt 撰写规范**（详见 [references/ernie_image_prompt_guide.md](references/ernie_image_prompt_guide.md)）：

```
{主体特征详细描述}，{具体动作姿态}，{环境背景细节}，{关键道具/文字内容}，{细节元素}，{风格关键词}
```

**对比示例**（展示如何写出高质量的 image_prompt）：

| 场景 | ❌ 问题示例 | ✅ 正确示例 |
|-----|-----------|-----------|
| 显示屏幕内容 | 手机屏幕显示差评内容 | 手机屏幕清晰显示"差评"二字 |
| 显示法条 | 电子屏显示刑法条文，红色高亮刑期 | 电子屏清晰显示刑法第221条"损害商业信誉、商品声誉罪，处二年以下有期徒刑"，刑期数字用红色大字体高亮 |
| 显示标语 | 标语清晰 | 餐厅入口上方挂着金色立体大字标语"金杯银杯不如老百姓口碑" |
| 显示判决结果 | 判决书标注数字 | 判决书上清晰标注"一年有期徒刑""1000元罚金" |

**完整示例**：

```
❌ 问题版本（太简略，缺少关键信息）：
餐厅内景，王五坐在桌前举手机，屏幕显示差评内容，服务员持菜单站旁神情严肃，背景顾客抬头注视，暖光吊灯下氛围紧张，写实漫画风格

✅ 正确版本（详细，关键信息完整）：
餐厅内景，王五坐在桌前举着手机，手机屏幕清晰显示"差评"二字，服务员穿着制服手持菜单站在桌旁神情严肃，背景中其他顾客纷纷抬头看向王五，暖光吊灯下氛围紧张，写实漫画风格，清晰轮廓
```

**另一个示例**：

```
❌ 问题版本（法条信息缺失）：
法庭场景，法官敲锤，电子屏显示刑法条文，红色高亮刑期部分，背景简化法庭元素，写实漫画风格

✅ 正确版本（法条编号和内容完整）：
法庭场景，法官敲法槌，前方电子屏清晰显示刑法第221条"损害商业信誉、商品声誉罪，处二年以下有期徒刑"和第246条"侮辱罪、诽谤罪，处三年以下有期徒刑"，刑期数字用红色大字体高亮突出，背景简化，写实漫画风格，清晰轮廓
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
3. 执行 Phase 1b 脚本校验（吸引力、清晰度、优质度）
4. 向用户展示推荐的 Panel 数量、校验结果及理由，获取确认

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

| 字段 | 必填 | 说明 |
|-----|------|------|
| `id` | ✅ | Panel 编号（从 1 开始），整数类型 |
| `scene` | ✅ | **场景描述**，中文，用于理解上下文 |
| `caption` | ✅ | **科普旁白**，中文，20字以内，简洁有力，用于展示在图像中或作为配文 |
| `image_prompt` | ✅ | **图像生成提示词**，中文，80-150字，包含主体、动作、环境、细节、风格 |
| `fact_check` | ✅ | **关键事实核对**，记录本画面涉及的数字、人物、时间等关键信息，确保准确性 |
| `key_facts` | ✅ | **全局关键信息**，汇总文章中的关键数字、名称、地点等，用于整体核对 |

> ⚠️ **重要**：以上字段均为必填，Agent 生成脚本时必须确保每个 Panel 包含所有 5 个字段（id、scene、caption、image_prompt、fact_check），不得遗漏。

**用户确认**: 向用户展示完整脚本，包含以下内容：

```
📋 连环画脚本预览

推荐 Panel 数量：{recommended_panels} 格
理由：{recommendation_reason}
风格：{style_seed}

--- Panels 内容 ---

Panel 1:
• 场景：{scene}
• 旁白：{caption}
• 图像提示：{image_prompt}
• 事实核对：{fact_check}

Panel 2:
...

--- 关键信息 ---
{key_facts 摘要}

---
是否接受此脚本？
[接受] [重新生成] [调整 Panel 数量]
```

> ⚠️ **重要**：输出给用户确认的脚本必须包含每个 Panel 的完整 5 个字段（id、scene、caption、image_prompt、fact_check），不得省略任何字段。用户需要看到完整信息才能做出确认决定。

---

### Phase 1b: 脚本内容校验

> 📖 详细规范参见 [references/script_writing_guide.md](references/script_writing_guide.md)

**目标**: 对生成的脚本进行质量校验，确保有吸引力、清晰、优质，通过后再进入用户确认环节。

#### ⚠️ 字段完整性校验（第一道检查）

**每个 Panel 必须包含以下 5 个字段，缺一不可**：

| 字段 | 类型 | 必填 | 校验规则 |
|-----|------|------|---------|
| `id` | 整数 | ✅ | 从 1 开始递增，无缺失 |
| `scene` | 字符串 | ✅ | 非空，包含主体、动作、环境描述 |
| `caption` | 字符串 | ✅ | 非空，20 字以内 |
| `image_prompt` | 字符串 | ✅ | 非空，80-150 字，包含主体、动作、环境、细节、风格 |
| `fact_check` | 字符串 | ✅ | 非空，记录关键事实 |

**字段完整性检查清单**：

```
□ 每个 Panel 是否都有 id 字段？
□ 每个 Panel 是否都有 scene 字段？
□ 每个 Panel 是否都有 caption 字段？
□ 每个 Panel 是否都有 image_prompt 字段？
□ 每个 Panel 是否都有 fact_check 字段？
□ 字段值是否非空？
```

**字段缺失处理**：

| 缺失情况 | 处理方式 |
|---------|---------|
| 缺少任意字段 | 拒绝脚本，要求重新生成 |
| 字段值为空 | 补充默认值或重新生成 |
| 字段类型错误 | 自动转换或要求重新生成 |

> ⚠️ **重要**：字段完整性校验不通过时，不进行后续的吸引力/清晰度/优质度评估，直接要求重新生成。

#### 叙事框架要求

脚本设计应遵循"**钩子-解释与案例-结论与展望**"的叙事逻辑：

| Panel | 功能 | 设计要点 |
|-------|------|---------|
| **Panel 1** | **钩子（Hook）** | 视觉冲击、情感共鸣、问题引入、悬念设置 |
| **Panel 2 ~ N-1** | **解释与案例** | 一图一义、逻辑递进、抽象可视化、案例支撑 |
| **Panel N** | **结论与展望** | 回应开篇、升华意义、启发思考、情感落点 |

#### 校验维度

| 维度 | 评估问题 | 评分标准 |
|-----|---------|---------|
| **吸引力** | 开篇是否抓人？叙事是否有起伏？ | 优秀/良好/一般/较差 |
| **清晰度** | 一图一义？逻辑连贯？无信息过载？ | 优秀/良好/一般/较差 |
| **优质度** | 科学准确？视觉可绘？收尾升华？ | 优秀/良好/一般/较差 |

#### 高质方法论（连环画脚本质量标准）

以下五大方法论是评判连环画脚本质量的核心标准，Agent 在生成脚本和校验脚本时必须遵循：

##### 1. 叙事吸引力（原"情节吸引力设计"）

**核心原则**：通过"钩子"构建叙事张力，利用认知反差和情绪起伏驱动读者持续阅读。

**连环画适配标准**：

| 技巧 | 说明 | 连环画应用 |
|-----|------|----------|
| **黄金开篇** | Panel 1 必须在"第一眼"抓住注意力 | 使用视觉冲击、悬念问题、反差场景 |
| **悬念留白** | 在 Panel 之间制造"想知道接下来发生什么"的冲动 | 每格结尾留下钩子，引出下一格 |
| **情绪起伏** | 叙事节奏有高低变化 | 钩子(高)→解释(中)→高潮(高)→收尾(中高) |
| **认知反差** | 打破读者预期，制造"没想到"的惊喜 | 如"看起来是X，其实是Y" |

**检查清单**：
- [ ] Panel 1 是否能在 3 秒内抓住注意力？
- [ ] Panel 之间是否有悬念或因果驱动？
- [ ] 叙事节奏是否有起伏变化？
- [ ] 是否有认知反差或意外元素？

##### 2. 逻辑层次感（原"逻辑层次"）

**核心原则**：信息输出有"层层递进感"，观点或情节之间环环相扣，形成顺滑的认知路径。

**连环画适配标准**：

| 要素 | 说明 | 连环画应用 |
|-----|------|----------|
| **起承转合** | 故事有完整的叙事弧线 | Panel 1(起)→Panel 2-3(承)→Panel 4(转)→Panel 5(合) |
| **因果链条** | 每个 Panel 与前后有明确的逻辑关系 | A导致B，B导致C，形成因果链 |
| **信息递进** | 信息量逐层深入，先易后难 | 概念引入→原理解释→案例展示→结论升华 |
| **无缝过渡** | Panel 之间过渡自然，无跳跃感 | 用时间、空间、因果等元素串联 |

**检查清单**：
- [ ] Panel 是否按照起承转合的逻辑排列？
- [ ] 每格与前后格是否有明确的因果或递进关系？
- [ ] 信息难度是否逐层递进？
- [ ] 过渡是否自然，读者能否顺畅理解？

##### 3. 内容准确性（原"内容准确严谨"）

**核心原则**：关键信息准确无误，表达客观，经得起推敲和验证。

**连环画适配标准**：

| 要素 | 说明 | 连环画应用 |
|-----|------|----------|
| **数据准确** | 数字、日期、百分比必须与原文一致 | 年份、金额、刑期、数量等原样保留 |
| **术语准确** | 专业术语、法条编号、科学概念必须准确 | 使用原文术语，不可意译或简化 |
| **人物准确** | 人物姓名、身份、外貌描述必须准确 | 不可张冠李戴，身份描述需核实 |
| **事实可证** | 关键事实可在原文中找到依据 | fact_check 字段记录来源 |

**检查清单**：
- [ ] 文章中的关键数字是否原样保留？
- [ ] 专业术语和法条编号是否准确？
- [ ] 人物信息是否与原文一致？
- [ ] fact_check 是否有据可查？

##### 4. 画面可绘性（原"有画面感"）

**核心原则**：内容具备"可画性"，让读者脑海中能自发构建出清晰、立体的场景影像。

**连环画适配标准**：

| 要素 | 说明 | 连环画应用 |
|-----|------|----------|
| **具体主体** | 有明确的人物或物体 | "一位戴眼镜的女科学家"而非"科学家" |
| **具体动作** | 有清晰的动作或状态 | "指着屏幕"而非"看屏幕" |
| **具体环境** | 有具体的场景设置 | "现代实验室，有显微镜和电脑"而非"实验室" |
| **具体细节** | 有可辨识的视觉元素 | "屏幕显示'差评'二字"而非"屏幕显示内容" |
| **具体氛围** | 有明确的情绪基调 | "氛围紧张"、"阳光明媚" |

**检查清单**：
- [ ] image_prompt 是否描述了具体的人物或物体？
- [ ] 动作是否足够具体，可以被画出来？
- [ ] 环境背景是否有足够的细节？
- [ ] 是否有明确可辨识的视觉元素？

##### 5. 风格一致性（原"人设稳定性"的适配版）

**核心原则**：在多格连环画中，保持画风、色调、人物形象的一致性。

**连环画适配标准**：

| 要素 | 说明 | 连环画应用 |
|-----|------|----------|
| **画风统一** | 所有 Panel 使用相同的绘画风格 | style_seed 在所有 Panel 中保持一致 |
| **色调统一** | 整体色调协调 | 使用相同的配色方案描述 |
| **人物统一** | 同一人物在不同格中形象一致 | 如果 Panel 1 的科学家戴眼镜，Panel 3 也应戴眼镜 |
| **氛围统一** | 整体氛围基调一致 | 同一主题下氛围描述保持一致 |

**检查清单**：
- [ ] 所有 Panel 是否使用相同的 style_seed？
- [ ] 同一人物在不同格中形象是否一致？
- [ ] 整体色调和氛围是否协调？

#### 校验流程

1. **自动校验**：系统对生成的脚本进行三个维度评估
2. **问题检测**：识别钩子强度、逻辑连贯、一图一义、视觉可绘、收尾升华等问题
3. **自动优化**：对明确问题（如 caption 过长）自动修复
4. **结果展示**：向用户展示校验摘要

#### 校验提示词模板

```
你是一位科普连环画脚本质量评估专家。请对以下脚本进行校验。

## 脚本内容
{生成的脚本JSON}

## 校验步骤

### 步骤一：字段完整性校验（必须通过）
检查每个 Panel 是否包含以下 5 个必需字段：
- id（整数，从1开始）
- scene（中文场景描述，非空）
- caption（科普旁白，20字以内，非空）
- image_prompt（图像生成提示，100-200字，非空）
- fact_check（关键事实，非空）

如缺少任何字段或字段为空，输出：
{
  "field_check": {
    "passed": false,
    "missing_fields": ["缺失的字段列表"],
    "empty_fields": ["为空的字段列表"]
  },
  "overall_score": "较差",
  "passed": false
}

### 步骤二：image_prompt 质量校验（关键检查）

#### 2.1 场景设计遵循检查
检查每个 Panel 的 image_prompt 是否完整还原 scene 字段中的所有元素：
- 主体人物是否描述详细？（姓名、外貌、服饰）
- 动作姿态是否具体？
- 环境背景是否完整？
- 关键道具是否体现？

#### 2.2 关键信息保留检查
检查 image_prompt 中是否包含：
- 具体数字：年份、金额、刑期、数量等是否原样写出？
- 具体文字：屏幕/标语/文件上的文字是否用引号明确标出？
- 专有名词：法条编号、术语、名称是否准确？
- 人物信息：姓名、身份是否准确？

#### 2.3 文字内容显示检查
画面中需要显示文字时，image_prompt 是否明确写出：
- "屏幕清晰显示'具体文字'"
- "标语上写着'具体内容'"
- ❌ 错误：屏幕显示差评内容（太模糊）
- ✅ 正确：手机屏幕清晰显示"差评"二字

#### 2.4 长度检查
image_prompt 字数是否在 100-200 字之间？过短会导致细节缺失。

### 步骤三：高质方法论评估（前两步通过后进行）

基于五大高质方法论进行评估：

#### 3.1 叙事吸引力评估
- **黄金开篇**：Panel 1 是否能在"第一眼"抓住注意力？
- **悬念留白**：Panel 之间是否有悬念或因果驱动？
- **情绪起伏**：叙事节奏是否有高低变化？
- **认知反差**：是否有打破预期的元素？

#### 3.2 逻辑层次感评估
- **起承转合**：Panel 是否按照完整的叙事弧线排列？
- **因果链条**：每格与前后格是否有明确的逻辑关系？
- **信息递进**：信息难度是否逐层深入？
- **无缝过渡**：Panel 之间过渡是否自然？

#### 3.3 内容准确性评估
- **数据准确**：关键数字是否与原文一致？
- **术语准确**：专业术语、法条编号是否准确？
- **人物准确**：人物姓名、身份是否与原文一致？
- **事实可证**：fact_check 是否有据可查？

#### 3.4 画面可绘性评估
- **具体主体**：image_prompt 是否描述了具体的人物或物体？
- **具体动作**：动作是否足够具体，可以被画出来？
- **具体环境**：环境背景是否有足够的细节？
- **具体细节**：是否有明确可辨识的视觉元素（如屏幕文字、标语）？

#### 3.5 风格一致性评估
- **画风统一**：所有 Panel 是否使用相同的 style_seed？
- **人物统一**：同一人物在不同格中形象是否一致？
- **氛围统一**：整体氛围基调是否协调？

## 输出格式

{
  "field_check": {
    "passed": true,
    "panel_count": <Panel数量>,
    "all_fields_present": true
  },
  "image_prompt_check": {
    "passed": <true/false>,
    "issues": [
      {
        "panel_id": <Panel编号>,
        "issue_type": "<scene_not_followed/key_info_missing/text_not_clear/too_short>",
        "description": "<问题描述>",
        "suggestion": "<改进建议，给出具体修改后的内容>"
      }
    ]
  },
  "overall_score": "<优秀/良好/一般/较差>",
  "methodology_scores": {
    "narrative_attractiveness": {
      "score": "<优秀/良好/一般/较差>",
      "golden_opening": <true/false>,
      "suspension": <true/false>,
      "emotional_variation": <true/false>,
      "cognitive_contrast": <true/false>,
      "issues": ["问题列表"],
      "strengths": ["优点列表"]
    },
    "logical_hierarchy": {
      "score": "<优秀/良好/一般/较差>",
      "story_arc": <true/false>,
      "causal_chain": <true/false>,
      "info_progression": <true/false>,
      "smooth_transition": <true/false>,
      "issues": ["问题列表"],
      "strengths": ["优点列表"]
    },
    "content_accuracy": {
      "score": "<优秀/良好/一般/较差>",
      "data_accuracy": <true/false>,
      "terminology_accuracy": <true/false>,
      "character_accuracy": <true/false>,
      "fact_verifiable": <true/false>,
      "issues": ["问题列表"],
      "strengths": ["优点列表"]
    },
    "visual_drawability": {
      "score": "<优秀/良好/一般/较差>",
      "specific_subject": <true/false>,
      "specific_action": <true/false>,
      "specific_environment": <true/false>,
      "specific_details": <true/false>,
      "issues": ["问题列表"],
      "strengths": ["优点列表"]
    },
    "style_consistency": {
      "score": "<优秀/良好/一般/较差>",
      "art_style_unified": <true/false>,
      "character_unified": <true/false>,
      "atmosphere_unified": <true/false>,
      "issues": ["问题列表"],
      "strengths": ["优点列表"]
    }
  },
  "improvement_suggestions": [
    {
      "panel_id": <需要改进的Panel编号，如果是整体问题则为0>,
      "methodology": "<对应的方法论名称>",
      "issue": "<问题描述>",
      "suggestion": "<具体改进建议>"
    }
  ],
  "passed": <true/false，是否通过校验>
}

仅输出 JSON，不要使用 markdown 代码块。
```

#### 校验结果处理

| 结果 | 处理方式 |
|-----|---------|
| **字段缺失** | 拒绝脚本，要求重新生成，提示缺失的字段 |
| **通过（优秀/良好）** | 向用户展示脚本，进入用户确认环节 |
| **需优化（一般）** | 自动优化后展示，告知用户优化内容 |
| **不通过（较差）** | 重新生成脚本，说明问题所在 |

#### 用户可见的校验摘要

**字段完整性检查通过时**：

```
📋 脚本校验结果

✅ 字段完整性：通过（5/5 字段齐全）

整体评分：良好

✅ 优点：
- 开篇有视觉冲击力
- 逻辑递进清晰
- 收尾有升华

⚠️ 改进建议：
- Panel 3 的 caption 超过20字，已自动精简
- Panel 4 可增加具体数字标注

是否接受此脚本？
[接受] [重新生成] [手动修改]
```

**字段完整性检查失败时**：

```
📋 脚本校验结果

❌ 字段完整性：未通过

缺失字段：
- Panel 2 缺少 "fact_check" 字段
- Panel 4 缺少 "caption" 字段

请重新生成脚本，确保每个 Panel 包含以下 5 个必需字段：
id, scene, caption, image_prompt, fact_check
```

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

| 参数 | 值 | 说明 |
|-----|-----|------|
| **字体大小** | 36px | 固定大小，适合 1024x1024 图像 |
| **文字颜色** | 白色 (#FFFFFF) | RGB(255, 255, 255) |
| **背景颜色** | 黑色半透明 | RGBA(0, 0, 0, 180)，约70%不透明度 |
| **背景圆角** | 8px | 圆角矩形更美观 |
| **描边效果** | 黑色 1px | 增强可读性 |
| **底部留白** | 60px | 文字距离图像底部 |

**⚠️ 字体路径（跨平台兼容）**:

| 操作系统 | 字体路径 | 备注 |
|---------|---------|------|
| **macOS** | `/System/Library/Fonts/PingFang.ttc` | 苹方字体 |
| **macOS 备选** | `/System/Library/Fonts/STHeiti Light.ttc` | 黑体 |
| **Windows** | `C:/Windows/Fonts/msyh.ttc` | 微软雅黑 |
| **Windows 备选** | `C:/Windows/Fonts/simhei.ttf` | 黑体 |
| **Linux** | `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf` | Droid Sans |
| **Linux 备选** | `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc` | Noto Sans CJK |

**完整实现代码**（使用 Pillow）:

```python
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def get_chinese_font(size: int = 36) -> ImageFont.FreeTypeFont:
    """获取中文字体，支持跨平台"""
    font_paths = [
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        # Linux
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except (IOError, OSError):
            continue

    # 如果所有字体都找不到，使用默认字体
    return ImageFont.load_default()

def add_caption(image_bytes: bytes, caption: str, font_size: int = 36) -> bytes:
    """在图像底部居中添加科普旁白

    Args:
        image_bytes: 原始图像字节数据
        caption: 科普旁白文字（20字以内）
        font_size: 字体大小，默认36px

    Returns:
        添加旁白后的图像字节数据
    """
    if not caption:
        return image_bytes

    # 打开图像
    image = Image.open(BytesIO(image_bytes))
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    draw = ImageDraw.Draw(image)

    # 获取中文字体
    font = get_chinese_font(font_size)

    # 计算文字位置（底部居中）
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 底部居中位置
    x = (image.width - text_width) // 2
    y = image.height - 60  # 底部留白 60px

    # 绘制半透明圆角背景
    padding = 10  # 内边距
    bg_x1 = x - padding
    bg_y1 = y - padding
    bg_x2 = x + text_width + padding
    bg_y2 = y + text_height + padding

    # 创建半透明背景层
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [bg_x1, bg_y1, bg_x2, bg_y2],
        radius=8,
        fill=(0, 0, 0, 180)  # 黑色，70%不透明度
    )
    image = Image.alpha_composite(image, overlay)

    # 重新获取 draw 对象
    draw = ImageDraw.Draw(image)

    # 绘制文字描边（黑色）
    for adj_x in [-1, 0, 1]:
        for adj_y in [-1, 0, 1]:
            if adj_x != 0 or adj_y != 0:
                draw.text((x + adj_x, y + adj_y), caption, font=font, fill=(0, 0, 0, 255))

    # 绘制主文字（白色）
    draw.text((x, y), caption, font=font, fill=(255, 255, 255, 255))

    # 输出
    output = BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()
```

> ⚠️ **重要**：Agent 在执行渲染时必须：
> 1. 使用 `get_chinese_font()` 函数获取字体，不要硬编码字体路径
> 2. 字体大小固定为 **36px**，除非图像尺寸非 1024x1024
> 3. 确保文字颜色为白色，背景为半透明黑色圆角矩形

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

> ⚠️ **重要变更**: 全局大图不再使用模型生成，而是**直接拼接用户确认的单 Panel 图像**。这样可以确保全局大图与用户确认的单 Panel 完全一致，避免风格漂移和内容不符的问题。

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

#### Phase 3b: 图像拼接（Pillow 实现）

> ⚠️ **核心原则**: 使用 **Phase 2 用户确认的单 Panel 图像**直接拼接，不调用模型重新生成。

**拼接逻辑**：
1. 读取所有用户确认的单 Panel 图像（已渲染旁白）
2. 根据布局计算画布尺寸
3. 按阅读顺序（从左到右、从上到下）拼接图像
4. 添加格子间的黑色分隔线
5. 若有空余格子，填充白色背景

**完整实现代码**：

```python
from PIL import Image, ImageDraw
from typing import List, Tuple

def create_comic_grid(
    panel_images: List[Image.Image],
    rows: int,
    cols: int,
    border_width: int = 4,
    border_color: Tuple[int, int, int] = (0, 0, 0)
) -> Image.Image:
    """将多个 Panel 图像拼接成连环画

    Args:
        panel_images: 用户确认的单 Panel 图像列表（已渲染旁白）
        rows: 行数
        cols: 列数
        border_width: 格子边框宽度，默认 4px
        border_color: 边框颜色，默认黑色

    Returns:
        拼接后的连环画大图
    """
    if not panel_images:
        raise ValueError("Panel 图像列表不能为空")

    # 获取单个 Panel 尺寸（假设所有 Panel 尺寸相同）
    panel_width, panel_height = panel_images[0].size

    # 计算画布总尺寸
    total_width = cols * panel_width + (cols + 1) * border_width
    total_height = rows * panel_height + (rows + 1) * border_width

    # 创建画布（白色背景）
    canvas = Image.new('RGB', (total_width, total_height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # 绘制边框线
    for i in range(rows + 1):
        y = i * (panel_height + border_width)
        draw.line([(0, y), (total_width, y)], fill=border_color, width=border_width)
    for j in range(cols + 1):
        x = j * (panel_width + border_width)
        draw.line([(x, 0), (x, total_height)], fill=border_color, width=border_width)

    # 按阅读顺序粘贴 Panel（从左到右，从上到下）
    for idx, panel_img in enumerate(panel_images):
        if idx >= rows * cols:
            break

        row = idx // cols
        col = idx % cols

        # 计算粘贴位置（考虑边框）
        x = border_width + col * (panel_width + border_width)
        y = border_width + row * (panel_height + border_width)

        # 确保 Panel 图像是 RGB 模式
        if panel_img.mode != 'RGB':
            panel_img = panel_img.convert('RGB')

        canvas.paste(panel_img, (x, y))

    return canvas


def assemble_comic_from_files(
    panel_paths: List[str],
    rows: int,
    cols: int,
    output_path: str,
    border_width: int = 4
) -> str:
    """从文件路径读取 Panel 图像并拼接

    Args:
        panel_paths: 单 Panel 图像文件路径列表
        rows: 行数
        cols: 列数
        output_path: 输出文件路径
        border_width: 边框宽度

    Returns:
        输出文件路径
    """
    panel_images = []
    for path in panel_paths:
        img = Image.open(path)
        panel_images.append(img)

    comic = create_comic_grid(panel_images, rows, cols, border_width)
    comic.save(output_path, 'PNG')

    return output_path
```

**使用示例**：

```python
# 假设用户已确认 4 个 Panel
panel_paths = [
    "panel_01_confirmed.png",
    "panel_02_confirmed.png",
    "panel_03_confirmed.png",
    "panel_04_confirmed.png"
]

# 拼接为 2x2 布局
output = assemble_comic_from_files(
    panel_paths=panel_paths,
    rows=2,
    cols=2,
    output_path="comic_2x2.png"
)
print(f"连环画已保存: {output}")
```

**5格布局处理（2x3 空出右下角）**：

```python
# 5格布局：2行3列，最后一个格子留白
panel_paths_5 = [
    "panel_01.png", "panel_02.png", "panel_03.png",
    "panel_04.png", "panel_05.png"
]

# 直接调用，函数会自动处理空余格子
# Panel 6 位置保持白色背景
output_5 = assemble_comic_from_files(
    panel_paths=panel_paths_5,
    rows=2,
    cols=3,
    output_path="comic_2x3_5panels.png"
)
```

#### Phase 3c: 大图反馈迭代（可选）

若用户对布局不满意，可：
1. 调整布局参数（rows, cols）重新拼接
2. 调整边框宽度或颜色
3. 返回 Phase 2 修改特定 Panel 后重新拼接

#### 全局大图与单 Panel 一致性保证

> ✅ **优势**：由于直接使用用户确认的单 Panel 图像拼接，全局大图与单 Panel 完全一致：
> - 风格一致：每个格子的风格与用户确认的单 Panel 完全相同
> - 内容一致：每个格子的内容与用户确认的单 Panel 完全相同
> - 旁白一致：每个格子的旁白位置、样式与单 Panel 完全相同
> - 无模型漂移：避免了模型重新生成导致的风格和内容偏差

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
3. **Phase 1b**: 脚本校验 → 评估吸引力/清晰度/优质度 → 自动优化 → 展示校验结果
4. **Phase 2**: 逐个生成 Panel → 渲染科普旁白 → 展示给用户确认 → 收集反馈 → 迭代优化 → **保存用户确认的 Panel 图像**
5. **Phase 3**: 确认布局 → **直接拼接用户确认的 Panel 图像** → 生成大图 → 可选迭代
6. **交付**: 保存所有 Panel 图像及最终大图（均含渲染后的旁白）

---

## 常见问题

**Q: 多张图像风格不统一？**
检查每次调用是否将 `style_seed` 原文追加至 Prompt 末尾。

**Q: 支持中文 Prompt？**
`ernie-image-turbo` 对中文 Prompt 效果最佳。

**Q: 旁白文字是如何添加的？**
旁白文字不是由图像生成模型直接生成，而是在模型生成图像后，通过 Pillow 库渲染到图像底部居中位置。用户看到的单 Panel 图像是已经渲染旁白后的成品。

**Q: 全局大图是如何生成的？**
全局大图**不是由模型重新生成**，而是通过 Pillow 直接拼接用户确认的单 Panel 图像。这样可以确保全局大图与用户确认的单 Panel 完全一致，避免风格漂移和内容不符的问题。

**Q: 全局大图与单 Panel 是否一致？**
完全一致。由于全局大图是直接拼接用户确认的单 Panel 图像，每个格子的风格、内容、旁白都与用户确认的单 Panel 完全相同。

**Q: base64 在 Windows 处理？**
PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("panel_01.png"))`