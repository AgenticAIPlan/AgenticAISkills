#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞桨星河社区项目评审专家Skill - 主执行脚本

使用方法:
    python run_review.py --project_url <项目链接> [--description <项目描述>] [--focus <full|quick|specific>]
"""

import json
import argparse
import sys
from pathlib import Path


class ProjectReviewer:
    """项目评审专家类"""

    def __init__(self, skill_path="aistudio-project-reviewer.skill.json"):
        """初始化评审专家

        Args:
            skill_path: skill配置文件路径
        """
        self.skill_path = Path(skill_path)
        self.skill_config = self._load_skill_config()

    def _load_skill_config(self):
        """加载skill配置"""
        if not self.skill_path.exists():
            raise FileNotFoundError(f"Skill配置文件不存在: {self.skill_path}")

        with open(self.skill_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_system_prompt(self):
        """获取系统提示词"""
        return self.skill_config.get('system_prompt', '')

    def get_input_schema(self):
        """获取输入参数schema"""
        return self.skill_config.get('input_schema', {})

    def get_examples(self):
        """获取示例"""
        return self.skill_config.get('examples', [])

    def validate_input(self, project_url, project_description="", review_focus="full"):
        """验证输入参数

        Args:
            project_url: 项目链接
            project_description: 项目描述
            review_focus: 评审深度

        Returns:
            (is_valid, error_message)
        """
        if not project_url:
            return False, "项目链接不能为空"

        schema = self.get_input_schema()
        required = schema.get('required', [])

        if 'project_url' in required and not project_url:
            return False, "项目链接是必需参数"

        if review_focus not in schema['properties']['review_focus']['enum']:
            return False, f"评审深度必须是: {', '.join(schema['properties']['review_focus']['enum'])}"

        return True, ""

    def prepare_review_context(self, project_url, project_description="", review_focus="full"):
        """准备评审上下文

        Args:
            project_url: 项目链接
            project_description: 项目描述
            review_focus: 评审深度

        Returns:
            包含system_prompt和user_message的字典
        """
        user_message = f"请评审以下项目：\n\n"
        user_message += f"项目链接: {project_url}\n"

        if project_description:
            user_message += f"项目描述: {project_description}\n"

        user_message += f"评审深度: {review_focus}\n"

        return {
            "system_prompt": self.get_system_prompt(),
            "user_message": user_message
        }

    def review(self, project_url, project_description="", review_focus="full", output_file=None):
        """执行项目评审

        Args:
            project_url: 项目链接
            project_description: 项目描述
            review_focus: 评审深度
            output_file: 输出文件路径（可选）

        Returns:
            评审结果字符串
        """
        # 验证输入
        is_valid, error_msg = self.validate_input(project_url, project_description, review_focus)
        if not is_valid:
            print(f"错误: {error_msg}", file=sys.stderr)
            return None

        # 准备上下文
        context = self.prepare_review_context(project_url, project_description, review_focus)

        # 生成评审结果（在实际应用中，这里会调用LLM）
        # 这里返回提示上下文供用户手动使用或集成到其他系统
        review_result = f"=== 评审请求已准备 ===\n\n"
        review_result += f"System Prompt:\n{context['system_prompt']}\n\n"
        review_result += f"User Message:\n{context['user_message']}\n\n"
        review_result += "提示: 将上述内容发送给支持的工具或API以获取完整的评审结果。"

        # 输出到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(review_result)
            print(f"评审结果已保存到: {output_file}")

        return review_result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='飞桨星河社区项目评审专家',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完整评审
  python run_review.py --project_url https://aistudio.baidu.com/projectdetail/123456

  # 快速评审
  python run_review.py --project_url https://aistudio.baidu.com/projectdetail/123456 --focus quick

  # 带项目描述的评审
  python run_review.py --project_url https://aistudio.baidu.com/projectdetail/123456 \\
                      --description "基于ResNet50的图像分类项目"

  # 保存结果到文件
  python run_review.py --project_url https://aistudio.baidu.com/projectdetail/123456 \\
                      --output review_result.txt
        """
    )

    parser.add_argument(
        '--project_url',
        required=True,
        help='AI Studio项目链接（必需）'
    )

    parser.add_argument(
        '--description',
        default='',
        help='项目描述或摘要（可选）'
    )

    parser.add_argument(
        '--focus',
        choices=['full', 'quick', 'specific'],
        default='full',
        help='评审深度: full=完整评审, quick=快速筛选, specific=针对特定问题评审（默认: full）'
    )

    parser.add_argument(
        '--output',
        help='输出文件路径（可选）'
    )

    parser.add_argument(
        '--skill',
        default='aistudio-project-reviewer.skill.json',
        help='Skill配置文件路径（默认: aistudio-project-reviewer.skill.json）'
    )

    args = parser.parse_args()

    try:
        reviewer = ProjectReviewer(args.skill)
        result = reviewer.review(
            project_url=args.project_url,
            project_description=args.description,
            review_focus=args.focus,
            output_file=args.output
        )

        if result and not args.output:
            print(result)

    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
