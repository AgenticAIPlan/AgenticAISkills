# ERNIE Case Creator

文心案例内容创作技能 - 基于案例材料自动生成标准化案例说明和PPT

## 📖 简介

ERNIE Case Creator 是一个专门用于文心大模型应用案例内容创作的技能。它能够：

1. **解析多种格式材料**：支持 Word、PPT、PDF 等格式
2. **生成标准化案例文字**：遵循"问题-场景-技术-方案-价值"五段式框架
3. **自动生成案例PPT**：基于固定模板，输出一页标准化案例PPT

## 🎯 适用场景

- 文心大模型应用案例整理
- 案例说明文档撰写
- 案例展示PPT制作
- AICA等项目案例汇总

## 🚀 快速开始

### 前置要求

```bash
# 安装Python依赖（可选，用于PPT生成）
pip install python-pptx

# 其他依赖（用于材料解析）
pip install python-docx PyPDF2
```

### 基本使用

#### 1. 解析案例材料

```python
from scripts.parse_material import MaterialParser

parser = MaterialParser()
result = parser.parse_file('案例材料.docx')

if result['success']:
    print(result['summary'])
```

#### 2. 生成案例文字

```python
from scripts.generate_case_text import CaseTextGenerator, CaseInfo

# 准备案例信息
case_info = CaseInfo(
    project_name="南京古田化工生产专家模型",
    industry="化工制造",
    ernie_models=["ERNIE-4.5-21B"],
    pain_points=["生产经验依赖老师傅", "知识难以标准化传承"],
    solution="基于SFT微调打造化工生产专家模型",
    effects=["新员工培训时间缩短60%", "异常处理效率提升40%"],
    quantitative_data={"percentage_improvements": ["60", "40"]},
    materials=["原始材料内容..."]
)

# 生成案例文字
generator = CaseTextGenerator()
result = generator.generate_from_info(case_info)
print(result['case_text'])
```

#### 3. 生成案例PPT

```python
from scripts.generate_ppt import CasePPTGenerator, CasePPTData

# 准备PPT数据
ppt_data = CasePPTData(
    title="南京古田化工生产专家模型",
    case_description="南京古田化工面临化工生产经验依赖老师傅...",
    effect_metrics=[
        {'value': '60%', 'label': '培训时间缩短'},
        {'value': '40%', 'label': '效率提升'}
    ]
)

# 生成PPT
generator = CasePPTGenerator()
result = generator.generate_ppt_content(ppt_data)
```

## 📋 案例文字框架

案例说明采用"问题-场景-技术-方案-价值"五段式结构：

```
1. 痛点/背景（1-2句话）
   - 明确行业痛点
   - 说明痛点带来的影响

2. 应用环境（1句话）
   - 行业领域
   - 使用场景
   - 目标用户

3. 技术支撑（1-2句话）
   - 文心模型型号
   - 技术适配性
   - 差异化优势

4. 解决方案（2-3句话）
   - 核心功能模块
   - 解决路径
   - 工作流程

5. 价值成果（2-3句话）
   - 量化业务提升
   - 落地应用规模
   - 长期价值
```

**字数要求**：250-350字

## 📊 PPT模板结构

生成的案例PPT采用固定模板布局：

```
┌─────────────────────────────────────┐
│        案例标题                [Logo] │
├────────────────┬────────────────────┤
│                │  [文心大模型应用]   │
│  案例说明文字  │                    │
│                │  效率提升: 95%     │
│  (250-350字)   │  处理时间: 10分钟  │
│                │  项目规模: 300个   │
└────────────────┴────────────────────┘
```

**设计风格**：
- 主色调：蓝色（#1E88E5）
- 辅助色：绿色（#4CAF50）
- 简洁专业风格

## 🔧 核心功能

### 1. 材料解析 (`scripts/parse_material.py`)

- 支持 Word、PPT、PDF、TXT、Markdown 格式
- 自动提取关键信息：
  - 项目名称和行业
  - 文心模型型号
  - 行业痛点
  - 技术方案
  - 量化效果数据

### 2. 文字生成 (`scripts/generate_case_text.py`)

- 生成标准化Prompt
- 遵循五段式框架
- 字数验证（250-350字）
- 内容质量检查

### 3. PPT生成 (`scripts/generate_ppt.py`)

- 基于固定模板布局
- 自动提取效果指标
- 内容格式优化
- 输出.pptx格式文件

## 📚 参考文档

- [案例框架详细说明](references/case_framework.md)
- [优秀案例示例](references/example_cases.md)

## 🎨 示例案例

### 国网四川电力

**案例说明**（328字）：
> 国网四川电力面对35千伏及以上项目投资问效分析效率低下的痛点，传统方法单项目分析耗时2-3小时，严重制约了投资决策的时效性。在电力投资决策场景中，服务于电网规划部门的项目评估团队。
> 
> 项目基于文心大模型与Agentic智能体架构，创新构建"自主规划-工具执行-结果反思"的闭环分析系统。该系统通过智能体自动识别项目关键要素，调度专业分析工具进行模拟计算，并对结果进行自我评估与优化，实现了端到端的智能化分析。
> 
> 实施后，单项目分析耗时从2-3小时骤降至10分钟内，效率提升95%以上。已成功完成300个项目分析，报告自动生成率100%、准确率超90%，为电力行业投资决策智能化树立了新标杆。

**PPT效果指标**：
- 效率提升：95%
- 处理时间：10分钟
- 项目规模：300个

更多示例请查看 [example_cases.md](references/example_cases.md)

## 🔍 使用建议

### 材料准备

1. **完整性**：确保材料包含完整的项目信息
2. **数据化**：尽可能提供量化数据和效果指标
3. **模型明确**：明确标注使用的文心模型型号

### 文字撰写

1. **字数控制**：严格控制在250-350字
2. **逻辑清晰**：遵循五段式框架
3. **数据支撑**：用数据说话，避免空泛描述

### PPT制作

1. **效果指标**：选择2-3个核心指标
2. **数据准确**：确保数据与文字内容一致
3. **视觉平衡**：注意左右布局的平衡

## ⚙️ 配置说明

### 模型识别模式

技能会自动识别以下文心模型型号：

- ERNIE-4.5-21B
- ERNIE-4.5-28B-VL
- ERNIE-5.0
- 文心-4.5-21B
- 文心-4.5-28B-VL
- 文心-5.0

### 数据提取规则

- 百分比提升：`\d+(?:\.\d+)?%`
- 时间对比：`数字+时间单位 → 数字+时间单位`
- 项目规模：`数字+单位（个/项/次/套/用户/场景）`

## 📝 更新日志

### v1.0.0 (2026-04-15)

- ✅ 初始版本发布
- ✅ 支持多种材料格式解析
- ✅ 实现五段式案例文字生成
- ✅ 基于模板生成案例PPT
- ✅ 完善的参考文档和示例

## 🤝 贡献指南

欢迎提交问题和改进建议！

## 📄 许可证

Complete terms in LICENSE.txt

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 技能作者：OpenClaw Team
- 反馈渠道：通过 OpenClaw 平台提交 Issue

---

**注意**：本技能基于"华东案例梳理SOP"开发，适用于所有文心大模型应用案例的标准化整理工作。