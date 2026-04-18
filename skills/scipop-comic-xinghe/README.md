# SciPop Comic Orchestrator Xinghe

> 基于百度星河社区 API 的自动化科普连环画生成工具
> 多模态解析 × 单 Panel 精修 × N×N 全局合成，三阶段闭环创作

---

## 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [安装](#安装)
- [使用方法](#使用方法)
- [工作流程](#工作流程)
- [API 参考](#api-参考)
- [示例](#示例)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 功能特性

### 三阶段闭环创作

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1 · 文章解析                                      │
│  ernie-5.0-thinking-preview                                  │
│  · 识别核心知识节点                                       │
│  · 拆解 4-6 个视觉场景                                    │
│  · 输出 style_seed + 各 Panel 中文 Prompt（JSON）         │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 2 · 单 Panel 迭代生成                              │
│  for each panel:                                         │
│    ① ernie-image-turbo → 生成图像                         │
│    ② 展示给用户确认                                       │
│    ③ 若不满意 → 多模态反馈 → 改进 Prompt → 重新生成        │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 3 · N×N 全局长图合成                              │
│  · 聚合所有审定 Panel Prompt → 全局结构化 Prompt           │
│  · ernie-image-turbo → 生成连环画大图（2048×2048）        │
│  · 可选：大图反馈迭代                                      │
└─────────────────────────────────────────────────────────┘
```

### 核心能力

| 能力 | 说明 |
|-----|------|
| **智能拆解** | 自动分析科普文章，拆解为 4-6 个视觉场景 |
| **风格一致** | style_seed 机制确保跨 Panel 风格统一 |
| **中文优化** | ernie-image-turbo 对中文 Prompt 效果最佳 |
| **迭代精修** | 多模态反馈闭环，支持用户满意度驱动优化 |
| **全局合成** | N×N 布局自动生成连环画长图 |

---

## 快速开始

### 前置条件

1. 百度星河社区账号：[aistudio.baidu.com](https://aistudio.baidu.com)
2. 已申请 API Key，具备以下模型权限：
   - `ernie-5.0-thinking-preview`（原生全模态大模型）
   - `ernie-image-turbo`（图像生成）

### 30秒体验

```bash
# 1. 设置 API Key
export AISTUDIO_API_KEY="your-key"

# 2. 克隆仓库
git clone https://github.com/your-username/scipop-comic-xinghe.git
cd scipop-comic-xinghe

# 3. 安装依赖
pip install requests

# 4. 生成连环画
python scripts/generate_comic.py --article "黑洞是宇宙中最神秘的天体之一..." --output ./output/
```

---

## 安装

### 方式一：Python 脚本

```bash
# 安装依赖
pip install requests

# 验证环境
python scripts/generate_comic.py --help
```

### 方式二：Claude Skill

将 `SKILL.md` 放入 Claude 的 skills 目录：

```bash
cp SKILL.md ~/.claude/skills/scipop-comic-xinghe/
```

### 方式三：直接 cURL

无需安装，直接使用系统自带的 `curl`：

```bash
export AISTUDIO_API_KEY="your-key"

# 测试连通性
curl -s https://aistudio.baidu.com/llm/lmapi/v3/chat/completions \n  -H "Content-Type: application/json" \n  -H "Authorization: Bearer $AISTUDIO_API_KEY" \n  -d '{"model": "ernie-5.0-thinking-preview", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}'
```

---

## 使用方法

### Python 脚本

```bash
# 完整流程
python scripts/generate_comic.py \n  --article "科普文章内容..." \n  --output ./output/ \n  --layout 2x3

# 仅执行 Phase 1（获取拆解结果）
python scripts/generate_comic.py \n  --article "科普文章内容..." \n  --phase1-only
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|-----|------|-------|
| `--article, -a` | 科普文章内容（必填） | - |
| `--output, -o` | 输出目录 | `./output/` |
| `--layout, -l` | 布局（如 2x2, 2x3） | 自动推荐 |
| `--phase1-only` | 仅执行 Phase 1 | `false` |

### 输出文件

```
output/
├── phase1_result.json    # Phase 1 解析结果
├── panel_01.png          # Panel 1 图像
├── panel_02.png          # Panel 2 图像
├── ...
└── global_comic.png      # 全局大图
```

---

## 工作流程

### Phase 1: 文章解析

输入科普文章，输出 JSON 结构：

```json
{
  "recommended_panels": 5,
  "recommendation_reason": "文章涵盖五个层次，5格可完整呈现叙事弧线。",
  "style_seed": "扁平插画风格，柔和粉彩配色，清晰轮廓，2D矢量艺术",
  "panels": [
    {
      "id": 1,
      "scene": "场景描述",
      "image_prompt": "中文图像生成提示"
    }
  ]
}
```

### Phase 2: 图像生成

为每个 Panel 生成图像，支持用户反馈迭代：

```bash
# 生成图像
{panel_image_prompt}，{style_seed}，高质量，连环画

# 用户不满意时，多模态反馈
输入：[当前图像 base64] + [用户反馈文字]
输出：改进后的 image_prompt
```

### Phase 3: 全局合成

将所有 Panel 合成为一张完整连环画：

```
2x3 格连环画，共 5 格，{style_seed}，
每格之间用粗黑边框清晰分隔，按阅读顺序排列：
第1格：{panel_1_image_prompt}
第2格：{panel_2_image_prompt}
...
```

---

## API 参考

详细 API 文档请参考 [references/api_reference.md](references/api_reference.md)

### 核心端点

```
POST https://aistudio.baidu.com/llm/lmapi/v3/chat/completions
Authorization: Bearer $AISTUDIO_API_KEY
```

### 模型

| 模型 | 用途 |
|-----|------|
| `ernie-5.0-thinking-preview` | 多模态分析、文章解析、图像理解 |
| `ernie-image-turbo` | 图像生成 |

---

## 示例

### 示例 1：黑洞科普

**输入文章**：
> 黑洞是宇宙中最神秘的天体之一。2019年，人类首次拍摄到黑洞的照片...

**输出结果**：
- 5 个 Panel
- 风格：扁平插画，深邃太空配色
- 场景：黑洞神秘形象 → 科学家观看首张照片 → EHT望远镜阵列 → 验证广义相对论 → 探索新道路

### 示例 2：疫苗原理

**输入文章**：
> 疫苗是如何工作的？疫苗通过模拟病原体来训练我们的免疫系统...

**输出结果**：
- 5 个 Panel
- 风格：可爱卡通，柔和粉彩
- 场景：疫苗角色登场 → 模拟病原体教学 → 产生抗体 → 病毒入侵反击 → mRNA疫苗原理

更多示例请参考 [examples/](examples/) 目录。

---

## 项目结构

```
scipop-comic-xinghe/
├── SKILL.md                    # Claude Skill 定义
├── README.md                   # 项目说明
├── references/
│   ├── api_reference.md        # API 参考文档
│   └── style_guide.md          # 风格指南
├── scripts/
│   ├── generate_comic.py       # Python 生成脚本
│   └── retry_utils.sh          # 重试工具函数
└── examples/                   # 示例输出
```

---

## 常见问题

**Q: 多张图像风格不统一？**
检查每次调用是否将 `style_seed` 原文追加至 Prompt 末尾。

**Q: 支持中文 Prompt？**
`ernie-image-turbo` 对中文 Prompt 效果最佳。

**Q: base64 在 Windows 处理？**
PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("panel_01.png"))`

**Q: 如何确认 API Key 余额？**
登录 [星河社区控制台](https://aistudio.baidu.com) 查看配额用量。

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 创建 Pull Request

---

## 许可证

本项目仅供研究与教育用途，请遵守[百度星河社区使用条款](https://aistudio.baidu.com)。

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 致谢

- 百度星河社区提供 API 支持
- Ernie 系列模型驱动