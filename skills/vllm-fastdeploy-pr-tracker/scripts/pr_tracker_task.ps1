# vllm-fastdeploy-pr-tracker 定时任务脚本
# 自动采集 vLLM 和 FastDeploy 的 PR 数据并生成报告

$ghPath = "C:\Program Files\GitHub CLI\gh.exe"
$date = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$reportDate = Get-Date -Format "yyyyMMdd"
$reportDir = Join-Path $env:USERPROFILE "Downloads\github_pr_reports"

# 确保报告目录存在
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null

# 采集 vllm PR 数据
$vllmPrs = & $ghPath pr list --repo vllm-project/vllm --state all --limit 50 --json number,title,author,createdAt,mergedAt,labels --search "created:>=$date"

# 采集 FastDeploy PR 数据
$fastdeployPrs = & $ghPath pr list --repo PaddlePaddle/FastDeploy --state all --limit 50 --json number,title,author,createdAt,mergedAt,labels --search "created:>=$date"

# 生成报告（此处为简化版，完整分析可保存原始 JSON 后用 Claude 分析）
$reportPath = Join-Path $reportDir "pr_daily_report_$reportDate.md"

$report = @"
# PR 每日简报

**日期：$reportDate**

## 概览

| 项目 | PR总数 |
|------|--------|
| vLLM | $($vllmPrs.Count) |
| FastDeploy | $($fastdeployPrs.Count) |

## 原始数据

详见 JSON 文件：
- vllm_prs_$reportDate.json
- fastdeploy_prs_$reportDate.json
"@

$report | Out-File -FilePath $reportPath -Encoding utf8

# 保存原始 JSON 数据
$vllmPrs | Out-File -FilePath (Join-Path $reportDir "vllm_prs_$reportDate.json") -Encoding utf8
$fastdeployPrs | Out-File -FilePath (Join-Path $reportDir "fastdeploy_prs_$reportDate.json") -Encoding utf8

Write-Host "Report saved to: $reportPath"