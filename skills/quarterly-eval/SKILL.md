---
name: quarterly-eval
description: |
    季度评优自动化评估筛选。当用户需要进行季度评优、季度考核、人员筛选、评优打分时使用此skill。
    支持从Excel/PDF/文本输入mentor评语和产出数据，自动按5个维度（产出质量30%、创新突破25%、
    成长进步20%、行动力15%、影响力10%）评分，分档排序识别优秀/达标/待改进人员，
    输出汇总排名Excel和个人评估报告。默认使用百度文心大模型。
---

# 季度评优自动化评估 Skill

## 使用场景

用户说以下类似内容时触发此skill：
- "帮我做季度评优"
- "筛选季度优秀"
- "评估这批人的季度表现"
- "季度考核打分"

## 工作流程

### Step 1: 确认数据来源

询问用户数据准备方式：
1. **Excel文件** — 已按模板填好（含mentor评语、产出、新颖度等字段）
2. **PDF文件** — 从如流导出的评优材料PDF
3. **文本粘贴** — 直接复制mentor评语

如果用户还没有数据模板，先生成：
```bash
cd okr-eval-agent && python3 main.py template --type quarterly --output data/input/quarterly_template.xlsx
```

### Step 2: 确认评分标准

| 维度 | 权重 | 说明 |
|------|------|------|
| 产出质量 | 30% | 季度核心产出完成度和质量 |
| 创新突破 | 25% | 项目新颖度、方法创新、重大贡献 |
| 成长进步 | 20% | 对比上季度的提升幅度 |
| 行动力 | 15% | 执行力和主动性 |
| 影响力 | 10% | 对团队/业务的实际影响 |

如需调整，修改 `okr-eval-agent/config/rubric_quarterly.yaml`。

### Step 3: 执行评估

**Excel方式：**
```bash
cd okr-eval-agent && python3 main.py quarterly --input <文件路径>
```

**PDF自动化：**
```bash
cd okr-eval-agent && python3 main.py auto --mode quarterly --input-dir <PDF目录>
```

**全自动（跳过确认）：**
```bash
cd okr-eval-agent && python3 main.py auto --mode quarterly --input-dir <PDF目录> -y
```

### Step 4: 展示结果

评估完成后汇报：
1. **等级分布**：S/A/B/C/D人数和占比
2. **推优候选**：S+A级人员名单和亮点
3. **达成目标**：S+A+B级总人数
4. **需关注**：C+D级人员和改进建议
5. **边界人员**：距等级线±0.2分的人员（建议复核）
6. 报告位置：`data/output/` 下的Excel和Markdown

### Step 5: 支持决策

- 告知用户汇总Excel可直接发给领导和HR
- 如需调整，支持修改后重新生成
- 对比上季度结果（如有历史数据）

## 环境要求

- Python 3.9+
- 百度千帆API密钥
- 依赖安装：`cd okr-eval-agent && pip3 install -r requirements.txt`

## 关键文件

- 评分标准：`okr-eval-agent/config/rubric_quarterly.yaml`
- 等级映射：`okr-eval-agent/config/grade_mapping.yaml`
- CLI入口：`okr-eval-agent/main.py`
- 输出目录：`okr-eval-agent/data/output/`
