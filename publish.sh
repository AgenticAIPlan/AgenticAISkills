#!/bin/bash
# 飞桨星河社区项目评审专家Skill - GitHub提交脚本

set -e

echo "========================================="
echo "飞桨星河社区项目评审专家Skill - GitHub提交工具"
echo "========================================="
echo ""

# 1. 检查git仓库
if [ ! -d .git ]; then
    echo "初始化git仓库..."
    git init
fi

# 2. 配置git用户信息（如果还没配置）
if [ -z "$(git config user.name)" ]; then
    read -p "请输入你的GitHub用户名: " GITHUB_USERNAME
    git config user.name "$GITHUB_USERNAME"
    git config user.email "$GITHUB_USERNAME@users.noreply.github.com"
fi

GITHUB_USERNAME=$(git config user.name)
echo "✓ Git用户: $GITHUB_USERNAME"
echo ""

# 3. 设置远程仓库（你的Fork）
FORK_REPO="https://github.com/$GITHUB_USERNAME/AgenticAISkills.git"
ORIGINAL_REPO="https://github.com/AgenticAIPlan/AgenticAISkills.git"

echo "检测远程仓库..."
if git remote get-url origin > /dev/null 2>&1; then
    echo "✓ 远程仓库已配置: $(git remote get-url origin)"
else
    echo "添加远程仓库: $FORK_REPO"
    git remote add origin "$FORK_REPO"
    git remote add upstream "$ORIGINAL_REPO"
fi

# 4. 创建或切换到feat分支
echo ""
echo "创建/切换分支: feat/aistudio-project-reviewer"
git checkout -b feat/aistudio-project-reviewer 2>/dev/null || git checkout feat/aistudio-project-reviewer

# 5. 添加所有文件
echo "添加文件到暂存区..."
git add .

# 6. 提交
echo "提交更改..."
if git diff --cached --quiet; then
    echo "✓ 没有需要提交的更改"
else
    git commit -m "feat: 添加飞桨星河社区项目评审专家Skill

- 实现多维度项目评审（创新性、技术深度、文档质量、可复现性、社区价值）
- 添加AI生成内容检测与减分机制
- 提供快速筛选功能
- 包含完整的模板资源库和评分标准
- 实现可执行评审脚本
- 符合仓库规范：skills/<skill-slug>/ 结构
"
    echo "✓ 提交成功"
fi

# 7. 推送到GitHub
echo ""
echo "========================================="
echo "推送到GitHub..."
echo "========================================="

echo ""
echo "选项1：推送到你的Fork仓库（推荐）"
echo "-----------------------------------"
echo "如果还没有Fork，请先："
echo "1. 访问: https://github.com/AgenticAIPlan/AgenticAISkills"
echo "2. 点击右上角 'Fork' 按钮"
echo "3. Fork后按回车继续"
read -p "已Fork? (按回车继续) "

echo "推送到你的Fork: $FORK_REPO"
git push -u origin feat/aistudio-project-reviewer

echo ""
echo "✓ 推送成功！"
echo ""

echo "下一步：创建Pull Request"
echo "-----------------------------------"
echo "访问以下链接创建PR："
echo "https://github.com/AgenticAIPlan/AgenticAISkills/compare/dev...$GITHUB_USERNAME:feat/aistudio-project-reviewer"
echo ""
echo "PR标题: feat: 添加飞桨星河社区项目评审专家Skill"
echo "目标分支: dev"
echo "来源分支: feat/aistudio-project-reviewer"
echo ""

echo "========================================="
echo "完成！"
echo "========================================="