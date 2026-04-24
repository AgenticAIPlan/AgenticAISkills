# 材料论文数据提取器 (Material Paper Extractor)

从合金研究论文（PDF）中提取结构化的成分-工艺-微观结构-性能数据。

## 功能概述

本工具从材料科学论文中自动提取结构化的 JSON 数据，包括：
- **成分信息** (Composition): 标称成分、实测成分、元素含量
- **工艺信息** (Process): 加工工艺、设备参数、热处理条件
- **微观结构** (Microstructure): 主相、析出相、孔隙率、晶粒度
- **性能数据** (Properties): 屈服强度、抗拉强度、伸长率、硬度等

## 处理流程

```
PDF
 │
 ▼
Step 1  OCR识别       →  01_ocr/{id}.json
 │
 ▼
Step 2  文本整合      →  02_combine/{id}.txt  ← 后续步骤的真值依据
 │
 ▼
Step 3  数据提取      →  03_extract/{id}.json
 │
 ▼
Step 4  脚本验证      →  04_validate/{id}.json  [+ _issues.md 如有问题]
 │
 ▼
Step 5  人工审核      →  05_review/{id}_review.md
 │
 ▼
Step 6  修订更正      →  06_revise/{id}_revised.json  [+ _revision_notes.md]
 │
 ├──▶ Step 7  对比评估 (可选，基于comparison_path)
 │              →  07_evaluate/{id}_evaluation.md
 │
 ▼
Step 8  汇总报告
 ├── 8A (脚本)  →  08_summary/06_revise_summary.json / .csv / _stats.md
 └── 8B (LLM)   →  08_summary/evaluation_summary.md (可选)
```

**真值原则**: `02_combine/{id}.txt` 是论文的标准文本，步骤 3 开始的所有数据都基于并以此为评估依据。

## 目录结构

```
{output_base}/
├── 01_ocr/            Step1 — PaddleOCR 输出
├── 02_combine/        Step2 — 整合后的原始文本（真值）
├── 03_extract/        Step3 — 提取结果
├── 04_validate/       Step4 — 验证后的数据
├── 05_review/         Step5 — 审核报告
├── 06_revise/         Step6 — 修订后的数据
├── 07_evaluate/       Step7 — 对比评估（可选）
└── 08_summary/        Step8 — 汇总报告
```

## 使用方法

### 前提条件

1. 安装 PaddleOCR 文档解析工具
2. 配置环境变量：

```bash
export PADDLEOCR_DOC_PARSING_API_URL="<your-paddleocr-endpoint>"
export PADDLEOCR_ACCESS_TOKEN="<your-paddleocr-token>"
```

### 执行步骤

1. 确定 `{output_base}` 输出目录（建议包含时间戳，如 `/path/to/output/20260408/`）
2. 确定每篇论文的 `{id}`（使用文件名或作者-年份格式）
3. 依次执行 Step 1-6
4. 如有对比数据，执行 Step 7
5. 所有论文处理完成后，执行 Step 8

### 关键约束

- **禁止猜测**: 论文中未提供的数据必须填充 `null`，禁止推断为常见值
- **温度隔离**: 试验温度字段仅用于机械/物理测试时的环境温度，绝不可填入制造温度
- **拉伸/压缩互斥**: 压缩试验数据必须使用 `_Compressive` 后缀
- **伸长率区分**:
  - `Elongation_Total`: 总伸长率 (A)
  - `Elongation_Uniform`: 均匀伸长率 (Ag)
  - `Elongation_At_Fracture`: 断裂伸长率 (Af)
- **相对密度**: 未提供时必须为 `null`，禁止默认为 100%

## 输出格式

提取的数据遵循严格的 JSON Schema，主要结构如下：

```json
{
  "Paper_Metadata": {
    "Paper_Title": "论文标题",
    "DOI": "DOI号"
  },
  "items": [
    {
      "Sample_ID": "样本ID",
      "Gradient_Material": false,
      "Composition_Info": {
        "Role": "Target/Reference",
        "Alloy_Name_Raw": "合金原始名称",
        "Nominal_Composition": {...},
        "Measured_Composition": {...},
        "Note": "特殊成分说明"
      },
      "Process_Info": {
        "Process_Category": "工艺类别",
        "Process_Text": {"original": "...", "simplified": "..."},
        "Equipment": "设备信息",
        "Key_Params": {"参数名": "值"}
      },
      "Microstructure_Info": {
        "Microstructure_Text": {"original": "...", "simplified": "..."},
        "Main_Phase": "主相",
        "Precipitates": [...],
        "Porosity_pct": null,
        "Relative_Density_pct": null,
        "Grain_Size_avg_um": null
      },
      "Properties_Info": [
        {
          "Property_Name": "Yield_Strength",
          "Test_Condition": "测试条件描述",
          "Value_Numeric": 850.0,
          "Value_Range": null,
          "Value_StdDev": 15.0,
          "Unit": "MPa",
          "Test_Temperature_K": 298.15,
          "Strain_Rate_s1": "1×10⁻³",
          "Tensile_Speed_mm_min": 1.0,
          "Data_Source": "text"
        }
      ]
    }
  ]
}
```

## 验证规则

Step 4 使用 Python 脚本进行自动验证，检查：
- 角色值是否合法 (Target/Reference)
- 成分总和是否 ≤ 100%
- 数值范围是否合理
- 是否错误使用 Main_Phase（禁止使用 Laves、碳化物等）
- 伸长率边界检查
- 屈服强度 ≤ 抗拉强度检查

## 文件路径规则

所有子代理必须严格遵循以下路径：

| 步骤 | 输出 | 路径 |
|------|------|------|
| Step1 | OCR JSON | `{output_base}/01_ocr/{id}.json` |
| Step2 | 整合文本 | `{output_base}/02_combine/{id}.txt` |
| Step3 | 提取JSON | `{output_base}/03_extract/{id}.json` |
| Step4 | 验证JSON | `{output_base}/04_validate/{id}.json` |
| Step5 | 审核报告 | `{output_base}/05_review/{id}_review.md` |
| Step6 | 修订JSON | `{output_base}/06_revise/{id}_revised.json` |
| Step7 | 评估报告 | `{output_base}/07_evaluate/{id}_evaluation.md` |
| Step8A | 汇总JSON | `{output_base}/08_summary/06_revise_summary.json` |
| Step8A | 汇总CSV | `{output_base}/08_summary/06_revise_summary.csv` |
| Step8B | 叙述总结 | `{output_base}/08_summary/evaluation_summary.md` |

## 相关文件

| 步骤 | 资源 | 路径 |
|------|------|------|
| Step3 | 提取规则+Schema | `references/03-extract-system-prompt.md` |
| Step3 | 提取工作流 | `references/03-extract-user-prompt.md` |
| Step4 | 验证脚本 | `scripts/04-validate.py` |
| Step5 | 审核提示 | `references/05-review.md` |
| Step6 | 修订提示 | `references/06-revise.md` |
| Step7 | 评估提示 | `references/07-evaluate.md` |
| Step8 | 汇总脚本 | `scripts/08-summarize.py` |
| Step8 | 汇总提示 | `references/08-summary.md` |

## 触发关键词

使用此技能处理：
- "extract materials" / "材料数据提取"
- "parse alloy paper" / "合金论文解析"
- "materials data extraction"
- "composition processing properties"
- 材料科学论文 PDF 结构化数据提取