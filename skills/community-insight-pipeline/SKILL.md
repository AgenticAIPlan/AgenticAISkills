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

### 脚本文件

脚本已包含在本 Skill 的 `scripts/` 目录中，**无需复制，直接通过路径调用**：

- `scripts/fetch_batch.py` — 抓取脚本（支持 `--tasks-file` 传入任务配置）
- `scripts/annotate.py`   — 标注脚本
- `scripts/export.py`     — 导出脚本

Credentials 通过环境变量传入（见下方说明），无需修改脚本内容。

### Reddit API Credentials

在工作目录创建 `.env` 文件：

```bash
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT=xxx    # 任意字符串，如 "MyBot/1.0"
```

**获取方式**：访问 https://www.reddit.com/prefs/apps，创建 **script** 类型应用，复制 client_id（应用名下方短字符串）和 secret。

### 数据库

脚本使用 SQLite，**首次运行 `scripts/fetch_batch.py` 时自动创建**。路径通过环境变量指定：

```bash
export DISCUSSION_DB_PATH=discussions.db   # 可选，不设置则默认 discussions.db
```

---

## 快速入口

根据当前场景选择起点，**按需执行 Preflight 检查，跳过不适用项**：

| 场景 | 起点 |
|------|------|
| 首次完整运行 | 完成 P1–P4 全部 Preflight，进入 Phase 1 |
| Credentials 已就绪，开始新一轮抓取 | 仅确认 P3 搜索目标，直接进入 Phase 1 |
| 数据已抓取，仅需 AI 标注 | 直接进入 Phase 2 |
| 标注已完成，仅需导出报告 | 直接进入 Phase 3 |

---

## Preflight 检查

### P1. Python 环境（首次运行时确认）

```bash
python3 --version    # 要求 3.9+
pip install praw openpyxl pillow
```

### P2. Reddit API Credentials（首次或 credentials 变更时确认）

检查环境变量是否已设置：

```bash
echo "CLIENT_ID=${REDDIT_CLIENT_ID:+已设置} SECRET=${REDDIT_CLIENT_SECRET:+已设置}"
```

- **均已设置** → 跳过，继续下一项
- **缺失** → 通过 `.env` 文件或 `export` 直接配置：

  ```bash
  # 方式 A：创建 .env 文件（脚本启动时自动加载）
  REDDIT_CLIENT_ID=你的client_id
  REDDIT_CLIENT_SECRET=你的client_secret
  REDDIT_USER_AGENT=MyBot/1.0

  # 方式 B：直接 export（当前 shell 生效）
  export REDDIT_CLIENT_ID=你的client_id
  export REDDIT_CLIENT_SECRET=你的client_secret
  ```

  **获取方式**：访问 https://www.reddit.com/prefs/apps，创建 **script** 类型应用，复制 client_id 和 secret。

### P3. 搜索目标（每次新抓取时必须确认）

向用户提问：
> 你想追踪哪个产品或话题？请提供搜索关键词。
> 搜索范围：全站搜索（global）、指定 AI/ML 子版块（subreddits），或两者都要？
> 是否同时抓取评论？（评论量通常远多于帖子）
> 是否需要精确匹配？例如 `ERNIE-Image` 是宽松匹配，`"ERNIE-Image"` 是精确短语匹配。

根据回答构建 `tasks.json`（见 Phase 1）。

### P4. 数据库路径（可选）

默认存储在当前目录的 `discussions.db`。如需修改：

```bash
export DISCUSSION_DB_PATH=你的路径
```

---

## 执行步骤

### Phase 1：配置并执行抓取

用 Write 工具将以下内容写入 `tasks.json`（根据 P3 确认结果填写，含中文必须写文件）：

```json
[
  {"label": "产品A 全站精确搜索", "query": "\"产品A\"", "mode": "global",     "include_comments": true},
  {"label": "产品A 子版块搜索",   "query": "产品A",     "mode": "subreddits", "include_comments": true}
]
```

执行抓取：

```bash
python3 scripts/fetch_batch.py --tasks-file tasks.json
```

验证结果：

```bash
sqlite3 "${DISCUSSION_DB_PATH:-discussions.db}" "SELECT content_type, COUNT(*) FROM discussions GROUP BY content_type;"
```

预期：看到 `post` 和 `comment` 的行数。若均为 0，检查 credentials 是否正确。

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
python3 scripts/annotate.py --batch --limit 40 > /tmp/ann_batch.json

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
python3 /tmp/batchNN_gen.py && python3 scripts/annotate.py --save /tmp/ann_results.json

# Step 6：查看进度，返回 Step 1 继续下一批
python3 scripts/annotate.py --stats
# 示例输出：Progress: 840/1552 (54.1%)
# 重复直到显示 100%
```

---

### Phase 3：导出报告

```bash
python3 scripts/export.py --output annotated_report.xlsx

# 仅导出相关条目：
python3 scripts/export.py --output annotated_report.xlsx --relevant-only
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

`scripts/fetch_batch.py` 使用 `INSERT OR REPLACE`，可安全重复执行，不产生重复条目。

### Reddit API 限速

praw 内置 1 req/s 限速，遇到限速时会自动等待。全量展开评论（`PRAW_COMMENT_LIMIT=0`）在热门帖子上耗时较长，可改为 `10` 限制展开深度。

---

## 输出要求

完成标准（按序检查）：

1. `python3 scripts/annotate.py --stats` 显示 **100%**
2. `annotated_report.xlsx` 存在，包含以下列：
   - 原始列：`platform_id`、`platform`、`content_type`、`title`、`content`、`url`、`author`、`subreddit`、`score`、`created_at`、`image_urls`
   - 标注列：`is_relevant`、`summary`、`advantages`、`disadvantages`、`tendency`
3. 随机抽查 10 条 `is_relevant=True` 的行，确认摘要和倾向与内容一致
