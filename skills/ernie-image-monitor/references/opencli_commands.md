# OpenCLI 命令参考

OpenCLI（`~/.local/bin/opencli`）是一个命令行工具，通过 Chrome 浏览器扩展访问需要登录 Cookie 的平台。

## 安装与诊断

```bash
# 安装
npm install -g @jackwener/opencli --prefix ~/.local

# 验证连通性
~/.local/bin/opencli doctor

# 查看版本
~/.local/bin/opencli --version
```

Chrome 扩展加载路径：
```
~/.local/lib/node_modules/@jackwener/opencli/extension/
```

---

## 知乎

```bash
# 搜索关键词
~/.local/bin/opencli zhihu search "ERNIE-Image" --limit 20

# 搜索并保存到文件
~/.local/bin/opencli zhihu search "ERNIE-Image" --limit 20 --output zhihu_result.json

# 获取问题详情（含回答列表）
~/.local/bin/opencli zhihu question <question_id> --limit 10

# 获取专栏文章
~/.local/bin/opencli zhihu article <article_id>
```

输出字段：`id`, `title`, `content`, `author`, `created_time`, `updated_time`, `url`, `vote_up_count`

---

## 小红书

```bash
# 搜索关键词
~/.local/bin/opencli xiaohongshu search "ERNIE-Image" --limit 20

# 搜索并保存
~/.local/bin/opencli xiaohongshu search "文心图像" --limit 20 --output xhs_result.json

# 获取笔记详情
~/.local/bin/opencli xiaohongshu note <note_id>

# 获取笔记评论
~/.local/bin/opencli xiaohongshu comments <note_id> --limit 20
```

输出字段：`id`, `title`, `desc`, `user.nickname`, `time`, `liked_count`, `comment_count`, `share_url`

---

## Google 搜索（微信公众号 / 百度）

Google 搜索不需要 Cookie，通过 `site:` 语法实现定向搜索：

```bash
# 微信公众号搜索
~/.local/bin/opencli google search "ERNIE-Image site:mp.weixin.qq.com" --limit 10

# 百度旗下平台搜索
~/.local/bin/opencli google search "ERNIE-Image site:baidu.com" --limit 10
~/.local/bin/opencli google search "文心图像 site:wenxin.baidu.com" --limit 10
```

输出字段：`title`, `snippet`, `url`, `displayLink`

> **注意**：Google 搜索默认超时 60 秒，网络不稳定时可能返回空结果，属正常情况。

---

## 常用选项

| 选项 | 说明 |
|------|------|
| `--limit N` | 限制返回条数（默认因平台而异） |
| `--output <file>` | 结果保存到 JSON 文件 |
| `--timeout N` | 超时秒数（默认 60） |
| `--verbose` | 显示详细日志 |
