# News Pipeline

当前项目中，新闻自动化能力来自现有脚本与工作流，而不是纯提示词约定。

## 相关文件

- 抓取脚本：`scripts/fetch-news.js`
- 输出文件：`public/auto-news.json`
- 工作流：`.github/workflows/schedule-news-fetch.yml`

## 现有流程

脚本的真实处理链路可概括为：

1. 多源采集：RSS + HTML 页面抓取
2. 关键词预过滤：围绕大模型、适配、推理、训练、国产算力等关键词
3. 正文穿透：访问新闻详情页抽取正文摘要
4. AI 清洗：优先 Gemini，失败后回退智谱 GLM
5. 输出静态 JSON，供前端新闻模块读取

## 现有数据源类型

- RSS：如 Hugging Face Blog、NVIDIA Developer News
- HTML 抓取：如华为昇腾、寒武纪、壁仞、昆仑芯、沐曦、海光、燧原、Intel Newsroom、安谋科技等页面

## 现有环境变量

根目录 `.env` 中已有以下命名约定：

- `GEMINI_API_KEY`
- `ZHIPU_API_KEY`
- `VITE_AI_CALCULATOR_URL`

Skill 在引用该能力时，应明确说明：

- 只有当工作区内真实存在这些脚本和密钥配置时，才能执行自动抓取
- 如果缺少密钥或工作流权限，应该回退为手动整理新闻数据，而不是宣称“已自动抓取”

## 定时任务信息

现有 GitHub Actions 工作流会定时执行 `npm run fetch-news`，并在 `public/auto-news.json` 发生变化时自动提交。
