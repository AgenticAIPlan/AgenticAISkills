---
name: aica10-avatar
description: |
  AICA 第十期专属头像生成器，融合图片合成与 AI 图生图两大能力。
  当用户需要制作带 AICA 第十期圆形头像框的个人头像时使用本 Skill，支持两种模式：
  ① 上传照片直接合成；② 上传参考图或输入提示词，调用 ERNIE-Image 生成 AI 照片后再合成。
  同时支持内网部署，供全体学员免安装使用。
---

# AICA 第十期头像生成器

## 适用场景

- 学员需要为 AICA 第十期活动制作带统一圆形头像框的个人头像
- 学员有喜欢的图片风格，想先用 AI 生成一张类似风格的新照片，再套上头像框
- 学员想直接用提示词生成 AI 头像照片
- 需要将工具部署到内网，供团队批量制作头像，零依赖、纯浏览器可用

头像框由 **ERNIE-Image** 创作生成，专为 AICA 第十期定制设计。

## 输入要求

**模式一：上传照片**
- 个人照片（JPG / PNG / WEBP，建议正方形人像）
- 可选：缩放比例、水平/垂直位置微调

**模式二：AI 图生图**
- 星河社区 API Key（`AISTUDIO_API_KEY`，在 [aistudio.baidu.com](https://aistudio.baidu.com) 获取）
- 参考图（可选，用于逆向推导提示词）或直接输入提示词

## 执行步骤

### 部署 / 本地启动

```bash
cd assets/frontend
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

内网部署：将 `assets/frontend/` 整个目录复制到任意静态 Web 服务器。

---

### 模式一：上传照片合成

1. 点击"📷 上传照片"标签，上传个人照片。
2. 用缩放/平移滑块调整人脸在圆框内的位置。
3. 点击"⬇ 下载头像"，获得 500×500 PNG。

---

### 模式二：AI 图生图

使用 ERNIE-4.5 多模态模型逆向分析参考图，生成提示词，再调用 ERNIE-Image 生成新头像照片。

#### 前端交互流程（浏览器）

1. 点击"✨ AI 生成"标签，填入星河社区 API Key（自动保存到 localStorage）。
2. 选择子模式：
   - **文生图**：直接在提示词框输入描述 → 点击"✨ AI 生成照片"
   - **图生图**：上传参考图 → 点击"🔍 分析图片" → 等待 AI 输出三版提示词 → 选择/编辑后生成
3. 生成完成后，照片自动加载到头像框合成区。
4. 微调位置后下载。

#### CLI 批量流程（命令行）

```bash
export AISTUDIO_API_KEY="your-key"

# 图生图：分析参考图，获得提示词
bash scripts/analyze_image.sh /path/to/reference.jpg

# 文生图：直接生成头像照片
bash scripts/generate_image.sh "日系动漫风格，正面人像，柔和自然光，简洁白色背景" 1024x1024 avatar.png
```

提示词写作参考 `references/prompt-writing-guide.md`；视觉分析使用的完整提示词见 `references/analysis-prompt.md`。

---

### 替换头像框

将新图片放入 `assets/frontend/frame/`，修改 `index.html` 顶部：

```js
const FRAME_URL = 'frame/新文件名.png';
```

## 输出要求

- 输出文件：`AICA10_avatar.png`，500×500 px PNG
- 头像框完整显示（圆环、丝带、AICA10 文字、星星均保留）
- 照片居中填充内圆，无白色背景残留
- 纯前端运行，照片及 API Key 均不上传任何第三方服务器

## 参考资料

| 文件 | 用途 |
|------|------|
| `assets/frontend/index.html` | 完整前端应用（含图生图功能） |
| `assets/frontend/frame/frame.png` | ERNIE-Image 生成的头像框图片 |
| `scripts/analyze_image.sh` | CLI：图片 → ERNIE-4.5 VL 逆向分析 → 提示词 |
| `scripts/generate_image.sh` | CLI：提示词 → ERNIE-Image-turbo → PNG |
| `references/analysis-prompt.md` | 8 维度视觉分析提示词模板（含条件附加模块）|
| `references/prompt-writing-guide.md` | ERNIE-Image 提示词写作规范与技巧 |
