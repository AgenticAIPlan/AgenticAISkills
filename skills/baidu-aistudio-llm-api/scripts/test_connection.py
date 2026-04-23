#!/usr/bin/env python3
"""
测试星河社区大模型API连接

使用方法:
1. 设置环境变量: export AI_STUDIO_API_KEY="您的Access Token"
2. 运行脚本: python test_connection.py
"""

import os
import sys

def test_connection():
    """测试API连接"""
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

    print("🔗 正在测试连接...")

    try:
        # 测试简单对话
        response = client.chat.completions.create(
            model="ernie-5.0-thinking-preview",
            messages=[
                {"role": "user", "content": "你好，请回复'连接成功'"}
            ]
        )

        content = response.choices[0].message.content
        print(f"\n✅ 连接成功!")
        print(f"📝 模型响应: {content}")
        print(f"\n📊 Token使用: {response.usage.total_tokens} tokens")

    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
