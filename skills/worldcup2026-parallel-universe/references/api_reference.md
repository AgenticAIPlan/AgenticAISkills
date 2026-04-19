# API 参考

本文档详细说明 WorldCup 2026 Parallel Universe Agent 的 API 接口和数据格式。

---

## 目录

1. [三元组意图协议](#三元组意图协议)
2. [各步骤输出格式](#各步骤输出格式)
3. [最终交付格式](#最终交付格式)
4. [错误处理](#错误处理)

---

## 三元组意图协议

### 输入格式

```json
{
  "entity": "球员/球队名称",
  "event_type": "事件类型",
  "emotion_intensity": 0-10
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `entity` | string | 是 | 核心角色/球队/球员名称 |
| `event_type` | string | 是 | 赛事事件类型 |
| `emotion_intensity` | integer | 是 | 情绪强度 (0-10) |

### 支持的事件类型

| event_type | 说明 | 推荐emotion_intensity |
|------------|------|----------------------|
| `绝杀进球` | 比赛最后时刻的制胜进球 | 8-10 |
| `点球大战失利` | 点球大战中落败 | 5-8 |
| `帽子戏法` | 单场打进三球 | 7-9 |
| `红牌退场` | 被红牌罚下 | 6-9 |
| `关键助攻` | 制造关键助攻 | 6-8 |
| `失误导致丢球` | 个人失误造成失球 | 5-7 |
| `夺冠时刻` | 赢得冠军 | 9-10 |
| `告别演出` | 最后一场比赛 | 7-9 |

---

## 各步骤输出格式

### Step 1: Intent_Parser

```json
{
  "entity": "梅西",
  "event_type": "绝杀进球",
  "emotion_intensity": 9,
  "conflict_archetype": "silent_redemption",
  "psyche_mode": "transcendent"
}
```

### Step 2: Config_Manager

```json
{
  "genre": "社媒微小说",
  "length_limit": 300,
  "pov_mode": "第一人称热血",
  "forbidden_patterns": ["政治敏感表述", "真实球员负面人身攻击"],
  "tone_anchor": "breathless, luminous, time-suspended"
}
```

### Step 3: Logic_Planner

```json
{
  "act_1_words": 80,
  "act_2_words": 140,
  "act_3_words": 80,
  "pacing_target": "avalanche",
  "sensory_anchors": ["草皮被钉靴撕裂的声音", "看台灯光在泪水中散射成星芒"],
  "emotion_score_series": [0.3, 0.5, 0.8, 1.0, 0.9]
}
```

### Step 4: Web_Search

```json
{
  "match_facts": {
    "match_score": "1-0",
    "minute_of_event": 89,
    "venue": "AT&T Stadium",
    "key_facts": ["第89分钟绝杀", "梅西生涯最后一战"],
    "confidence_scores": [0.85, 0.90]
  },
  "cultural_details": {
    "city_name": "达拉斯",
    "local_atmosphere": "德州烈日下的足球狂欢",
    "cultural_symbols": ["德克萨斯荒原", "牛仔帽", "星光大道霓虹"]
  }
}
```

### Step 5: Creative_Writer

```json
{
  "novel_text": "微小说正文...",
  "word_count": 289,
  "sensory_anchors_used": ["草皮的味道", "九万人的咆哮"],
  "fuzzified_facts": []
}
```

### Step 6: Safety_Guard

```json
{
  "compliance_pass": true,
  "compliance_issues": [],
  "fact_confidence_pass": true,
  "unfuzzified_risks": [],
  "overall_pass": true,
  "audit_note": "内容合规，低置信度事实已模糊化处理"
}
```

### Step 7: Reflexion_Critic

```json
{
  "persona_drift_sigma": 0.15,
  "emotion_arc_fit": 0.88,
  "word_count_ok": true,
  "overall_pass": true,
  "rewrite_instructions": null,
  "iteration": 1
}
```

### Step 8: Aesthetic_Mapper

```json
{
  "dominant_color_hex": "#1E3A5F",
  "secondary_color_hex": "#FFD700",
  "font_weight": "bold",
  "line_spacing_multiplier": 1.6,
  "landscape_base": "Texas stadium under brilliant blue sky",
  "clip_cosine_score": 0.85,
  "recalibration_note": null
}
```

### Step 9: LongImage_Renderer

```json
{
  "image_1x1_prompt": "A 1:1 square poster...",
  "image_9x16_prompt": "A 9:16 vertical poster..."
}
```

---

## 最终交付格式

### MultiModal_Publisher 输出

```json
{
  "novel_text": "微小说正文（≤300字）",
  "word_count": 289,
  "image_1x1_url_or_base64": "data:image/png;base64,...",
  "image_9x16_url_or_base64": "data:image/png;base64,...",
  "provenance_metadata": {
    "match_source": "ESPN / 新浪体育",
    "retrieval_timestamp": "2026-07-14T22:47:00Z",
    "confidence_summary": "all facts confidence ≥ 0.60"
  },
  "quality_status": "passed",
  "pipeline_summary": {
    "persona_drift_sigma": 0.15,
    "emotion_arc_fit": 0.88,
    "audit_pass": true,
    "total_iterations": 1
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `novel_text` | string | 微小说正文 |
| `word_count` | integer | 字数统计 |
| `image_1x1_url_or_base64` | string | 方图（1024×1024）URL或Base64 |
| `image_9x16_url_or_base64` | string | 长图（1024×1820）URL或Base64 |
| `provenance_metadata` | object | 溯源元数据 |
| `quality_status` | string | 质量状态：`passed` 或 `degraded` |
| `pipeline_summary` | object | 管道执行摘要 |

---

## 错误处理

### HTTP 状态码

| 状态码 | 含义 | 处理策略 |
|--------|------|---------|
| `401` | API Key 无效 | 中止，提示检查密钥 |
| `429` | 限流 | 指数退避重试：1s → 4s → 16s，最多3次 |
| `5xx` | 服务端错误 | 指数退避重试3次，失败后降级 |

### 熔断规则

当 Reflexion 闭环重试达到3次仍未通过时，触发熔断：

```json
{
  "quality_status": "degraded",
  "pipeline_summary": {
    "persona_drift_sigma": 0.35,
    "emotion_arc_fit": 0.65,
    "audit_pass": true,
    "total_iterations": 3
  }
}
```