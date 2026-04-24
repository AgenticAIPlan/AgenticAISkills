# GitHub CLI 使用说明

## 安装

```bash
# macOS/Linux
brew install gh

# Windows
winget install --id GitHub.cli

# 或下载安装包
# https://cli.github.com/
```

## 认证

```bash
gh auth login
```

## 获取 PR 数据

```bash
# 基本语法
gh search prs --repo <owner>/<repo> --created "YYYY-MM-DD" --json <fields> --limit <number>

# 示例：获取 vLLM 过去24小时的 PR
gh search prs --repo vllm-project/vllm --created "2026-04-23" --json number,title,author,createdAt,state,url,labels --limit 100

# 示例：获取 FastDeploy 过去24小时的 PR
gh search prs --repo PaddlePaddle/FastDeploy --created "2026-04-23" --json number,title,author,createdAt,state,url,labels --limit 100
```

## 常用字段

| 字段 | 说明 |
|------|------|
| number | PR 编号 |
| title | PR 标题 |
| author | PR 作者 |
| createdAt | 创建时间 |
| state | 状态（open/closed/merged） |
| url | PR 链接 |
| labels | PR 标签 |

## 注意事项

1. 日期格式：`YYYY-MM-DD`
2. 需要认证才能访问私有仓库
3. 无 Token 情况下有 API 限流