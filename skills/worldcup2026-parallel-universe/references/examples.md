# 完整示例

本文档提供 WorldCup 2026 Parallel Universe Agent 的完整使用示例。

---

## 目录

1. [示例1：绝杀进球（高情绪强度）](#示例1绝杀进球高情绪强度)
2. [示例2：点球大战失利（中等情绪强度）](#示例2点球大战失利中等情绪强度)
3. [示例3：帽子戏法（三元组格式）](#示例3帽子戏法三元组格式)

---

## 示例1：绝杀进球（高情绪强度）

### 用户输入

```
为梅西在2026世界杯的绝杀进球写一个平行宇宙故事，情绪强度9
```

### Step 1: 意图解析

```json
{
  "entity": "梅西",
  "event_type": "绝杀进球",
  "emotion_intensity": 9,
  "conflict_archetype": "last_stand",
  "psyche_mode": "transcendent"
}
```

### Step 2: 契约锁定

```json
{
  "genre": "社媒微小说",
  "length_limit": 300,
  "pov_mode": "第一人称热血",
  "forbidden_patterns": ["政治敏感表述", "真实球员负面人身攻击", "未经证实的伤情细节"],
  "tone_anchor": "breathless, luminous, time-suspended"
}
```

### Step 3: 叙事规划

```json
{
  "act_1_words": 80,
  "act_2_words": 140,
  "act_3_words": 80,
  "pacing_target": "avalanche",
  "sensory_anchors": [
    "草皮被钉靴撕裂的声音",
    "看台灯光在泪水中散射成星芒",
    "球进网瞬间肾上腺素涌上喉头的苦味"
  ],
  "emotion_score_series": [0.3, 0.5, 0.8, 1.0, 0.9]
}
```

### 最终输出

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

## 示例2：点球大战失利（中等情绪强度）

### 用户输入

```
巴西队在2026世界杯点球大战失利，帮我创作一个诗意叙事，情绪强度7
```

### Step 1: 意图解析

```json
{
  "entity": "巴西队",
  "event_type": "点球大战失利",
  "emotion_intensity": 7,
  "conflict_archetype": "hero_falls",
  "psyche_mode": "melancholic"
}
```

### Step 2: 契约锁定

```json
{
  "genre": "社媒微小说",
  "length_limit": 300,
  "pov_mode": "伪纪实",
  "forbidden_patterns": ["政治敏感表述", "真实球员负面人身攻击"],
  "tone_anchor": "wistful, measured, heavy with unspoken weight"
}
```

### 最终输出

```json
{
  "novel_text": "新泽西的夏夜，大都会人寿体育场的灯光将每一个影子都拉得很长。八万二千五百人的呼喊声在某个瞬间陷入了诡异的寂静——那是十二码点前的寂静，连风中都听不到自由女神遥远的叹息。记分牌上的2-2已经凝固了一小时。巴西队的球员们站在中圈，双手搭肩，像一座座即将崩塌的雕像。他们的球衣已被汗水浸透，黄绿色的光泽在夜灯下显得黯淡。第五轮点球，胜负在此一举。踢还是不踢，这从来不是问题；问题在于，命运之手会选择哪一侧的门柱。皮球划过夜空的弧线很美，美得像一个几乎可以触及的梦。然后它偏离了，偏离了那么几厘米，却偏离了整整一个时代。看台上骤然凝固的呼吸终于化作一声叹息，从里约到圣保罗，从玛瑙斯到阿雷格里港，万里之外的祖国此刻也在沉默。有人蹲下身，有人仰望天际线——那里有纽约的灯火在闪烁，仿佛在无声地诉说：有些故事，注定没有童话般的结局。桑巴军团的这个夏天，结束了。",
  "word_count": 298,
  "quality_status": "passed",
  "pipeline_summary": {
    "persona_drift_sigma": 0.15,
    "emotion_arc_fit": 0.85,
    "audit_pass": true,
    "total_iterations": 1
  }
}
```

---

## 示例3：帽子戏法（三元组格式）

### 用户输入

```
用三元组格式生成一个世界杯故事：entity=姆巴佩, event_type=帽子戏法, emotion_intensity=8
```

### Step 1: 意图解析

```json
{
  "entity": "姆巴佩",
  "event_type": "帽子戏法",
  "emotion_intensity": 8,
  "conflict_archetype": "last_stand",
  "psyche_mode": "volcanic"
}
```

### Step 2: 契约锁定

```json
{
  "genre": "社媒微小说",
  "length_limit": 300,
  "pov_mode": "第一人称热血",
  "forbidden_patterns": ["政治敏感表述", "真实球员负面人身攻击"],
  "tone_anchor": "explosive, triumphant, heartbeat-racing"
}
```

### Step 8: 视觉映射

```json
{
  "dominant_color_hex": "#1E3A5F",
  "secondary_color_hex": "#FFD700",
  "font_weight": "bold",
  "line_spacing_multiplier": 1.6,
  "landscape_base": "Texas stadium under brilliant blue sky, golden sunset rays piercing through open roof",
  "clip_cosine_score": 0.85
}
```

### 最终输出

```json
{
  "novel_text": "达拉斯的烈日灼烧着我的后背，但我感觉不到热。草皮在脚下撕裂，第一球——左脚抽射，网窝震颤。二十三分钟，这只是开始。六十七分钟，点球。我甚至没看清门将扑向哪边，球已经钻入死角。观众的咆哮像海啸一样吞没了AT&T Stadium。第八十九分钟。禁区外。我听到心跳盖过了八万人的呐喊。右脚外侧划出一道弧线——世界波。帽子戏法。我想起巴黎郊区的那些夜晚，想起每一滴汗水。此刻，我不是为法国进球，我是为那个从未放弃的自己。德州的天空很蓝，蓝得像我的梦。",
  "word_count": 196,
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

## 更多示例

### 低情绪强度示例

**输入**：
```
用三元组格式生成故事：entity=德国队, event_type=小组赛出局, emotion_intensity=3
```

**特点**：
- POV: 第三人称冷峻
- 文风：疏离、白描、克制
- 情绪弧线：平稳，无明显起伏

### 降级示例

当 Reflexion 闭环3次重试仍未通过时：

```json
{
  "quality_status": "degraded",
  "pipeline_summary": {
    "persona_drift_sigma": 0.35,
    "emotion_arc_fit": 0.65,
    "audit_pass": true,
    "total_iterations": 3
  },
  "note": "质量自评未完全通过，但输出仍可用。建议人工审核。"
}
```