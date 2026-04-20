# GitHub API 使用指南

## API 基础

GitHub Outreach Hub 使用 GitHub REST API v3 进行项目搜索和用户信息获取。

### 核心接口

| 接口 | 用途 | 速率限制 |
|------|------|---------|
| `GET /search/repositories` | 搜索项目 | 10次/分钟（未认证）30次/分钟（认证） |
| `GET /users/{username}` | 获取用户信息 | 60次/小时（未认证）5000次/小时（认证） |
| `GET /repos/{owner}/{repo}` | 获取项目详情 | 同上 |

### 搜索语法

```
# 按关键词 + 语言搜索
q=openai+language:python&sort=stars&order=desc

# 按主题标签搜索
q=topic:ocr+language:python&sort=stars

# 组合搜索（OR 逻辑）
q=openai OR langchain OR llm+language:python
```

### Token 配置

在设置页面填入 GitHub Personal Access Token 可将速率限制从 60次/小时提升到 5000次/小时。

生成 Token：GitHub → Settings → Developer settings → Personal access tokens → Generate new token

所需权限：`public_repo`（只读公开仓库即可）

## 速率限制处理

- 未认证请求：60次/小时
- Token 认证请求：5000次/小时
- 搜索 API 额外限制：10次/分钟（未认证）/ 30次/分钟（认证）
- 响应头 `X-RateLimit-Remaining` 可查看剩余次数
- 触发限制时返回 HTTP 403，需等待 `X-RateLimit-Reset` 时间戳后重试

## 常见搜索场景

### LLM/大模型项目
```
q=openai OR langchain OR llm OR chatgpt OR gpt-4+language:python&sort=stars&per_page=30
```

### OCR 项目
```
q=tesseract OR easyocr OR ocr+language:python&sort=stars&per_page=30
```

### AI Agent 项目
```
q=ai-agent OR autogpt OR "langchain agent"+language:python&sort=stars&per_page=30
```
