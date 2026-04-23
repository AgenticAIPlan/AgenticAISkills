#!/usr/bin/env python3
"""
查询星河社区可用的大模型列表

使用方法:
1. 设置环境变量: export AI_STUDIO_API_KEY="您的Access Token"
2. 运行脚本: python list_models.py
"""

import os
import sys

def list_models():
    """列出所有可用模型"""
    # 检查环境变量
    api_key = os.environ.get("AI_STUDIO_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 AI_STUDIO_API_KEY 环境变量")
        print("\n请访问 https://aistudio.baidu.com/account/accessToken 获取您的访问令牌")
        print("然后运行: export AI_STUDIO_API_KEY='您的令牌'")
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("❌ 错误: 未安装 openai 库")
        print("请运行: pip install openai")
        sys.exit(1)

    # 创建客户端
    client = OpenAI(
        api_key=api_key,
        base_url="https://aistudio.baidu.com/llm/lmapi/v3"
    )

    print("📋 正在查询可用模型...\n")

    try:
        models = client.models.list()

        print("=" * 60)
        print("星河社区可用模型列表")
        print("=" * 60)

        # 分类显示
        ernie_models = []
        deepseek_models = []
        other_models = []

        for model in models.data:
            model_id = model.id
            if 'ernie' in model_id.lower():
                ernie_models.append(model_id)
            elif 'deepseek' in model_id.lower():
                deepseek_models.append(model_id)
            else:
                other_models.append(model_id)

        if ernie_models:
            print("\n🤖 ERNIE 系列（百度文心）:")
            for m in sorted(ernie_models):
                print(f"   - {m}")

        if deepseek_models:
            print("\n🧠 DeepSeek 系列:")
            for m in sorted(deepseek_models):
                print(f"   - {m}")

        if other_models:
            print("\n📦 其他模型:")
            for m in sorted(other_models):
                print(f"   - {m}")

        print(f"\n总计: {len(models.data)} 个模型")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    list_models()
