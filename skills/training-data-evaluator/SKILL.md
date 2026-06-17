---
name: training-data-evaluator
description: |
  大模型训练数据质量评估工具 v2.0。用于全自动化评估合作伙伴提供的样例数据价值，支持预训练/中训练/后训练数据、代码数据、Agent轨迹、Thinking推理数据、GUI交互数据等多种类型。
  
  触发场景：
  - 用户需要评估训练数据质量、数据价值、数据完整性
  - 用户提到"数据评估"、"数据质量"、"样例评估"、"数据验收"
  - 用户提供数据文件（zip/txt/json/jsonl等）需要分析
  - 用户需要生成数据评估报告
  - 评估供应商/合作伙伴提供的数据样本
  - 需要检测数据使用的模型和智能体信息
  
  支持的输入格式：zip, rar, txt, json, jsonl
  输出形式：Vim配色风格的HTML评估报告
---

# 大模型训练数据评估器 v2.0

## 概述

本Skill用于全自动化评估大模型训练数据质量，帮助数据引入负责人快速判断合作伙伴提供数据的价值。

**核心能力：**
- 数据类型自动分类（预训练/中训练/后训练）
- 模型和智能体信息检测
- 统一维度展示（Tokens/Size/Samples/Language/Models/Agents）
- Vim配色风格的HTML报告
- 累加模式（自动检测新数据集）

## 评估流程

```
输入文件 → 解压解析 → 数据类型识别 → 模型/智能体检测 → 维度评估 → 生成HTML报告
```

## 一、数据类型分类

基于百度代码数据扩量攻坚需求文档的分类体系：

| 训练阶段 | 数据类型 | 识别特征 |
|---------|---------|---------|
| **预训练** | 技术文档 | API文档、框架文档、SDK/CLI文档 |
| | 教程/实践 | step-by-step项目教程 |
| | Q&A/Debug | StackOverflow类问答、报错解决 |
| | 博客/技术文章 | 架构设计、性能优化 |
| | Demo/示例 | 前端组件示例、UI库展示 |
| **中训练** | SWE-工程 | Bug修复、新功能、重构、单测生成 |
| | Agent轨迹 | 工具调用、多步推理、代码修改 |
| **后训练** | RL数据 | 反馈、评分、偏好数据 |
| **基础** | 源代码 | GitHub代码库 |
| | 推理/Reasoning | Thinking数据、推理链 |
| | GUI交互 | 桌面应用交互轨迹 |

## 二、检测能力

### 2.1 模型检测

自动检测数据生成使用的模型：
- Claude系列：Claude Sonnet 4.5, Claude 3.5 Sonnet, Claude 3 Opus
- GPT系列：GPT-4o, GPT-4 Turbo, GPT-4
- 国产模型：DeepSeek-V3, Qwen 2.5, GLM-4, ERNIE 4.0
- 开源模型：Llama 3

### 2.2 智能体检测

自动检测使用的智能体/工具：
- Coding Agent：cline, copilot, cursor
- GUI Agent：Terminal, Thunderbird, LibreOffice
- 工具调用：shell, git, docker, API

### 2.3 收集方式检测

- human：真人采集轨迹
- synthetic：模型合成数据
- mixed：混合来源

## 三、评估维度体系

### 3.1 统一显示维度

所有数据集统一显示以下维度（无则显示"-"）：

| 维度 | 说明 | 示例 |
|------|------|------|
| **Tokens** | 估算token数 | 67.3M |
| **Size** | 文件大小 | 256.7MB |
| **Samples** | 样本数量 | 794 |
| **Language** | 编程语言 | Go, python, javascript |
| **Models** | 检测到的模型 | Claude Sonnet 4.5, GPT-4o |
| **Agents** | 检测到的智能体 | cline, Terminal |

### 3.2 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| **规模** | 动态 | 基于token数分级评分 |
| **质量** | 动态 | 基于数据类型评估 |
| **稀缺性** | 动态 | 数据稀有程度 |
| **训练价值** | 动态 | 对模型训练的价值 |
| **完整性** | 固定 | 数据完整程度 |
| **场景覆盖** | 动态 | 语言/场景多样性 |

