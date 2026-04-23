---
name: github-pr-daily-monitor
description: |
  GitHub PR 每日监控与分析 Skill。用于自动拉取指定 GitHub 仓库过去24小时的 PR 记录，对比分析多个项目的 PR 动态，识别高价值 PR（新模型支持、新推理能力、性能优化等），按可宣传性排序生成简明日报。

  触发场景：
  - 用户要求"监控XX项目的PR动态"、"每日PR简报"
  - 用户要求"对比XX和YY的PR"、"分析PR亮点"
  - 用户要求"追踪XX的技术进展"、"观测推理工具进展"
  - 说"PR日报"、"github动态"、"监控PR"、"拉取PR记录"
  - 设置定时 PR 监控任务

  关键原则：凡是技术动态追踪、产品进展观测等场景，必须实时拉取 GitHub 数据，不得仅凭训练知识回答（训练知识已过时）。
---

# GitHub PR 每日监控与分析

本 Skill 自动完成 GitHub PR 数据采集、对比分析、高价值标注、日报生成全流程。

## 环境前置检查

```bash
# 1. 确认 gh CLI 已安装并登录
gh --version

# 2. 确认已登录 GitHub
gh auth status
```

若未安装 gh，请参考：[GitHub CLI 安装指南](https://cli.github.com/manual/installation)

若未登录，运行 `gh auth login` 完成认证。

---

## 执行步骤

### Step 1：采集 PR 数据

使用 `gh pr list` 命令分别获取各项目的 PR 记录。

#### 命令格式

```bash
gh pr list --repo <owner/repo> --state all --limit 100 --json number,title,author,createdAt,mergedAt,labels --search "created:>=$(date -v-1d '+%Y-%m-%d')"
```

#### 示例：采集 vllm 和 fastdeploy

**vllm 项目：**

```bash
gh pr list --repo vllm-project/vllm --state all --limit 50 \
  --json number,title,author,createdAt,mergedAt,labels \
  --search "created:>=$(date -v-1d '+%Y-%m-%d')" > /tmp/vllm_prs.json
```

**fastdeploy 项目：**

```bash
gh pr list --repo PaddlePaddle/FastDeploy --state all --limit 50 \
  --json number,title,author,createdAt,mergedAt,labels \
  --search "created:>=$(date -v-1d '+%Y-%m-%d')" > /tmp/fastdeploy_prs.json
```

**Windows 系统使用 `date` 替代命令：**

```powershell
# PowerShell 格式
$date = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
gh pr list --repo vllm-project/vllm --state all --limit 50 --json number,title,author,createdAt,mergedAt,labels --search "created:>=$date"
```

#### 输出格式示例

```json
[
  {
    "number": 1234,
    "title": "feat: support new attention kernel",
    "author": { "login": "contributor" },
    "createdAt": "2026-04-19T10:00:00Z",
    "mergedAt": "2026-04-19T14:00:00Z",
    "labels": ["enhancement", "performance"]
  }
]
```

---

### Step 2：合并 PR 数据

将两个项目的 PR 数据合并为一个 JSON 文件：

```bash
jq -s '.[0] + .[1]' /tmp/vllm_prs.json /tmp/fastdeploy_prs.json > /tmp/all_prs.json
```

或手动读取两个 JSON 文件内容后合并。

---

### Step 3：分析并生成报告

将 PR 数据发送给 Claude 进行分析，prompt 模板如下：

---

**分析 Prompt：**

```
请分析以下两个开源项目（vLLM 和 FastDeploy）过去24小时内的 PR 记录。

【PR 数据】
（将 /tmp/all_prs.json 的内容粘贴在此）

【分析要求】
1. **对比分析**：对比两个项目的 PR 数量、类型、贡献者活跃度
2. **高价值 PR 识别**：重点标注以下类型的 PR：
   - 新模型支持（如支持新模型架构、新模型权重）
   - 新推理能力（如新量化方法、新调度策略）
   - 性能优化（显著性能提升）
   - 重大功能更新（新增核心功能）
   - Bug 修复（影响大的关键修复）
3. **可宣传性评估**：评估每个高价值 PR 对外宣传的价值（1-5星）
4. **排序输出**：按可宣传性从高到低排序

【输出格式】
## PR 每日简报
**日期：YYYY-MM-DD**

### 概览
| 项目 | PR总数 | 合入数 | 活跃贡献者 |
|------|--------|--------|------------|
| vLLM | XX | XX | XX |
| FastDeploy | XX | XX | XX |

### 高价值 PR 排名（按可宣传性排序）
1. **[项目名] #PR号 - PR标题**
   - 类型：新模型支持 / 新推理能力 / 性能优化 / 重大功能 / Bug修复
   - 描述：（简要说明）
   - 可宣传性：⭐⭐⭐⭐⭐
   - 合入时间：YYYY-MM-DD

2. ...

### 分析小结
（2-3句话总结两个项目的技术动态对比）
```

---

### Step 4：保存报告

将生成的报告保存到本地文件：

```bash
REPORT_DATE=$(date '+%Y%m%d')
REPORT_DIR="$HOME/Downloads/github_pr_reports"
mkdir -p "$REPORT_DIR"
```

报告内容写入：

```
~/Downloads/github_pr_reports/pr_daily_report_YYYYMMDD.md
```

---

## 定时任务设置

完成后，询问用户是否需要设置每日定时任务：

> "是否设置每天上午10点自动执行 PR 监控并生成简报？"

若用户确认，使用 CronCreate 工具设置：

```
cron: "0 10 * * *"
recurring: true
prompt: <包含完整 PR 采集-分析-保存流程的 prompt>
```

---

## 错误处理

| 问题 | 解决方案 |
|------|----------|
| gh: command not found | 安装 GitHub CLI：https://cli.github.com/ |
| gh auth required | 运行 `gh auth login` 完成登录 |
| API rate limit | 使用 `--paginate` 或设置 `GH_TOKEN` 环境变量增加限额 |
| 无 PR 数据 | 可能项目24小时内确实没有PR，检查日期是否正确 |

---

## 参考文件

- `references/target_repos.md` — 监控目标仓库列表
- `references/value_keywords.md` — 高价值 PR 关键词列表