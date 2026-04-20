# Agent Server 集成与配置指南

## 概述

Agent Server 是一个 Node.js HTTP 服务，作为前端页面与本地 Agent CLI 工具之间的桥梁，提供 AI 智能搜索、代码分析和文案生成能力。

## 架构

```
浏览器 (index.html)
    ↓ fetch POST
Agent Server (server.js, port 8090)
    ↓ execFile
Agent CLI 工具 (本地 CLI)
    ↓
AI 模型响应
```

## 启动方式

```bash
# 进入项目目录
cd github-outreach

# 启动 Agent Server
node server.js

# 服务默认监听 0.0.0.0:8090，支持局域网访问
```

## API 接口

### 请求格式

```json
POST http://localhost:8090
Content-Type: application/json

{
  "action": "search | analyze | draft",
  "query": "搜索关键词",        // search 动作必填
  "lang": "Python",             // search 动作可选
  "owner": "username",          // analyze/draft 动作必填
  "repo": "repo-name",         // analyze/draft 动作必填
  "purpose": "ernie",          // draft 动作可选
  "draftLang": "zh"            // draft 动作可选
}
```

### 响应格式

```json
{
  "ok": true,
  "data": "AI 生成的文本结果"
}
```

### 动作说明

| 动作 | 用途 | 必填参数 |
|------|------|---------|
| `search` | 智能项目搜索，返回带技术分析的结果 | `query` |
| `analyze` | 分析项目代码，评估迁移可行性 | `owner`, `repo` |
| `draft` | 生成个性化建联文案 | `owner`, `repo` |

## 前端集成

前端通过 `duccAgent()` 函数调用 Agent Server：

```javascript
const DUCC_API = location.hostname === 'localhost' || location.hostname === '127.0.0.1'
  ? 'http://localhost:8090'
  : `http://${location.hostname}:8090`;

async function duccAgent(action, params = {}) {
  const res = await fetch(DUCC_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, ...params }),
  });
  if (!res.ok) throw new Error('Agent server error: ' + res.status);
  const json = await res.json();
  if (!json.ok) throw new Error(json.error || 'Agent error');
  return json.data;
}
```

## CORS 配置

Server 默认开启 CORS 支持：

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

## 注意事项

- Agent CLI 调用可能耗时较长（30-120 秒），前端需做好加载状态展示
- Agent Server 需要本地安装并配置好 Agent CLI 工具
- 局域网访问时，前端会自动将 API 地址从 localhost 切换为当前主机 IP
- 建议在 Agent Server 前端使用 loading 动画提示用户等待