## 四、评分体系

### 4.1 数据集级评分（0-100分）

```
总分 = 各维度平均分
```

### 4.2 数据规模分级

| 级别 | Token数量 | 规模得分 |
|------|----------|---------|
| 50M+ | 95分 |
| 10M+ | 85分 |
| 1M+ | 75分 |
| <1M | 60分 |

### 4.3 采购建议

| 得分 | 等级 | 建议 |
|------|------|------|
| ≥85 | A | BUY（推荐采购） |
| 70-84 | B | EXPAND（需补充） |
| <70 | C | VERIFY（需验证） |

## 五、UI风格

### Vim Default配色方案

| 元素 | 颜色 | Vim对应 |
|------|------|---------|
| 背景 | #1c1c1c | Normal |
| 卡片 | #262626 | - |
| 边框 | #3a3a3a | - |
| 主文字 | #d0d0d0 | Normal |
| 注释/次要 | #808080 | Comment |
| 高分/绿 | #87af87 | String |
| 中分/黄 | #d7af5f | Function |
| 低分/红 | #ff5f5f | Error |
| 关键词/蓝 | #87afd7 | Keyword |
| 数字/紫 | #af87af | Number |
| 类型/黄绿 | #afaf87 | Type |
| 模型标签 | #af87af | Number |
| 智能体标签 | #afaf87 | Type |

## 六、使用方法

### 6.1 命令行使用

```bash
# 评估工作目录下的所有数据文件
python3 evaluate_data.py

# 数据文件会自动检测（zip/rar/txt）
# 报告生成在 data_eval/reports/index.html
```

### 6.2 评估脚本参数

```python
WORKSPACE = "/path/to/data"      # 数据目录
OUTPUT_DIR = f"{WORKSPACE}/reports"  # 报告输出目录
HISTORY_FILE = f"{WORKSPACE}/eval_history.json"  # 历史记录
```

## 七、输入文件处理

### 7.1 支持的格式

| 格式 | 处理方式 | 说明 |
|------|---------|------|
| **ZIP** | ditto解压 | macOS中文编码支持 |
| **RAR** | unrar解压 | 需安装unrar |
| **TXT** | 直接读取 | 大文件流式处理 |
| **JSON** | json解析 | 结构化数据 |
| **JSONL** | 逐行解析 | 轨迹数据 |

### 7.2 文件识别规则

| 文件名关键词 | 数据类型 | 分析方式 |
|------------|---------|---------|
| thinking | 推理/Reasoning | Thinking数据分析 |
| gui | GUI交互 | GUI轨迹分析 |
| agent coding | Agent轨迹 | Agent轨迹分析 |
| swebench | SWE-工程 | SWE-bench分析 |
| l3/l4 | 任务轨迹 | 任务数据分析 |
| 网页/站点 | 预训练 | 通用分析 |

## 八、输出报告结构

### 8.1 汇总表格

| Dataset | Type | Size | Tokens | Score | Grade | Recommendation |
|---------|------|------|--------|-------|-------|----------------|

### 8.2 详细卡片

每个数据集包含：
1. 数据类型标签（预训练/中训练/后训练）
2. 统计信息（Tokens/Size/Samples/Language）
3. 模型标签（紫色）
4. 智能体标签（黄绿色）
5. 评分维度条
6. 评估原因
7. 改进建议
8. 采购建议（BUY/EXPAND/VERIFY）

## 九、质量阈值参考

| 等级 | 综合得分 | 采购建议 |
|------|---------|---------|
| A | ≥85 | 推荐采购 |
| B | 70-84 | 需补充数据 |
| C | <70 | 需验证 |

## 十、注意事项

1. **累加模式**：新数据集自动加入报告，不删除历史
2. **模型检测**：基于文件内容正则匹配，可能漏检
3. **Token估算**：基于文件大小/4，仅供参考
4. **中文编码**：ZIP文件使用ditto解压避免乱码

---

使用本Skill时，请提供：
1. 数据文件路径（支持zip/rar/txt等多种格式）
2. 工作目录路径（用于自动扫描）

输出将保存在 `<workspace>/data_eval/reports/index.html`。
