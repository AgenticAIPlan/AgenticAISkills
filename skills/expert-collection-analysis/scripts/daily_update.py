#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日数据更新脚本
用于定时采集、分析和同步专家数据
"""

import sys
import os
from datetime import datetime
from enhanced_main import Config, EnhancedExpertDataPipeline

def main():
    """执行每日数据更新"""
    print("=" * 70)
    print(f"🔄 每日数据更新")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    try:
        # 初始化系统
        config = Config("config.ini")
        system = EnhancedExpertDataPipeline(config)

        # 执行完整工作流
        print("开始采集和分析...")
        results = system.run_full_pipeline()

        print()
        print("=" * 70)
        print("✅ 每日更新完成！")
        print("=" * 70)
        print()
        print("📊 查看结果:")
        print("  - 本地Excel: output/专家分析报告_*.xlsx")
        print("  - 飞书表格: 需手动导入或等待API权限")
        print()

    except Exception as e:
        print(f"❌ 更新失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
