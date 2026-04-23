# Data Contracts

本文件总结当前项目中真实出现的数据结构和前端约束，供 Skill 在维护时对齐。

## 新闻结构

类型定义位于 `src/types/news.ts`，核心字段包括：

- `id`
- `date`
- `title`
- `imageUrl`
- `summary`
- `link`
- `isManual`
- `sourceType`
- `vendor`

## 案例结构

类型定义位于 `src/types/ecoCase.ts`，核心字段包括：

- `id`
- `title`
- `description`
- `industry`
- `hardware`
- `url`
- `isPinned`
- `createdAt`

## 常见 LocalStorage 键

README 中明确列出的键包括：

- `manual_ecosystem_news`
- `deleted_news_ids`
- `edited_news_overrides`
- `xinghe_courses_data`
- `xinghe_activities_data`
- `xinghe_hardware_products_data`
- `xinghe_feedback_data`

案例 Hook 中还额外使用：

- `xinghe_cases_data`

兼容矩阵组件中还使用：

- `hardware_matrix_data`

## 维护原则

- 变更时优先复用现有字段，避免给前端注入未消费的新结构
- 如需补默认链接，应保留项目已有的占位策略，而不是写入空字符串导致 UI 异常
- 如果 README 与代码细节不一致，应以实际类型、Hook 和组件逻辑为准
