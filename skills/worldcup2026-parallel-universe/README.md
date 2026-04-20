# WorldCup 2026 Parallel Universe Agent (WP26_PUA)

> 2026 世界杯赛后平行宇宙叙事引擎
> 三元组意图驱动 × 实时联网检索 × 深度创意写作 × 多模态长图渲染

---

## 简介

WorldCup 2026 Parallel Universe Agent 是一个创意叙事引擎，能够将世界杯比赛事件转化为"平行宇宙"式的文学叙事——基于真实赛况事实，以诗意、文学化的方式重新诠释，创造出既有事实根基又富有艺术想象力的微小说作品。

### 核心特性

- **三元组意图协议**：通过 `(entity, event_type, emotion_intensity)` 简洁表达创作意图
- **智能视角路由**：根据情绪强度自动选择第一人称热血/伪纪实/第三人称冷峻视角
- **10步闭环流水线**：从意图解析到多模态交付的全自动化创作
- **质量自评机制**：Reflexion闭环确保人设一致性与情绪弧线拟合
- **事实模糊化**：低置信度事实自动虚化，确保叙事不误导读者

---

## 安装

### 方式一：直接安装

将 `worldcup2026-parallel-universe` 文件夹放入 Claude Code 的 skills 目录：

```bash
cp -r worldcup2026-parallel-universe ~/.claude/skills/
```

### 方式二：从 .skill 文件安装

```bash
claude skill install worldcup2026-parallel-universe.skill
```

---

## 快速开始

### 基本用法

```
为梅西在2026世界杯的绝杀进球写一个平行宇宙故事，情绪强度9
```

### 三元组格式

```
用三元组格式生成世界杯故事：entity=姆巴佩, event_type=帽子戏法, emotion_intensity=8
```

---

## 三元组意图协议

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `entity` | string | 核心角色/球队/球员 | `"梅西"` / `"巴西队"` |
| `event_type` | string | 赛事事件类型 | `"绝杀进球"` / `"点球大战失利"` |
| `emotion_intensity` | integer 0–10 | 情绪强度 | `9` |

### 情绪强度路由规则

| emotion_intensity | 叙事视角 | 文风特点 |
|-------------------|---------|---------|
| ≥ 8 | 第一人称热血 | 内心独白，高密度感官意象 |
| 5–7 | 伪纪实 | 第三人称限知，新闻笔法夹叙事 |
| < 5 | 第三人称冷峻 | 疏离感，白描，克制 |

---

## 10步执行工作流

```
Phase 1: 意图解构与契约锁定
├── Step 1: Intent_Parser    → 解析三元组，提取冲突原型
└── Step 2: Config_Manager   → 锁定体裁契约(300字微小说)

Phase 2: 逻辑规划与实时搜索
├── Step 3: Logic_Planner    → 路由叙事视角，配置节奏
└── Step 4: Web_Search       → 双路检索：赛况事实 + 在地文化

Phase 3: 创意生产与多重审计
├── Step 5: Creative_Writer  → 高质微小说创作
├── Step 6: Safety_Guard     → 合规审查 + 事实置信度核查
└── Step 7: Reflexion_Critic → 自评闭环(最多3次重试)

Phase 4: 审美映射与多模态交付
├── Step 8: Aesthetic_Mapper → 色彩/字体/间距映射
├── Step 9: LongImage_Renderer → 长图渲染(1:1 & 9:16)
└── Step 10: MultiModal_Publisher → 最终交付
```

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

## 项目结构

```
worldcup2026-parallel-universe/
├── SKILL.md              # 主技能说明文件
├── README.md             # 本文档
├── references/           # 参考文档
│   ├── api_reference.md  # API 参考
│   ├── conflict_archetypes.md  # 冲突原型详解
│   └── examples.md       # 完整示例
└── scripts/              # 辅助脚本
    ├── validate_triplet.py  # 三元组验证
    └── run_pipeline.py   # 完整10步管道运行脚本
```

### 脚本能力说明

`run_pipeline.py` 实现了完整的 10 步 Pipeline：

| 步骤 | 功能 | API 调用 |
|------|------|---------|
| Step 1 | 意图解析 | `ernie-5.0-thinking-preview` |
| Step 2 | 契约锁定 | `ernie-5.0-thinking-preview` |
| Step 3 | 叙事规划 | `ernie-5.0-thinking-preview` |
| Step 4 | 联网检索 | `ernie-5.0-thinking-preview` + `web_search` |
| Step 5 | 微小说创作 | `ernie-5.0-thinking-preview` |
| Step 6 | 安全审计 | `ernie-5.0-thinking-preview` |
| Step 7 | Reflexion 闭环 | `ernie-5.0-thinking-preview` |
| Step 8 | 审美映射 | `ernie-5.0-thinking-preview` |
| Step 9 | 图片提示词生成 | `ernie-5.0-thinking-preview` |
| Step 10 | 图片生成 | `ernie-image-turbo` |

