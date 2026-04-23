#!/bin/bash
# 飞桨星河社区项目评审专家Skill - GitHub提交脚本

set -e  # 遇到错误立即退出

echo "开始提交流程..."

# 1. 初始化git仓库（如果还没有）
if [ ! -d .git ]; then
    echo "初始化git仓库..."
    git init
fi

# 2. 添加远程仓库
echo "添加远程仓库..."
if ! git remote get-url origin > /dev/null 2>&1; then
    git remote add origin https://github.com/AgenticAIPlan/AgenticAISkills.git
else
    echo "远程仓库已存在"
fi

# 3. 拉取最新的dev分支（用于合并）
echo "拉取dev分支..."
git fetch origin dev || echo "dev分支不存在或无法访问"

# 4. 创建或切换到feat分支
echo "切换到feat/aistudio-project-reviewer分支..."
git checkout -b feat/aistudio-project-reviewer || git checkout feat/aistudio-project-reviewer

# 5. 添加所有文件
echo "添加文件到暂存区..."
git add .

# 6. 提交
echo "提交更改..."
if git diff --cached --quiet; then
    echo "没有需要提交的更改"
else
    git commit -m "feat: 添加飞桨星河社区项目评审专家Skill

- 实现多维度项目评审（创新性、技术深度、文档质量、可复现性、社区价值）
- 添加AI生成内容检测与减分机制
- 提供快速筛选功能
- 包含完整的模板资源库和评分标准
- 实现可执行评审脚本
- 符合仓库规范：skills/<skill-slug>/ 结构"
fi

# 7. 推送到GitHub
echo "推送到GitHub..."
git push -u origin feat/aistudio-project-reviewer --force

echo ""
echo "==================================="
echo "✅ 本地提交完成！"
echo "==================================="
echo ""
echo "下一步操作："
echo "1. 访问GitHub创建Pull Request："
echo "   https://github.com/AgenticAIPlan/AgenticAISkills/compare/dev...feat/aistudio-project-reviewer"
echo ""
echo "2. 或者使用GitHub CLI创建PR："
echo "   gh pr create --title 'feat: 添加飞桨星河社区项目评审专家Skill' --body '## 变更内容
- 新增飞桨星河社区项目评审专家Skill
- 符合仓库规范：skills/<skill-slug>/ 结构
- 包含完整的SKILL.md、assets/和references/
- 实现AI生成内容检测与减分机制' --base dev"
echo ""
echo "注意：如果推送失败，请确保："
echo "- 你有该仓库的push权限"
echo "- 或者先Fork仓库到你的账号，然后修改上面的远程仓库地址"
echo ""