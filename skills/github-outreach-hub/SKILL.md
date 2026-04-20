---
name: github-outreach-hub
description: GitHub 开源项目作者建联与推广工具。当用户需要以下操作时使用此 Skill：(1) 批量搜索 GitHub 上使用特定技术栈（如 LLM API、OCR 库）的开源项目 (2) 自动发现项目作者联系方式（邮箱、社交账号） (3) 生成个性化建联文案（支持文心大模型、PaddleOCR 推广模板） (4) 管理建联 CRM（联系人状态跟踪、CSV/Excel 导入导出） (5) 通过 Agent 能力进行智能项目分析和迁移可行性评估。触发关键词：GitHub 建联、开源推广、作者联系、技术迁移、LLM 替换推广、PaddleOCR 推广、文心大模型推广、开源项目 CRM、批量建联。
---

# GitHub 开源项目作者建联 Hub

## 适用场景

当用户需要系统化地与 GitHub 开源项目作者建立联系，推广百度文心大模型（ERNIE）或 PaddleOCR 等产品时使用本 Skill。典型场景包括：

- 搜索使用 OpenAI / GPT / LLM API 的项目，推荐作者迁移至文心大模型
- 搜索使用 Tesseract / EasyOCR 等 OCR 库的项目，推荐作者切换至 PaddleOCR
- 批量发现项目作者联系方式并生成个性化建联邮件
- 管理建联进度（待联系 → 已发送 → 已回复 → 已合作）
- 利用 AI Agent 能力分析项目代码，评估技术迁移可行性和工作量

## 输入要求

- **搜索关键词**：技术栈关键词（如 `openai`、`langchain`、`tesseract`、`easyocr`）
- **筛选条件**：可选，编程语言、最低 star 数、最近更新时间
- **推广产品**：文心大模型（ERNIE）或 PaddleOCR 或两者兼有
- **建联语言**：中文 / 英文 / 双语
- **GitHub Token**：可选，用于提升 API 速率限制（60次/小时 → 5000次/小时）

## 执行步骤

### 步骤 1：项目搜索与筛选

1. 通过 GitHub Search API 搜索匹配关键词的项目
2. 支持快捷场景按钮一键筛选：
   - **LLM/大模型项目**：`openai OR langchain OR llm OR chatgpt OR gpt-4`
   - **OCR 项目**：`tesseract OR easyocr OR ocr OR paddle-ocr`
   - **文心相关**：`ernie OR wenxin OR paddlenlp`
   - **PaddleOCR 相关**：`paddleocr OR paddlepaddle ocr`
   - **AI Agent 项目**：`ai-agent OR autogpt OR langchain agent`
   - **多模态项目**：`multimodal OR vision-language OR clip`
3. 按 star 数排序，筛选活跃维护的项目（有近期 commit）
4. 可选：使用 AI Agent 进行智能搜索，获取带技术分析的结果

### 步骤 2：作者信息发现

1. 通过 GitHub User API 获取项目 owner 的公开信息
2. 自动提取联系方式：
   - 个人资料中的邮箱
   - 个人主页 / 博客链接
   - Twitter / 社交媒体账号
   - README 中的联系信息
3. 汇总展示在作者详情页中

### 步骤 3：AI 项目分析（Agent 能力）

1. 调用 Agent 分析项目代码结构和技术依赖
2. 评估迁移可行性：
   - 当前使用的 LLM/OCR 库及版本
   - 迁移到文心大模型 / PaddleOCR 的工作量估算
   - 兼容性风险点
   - 迁移收益分析
3. 输出结构化分析报告，辅助建联文案撰写

### 步骤 4：建联文案生成

1. 提供预设模板：
   - **文心大模型推广模板**（中/英文）：突出 ERNIE 的性能优势、免费额度、中文能力
   - **PaddleOCR 推广模板**（中/英文）：突出 PP-OCRv5 的精度、多语言支持、轻量部署
   - **通用建联模板**：适用于一般技术交流
2. 可选：使用 AI Agent 生成个性化文案，结合项目特点定制内容
3. 支持一键复制文案，方便通过邮件或 GitHub Issue 发送

### 步骤 5：CRM 联系人管理

1. 将建联对象添加到联系人列表
2. 跟踪状态流转：`待联系` → `已发送` → `已回复` → `已合作`
3. 记录每次建联的时间和方式
4. 数据持久化：localStorage 本地存储 + CSV/Excel 导入导出

### 步骤 6：数据导出与协作

1. 支持 CSV 格式导出（UTF-8 BOM 编码，兼容 Excel 直接打开）
2. 支持 Excel XML 格式导出（SpreadsheetML）
3. 支持 CSV 文件导入，批量加载历史建联数据
4. 导出字段：作者、项目、联系方式、状态、添加时间、发送时间

## 输出要求

### 必须输出

1. **项目搜索结果**：项目名、star 数、语言、描述、最近更新时间
2. **作者信息卡片**：头像、用户名、邮箱、主页、社交链接
3. **建联文案**：至少提供一版可直接发送的文案（中文或英文）
4. **联系人列表**：包含状态、时间线的 CRM 视图

### 可选输出

- AI 迁移分析报告（依赖 Agent Server 运行）
- AI 生成的个性化文案（依赖 Agent Server 运行）
- Dashboard 统计面板（总联系人数、各状态分布、回复率）

### 输出格式

- 前端页面：单 HTML 文件，内嵌 CSS + JS，暗色高端 UI 风格
- 数据导出：CSV（UTF-8 BOM）或 Excel XML
- API 交互：GitHub REST API v3 + 可选 Agent Server（Node.js 桥接）

## 技术架构

### 前端（index.html）

- 纯前端单文件应用，零构建依赖
- 侧边栏导航：搜索、联系人、Dashboard、设置
- GitHub REST API 集成（支持 Token 认证）
- localStorage 数据持久化
- 响应式布局，支持局域网多人访问

### Agent Server（server.js）

- Node.js HTTP 服务，端口 8090
- 桥接前端 fetch 请求与本地 Agent CLI 工具
- 三种 Agent 动作：
  - `search`：智能项目搜索（带技术分析）
  - `analyze`：项目代码分析与迁移评估
  - `draft`：个性化建联文案生成
- CORS 支持，局域网可访问

### 本地部署

```bash
# 启动页面服务
cd github-outreach && npx serve . -l 8081

# 启动 Agent Server（可选，需要本地 Agent CLI）
node server.js
```

## 参考资料

- [references/github-api-guide.md](references/github-api-guide.md) - GitHub API 使用指南与速率限制说明
- [references/outreach-templates.md](references/outreach-templates.md) - 建联文案模板库（文心大模型 & PaddleOCR）
- [references/agent-integration.md](references/agent-integration.md) - Agent Server 集成与配置指南

## 验证清单

提交前请确认：

- [ ] 项目搜索功能正常（GitHub API 调用成功）
- [ ] 场景快捷按钮至少覆盖 LLM 和 OCR 两大类
- [ ] 作者详情页能正确展示联系方式
- [ ] 建联文案模板包含文心大模型和 PaddleOCR 版本
- [ ] CSV 导出文件可被 Excel 正确打开（无乱码）
- [ ] CRM 状态流转逻辑正确
- [ ] Agent Server 启动后 AI 功能可用（搜索/分析/文案）
- [ ] 局域网内其他设备可正常访问
