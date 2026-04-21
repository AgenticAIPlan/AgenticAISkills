---
name: community-insight-pipeline
description: 针对指定产品或话题，从 Reddit 批量抓取社区讨论，再由 AI 逐批标注相关性、优劣势与情感倾向，最终导出结构化分析报告。适用于产品口碑监控、竞品调研、用户洞察等场景。
---

# Community Insight Pipeline：Reddit 社区讨论抓取与 AI 批量标注

## 适用场景

- **产品口碑监控**：追踪 Reddit 上对某个 AI 模型、开源项目或产品的社区评价
- **竞品调研**：批量收集竞争产品的用户反馈，提炼结构化优劣势
- **用户洞察**：从大量社区讨论中提取情感标签和摘要，供产品/运营团队使用

---

## 输入要求

**Agent 执行前必须逐项确认，任意一项不满足则中止并告知用户。**

### 系统依赖

```bash
python3 --version    # 要求 3.9+
```

### Python 依赖

```bash
pip install praw openpyxl pillow
```

### 脚本文件

将本 Skill 的 `scripts/` 目录下三个脚本复制到工作目录：

```
工作目录/
├── .env             # Reddit API credentials（见下方说明）
├── fetch_batch.py   # 抓取脚本
├── annotate.py      # 标注脚本
└── export.py        # 导出脚本
```

无需任何其他项目依赖，三个脚本均可独立运行。

### Reddit API Credentials

在工作目录创建 `.env` 文件：

```bash
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT=xxx    # 任意字符串，如 "MyBot/1.0"
```

**获取方式**：访问 https://www.reddit.com/prefs/apps，创建 **script** 类型应用，复制 client_id（应用名下方短字符串）和 secret。

### 数据库

脚本使用 SQLite，**首次运行 `fetch_batch.py` 时自动创建**。路径通过环境变量指定：

```bash
export DISCUSSION_DB_PATH=discussions.db   # 可选，不设置则默认 discussions.db
```

---

## 启动确认（Agent 必须在执行任何命令前完成）

Agent 启动后，依次向用户确认以下信息，**全部确认完毕再进入执行步骤**。

### 1. 确认搜索目标

向用户提问：
> 你想追踪哪个产品或话题？请提供搜索关键词。
> 是否需要精确匹配（加引号）？例如 `ERNIE-Image` 是宽松匹配，`"ERNIE-Image"` 是精确短语匹配。

根据回答修改 `fetch_batch.py` 顶部的 `TASKS` 列表。

### 2. 确认搜索范围

向用户提问：
> 搜索范围偏好哪种？
> - **全站搜索**（global）：覆盖整个 Reddit，结果更广
> - **指定子版块**（subreddits）：仅在预配置的 AI/ML 相关子版块中搜索，噪音更少
> - **两者都要**：同时执行两种模式

`subreddits` 模式使用的子版块列表定义在 `fetch_batch.py` 顶部的 `SUBREDDITS` 变量中，可按需增减。

### 3. 确认是否抓取评论

向用户提问：
> 是否同时抓取帖子下的评论？评论量通常远多于帖子，标注时间也更长。

根据回答设置 `TASKS` 中的 `include_comments` 字段。

### 4. 检查 Reddit API Credentials

执行以下命令检查 `.env` 是否存在且包含必要字段：

```bash
grep -E "^(REDDIT_CLIENT_ID|REDDIT_CLIENT_SECRET|REDDIT_USER_AGENT)=.+" .env 2>/dev/null
```

- **三项均存在且非空** → 告知用户"credentials 已就绪，继续执行"
- **缺失任意一项** → 引导用户完成配置：

  > 需要先配置 Reddit API credentials，步骤如下：
  > 1. 登录 Reddit，访问 https://www.reddit.com/prefs/apps
  > 2. 点击"create another app"，类型选择 **script**
  > 3. 填写任意名称，redirect uri 填 `http://localhost`，提交
  > 4. 应用名下方短字符串为 `client_id`，"secret"字段为 `client_secret`
  > 5. 创建 `.env` 文件：
  >    ```bash
  >    REDDIT_CLIENT_ID=你的client_id
  >    REDDIT_CLIENT_SECRET=你的client_secret
  >    REDDIT_USER_AGENT=MyBot/1.0
  >    ```
  > 完成后告诉我继续。

### 5. 确认数据库路径

向用户确认：
> 数据默认存储在当前目录的 `discussions.db`，是否需要修改？
> 如需修改：`export DISCUSSION_DB_PATH=你的路径`

**以上 5 项全部确认后，进入执行步骤。**

---

## 执行步骤

### Phase 1：配置并执行抓取

编辑 `fetch_batch.py` 顶部的 `TASKS` 列表（根据启动确认中的信息填写）：

```python
TASKS = [
    # (描述,               query,        mode,         include_comments)
    ("产品A 全站精确搜索",  '"产品A"',   "global",     True),
    ("产品A 子版块搜索",    "产品A",     "subreddits", True),
]
```

执行抓取：

```bash
python3 fetch_batch.py
```

