#!/usr/bin/env python3
"""
测试脚本 - 使用真实政策URL写入飞书多维表格
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from feishu_bitable import PolicyBitableWriter
from datetime import datetime, timedelta

# 真实政策数据（使用真实可访问的URL）
real_policies = [
    {
        "title": "信息化标准建设行动计划（2024—2027年）",
        "url": "https://www.cac.gov.cn/2024-05/29/c_1718573626260067.htm",
        "pub_date": "2024-05-29",
        "source_id": "cac_internet",
        "source_name": "国家互联网信息办公室",
        "categories": ["data"],
        "summary": "中央网信办、市场监管总局、工业和信息化部联合印发，加强信息化标准建设，健全国家信息化标准体系"
    },
    {
        "title": "促进和规范数据跨境流动规定",
        "url": "https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm",
        "pub_date": "2024-03-22",
        "source_id": "cac_internet",
        "source_name": "国家互联网信息办公室",
        "categories": ["data"],
        "summary": "国家互联网信息办公室令第16号，保障数据安全，保护个人信息权益，促进数据依法有序自由流动"
    },
    {
        "title": "深圳市打造人工智能先锋城市项目扶持计划操作规程",
        "url": "https://www.sz.gov.cn/cn/xxgk/zfxxgj/zcfg/content/post_12077754.html",
        "pub_date": "2025-03-19",
        "source_id": "shenzhen_zc",
        "source_name": "深圳市人民政府",
        "categories": ["ai"],
        "summary": "落实深圳市打造人工智能先锋城市的若干措施，规范项目扶持计划组织实施"
    },
    {
        "title": "深圳市打造人工智能先锋城市的若干措施政策解读",
        "url": "https://www.sz.gov.cn/zfgb/zcjd/content/post_11932960.html",
        "pub_date": "2024-12-30",
        "source_id": "shenzhen_zc",
        "source_name": "深圳市人民政府",
        "categories": ["ai"],
        "summary": "发挥深圳优势，强化应用牵引，实现算力供给最普惠、场景应用最开放、产业生态最健全"
    },
    {
        "title": "2024年度中小企业数字化转型典型案例征集",
        "url": "https://zjtx.miit.gov.cn/zxqySy/tzggView?id=3933c3854e0b4a6fb8a42d0ef1984c1a",
        "pub_date": "2024-07-31",
        "source_id": "miit_zjtx",
        "source_name": "中华人民共和国工业和信息化部",
        "categories": ["data"],
        "summary": "聚焦制造业重点行业领域，征集中小企业数字化转型典型案例，加强典型路径模式梳理总结"
    },
    {
        "title": "制造业数字化转型综合信息服务平台",
        "url": "https://szgx.miit.gov.cn/",
        "pub_date": "2024-12-13",
        "source_id": "miit_szgx",
        "source_name": "中华人民共和国工业和信息化部",
        "categories": ["ai", "data"],
        "summary": "工业和信息化部办公厅关于公布2024年先进计算赋能新质生产力典型应用案例名单"
    }
]

def main():
    print("="*70)
    print("测试 - 使用真实政策URL写入飞书多维表格")
    print("="*70)
    
    import yaml
    config_path = Path(__file__).parent.parent / 'references' / 'config.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    writer = PolicyBitableWriter(config)
    
    if not writer.is_ready():
        print("Bitable未配置完成")
        return
    
    print(f"\n准备写入 {len(real_policies)} 条真实政策数据...")
    print("\n政策列表：")
    for i, policy in enumerate(real_policies, 1):
        print(f"{i}. {policy['title']}")
        print(f"   来源：{policy['source_name']}")
        print(f"   URL：{policy['url']}")
        print()
    
    result = writer.write_policies(real_policies)
    
    print("="*70)
    print(f"写入完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")
    print("="*70)
    
    base_token = config.get('feishu_bitable', {}).get('base_token', '')
    if base_token:
        print(f"\n查看数据: https://fcnhy42ew3lq.feishu.cn/base/{base_token}")
        print("\n注意：点击'原文链接'字段中的URL即可访问政策原文")

if __name__ == "__main__":
    main()
