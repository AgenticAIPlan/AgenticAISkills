---
name: project-handover
version: 1.0
description: |
  辅助项目/岗位交接的全流程 Agent Skill。将原负责人的隐性知识转化为可复用的数字资产，交接后可随时向 Agent 追问细节。
  触发条件（满足任一即激活）：
  - "项目交接""岗位交接""知识转移""handover""knowledge transfer"
  - "我要接手XX的工作""XX要走了需要交接""新人入职交接"
  - "帮我规划交接方案""生成交接清单""交接知识库"
  - "帮我整理交接文档""交接手册"
  不触发（这些是其他 Skill 的职责）：
  - 纯文档总结/会议纪要整理/项目进度汇报 → 通用写作任务
  - 新建项目/制定项目计划 → 项目管理类 Skill
  - 单纯的问答/知识检索 → RAG 或搜索类 Skill
  - 单独的"交接"一词（如交接文件、交接班）→ 非本 Skill 范围
---

# 项目交接 Skill

把"项目/岗位交接"这件事，稳定地执行成一条可复用的流水线。

核心理念：**Agent 成为原负责人的"代言人"**——不是被动回答问题，而是主动挖掘隐性知识、发现交接盲区、沉淀为可长期查询的数字资产。

```
输入 → Step0 范围评估(门禁) → Step1 问题清单(6维度) → Step2 材料收集
     → Step3 知识提炼(分类+交叉验证) → Step4 覆盖度自检(门禁≥60%)
     → Step5 手册生成 → Step6 记忆写入 → Step7 终审(质量门禁)
     → 输出：交接手册 + 记忆文件 + 覆盖度报告
```

## 适用场景

同事离职/轮岗交接 | 新人入职快速上手 | 项目移交 | 长期项目归档 | 主动知识资产化

## 输入约定

### 必填项

| 字段 | 说明 | 示例 |
|------|------|------|
| `交接人`（原负责人） | 知识的来源方 | "张三 / 学科运营组" |
| `被交接人`（接手方） | 知识的接收方 | "李四 / 我自己" |
| `交接范围` | 需要交接的具体内容 | "教师运营全流程 + 星河社区维护" |

### 可选项

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `材料路径` | 原始文档/知识库的路径 | 无，Step 2 再收集 |
| `交接截止日` | 交接完成的日期 | 无，不设截止 |
| `调研深度` | 快速 / 标准 / 深度 | 标准 |
| `已有记忆文件` | Agent 记忆路径 | `.claude/memory/` |

### 输入校验规则

- 用户只说"帮我做个交接"但没说交接什么 → **追问**，不要猜测范围
- 用户说了交接对象但描述模糊（如"运营相关的工作"）→ 按标准维度走完整流程
- 用户已提供完整材料路径 → 可跳过 Step 2 直接进入 Step 3

## 工具选择

| 能力 | 用途 | 优先级 |
|------|------|--------|
| `WebFetch` / `Read` | 读取文档、知识库、代码仓库 | 首选 |
| `Glob` / `Grep` | 搜索项目文件、配置 | 首选 |
| `Bash` | 执行脚本（覆盖度评分等） | 按需 |
| `Write` / `Edit` | 写入手册、记忆文件 | 输出阶段 |
| `CronCreate` | 设置交接跟进提醒 | Step 6（可选） |

如果需要外部搜索（原负责人的公开资料等），使用 WebSearch。

## 依赖与兼容性

| 依赖项 | 类型 | 必要性 | 不可用时的降级方案 |
|--------|------|--------|-------------------|
| `Write`/`Edit`/`Read` 工具 | Agent 能力 | **硬依赖** | 无法写入文件时，全部内容输出到交接手册，提示用户手动保存记忆文件 |
| `.claude/memory/` 目录 | 文件系统 | **硬依赖** | 目录不存在时，使用用户指定的路径或当前目录下 `memory/` |
| `WebFetch` | Agent 能力 | 软依赖 | 无法访问外部 URL 时，仅处理本地文件，标注 `[外部资源不可读]` |
| `CronCreate` | Agent 能力 | 可选 | 无法设置定时提醒时，在手册中列出需跟进事项，由用户自行安排 |
| `knowledge_coverage_scorer.py` | 脚本 | 可选 | 脚本不可执行时，Agent 在 Step 4 手动评估覆盖率（精确度略低） |

**与相邻 Skill 的兼容性**：当本 Skill 与 `org-research`、`data-resource-evaluation` 等同时安装时，以用户明确指令为准。如果用户说"交接"，走本 Skill 流程；如果说"调研某个机构"，走 `org-research`。

