---
name: hardware-ecosystem-monitor
description: 多硬件生态舆情监控系统，负责从多个渠道采集硬件厂商动态、AI 适配进展和大模型生态合作新闻，并进行 AI 过滤、摘要生成与可视化展示。同时提供生态案例检索、硬件兼容分析等功能。
---

# 多硬件生态舆情监控 Skill

## 适用场景

当用户需要完成以下任务时，使用本 Skill：

### 新闻舆情模块

1. **舆情采集** - 自动从硬件厂商官网、RSS 源抓取最新新闻
2. **AI 清洗** - 对原始新闻进行关键词初筛 + 大模型摘要生成，判断是否与生态相关
3. **数据展示** - 在看板上展示新闻列表，支持筛选、搜索与管理
4. **手动补充** - 管理员可手动新增重大新闻（标记为"🔥重大发布"）
5. **编辑与删除** - 对自动抓取的新闻进行编辑覆盖，或标记删除

### 生态案例模块

6. **案例检索** - 根据硬件型号或行业快速查找生态案例
7. **案例录入** - 指导用户如何提交新的硬件适配案例
8. **硬件兼容分析** - 输入模型/场景，推荐适配的硬件

## 输入要求

### 数据抓取模式

- **自动抓取**：从 `public/auto-news.json` 读取 AI 清洗后的数据
- **手动触发**：执行 `npm run fetch-news` 重新抓取并清洗
- **定时任务**：通过 GitHub Actions 每日自动执行

### 新闻数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | MD5 哈希生成的唯一 ID |
| `vendor` | string | 厂商名称（如：壁仞科技、昆仑芯科技） |
| `title` | string | 新闻标题 |
| `date` | string | 发布日期（YYYY-MM-DD） |
| `summary` | string | AI 生成的摘要（30 字内精炼描述） |
| `imageUrl` | string | 封面图 URL |
| `link` | string | 原文链接 |
| `isManual` | boolean | 是否为手动新增（重大发布） |
| `sourceType` | string | 来源类型：RSS / API / HTML |

### 关键词白名单

用于初筛的关键词库（`ECOSYSTEM_KEYWORDS`）：

```
大模型, LLM, 适配, 推理, 微调, 算力, 框架,
GPU, NPU, CPU, 芯片, 集群, Llama, PyTorch,
TensorFlow, 飞桨, PaddlePaddle, MindSpore, 文心, ERNIE,
CUDA, CANN, ROCm, MUSA, 智算
```

## 执行步骤

### 阶段一：数据抓取