验证结果：

```bash
sqlite3 discussions.db "SELECT content_type, COUNT(*) FROM discussions GROUP BY content_type;"
```

预期：看到 `post` 和 `comment` 的行数。若均为 0，检查 `.env` credentials 是否正确。

---

### Phase 2：AI 批量标注

**标注字段定义：**

| 字段 | 类型 | 取值范围 | 说明 |
|------|------|----------|------|
| `platform_id` | str | — | 主键，必须与数据库完全一致 |
| `is_relevant` | bool | true / false | 是否与目标产品/话题相关 |
| `summary` | str | 中文 1-2 句 | 聚焦评论者核心结论，非内容复述 |
| `advantages` | str | 逗号分隔 | 提及的优点；无则空字符串 |
| `disadvantages` | str | 逗号分隔 | 提及的缺点；无则空字符串 |
| `tendency` | str | 正面/负面/中立/混合/"" | `is_relevant=false` 时留空 |

**标注循环（每批 40 条，循环至 100%）：**

```bash
# Step 1：获取本批待标注数据
python3 annotate.py --batch --limit 40 > /tmp/ann_batch.json

# Step 2：解析并预览内容（无中文，可用 -c 内联执行）
python3 -c "
import json
data = json.load(open('/tmp/ann_batch.json'))
rows = data.get('rows', [])
print('status:', data.get('status'), '| count:', len(rows))
for i, d in enumerate(rows):
    has_img = '[IMG]' if d.get('image_urls') else ''
    snippet = str(d.get('content') or '')[:120].replace('\n', ' ')
    print(i, d['platform_id'], has_img, snippet)
"

# Step 3：（如有图片）下载并检查尺寸
curl -sL "IMAGE_URL" -o /tmp/img_PLATFORMID.png
python3 -c "from PIL import Image; print(Image.open('/tmp/img_PLATFORMID.png').size)"
# 宽/高均 <= 2000px → 可用 Read 工具查看图片内容
# 任一边 > 2000px  → 仅依据文字上下文标注，不调用 Read
```

# Step 4：将标注结果写入文件（含中文必须写文件，严禁 -c 内联执行）

用 Write 工具将以下 Python 内容写入 `/tmp/batchNN_gen.py`：

```python
import json
annotations = [
  {
    "platform_id":    "reddit__abc123",
    "is_relevant":    True,
    "summary":        "作者认为文字渲染出色，但生成速度较慢。",
    "advantages":     "文字渲染准确,提示词跟随好",
    "disadvantages":  "生成速度慢",
    "tendency":       "混合"
  },
  # 覆盖本批全部条目；不相关的 is_relevant=False，其余字段留空字符串
]
result = {"model": "claude-sonnet-4-6", "annotations": annotations}
with open("/tmp/ann_results.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```

```bash
# Step 5：执行并保存
python3 /tmp/batchNN_gen.py && python3 annotate.py --save /tmp/ann_results.json

# Step 6：查看进度，返回 Step 1 继续下一批
python3 annotate.py --stats
# 示例输出：Progress: 840/1552 (54.1%)
# 重复直到显示 100%
```

---

### Phase 3：导出报告

```bash
python3 export.py --output annotated_report.xlsx

# 仅导出相关条目：
python3 export.py --output annotated_report.xlsx --relevant-only
```

---

## 边界条件

### 含中文代码必须写文件执行（Critical）

```bash
# ❌ 错误：含中文字符串在部分环境下触发 SyntaxError
python3 -c "summary = '效果良好'"

# ✅ 正确：写入 .py 文件后执行
python3 /tmp/batchNN_gen.py
```

### JSON 序列化必须指定编码（Critical）

```python
json.dump(result, f, ensure_ascii=False, indent=2)  # 必须 ensure_ascii=False
```

### 相关性判断原则

- **不相关**：未提及目标产品；通用 AI 评论；极短无实质评价（"Nice"、"Thanks"、单个表情）
- **相关**：明确评价目标产品的质量/性能/功能/对比，哪怕只有一句话

### 批次大小

默认 40 条/批。含大量图片时改为 `--limit 20`，避免上下文溢出。

### 数据去重

`fetch_batch.py` 使用 `INSERT OR REPLACE`，可安全重复执行，不产生重复条目。

### Reddit API 限速

praw 内置 1 req/s 限速，遇到限速时会自动等待。全量展开评论（`PRAW_COMMENT_LIMIT=0`）在热门帖子上耗时较长，可改为 `10` 限制展开深度。

---

## 输出要求

完成标准（按序检查）：

1. `python3 annotate.py --stats` 显示 **100%**
2. `annotated_report.xlsx` 存在，包含以下列：
   - 原始列：`platform_id`、`platform`、`content_type`、`title`、`content`、`url`、`author`、`subreddit`、`score`、`created_at`、`image_urls`
   - 标注列：`is_relevant`、`summary`、`advantages`、`disadvantages`、`tendency`
3. 随机抽查 10 条 `is_relevant=True` 的行，确认摘要和倾向与内容一致