## 执行流程

### Step 0：交接范围评估

**目标**：明确交接边界，防止范围蔓延。

1. 从输入中提取 `交接人`、`被交接人`、`交接范围`
2. 范围模糊则向用户确认（最多 2 轮）：交接哪些模块？有没有不在范围内的？
3. 输出交接范围确认单（含交接人、被交接人、交接范围列表、预计产出）

> **门禁**：没有明确交接人和交接范围 → 不得进入 Step 1。

### Step 1：生成交接问题清单

**目标**：按 6 个维度生成结构化问题清单，确保不遗漏关键信息。

维度定义详见 [`references/handover-dimensions.md`](references/handover-dimensions.md)。

6 个维度：业务流程 | 项目与待办 | 联系人 | 隐性知识与决策 | 模板与资产 | 风险与异常

**裁剪规则**：
- `快速`模式：每维度 3-4 题，合计 18-24 题
- `标准`模式：每维度 5-6 题，合计 30-36 题
- `深度`模式：每维度 6-8 题，合计 36-48 题

> **门禁**：问题总数 < 15 → 检查是否遗漏维度。

### Step 2：收集原始材料

**目标**：系统收集交接所需的全部素材。

材料类型：业务文档 | 项目文件 | 聊天记录（需导出）| 会议纪要 | 权限清单 | 联系人信息

1. 用户已提供材料路径 → 直接读取
2. 未提供 → 按维度列出需收集的材料清单
3. 对已收集材料做维度分类
4. 关键材料缺失标注为 `信息缺口`

完成后输出**材料覆盖摘要**，展示每个维度的已收集材料和缺口。

> **检查点**：展示摘要给用户。确认 OK → 进入 Step 3。

### Step 3：知识提炼与结构化

**目标**：从原始材料中提取结构化知识。

**详细操作规则**详见 [`references/extraction-rules.md`](references/extraction-rules.md)。

执行流程：
1. **分类**：判断每份材料的文档类型（SOP/会议纪要/项目文档/联系人/报表/话术/口述/其他）
2. **提取**：按文档类型对应的模板提取关键信息（每种类型有固定的输出格式和字段）
3. **交叉验证**：比对多个材料，标注矛盾（`[矛盾]`）和过期信息（`[可能过期]`/`[可能失效]`）
4. **自检**：确认所有材料已分类、来源已标注、矛盾已处理

### Step 4：覆盖度自检

**目标**：对照问题清单检查知识覆盖率。

每个问题标记为：✅已覆盖(100%) | ⚠️部分覆盖(50%) | ❌未覆盖(0%) | 🔍需口述(不计入)

```
维度覆盖率 = (✅×1.0 + ⚠️×0.5) / (✅+⚠️+❌) × 100%
```

自动化评分（快速预筛）：`python3 scripts/knowledge_coverage_scorer.py --questions [清单] --materials [目录]`

> **门禁**：总覆盖率 < 60% → 回 Step 2 补充。任一维度 = 0% → 标记 `[信息缺口]`。

覆盖度报告模板见 [`assets/coverage-report-template.md`](assets/coverage-report-template.md)。

### Step 5：生成交接手册

**目标**：按固定模板输出可交付的交接手册。

输出模板详见 [`assets/handover-manual-template.md`](assets/handover-manual-template.md)。

**硬规则**：
1. 严格遵循模板结构，不得随意增减章节
2. 每条知识标注来源
3. 未覆盖信息标记为 `[待补充]`，**不得编造**
4. 矛盾信息列明双方说法，标记 `[矛盾，需确认]`
5. 术语首次出现时简要解释

**手册命名**：`[项目名]-交接手册-[交接人]-[日期].md`

### Step 6：写入记忆文件

**目标**：将知识写入 Agent 记忆，实现交接后的持续"代言人"能力。

**这是本 Skill 与普通"文档整理"的核心区别。**

记忆持久化规则详见 [`references/memory-persistence-guide.md`](references/memory-persistence-guide.md)。

简要操作：
1. 创建 `handover-[项目名].md`，写入快速参考（核心流程 + 关键联系人 + FAQ + 风险备忘）
2. 在 MEMORY.md 中追加索引条目
3. **Write 后立即 Read 验证**（防静默失败）
4. 记忆文件放在 Skill 目录**外部**（防卸载 Skill 时丢失）

### Step 7：Reviewer 终审

**目标**：对交接手册做最终质量检查。

