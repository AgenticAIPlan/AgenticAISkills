---
name: llm-solution-techdoc-latex
description: 通过 LaTeX 生成面向客户交付的「企业大模型技术方案」类 PDF（学术/公文风格排版），包含能力与客户系统映射、集成架构示意、分场景收益与 KPI、部署/安全/运维与版本控制表。适用于投标/POC 技术附件、客户技术建议书、需版式统一且可追溯的交付文档场景。
---

# 企业大模型技术方案（LaTeX）

用 LaTeX 生成典型「技术方案 / 交付文档」结构，显式建立 **大模型可交付能力** 与 **客户现有产品/系统** 之间的映射关系；不绑定特定厂商或模型品牌，具体平台与指标以合同与官方材料为准。

## 输入（收集或由用户给定）

- 客户画像：`customer_name`、`industry`、`current_products[]`
- 目标场景：`scenarios[]`（痛点 → 能力 → 集成 → KPI）
- 大模型能力范围：`llm_capabilities[]`（仅写已开通/已采购项；否则标「待确认」）
- 集成约束：`data_sources[]`、`deployment_mode`、`security_compliance[]`
- 运维要求：`sla`、`monitoring`、`cost_model`（允许占位）

## 执行流程

1. 编辑 `assets/sample-input.json`（或自建 JSON，字段名与样例一致）。
2. 运行：
   - `python3 scripts/generate_techdoc.py --input assets/sample-input.json --outdir output --compile --engine tools/tectonic/tectonic`
   - 若本机未装 LaTeX，可用 `--preview` 生成可审阅的纯文本（并尝试用系统 `cupsfilter` 生成简易 PDF）：`... --preview`
3. 交付物：
   - `output/llm-solution-techdoc.tex`
   - `output/llm-solution-techdoc.pdf`（编译成功时）
   - `output/llm-solution-techdoc.preview.pdf`（使用 `--preview` 且 `cupsfilter` 可用时）

## 安装 Tectonic（推荐）

若 `tools/tectonic/tectonic` 不存在，可在 Unix/macOS 下安装：

1. 下载安装脚本：`curl -L --fail --silent --show-error -o install-tectonic.sh https://drop-sh.fullyjustified.net`
2. 在 `tools/tectonic/` 目录执行：`sh install-tectonic.sh`

（`tectonic` 是独立的 TeX/LaTeX 引擎，负责解析 `.tex` 并输出 PDF；`curl` 用于下载官方分发脚本。）

## 规则（保证表述可审计）

- 无合同或官方材料时，**不要**写死具体模型版本或评测指标；用「以实际开通能力为准 / 待确认」占位。
- 优势描述与 **场景** 绑定（时延、成本、准确率、合规、TCO 等），避免空洞营销话术。
- 映射关系优先用表格：能力 ↔ 产品模块 ↔ 集成方式 ↔ 预期收益 ↔ KPI。

## 随包资源

- `assets/techdoc-template.tex`：LaTeX 模板（`ctexart` + 企业文档结构）
- `assets/sample-input.json`：可跑通的示例数据
- `scripts/generate_techdoc.py`：JSON → `.tex` 渲染，并可选用 `tectonic` / `xelatex` / `pdflatex` 编译

### 依赖说明（Python 标准库）

- `argparse`：命令行参数（`--input` / `--outdir` / `--compile` 等）。
- `json`：读取结构化输入。
- `pathlib.Path`：路径拼接与读写文件。
- `subprocess`：调用外部 LaTeX 引擎或 `cupsfilter`。
- `shutil.which`：在 `PATH` 中查找可执行文件。
