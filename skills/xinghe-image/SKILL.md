---
name: xinghe-image
description: 星河 AI 创作平台统一生图入口。支持信息图、文章配图、封面图、小红书图文。触发词："xinghe-image"、"生图"、"配图"、"封面"、"信息图"、"小红书图片"、"小红书图文"、"小红书帖子"。
---

# 星河 AI 生图 Skill

> 统一生图入口，两条风格路线，按场景自动路由。

## 依赖

- **生图脚本**：`scripts/generate.py`
- **Python 3.8+** + `openai` 库（`pip install openai`）
- **提示词语言**：强制中文（中文效果更好）
- **API**：百度 AIStudio API + **API Key**（见下方首次配置）

---

## 首次配置：API Key 检测 ⛔ BLOCKING（每次启动执行）

**每次 Skill 启动时，先运行以下检测命令：**

```bash
test -n "$AISTUDIO_API_KEY" && echo "KEY_ENV=OK" || echo "KEY_ENV=MISSING"
```

**KEY_ENV=OK** → 直接进入 Step 0。

**KEY_ENV=MISSING** → 向用户说明并请求 API Key，**配置完成前不继续**：

```
⚠️ 未检测到 API Key，需要完成一次性配置才能生图。

请前往以下地址获取你的 Access Token（免费，登录百度账号即可）：
  https://aistudio.baidu.com/account/accessToken

获取后，把 Key 直接粘贴到这里，我来帮你完成配置。
```

用户提供 Key 后，**由 AI 自动完成以下全部步骤，无需用户手动操作**：

**Step A：检测当前 Shell**

```bash
basename "$SHELL"
```

根据结果选择写入文件：`zsh` → `~/.zshrc`，`bash` → `~/.bashrc`，其他 → `~/.profile`。

**Step B：写入并生效**

```bash
# 以 zsh 为例，实际根据 Step A 结果选择对应文件
echo 'export AISTUDIO_API_KEY={用户提供的Key}' >> ~/.zshrc && source ~/.zshrc
```

**Step C：验证**

```bash
python3 {baseDir}/scripts/generate.py \
  --prompt "测试" --size 1024x1024 --output /tmp/xinghe-test.png
```

- 输出 `✓ 已保存` → 配置成功，告知用户后继续 Step 0。
- 输出 `错误:` → 提示 Key 可能有误，请用户重新获取后再次粘贴。

---

## Step 0：欢迎菜单

**智能跳过**：若用户消息已包含以下触发词，**直接进入 Step 1，不弹菜单**。

| 触发词 | 对应场景 |
|--------|---------|
| 信息图、数据可视化、知识图谱、流程图 | 信息图 |
| 文章配图、章节配图 | 文章配图 |
| 封面、Banner、封面图 | 封面图 |
| 小红书图文、小红书帖子、小红书图片 | 小红书图文 |

**无法识别场景时** ⛔ BLOCKING，使用 AskUserQuestion 展示以下选项：

```
你好！我是星河 AI 生图助手。

请选择你需要的生图类型：
1. 📊 信息图 —— 数据可视化、知识图谱、流程图海报
2. 🖼️ 文章配图 —— 为文章每个章节生成「海报级」配图（激进风格化）
3. 🎨 封面图 —— 博客/公众号/视频封面
4. 📱 小红书图文 —— 内容分析 + 多图卡片 + 文案包，一键生成完整发帖包
```

用户选择后，跳转到对应子流程（见下方路由表）。

---

## Step 1：内容输入

根据选择的场景，引导用户提供：

| 场景 | 需要的输入 |
|------|-----------|
| 信息图 | 要可视化的内容/数据/主题，以及期望传达的核心信息 |
| 文章配图 | 文章全文或分段摘要 |
| 封面图 | 文章标题/主题描述，期望的视觉风格倾向（可选） |
| 小红书图文 | 文章/笔记/文案等已有内容，AI 自动分析拆解 |

**文字来源原则**：
- 凡是会出现在图片上或文案包里的文字内容，默认都应来自用户提供的文章、笔记、标题、数据或明确的措辞要求
- 允许为了版面和平台表达做压缩、改写、口语化重组，但**不得新增**原文中没有的事实、数据、结论、承诺、人物经历或卖点
- 如果用户只给了主题而没有给可直接上图的文案，优先生成无字视觉稿，或仅使用用户明确提供的标题

---

## Step 2：风格路线选择

**两条路线，按场景自动路由：**