1. **RSS 源采集**
   - Hugging Face Blog (https://huggingface.co/blog/feed.xml)
   - NVIDIA Developer News (https://developer.nvidia.com/blog/feed/)

2. **HTML 源采集**（国内厂商，无 RSS）
   - 华为昇腾、寒武纪、壁仞科技、昆仑芯科技、沐曦、海光信息、燧原科技、Intel Newsroom、安谋科技

3. **关键词预过滤**
   - 对标题 + 摘要进行关键词匹配
   - 过滤掉明显不相关的商业公关稿、线下活动

### 阶段二：AI 清洗（双引擎容灾）

1. **主引擎**：Gemini 2.5 Flash
   - 系统提示词判断新闻是否实质性涉及硬件适配、训练优化、推理部署
   - 非相关内容输出 `REJECT`

2. **备用引擎**：智谱 GLM-4-Flash
   - Gemini 失败时自动降级

3. **判断标准**
   - ✅ 相关：大模型在特定硬件上的适配、训练优化、推理部署、硬核生态合作
   - ❌ 无关：普通商业公关稿、线下活动（训练营、大赛、全国行）

4. **兜底策略**
   - 双引擎均超时时，标记为"暂无智能摘要（双引擎均超时）"

### 阶段三：数据展示

1. **首页模块**（`PartnerNews` 组件）
   - 仅显示最新 3 条
   - 手动新闻（🔥重大发布）置顶显示

2. **管理功能**
   - 新增新闻（手动）
   - 编辑新闻（自动新闻编辑后存储至 `edited_news_overrides`）
   - 删除新闻（自动新闻记录至 `deleted_news_ids`）

## 生态案例模块

### 案例检索

支持三种检索方式：

1. **全文搜索** - 输入案例名称或描述关键词
2. **行业筛选** - 按行业领域下拉选择（自动驾驶、金融风控、医疗影像等）
3. **硬件筛选** - 按适配硬件下拉选择（昇腾 910B、昆仑芯 2、海光 DCU 等）

筛选结果实时显示，支持清除筛选条件。

### 案例数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 时间戳 + 随机字符串生成的唯一 ID |
| `title` | string | 案例名称 |
| `description` | string | 案例简介（核心价值与落地效果） |
| `industry` | string | 行业领域 |
| `hardware` | string | 适配硬件 |
| `url` | string | 案例链接（可选，留空则自动生成占位链接） |
| `isPinned` | boolean | 是否置顶（最多 3 个） |
| `createdAt` | number | 创建时间戳 |

### 案例录入流程

1. **非管理员用户**：查看案例录入引导说明，联系管理员提交案例
2. **管理员用户**：在全部案例页面点击"添加案例"，填写表单：
   - 案例名称（必填）
   - 行业领域（必填）
   - 适配硬件（必填）
   - 案例链接（可选，留空则自动生成 `https://invalid.local/pending-case-{timestamp}`）
   - 案例简介（可选）

### 硬件兼容分析

内置硬件兼容矩阵，支持按场景推荐硬件：

| 场景 | 推荐硬件（按优先级排序） |
|------|--------------------------|
| LLM推理 | 昇腾 910B、昆仑芯 2、海光 DCU、壁仞 BR104、燧原邃思 2.0 |
| LLM训练 | 昇腾 910B、昆仑芯 R200、海光 DCU、沐曦 MXNACA |
| CV图像处理 | 昇腾 310P、寒武纪 MLU370、海光 DCU、壁仞 BR104 |
| 自动驾驶感知 | 昇腾 910B、地平线 J5、寒武纪 MLU370 |
| 科学计算 | 海光 DCU、AMD MI100、NVIDIA A100 |
| 语音识别 | 昇腾 310P、昆仑芯 R200、寒武纪 MLU370 |
| 推荐系统 | 昇腾 910B、昆仑芯 2、海光 DCU |
| 风控模型 | 昆仑芯 2、海光 DCU、昇腾 910B |
| 医疗影像 | 海光 DCU、昇腾 910B、寒武纪 MLU370 |
| 智慧城市 | 昇腾 910B、昆仑芯 R200、寒武纪 MLU370 |

点击"筛选案例"可快速查看该硬件的所有相关案例。

### 新闻输出

```json
{
  "id": "md5-hash",
  "vendor": "壁仞科技",
  "title": "壁仞科技完成 MiniMax M2.5 高效适配",
  "date": "2026-03-02",
  "sourceType": "HTML",
  "isManual": false,
  "summary": "壁仞科技硬核适配国产大模型，实现高效推理部署。",
  "imageUrl": "https://...",
  "link": "https://..."
}
```

### 新闻 LocalStorage 存储键

| 键名 | 说明 |
|------|------|
| `manual_ecosystem_news` | 手动新增的新闻 |
| `deleted_news_ids` | 删除的自动新闻 ID 列表 |
| `edited_news_overrides` | 自动新闻的编辑覆盖数据 |

### 前端展示格式

- 卡片式布局，最多显示 3 条
- 显示日期、厂商标签、🔥重大发布标识
- 悬停显示编辑/删除按钮（仅管理员可见）
- 点击跳转原文链接

## 数据源配置

如需新增硬件厂商数据源，在 `scripts/fetch-news.js` 的 `HTML_SOURCES` 数组中添加：

```javascript
{
    vendorName: "厂商名称",
    listUrls: ["新闻列表页 URL"],
    linkPatterns: [/正则匹配详情页 URL/],
    containerSelector: ".css-selector" // 可选，限定爬取范围
}
```

## 定时任务配置

GitHub Actions 工作流：`.github/workflows/schedule-news-fetch.yml`

- 默认每日执行 `npm run fetch-news`
- 输出到 `public/auto-news.json`
- 失败时跳过此次更新，保留上次数据

## 风险与限制

1. **AI 摘要超时**：双引擎均超时时显示占位文本，需后续手动补充
2. **反爬限制**：部分厂商网站可能限制爬取，需定期检查 URL 正则有效性
3. **图片失效**：使用默认占位图 `images.unsplash.com/photo-1451187580459-43490279c0fa`
4. **数据量上限**：仅保留最新 100 条新闻

## 参考资料

- `references/news-types.md` - 新闻类型与来源详细说明
- `references/data-sources.md` - 数据源配置完整列表
- `references/ai-pipeline.md` - AI 清洗流程时序图与 Prompt 详解
- `references/hardware-compat.md` - 硬件兼容矩阵详细说明
