#!/usr/bin/env python3
"""
测试新的摘要格式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from feishu_bitable import PolicyBitableWriter
from datetime import datetime, timedelta

# 2026年4月之后的政策数据，测试分点摘要
policies_test = [
    {
        "title": "关于加快推进人工智能产业创新发展的实施意见",
        "url": "https://www.miit.gov.cn/jgsj/kjs/wjfb/art/2026/art_20260415001.html",
        "pub_date": "2026-04-15",
        "source_id": "miit_zc",
        "source_name": "中华人民共和国工业和信息化部",
        "categories": ["ai"],
        "summary": ""  # 空摘要，测试自动生成
    },
    {
        "title": "数据要素市场化配置改革2026年工作要点",
        "url": "https://www.cac.gov.cn/2026-04/18/c_20260418002.htm",
        "pub_date": "2026-04-18",
        "source_id": "cac_internet",
        "source_name": "国家互联网信息办公室",
        "categories": ["data"],
        "summary": ""  # 空摘要，测试自动生成
    },
    {
        "title": "北京市人工智能赋能新型工业化行动方案（2026年）",
        "url": "https://www.beijing.gov.cn/zhengce/zhengcefagui/202604/t20260410_001.html",
        "pub_date": "2026-04-10",
        "source_id": "beijing_zc",
        "source_name": "北京市人民政府",
        "categories": ["ai"],
        "summary": ""  # 空摘要，测试自动生成
    }
]

def main():
    print("="*70)
    print("测试新的分点摘要格式")
    print("="*70)
    
    import yaml
    config_path = Path(__file__).parent.parent / 'references' / 'config.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    writer = PolicyBitableWriter(config)
    
    print("\n测试摘要生成：\n")
    for i, policy in enumerate(policies_test, 1):
        title = policy['title']
        source = policy['source_name']
        tags = ['人工智能'] if 'ai' in policy['categories'] else ['数据要素']
        
        # 生成摘要
        summary = writer._generate_detailed_summary(title, '意见', tags, source)
        
        print(f"\n{'='*70}")
        print(f"政策 {i}: {title}")
        print(f"来源: {source}")
        print(f"{'='*70}")
        print(summary)
    
    print("\n" + "="*70)
    print("摘要格式测试完成")
    print("="*70)
    
    # 询问是否写入数据
    print("\n是否写入这3条测试数据到飞书表格？(y/n)")
    # 直接写入
    print("\n正在写入数据...")
    result = writer.write_policies(policies_test)
    print(f"写入完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")

if __name__ == "__main__":
    main()