| 场景 | 路线 | 风格来源 |
|------|------|---------|
| 信息图 | **预设路线** | `references/image-presets.csv`（完整提示词预设，直接可用） |
| 小红书图文 | **预设路线** | `references/image-presets.csv` |
| 文章配图 | **组装路线** | `references/styles-index.csv` + `prompt-assembly.md` Skeleton 组装 |
| 封面图 / Banner | **组装路线** | `references/styles-index.csv` + `prompt-assembly.md` Skeleton 组装 |

> **预设路线（信息图 / 小红书图文）**：风格选型在各自子流程内完成（子流程中有 ⚠️ BLOCKING 的预设选型步骤），**Step 2 对预设路线不需要额外操作，直接进入 Step 3。**

**组装路线**：从 `styles-index.csv` 推荐 3 个风格（mood 列不同），用户确认后按 `prompt-assembly.md` Part 1 规则组装提示词。组装展示格式：

```
为你的「[场景]」推荐几个风格方向：

**方向 A：[风格名称]**
视觉效果：[具体描述，100字内]

**方向 B：[风格名称]**
视觉效果：[具体描述]

**方向 C：[风格名称]**
视觉效果：[具体描述]

请选择一个方向，或描述你想要的其他风格。
```

风格推荐约束：3 个推荐必须跨越不同大类，详见 `references/workflows/prompt-assembly.md` Part 1。

---

## Step 3：执行子流程

根据 Step 0 选择，加载对应工作流：

| 用户选择 | 子流程文件 |
|---------|----------|
| 信息图 | `references/workflows/infographic.md` |
| 文章配图 | `references/workflows/article-illustration.md` |
| 封面图 | `references/workflows/cover-image.md` |
| 小红书图文 | `references/workflows/xiaohongshu.md` |

传入参数：
- `{content}` = 用户提供的内容
- `{style}` = Step 2 确认的风格（预设名 或 styles-index 风格名）
- `{scene}` = 选择的场景类型

---

## 生图调用

所有子流程通过 `scripts/generate.py` 调用生图 API。

> ⚠️ **模型名称锁定**：API 实际接受的模型名为 `ernie-image-turbo`（全小写）。官方文档中出现的 `ERNIE-Image-Turbo` 大写写法会导致 HTTP 400 报错。**任何情况下不得修改此名称的大小写。**

> **`{baseDir}` 说明**：本 `SKILL.md` 所在目录的绝对路径。执行生图命令前，先确认路径：
> ```bash
> # 示例：skill 安装在全局
> # {baseDir} = ~/.codex/skills/xinghe-image
> # 示例：符号链接
> # {baseDir} = /path/to/xinghe-image（链接源目录）
> ```
> 不确定时，运行 `find ~ -name "SKILL.md" -path "*/xinghe-image/*"` 定位。

> **尺寸必须显式传 `--size`**，不要依赖任何隐式默认值，避免模型或调用链回落到错误比例。

### 完整调用格式

```bash
python3 {baseDir}/scripts/generate.py \
  --prompt "提示词（中文）" \
  --size 1264x848 \
  --output output.png \
  [--n 1] \
  [--steps 8] \
  [--guidance 1.0] \
  [--no-pe] \
  [--seed 42]
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--prompt` / `-p` | ✅ | — | 生图提示词，**强制中文**（中文效果更好） |
| `--size` / `-s` | ✅ | `1024x1024` | 图片尺寸，必须是下方 7 个合法值之一 |
| `--output` / `-o` | ✅ | — | 输出文件路径，`.png` 格式 |
| `--n` | — | `1` | 一次生成张数，可选 1 / 2 / 3 / 4 |
| `--steps` | — | `8` | 推理步数：`8` = Turbo 快速（约 3-5s），`50` = 标准高质量 |
| `--guidance` | — | `1.0` | 引导强度 `guidance_scale`，控制提示词对生成结果的影响程度 |
| `--no-pe` | — | 关闭 | 加上此标志则**禁用**提示词增强（PE）；默认开启 PE，模型会自动优化 prompt |
| `--seed` | — | `-1` | 随机种子，`-1` 为随机；指定相同 seed 可复现结果 |
| `--api-key` | — | 读环境变量 | 临时覆盖 `AISTUDIO_API_KEY`，一般不需要手动传 |

### 常用调用示例

**普通生图（快速，默认参数）：**
```bash
python3 {baseDir}/scripts/generate.py \
  --prompt "提示词" --size 1264x848 --output out.png
```

