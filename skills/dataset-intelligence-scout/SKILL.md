---
name: dataset-intelligence-scout
description: 数据资产智能发现与搬运编排 Skill。用于从外部数据集社区发现最新可搬运数据资产，完成去重、详情采集、大小/license/tag 标准化、CSV 入库清单和 TODO 进度管理；适用于数据集引入、数据资产盘点、搬运候选池建设和数据生态运营场景。
---

# 数据资产智能发现与搬运编排

## 适用场景

当用户需要从外部数据集社区发现最新数据集，并形成可交给搬运/上架链路使用的标准 CSV 清单时，使用本 Skill。

典型任务包括：

- 发现最近更新的数据集候选
- 生成数据资产搬运 CSV
- 去重已有搬运候选，避免重复登记
- 补齐数据集简介、标签、许可协议、大小等元数据
- 维护单次搬运任务的进度和跳过原因

当前默认采集入口是魔搭社区最近更新数据集页；如用户指定其他数据集来源，也应沿用本 Skill 的去重、字段标准化和进度管理规则。

## 关键约束

- 开始前必须建立任务记录，避免浏览器自动化产生大量上下文后丢失进度。
- 每次任务创建独立目录，目录名使用 `dataset_scout_YYYY-MM-DD_HH-MM-SS`。
- 写入 CSV 前必须运行去重脚本。
- 数据集大小大于 512GB 时跳过，不写入 CSV。
- 数据集大小未显示时允许留空并继续登记。
- CSV 的 Hugging Face 链接列留空，后续如有映射再补。
- 上传令牌不得写死在公开仓库中，必须由用户在私有配置或运行时输入提供。
- 单个数据集最多 5 个标签，标签之间用中文顿号分隔。
- license 映射失败时填 `8`。

## 执行流程

### 1. 创建任务目录和进度文件

在用户指定的工作目录下创建：

```text
dataset_scout_YYYY-MM-DD_HH-MM-SS/
├── datasets.csv
└── TODO.md
```

如果工作目录下已有 `dataset_scout_*` 目录，先查看近期任务，判断是否已经处理过同一批最近更新数据集。

### 2. 获取候选数据集列表

默认访问魔搭社区最近更新数据集页：

```text
https://www.modelscope.cn/datasets?sort=latest
```

从列表页提取候选数据集名称和详情页链接。获取候选列表后，立即写入任务记录或 `TODO.md`，标记为待处理。

### 3. 执行批量去重

在工作目录下运行本 Skill 自带脚本：

```bash
python skills/dataset-intelligence-scout/scripts/check_duplicate.py "数据集名1" "数据集名2"
```

脚本会扫描当前工作目录下所有 `dataset_scout_*/datasets.csv`，返回重复项和可新增项。

处理规则：

- 重复数据集：跳过，并在 `TODO.md` 记录跳过原因。
- 新数据集：继续进入详情采集。

### 4. 逐个采集详情

对每个新数据集进入详情页，采集：

- 数据集名称
- 详情页链接
- 简介
- 标签
- 开源协议
- 大小

大小只以详情页展示为准。列表页没有可靠大小信息时，不要推断。

名称清洗规则：

- 如果名称带有来源平台或组织前缀，只在“数据集名称”列保留后半部分的资产名。
- 详情页链接保留完整 URL。

### 5. 标准化字段并写入 CSV

CSV 字段和格式见 [references/csv_format.md](references/csv_format.md)。

处理时按需读取：

- license 映射：[references/license_mapping.md](references/license_mapping.md)
- 标签规范：[references/tag_spec.md](references/tag_spec.md)

写入要求：

- 只写入去重后的新数据集。
- 每完成一个数据集就立即写入 CSV，不要等全部处理完再统一保存。
- 上传令牌从用户提供的私有令牌池中选择；如果用户未提供令牌，填 `<UPLOAD_TOKEN_REQUIRED>` 并在 TODO 中标注待补。

### 6. 更新 TODO.md

每处理完一个数据集，立即更新进度：

```markdown
# 数据资产搬运候选进度

任务开始：2026-02-24 14:30:15
任务结束：（完成后填写）

## 统计
- 目标数量：20
- 已完成：15
- 已跳过(>512GB)：2
- 已跳过(重复)：3

## 已完成
- [x] WorldVQA - 已记录 CSV

## 已跳过
- [ ] big-dataset - 超过 512GB
- [ ] existing-dataset - 已在历史 CSV 中登记
```

## 输出要求

最终向用户汇报：

- 任务目录路径
- 新增登记数量
- 重复跳过数量
- 超大数据集跳过数量
- 需要人工补齐的字段，如上传令牌、缺失大小或待确认 license
- `datasets.csv` 和 `TODO.md` 的位置

## 参考资料

- CSV 格式：[references/csv_format.md](references/csv_format.md)
- License 映射：[references/license_mapping.md](references/license_mapping.md)
- 标签规范：[references/tag_spec.md](references/tag_spec.md)
- 去重脚本：[scripts/check_duplicate.py](scripts/check_duplicate.py)
