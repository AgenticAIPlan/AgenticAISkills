---
name: paddle-twitter-content-ops
description: PaddlePaddle Twitter 内容运营自动化 - 从公众号文章/飞书文档/各种素材生成英文推特文案
---

# PaddlePaddle Twitter Content Operations

## 适用场景

当用户需要将中文内容素材（微信公众号文章、飞书文档、技术资料等）转换为适合发布的英文推特文案时，使用本 Skill。

## 输入要求

- 内容来源：微信公众号链接、飞书文档链接、文件夹路径或原始文本
- 需要明确的内容分类（模型发布、官网更新、重要公告、合作公告等）
- 可选：目标发布时间、特殊要求

## 执行步骤

1. **内容获取**：根据输入类型（微信链接/飞书文档/文件夹/原始文本）选择对应的解析方式
2. **内容分类**：根据关键词识别内容类型（model_release、website_update、major_announcement、partnership、general）
3. **信息提取**：提取产品名称、核心技术特点、性能数据、技术架构、对比优势、应用场景
4. **文案生成**：按照对应内容类型的模板生成英文推特文案
5. **图片处理**：识别原文图片语言，选择合适的配图方案
6. **输出预览**：展示完整图文预览，等待用户确认
7. **检查清单**：用户确认后输出发布前检查清单

## 内容分类与风格

| 类型 | 关键词 | 风格 |
|------|--------|------|
| model_release | 发布、模型、开源、PaddleOCR | 重磅宣布 |
| website_update | 官网、更新、新版、launch | 重磅宣布 |
| major_announcement | 计划、赛事、大赛、峰会 | 重磅宣布 |
| partnership | 合作、携手、联合、共建 | 双方握手 + @合作方 |
| general | 其他 | 科技风格 |

## 文案结构模板

```
[Emoji] [包含核心信息的标题]

[简短介绍，1-2句点明核心价值]

📊 Key Highlights:
• [具体数据点1]
• [具体数据点2]
• [技术特点3]
• [对比优势4]

🔗 Read more: [链接]

#PaddlePaddle #DeepLearning #AI
```

## Emoji 使用规范

| 位置 | Emoji | 使用场景 |
|------|------|---------|
| 标题前 | 🚀 | 新模型发布、重磅功能 |
| 标题前 | 🔥 | 里程碑、排行榜 |
| 句尾 | 🌍 | 技术特点补充 |
| 句尾 | 🙌 | 感谢、宣布 |
| 句尾 | ❤️ | 社区感谢 |

## 图片处理策略

**必须识别图片语言**：
- 英文图片 → 可直接使用
- 中文图片 → 选择替代方案

**配图方案优先级**：
1. 链接预览卡（默认推荐）
2. 官网截图（paddlepaddle.org）
3. 文生图（需手动）

## 输出要求

- 标题必须明确体现核心信息（产品名、技术点）
- 包含具体性能数据（如 2.2x、27.4%）
- 包含技术细节和对比优势
- Emoji 使用恰当，每条推文 3-5 个为宜
- 标签准确，不超过 4-6 个
- 链接可访问

## 参考资料

- [references/STYLE.md](references/STYLE.md) - 文案写法风格详细规范
- [references/SOUL.md](references/SOUL.md) - 内容取舍原则
- [references/AUTHOR.md](references/AUTHOR.md) - 作者长期偏好
- [references/MEMORY.md](references/MEMORY.md) - 历史经验、术语对照表
- [references/templates.md](references/templates.md) - 不同内容类型的处理模板
