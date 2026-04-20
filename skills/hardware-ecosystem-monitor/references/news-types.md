# 新闻类型与来源说明

## 新闻分类体系

### 按来源类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `RSS` | 通过 RSS 协议订阅的博客/新闻源 | Hugging Face Blog、NVIDIA Developer News |
| `API` | 通过厂商提供的 API 接口获取 | 华为昇腾（若有 API） |
| `HTML` | 解析 HTML 页面提取 | 壁仞科技、昆仑芯科技等国内厂商 |

### 按内容性质

| 类型 | 标记 | 说明 |
|------|------|------|
| 重大发布 | `isManual: true` + 🔥 标签 | 手动新增的重要新闻，优先级最高 |
| 自动采集 | `isManual: false` | 系统自动抓取的常规新闻 |

### 按生态相关性（AI 判断）

| 分类 | AI 响应 | 说明 |
|------|---------|------|
| 生态相关 | 摘要文本 | 大模型适配、推理优化、硬件合作等 |
| 非生态相关 | `REJECT` | 商业公关稿、线下活动、赛事通知等 |

## 厂商分类

### 国际厂商

| 厂商 | 主要内容 | 来源 |
|------|----------|------|
| NVIDIA | GPU 技术博客、SDK 更新 | RSS |
| Intel | 数据中心 GPU、至强处理器 | HTML |
| Hugging Face | 框架与硬件适配合作 | RSS |

### 国产厂商

| 厂商 | 产品线 | 来源 |
|------|--------|------|
| 华为昇腾 | 昇腾 910B、MindSpore | HTML |
| 寒武纪 | MLU370、MLU290 | HTML |
| 壁仞科技 | BR100、BR104 | HTML |
| 昆仑芯科技 | R200、R200-8E | HTML |
| 沐曦 | MXNACA、MXCNA | HTML |
| 海光信息 | DCU Z100、Z100L | HTML |
| 燧原科技 | 邃思 2.0、邃思 3.0 | HTML |
| 安谋科技 | 玲珑 GPU、Arm China | HTML |

## 关键词白名单用途

ECOSYSTEM_KEYWORDS 用于**初筛**，降低 AI 调用成本：

1. **模型框架类**：大模型、LLM、PyTorch、飞桨、PaddlePaddle、MindSpore
2. **硬件类**：GPU、NPU、CPU、芯片、集群、智算
3. **场景类**：适配、推理、微调、训练、部署
4. **生态类**：CUDA、CANN、ROCm、MUSA

初筛逻辑：
```
IF (标题 + 摘要) 包含任一关键词 THEN 送入 AI 清洗
ELSE 直接 REJECT
```

## 新闻数据字段详解

| 字段 | 示例 | 说明 |
|------|------|------|
| `id` | `5dd3a65de532ef12e7619c510dfbd191` | MD5(URL) 生成，唯一标识 |
| `vendor` | `壁仞科技` | 原始厂商名称 |
| `title` | `壁仞科技完成 MiniMax M2.5 高效适配` | 原始标题 |
| `date` | `2026-03-02` | 标准化日期格式 |
| `summary` | `壁仞科技硬核适配国产大模型` | AI 精炼摘要（≤30 字） |
| `imageUrl` | `https://images.unsplash.com/...` | 封面图（默认占位图） |
| `link` | `https://www.birentech.com/news/...` | 原文链接 |
| `sourceType` | `HTML` | 来源类型 |
| `isManual` | `false` | 是否手动新增 |
