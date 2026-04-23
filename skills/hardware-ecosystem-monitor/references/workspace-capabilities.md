# Workspace Capabilities

以下能力来自当前“多硬件生态监控看板 Demo”项目的真实文件结构，可作为 Skill 的能力边界依据。

## 技术与入口

- 前端：React + TypeScript + Vite
- 路由入口：`src/App.tsx`
- 首页：`src/pages/Dashboard.tsx`
- 子页面：`/news`、`/courses`、`/activities`、`/products`、`/feedback`、`/cases`

## 首页模块

首页当前真实接入的模块包括：

1. 硬件伙伴新闻 `PartnerNews`
2. 适配矩阵 `AdaptationMatrix`
3. 课程与活动 `CoursesAndEvents`
4. 产品展示 `FeaturedProducts`
5. 用户反馈 `UserFeedback`
6. 外部工具嵌入 `ToolEmbedContainer`

## 内容维护方式

项目中的多类内容支持通过前端页面或静态数据进行维护：

- 新闻：自动新闻 + 手动新闻混合
- 课程：列表、置顶、编辑
- 活动：列表、置顶、编辑
- 产品：列表、高亮、编辑
- 反馈：时间轴展示、增删改
- 案例：搜索、筛选、置顶、编辑
- 兼容矩阵：模型、硬件、子能力和适配状态维护

## 能力边界提醒

- 当前项目确实存在新闻抓取脚本与 GitHub Actions 工作流
- 当前项目确实存在案例页与兼容矩阵组件
- 但 Skill 仓库本身不自带这些源码；在 Skill 中只能把它们描述为“适用于已有此类项目时的操作规范”，不能假装 Skill 自带完整系统实现
