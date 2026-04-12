---
name: okr-review
description: |
    OKR自动化评审评估。当用户需要进行OKR review、OKR评审、OKR打分、OKR评估时使用此skill。
    支持从Excel/PDF/文本输入OKR数据，自动按5个维度（KR完成度35%、目标挑战性20%、战略对齐度20%、
    OKR书写质量10%、自评合理性15%）进行评分，1-5分映射S/A/B/C/D等级，输出个人评估报告和汇总排名表。
    默认使用百度文心大模型，数据自动脱敏保障安全。
---

# OKR自动化评审 Skill

## 使用场景

用户说以下类似内容时触发此skill：
- "帮我做OKR评审"
- "评估一下这批OKR"
- "OKR打分"
- "review一下OKR"

## 工作流程

### Step 1: 确认数据来源

询问用户数据准备方式：
1. **Excel文件** — 已有按模板填好的Excel
2. **PDF文件** — 从如流导出的PDF（支持批量，放在一个目录下）
3. **文本粘贴** — 直接复制如流页面内容

如果用户还没有数据模板，先生成模板：
```bash
cd okr-eval-agent && python3 main.py template --type okr --output data/input/okr_template.xlsx
```

### Step 2: 确认评分标准

告知用户当前评分维度和权重，询问是否需要调整：

| 维度 | 权重 | 说明 |
|------|------|------|
| KR完成度 | 35% | 定量指标达成率 + 客观打标 |
| 目标挑战性 | 20% | O的难度和野心程度 |
| 任务完成度 | 20% | 与团队/部门目标关联 |
| OKR书写质量 | 10% | SMART原则、可衡量性 |
| 自评合理性 | 15% | 主观自评与客观结果一致性 |

如需调整，修改 `okr-eval-agent/config/rubric_okr.yaml`。

### Step 3: 执行评估

根据用户选择的数据来源执行对应命令：

**Excel方式：**
```bash
cd okr-eval-agent && python3 main.py okr --input <用户提供的文件路径>
```

**PDF自动化方式：**
```bash
cd okr-eval-agent && python3 main.py auto --mode okr --input-dir <PDF目录>
```

**PDF + Vision模式（复杂PDF）：**
```bash
cd okr-eval-agent && python3 main.py auto --mode okr --input-dir <PDF目录> --vision
```

### Step 4: 展示结果

评估完成后，向用户汇报：
1. 等级分布（S/A/B/C/D各多少人）
2. 推优候选名单（S+A级）
3. 需关注人员（C+D级）
4. 边界人员（建议人工复核）
5. 告知报告文件位置（`data/output/` 下的Markdown和Excel）

### Step 5: 交互调整

如果用户对结果不满意：
- 支持调整个别人的评分
- 支持修改评分标准后重新跑
- 支持导出调整后的最终报告

## 环境要求

- Python 3.9+
- 百度千帆API密钥（环境变量 QIANFAN_ACCESS_KEY / QIANFAN_SECRET_KEY）
- 依赖安装：`cd okr-eval-agent && pip3 install -r requirements.txt`

## 关键文件

- 评分标准：`okr-eval-agent/config/rubric_okr.yaml`
- 等级映射：`okr-eval-agent/config/grade_mapping.yaml`
- CLI入口：`okr-eval-agent/main.py`
- 输出目录：`okr-eval-agent/data/output/`
