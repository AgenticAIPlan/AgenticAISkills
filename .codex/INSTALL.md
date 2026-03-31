# 在 Codex 中安装 AgenticAISkills

本仓库参考 `superpowers` 的安装方式，使用本地克隆加软链接的形式，让 Codex 自动发现 `skills/` 目录下的 Skills。

## 安装步骤

1. 克隆仓库到本地：

```bash
git clone https://github.com/AgenticAIPlan/AgenticAISkills.git ~/.codex/AgenticAISkills
```

2. 建立 Skills 软链接：

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/AgenticAISkills/skills ~/.agents/skills/agentic-ai-skills
```

3. 重启 Codex，使 Skills 被重新发现。

## 更新

```bash
cd ~/.codex/AgenticAISkills && git pull
```

## 校验

```bash
ls -la ~/.agents/skills/agentic-ai-skills
```

如果输出指向 `~/.codex/AgenticAISkills/skills`，说明安装完成。