检查清单详见 [`references/handover-checklist.md`](references/handover-checklist.md)，共 7 类 28 项（A-D 类 error，E-G 类 warning）。

> **门禁**：存在未修复的 `error` 级问题 → 降级为"阶段性交接稿"。

## 最终输出顺序

完成全部流程后，按以下顺序交付：

1. **交接手册**（主要交付物）
2. **覆盖度报告**
3. **交接问题清单**（含填写状态）
4. **信息缺口清单**（如有）
5. **记忆文件路径**

## 输出约定

**交接中**：主动提问补充信息，每次会议后更新知识库，追踪缺口补充进度。

**交接后（代言人模式）**：回答基于交接知识并标注来源。不知道的内容诚实说"交接资料中未覆盖，建议向 [交接人] 确认"。**不要编造或用通用知识冒充交接知识。**

**评估/Dry-run 模式**：输出"本次是评估 dry run：未实际写入记忆文件和手册"，展示步骤和产出物但不执行。

## 降级处理

当理想执行条件不满足时，按降级方案处理。详见 [`references/degradation.md`](references/degradation.md)。

简要规则：宁可降级产出不完美的交接稿，也不产出空白。

常见降级场景：材料完全缺失 → 纯口述版 | 文档过大 → 分批处理 | 交接时间紧迫 → 快速模式 | 记忆写入失败 → 会话内输出 + 提示手动保存

## 常见失败模式

详见 [`references/failure-modes.md`](references/failure-modes.md)。

核心预防：Step 0/4/7 的门禁机制专门针对记忆不持久、知识盲区、编造内容等 6 种典型失败模式设计。

## 示例

### 示例 1：完整交接流程

**输入**："张三下周离职，我要接手他负责的教师运营工作，他的文档在 ~/docs/teacher-ops/"

**执行路径**：Step 0 → Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7

**输出**：`教师运营-交接手册-张三-20260422.md` + 覆盖度报告 + 记忆文件

### 示例 2：知识盲区分析

**输入**："我要接手星河社区的维护，但张三只给了一份简单的文档，帮我分析一下还缺什么"

**执行路径**：跳过 Step 0 → Step 1 → Step 2 → Step 3 → Step 4（覆盖度仅 45%）

**输出**：覆盖度报告 + 信息缺口清单，不生成交接手册，等待补充材料

### 示例 3：交接后代言人

**输入**（交接完成后）："教师认证考试的流程具体是哪几步？"

**执行路径**：Read 记忆文件 → 在"业务流程"维度查找 → 找到对应 SOP → 回答并标注来源

### 示例 4：实战完整案例

> 完整的输入→Step 0~7→产出物演示（含手册片段），详见 [`references/example-full-run.md`](references/example-full-run.md)。

## 参考资料

按需加载，不要一次性全文展开：

**规则与检查**：
- [`references/handover-dimensions.md`](references/handover-dimensions.md)：6 维度详细定义和问题生成规则
- [`references/extraction-rules.md`](references/extraction-rules.md)：Step 3 知识提炼的具体操作规则和模板
- [`references/handover-checklist.md`](references/handover-checklist.md)：Step 7 Reviewer 终审检查清单
- [`references/memory-persistence-guide.md`](references/memory-persistence-guide.md)：记忆持久化完整规则和常见陷阱
- [`references/failure-modes.md`](references/failure-modes.md)：6 种典型失败模式和预防措施
- [`references/degradation.md`](references/degradation.md)：7 种降级方案的详细规则
- [`references/example-full-run.md`](references/example-full-run.md)：实战完整案例（含各步骤输出片段）

**输出模板**：
- [`assets/handover-manual-template.md`](assets/handover-manual-template.md)：交接手册标准模板
- [`assets/coverage-report-template.md`](assets/coverage-report-template.md)：覆盖度报告标准模板

**工具**：
- [`scripts/knowledge_coverage_scorer.py`](scripts/knowledge_coverage_scorer.py)：知识覆盖度自动化评分（关键词预筛，非精确评估）

## 与相邻 Skill 的区分

| 可能混淆的 Skill | 区分标准 |
|-----------------|---------|
| `org-research` | org-research 是对外部机构的调研，本 Skill 是内部项目/岗位的知识转移 |
| `data-resource-evaluation` | 那个 Skill 是评估外部数据资源，本 Skill 不涉及资源评估 |
| 通用文档总结 | 通用总结是"读完生成摘要"，本 Skill 是"提取 + 结构化 + 持久化 + 持续查询" |
| RAG 知识库 | RAG 侧重检索，本 Skill 侧重知识提取、结构化和资产沉淀 |