**使用方式**：

```bash
# 设置 API Key
export AISTUDIO_API_KEY="your-api-key"

# 基本用法
python scripts/run_pipeline.py --entity "梅西" --event_type "绝杀进球" --emotion_intensity 9

# 从 JSON 文件读取
python scripts/run_pipeline.py --json triplet.json --output result.json

# 跳过图片生成（仅生成文本和图片提示词）
python scripts/run_pipeline.py --entity "梅西" --event_type "绝杀进球" --emotion_intensity 9 --skip-image
```

---

## 质量控制

### Reflexion 闭环

| 评估维度 | 阈值 | 不通过处理 |
|---------|------|-----------|
| 人设漂移 σ | ≤ 0.30 | 变异参数后回流 Step 5 |
| 情绪弧线拟合度 | ≥ 0.70 | 调整三幕字数后回流 Step 5 |
| 字数达标 | ≤ 300字 | 压缩后回流 Step 5 |
| **最大重试次数** | **3次** | 超限触发熔断降级 |

### 事实模糊化规则

| confidence_score | 处理方式 | 示例转换 |
|-----------------|---------|---------|
| ≥ 0.80 | 直接使用 | "第89分钟" |
| 0.60–0.79 | 轻度模糊 | "比赛尾声" |
| < 0.60 | 强制虚化 | "某个注定的瞬间" |

---

## 示例输出

### 输入

```
为梅西在2026世界杯的绝杀进球写一个平行宇宙故事，情绪强度9
```

### 输出

```json
{
  "novel_text": "我听见自己的心跳。加时赛第118分钟，AT&T的穹顶半开着，达拉斯的夜风灌进来，混着草皮的味道和九万人屏住的呼吸。我的腿已经没有知觉了——五届世界杯，这是最后一分钟。最后一分钟。球从德保罗脚下飞来。时间在这个瞬间停止了。我看到一切：洛里的站位偏了一寸，登贝莱的回追慢了半步，帕雷德斯在前点扯出的空当。我甚至看到了看台上那个穿10号球衣哭泣的孩子。这不是我的眼睛，是二十年的肌肉记忆在替我看见。左脚。没有思考。只有灵魂里那道金色弧线。当球触网的那一刻，我什么都没听见。九万人的咆哮化成一片白光。我跪倒在草地上，孤星旗在头顶飘扬。这不是一个进球——这是一个时代的完整句号。三十九岁。最后一战。我站起身，眼泪流进嘴里。咸的。这是活着的味道。",
  "word_count": 289,
  "quality_status": "passed",
  "pipeline_summary": {
    "persona_drift_sigma": 0.15,
    "emotion_arc_fit": 0.88,
    "audit_pass": true,
    "total_iterations": 1
  }
}
```

---

## 环境要求

### API 配置

使用本 skill 需要百度星河社区 API Key。

**获取 API Key**：访问 [百度星河社区](https://aistudio.baidu.com/) 注册并获取 API Key

> 💡 **提示**：执行 Skill 时会自动检查 API Key，如未配置会引导您设置。您只需告知 API Key，系统会自动为您配置，无需手动设置环境变量。

### API 端点

| 配置项 | 值 |
|--------|-----|
| **API Base URL** | `https://aistudio.baidu.com/llm/lmapi/v3` |
| **创作模型** | `ernie-5.0-thinking-preview`（原生全模态大模型） |
| **目标生图模型** | `ernie-image-turbo`（通过星河社区调用） |
| **最大输出Token** | `65536` |

### 依赖

```bash
pip install openai
```

### API 调用示例

**文本生成 API (OpenAI SDK)**：
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

**图片生成 API (OpenAI SDK)**：
```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://aistudio.baidu.com/llm/lmapi/v3",
)

response = client.images.generate(
    model="ernie-image-turbo",
    prompt="一只可爱的猫咪坐在窗台上",
    n=1,
    response_format="url",
    size="1024x1024",
    extra_body={"seed": 42, "use_pe": True, "num_inference_steps": 8, "guidance_scale": 1.0}
)

# 获取图片 URL
image_url = response.data[0].url
```

**支持的图片尺寸**：
- `1024x1024` - 方图 (1:1)
- `1376x768`, `1264x848`, `1200x896` - 横版
- `896x1200`, `848x1264`, `768x1376` - 竖版
- `1024x1820` - 长图 (9:16)

### 依赖 Skills

| Skill | 用途 |
|-------|------|
| `web-access` | 执行联网检索，获取赛况事实和在地文化信息 |

---

## 免责声明

> 本工具仅供创意写作与体育人文传播用途。
> 所有生成内容均为 AI 创意叙事，不构成新闻报道，请勿作为事实依据传播。

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request