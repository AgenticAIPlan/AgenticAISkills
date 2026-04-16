---
name: aica10-avatar
description: 生成 AICA 第十期专属圆形头像框图片。当用户需要为 AICA 第十期活动制作带统一头像框的个人头像，或需要部署、分享头像生成工具给团队成员时，使用本 Skill。
---

# AICA 第十期头像生成器

## 适用场景

- 用户需要为 AICA 第十期活动制作带统一圆形头像框的个人头像
- 用户需要将头像生成工具部署到内网，供团队成员批量制作头像
- 用户需要替换头像框图片为新的官方素材
- 用户需要将本工具分享给同事，要求零依赖、纯浏览器可用

头像框图片由 **ERNIE-Image** 创作生成，专为 AICA 第十期定制设计。

## 输入要求

- 用户的个人照片（JPG / PNG / WEBP，建议正方形人像）
- 可选：缩放比例、水平/垂直位置微调参数
- 可选：新的头像框图片路径（用于替换默认框）

## 执行步骤

1. 将 `assets/frontend/` 目录完整复制到目标 HTTP 服务器或共享目录。
2. 用浏览器访问 `index.html`（建议通过 HTTP 服务，避免本地 `file://` 跨域限制）：
   ```bash
   cd assets/frontend
   python3 -m http.server 8080
   # 浏览器打开 http://localhost:8080
   ```
3. 用户在页面上传个人照片，系统自动：
   - 使用泛洪填充（flood fill）从图片边缘和中心双向去除头像框背景
   - 将照片裁剪为圆形并合成到头像框内圈
   - 实时预览合成效果
4. 用户通过缩放、水平、垂直滑块调整照片位置，直到满意。
5. 点击「下载头像」，获得 500×500 px 的 PNG 文件。
6. 将 PNG 设置为微信、企业微信或飞书头像。

### 替换头像框

如需使用新的官方头像框：
1. 将新图片（500×500 PNG，圆环内部可为任意背景色）放入 `assets/frontend/frame/` 目录。
2. 修改 `index.html` 顶部配置：
   ```js
   const FRAME_URL = 'frame/新文件名.png';
   ```
3. 如背景去除效果不理想，调整 `BG_TOLERANCE`（默认 45，可适当增大）。

### 内网部署

```bash
# 将前端目录复制到内网 Web 服务器
cp -r assets/frontend/ /var/www/html/aica10/
# 分享链接：http://内网IP/aica10/
```

## 输出要求

- 输出文件：`AICA10_avatar.png`，尺寸 500×500 px，PNG 格式
- 头像框完整显示（圆环、丝带、文字、装饰元素均保留）
- 照片居中填充内圆，无白色背景残留
- 纯前端运行，照片不上传任何服务器

## 参考资料

- `assets/frontend/index.html`：完整前端应用（HTML + CSS + JS 单文件，无外部依赖）
- `assets/frontend/frame/frame.png`：ERNIE-Image 生成的 AICA 第十期头像框
- `assets/frame/frame.svg`：备用占位头像框（商务蓝渐变 SVG）