**高质量生图（50步，关闭 PE 以精确控制 prompt）：**
```bash
python3 {baseDir}/scripts/generate.py \
  --prompt "提示词" --size 848x1264 --output out.png \
  --steps 50 --no-pe
```

**可复现生图（固定 seed）：**
```bash
python3 {baseDir}/scripts/generate.py \
  --prompt "提示词" --size 1024x1024 --output out.png \
  --seed 42
```

### 尺寸

> **API 只接受以下 7 个精确尺寸，不可使用其他值（会报错）。**

| 尺寸 | 比例 | 方向 |
|------|------|------|
| `1024x1024` | 1:1 | 方形 |
| `848x1264` | 3:4 | 竖版 |
| `768x1376` | 9:16 | 竖版 |
| `896x1200` | 3:4 | 竖版 |
| `1264x848` | 3:2 | 横版 |
| `1376x768` | 16:9 | 横版 |
| `1200x896` | 4:3 | 横版 |

**各场景默认尺寸**：

| 场景 | 默认尺寸 | 备选 |
|------|---------|------|
| 信息图 | `1264x848`（横版 3:2） | `1200x896`、`1024x1024` |
| 文章配图 | `1264x848`（横版 3:2） | `1376x768`、`1024x1024` |
| 封面图 / Banner | `1376x768`（横版 16:9） | `1264x848`、`1200x896` |
| 小红书图文 | `848x1264`（竖版 3:4） | `768x1376`、`1024x1024` |

### 中文渲染约束

**当以下任一条件成立时，在提示词末尾追加中文渲染约束：**
- 提示词或用户内容中含有中文
- 用户未明确指定输出语言

**若用户明确要求英文输出（如"英文版面"、"English text only"、"文案语言为英文"），则跳过此约束。**

中文渲染约束内容：
```
所有中文文字清晰可辨，笔画完整，无乱码、无变形、无错位；中文字符独立排版，字体工整易读。图中所有文字必须使用中文，不得出现日文、韩文或其他语言文字。
```

### 生成后处理

脚本输出中每个 `OUTPUT: {path}` 行对应一张生成的图片。生成完成后：

1. 将所有图片路径告知用户
2. 用 `open` 命令直接打开图片（macOS）：

```bash
open {path}           # 单张
open {path1} {path2}  # 多张
```

---

## 多图生成

适用场景：小红书图文（多图卡片）、信息图系列。

### 执行规则

**封面先行**（同步，阻塞等待完成后再进行下一步）：

```bash
python3 {baseDir}/scripts/generate.py \
  --prompt "[封面提示词]" \
  --size [尺寸] \
  --output [output-dir]/01-cover-[slug].png
```

**内容页并发**（同一条消息发起多个 Bash，每个加 `run_in_background: true`）：

```bash
# 02、03 ... NN 同时发起，每个独立的 Bash 调用
python3 {baseDir}/scripts/generate.py \
  --prompt "[第N页提示词]" \
  --size [尺寸] \
  --output [output-dir]/NN-[type]-[slug].png
```

**统一等待**（同一条消息发起多个 TaskOutput，每个 `block=true`）：

等待所有后台任务完成后统一报告结果。

### 进度报告

每张发起前：`⏳ 生成中 [N/总数]...`

每张完成后：`✓ [N/总数] → 已保存: [路径]`

### 失败处理

单张失败 → 重试一次 → 仍失败则记录跳过，继续其余图片，最后汇报失败列表。

### 视觉一致性

星河 API 不支持 `--ref` 参数。保持系列一致性的方式：**第 2 张起完整复用第 1 张的风格描述部分**，并在提示词末尾追加：

```
风格、色调、渲染质感与系列第一张图保持高度一致。
```

---

## 参考文件索引

| 文件 | 用途 |
|------|------|
| `references/styles-index.csv` | 组装路线风格库（40+ 款抽象设计风格，含 rendering_keywords/visual_rule/color_rule） |
| `references/image-presets.csv` | 预设路线风格库（25 条完整提示词预设，信息图/小红书直接可用） |
| `references/workflows/prompt-assembly.md` | 组装路线规则：风格推荐逻辑 + Skeleton 填槽指南 |
| `references/workflows/infographic.md` | 信息图子流程 |
| `references/workflows/article-illustration.md` | 文章配图子流程（表达性/说明性双模式） |
| `references/workflows/cover-image.md` | 封面图子流程 |
| `references/workflows/xiaohongshu.md` | 小红书图文生成（预设选型 + 大纲 + 生图 + 文案包）|
