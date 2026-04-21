# 历史经验与术语对照表

*基于 @PaddlePaddle 2026 年以来的推特内容分析（数据来源：x.com/PaddlePaddle）*

---

## 文案结构风格

### Emoji 使用习惯

| 位置 | Emoji | 使用场景 |
|------|------|---------|
| 标题前 | 🚀 | 新模型发布、重磅功能 |
| 标题前 | 🔥 | 里程碑、排行榜 |
| 标题前 | 🚨 | 特殊通知 |
| 句尾 | 🌍 | 技术特点补充 |
| 句尾 | 🙌 | 感谢、宣布 |
| 句尾 | ❤️ | 社区感谢 |
| 句尾 | 👉 | 号召参与、行动 |

**原则**：不过度使用，每条推文 3-5 个 emoji 为宜

### 常用标签模式

| 内容类型 | 基础标签 | 技术标签 |
|---------|---------|---------|
| OCR 相关 | #PaddleOCR #ComputerVision | #DocumentAI #OCR |
| ERNIE 模型 | #ERNIE #NLP | #DeepLearning |
| 通用发布 | #AI #DeepLearning | #OpenSource |
| 里程碑 | #AI | #OpenSourceCommunity |

### 性能数据呈现方式

1. **SOTA 表达**：使用 "SOTA"、"state-of-the-art"
2. **排行表达**：
   - "hitting #1 on Hugging Face Trending"
   - "became the most-starred OCR project"
3. **模型规模**：明确参数量（如 "0.9B parameters"）
4. **对比评测**：
   - "Benchmark Series | Episode 1"
   - 对比多个竞品

### 合作方提及习惯
- **@BaiduResearch**：母公司研究部门
- 提及方式：Quote 转发（非 @）
- 合作内容：共同发布、技术背书

### 图片使用习惯

| 内容类型 | 图片类型 |
|---------|---------|
| 模型发布 | 产品演示图、架构图 |
| 里程碑 | 徽章图片、排行榜截图 |
| 对比评测 | 性能对比图表 |
| 官网更新 | 界面截图 |
| 通用 | 产品 Logo、技术示意图 |

### 互动回复风格
- **感谢社区**：明确感谢 "all of our partners, contributors, developers and users"
- **号召行动**："come and drop a ❤️ now!"
- **鼓励讨论**："Let's keep pushing boundaries"
- **开放态度**：强调 Open Source 社区价值

---

## 技术术语对照表

### 常见中文 → 英文映射

| 中文 | 英文 | 用例 |
|------|------|------|
| 零侵入 | zero code intrusion | CINN 插件式接入 |
| 即插即用 | plug-and-play | 硬件接入 |
| 解耦 | decoupling | 架构设计 |
| 端到端 | end-to-end | 全流程 |
| 动态形状 | dynamic shape | 形状变化场景 |
| 科学计算 | scientific computing | PDE 求解 |
| 微分方程 | PDE | 偏微分方程 |
| 显存 | device memory | GPU 内存 |
| 编译器 | compiler | CINN、NVCC |
| 算子 | operator / kernel | 底层计算单元 |
| 推理 | inference | 模型预测 |
| 训练 | training | 模型学习 |
| 最先进 | SOTA | state-of-the-art |
| 开源 | open-source | GitHub 开源 |
| 贡献者 | contributors | 社区贡献者 |
| 开发者 | developers | 研发人员 |

### 数据表达规范

| 指标类型 | 英文表达 | 示例 |
|---------|---------|------|
| 速度倍增 | X times faster | 2.2x faster |
| 百分比提升 | X% faster / X% speedup | 27.4% faster |
| 对比优势 | X% faster than [竞品] | 115% faster than PyTorch |
| 模型规模 | XB parameters | 0.9B parameters |
| 排行成就 | #1 on Trending | hitting #1 on Hugging Face |
| 星标成就 | most-starred | most-starred project |

### GitHub / 官网链接模式

| 内容类型 | 推荐链接 |
|---------|---------|
| 框架更新 | https://github.com/PaddlePaddle/Paddle/releases |
| 新模型/组件 | https://github.com/PaddlePaddle/[仓库名] |
| 官网更新 | https://paddlepaddle.org |
| 技术文档 | https://paddlepaddle.org/documentation |
| 博客文章 | https://paddlepaddle.org/blog/[文章名] |
| Hugging Face | https://huggingface.co/[模型名] |
