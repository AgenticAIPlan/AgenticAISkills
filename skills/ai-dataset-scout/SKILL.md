---
name: ai-dataset-scout
description: "AI数据集发现与采集工具。使用Playwright自动访问AI数据集平台获取最新数据集，将数据集信息记录到CSV文件，支持去重检查和进度追踪。触发词包括：发现数据集、采集数据集、数据集调研、数据集搬运、批量数据集记录。"
---

# AI Dataset Scout

AI数据集发现与采集工具，用于自动从AI数据集平台获取最新数据集信息并记录到CSV，支持批量去重与进度管理。

## 重要警告

**Playwright MCP会产生大量上下文占用**。每次页面快照可能超过50KB。

应对策略：
1. 使用 `TaskCreate` 创建任务记录详细信息，上下文丢失时可回看
2. 每处理完一个数据集，立即更新任务状态并记录关键信息
3. 不要在单次对话中处理过多数据集，建议每次5-10个

## 文件夹结构

每次采集任务创建独立文件夹，精确到秒：

```
工作目录/
└── dataset_scout_YYYY-MM-DD_HH-MM-SS/
    ├── datasets.csv          # 数据集记录
    └── TODO.md               # 任务进度记录
```

示例：`dataset_scout_2026-02-24_14-30-15/`

## 执行流程

### 开始前检查：日期判断与已有任务

**任务文件夹按日期时间命名**，可通过日期判断哪些数据集可能已处理：

```
dataset_scout_2026-02-24_16-04-22/  ← 2月24日16点采集的
dataset_scout_2026-02-23_10-30-00/  ← 2月23日10点采集的
```

**建议操作**：
```bash
# 查看已有任务
ls -la 工作目录/

# 查看已记录的数据集
cd 工作目录
python ~/.claude/skills/ai-dataset-scout/scripts/check_duplicate.py --list
```

### Step 0: 创建任务记录（必须）

**开始前必须创建Task记录！** 这是应对上下文占用的关键措施。

```
TaskCreate:
  subject: 采集N个AI数据集
  description: |
    任务目标：采集N个最新AI数据集信息

    进度记录：
    - [待处理] 数据集列表（开始后填写）

    已完成数据集详情：
    （每完成一个追加记录）
```

### Step 1: 创建任务文件夹

```bash
mkdir -p "工作目录/dataset_scout_$(date +%Y-%m-%d_%H-%M-%S)"
```

### Step 2: 访问数据集平台获取列表

使用Playwright MCP访问目标数据集平台，按最近更新排序获取数据集列表。

从列表页提取：
- 名称
- 链接

**获取列表后立即更新Task记录**，将所有数据集名称写入description。

### Step 3: 批量去重检查（必须）

**在写入CSV前必须执行去重检查！** 避免重复记录已采集过的数据集。

使用去重脚本检查：

```bash
cd 工作目录
python ~/.claude/skills/ai-dataset-scout/scripts/check_duplicate.py "数据集名1" "数据集名2" ...
```

脚本会扫描当前目录下所有 `dataset_scout_*/datasets.csv` 文件，检查是否有重复。

输出示例：
```
============================================================
发现重复数据集：
============================================================
  [重复] xcopa
         已存在于: dataset_scout_2026-02-24_14-30-15/datasets.csv:2

------------------------------------------------------------
新数据集（可添加）：
------------------------------------------------------------
  [新] WorldVQA
  [新] DeepPlanning

摘要: 检查 3 个, 重复 1 个, 新增 2 个
```

**处理规则**：
- 重复的数据集：跳过，不记录到CSV
- 新数据集：继续进入Step 4处理

**其他用法**：
```bash
# 列出所有已记录的数据集
python ~/.claude/skills/ai-dataset-scout/scripts/check_duplicate.py --list
```

### Step 4: 逐个处理数据集

对每个**去重后**的新数据集：

1. **进入详情页获取完整信息**：
   - 点击进入数据集详情页
   - 提取：简介、标签、开源协议、大小
   - **大小过滤**：如果 >512GB，跳过此数据集

2. **记录到CSV**
3. **立即更新Task状态**

### 大小获取规则

**大小信息在详情页，不在列表页！** 必须点进每个数据集详情页才能看到大小。

大小处理规则：
- ≤512GB：正常登记
- >512GB：跳过，不登记
- **未显示大小**：留空，正常登记

### Step 5: 生成CSV

CSV格式详见 [references/csv_format.md](references/csv_format.md)

字段：
```
是否搬运完成,数据集名称,来源链接,标签,简介,开源协议,大小,license映射,抓取渠道
```

### Step 6: 更新TODO.md

每完成一个数据集，更新文件夹内的TODO.md：

```markdown
# 数据集采集进度

任务开始：2026-02-24 14:30:15
任务结束：（完成后填写）

## 统计
- 目标数量：20
- 已完成：15
- 已跳过(>512GB)：2

## 已完成
- [x] moonshotai/WorldVQA - 已记录CSV
- [x] Qwen/DeepPlanning - 已记录CSV

## 已跳过(>512GB)
- [ ] big-dataset - 超过512GB
```

## 参考文档

- **License映射**：[references/license_mapping.md](references/license_mapping.md)
- **标签规范**：[references/tag_spec.md](references/tag_spec.md)
- **CSV格式**：[references/csv_format.md](references/csv_format.md)
- **去重脚本**：[scripts/check_duplicate.py](scripts/check_duplicate.py)

## 注意事项

1. **先创建Task再操作** - 上下文可能随时溢出
2. **每完成一个就更新** - 不要积攒到最后
3. **大小必须从详情页获取** - 列表页没有大小信息，必须点进去看
4. **>512GB的数据集跳过** - 不登记到CSV
5. **大小未显示时留空** - 仍然登记，大小字段为空
6. **写入CSV前必须去重** - 使用 `check_duplicate.py` 脚本检查，跳过已记录的数据集
7. 单个数据集最多5个标签，用中文顿号分隔
8. license映射失败默认为8
9. **数据集名称去除平台前缀** - 如名称包含平台官方前缀，只保留数据集本身名称部分
10. **平台访问如需登录态，请提前准备好认证信息**
