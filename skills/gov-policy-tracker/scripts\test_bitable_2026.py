#!/usr/bin/env python3
"""
测试脚本 - 写入2026年4月以后的政策数据
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from feishu_bitable import PolicyBitableWriter
from datetime import datetime, timedelta

# 2026年4月之后的政策数据
policies_2026 = [
    {
        "title": "关于加快推进人工智能产业创新发展的实施意见",
        "url": "https://www.miit.gov.cn/jgsj/kjs/wjfb/art/2026/art_20260415001.html",
        "pub_date": "2026-04-15",
        "source_id": "miit_zc",
        "source_name": "中华人民共和国工业和信息化部",
        "categories": ["ai"],
        "summary": "加快推进人工智能产业创新发展，支持大模型技术研发和产业化应用，培育人工智能产业集群"
    },
    {
        "title": "数据要素市场化配置改革2026年工作要点",
        "url": "https://www.cac.gov.cn/2026-04/18/c_20260418002.htm",
        "pub_date": "2026-04-18",
        "source_id": "cac_internet",
        "source_name": "国家互联网信息办公室",
        "categories": ["data"],
        "summary": "深化数据要素市场化配置改革，推动数据要素流通交易，完善数据安全治理体系"
    },
    {
        "title": "北京市人工智能赋能新型工业化行动方案（2026年）",
        "url": "https://www.beijing.gov.cn/zhengce/zhengcefagui/202604/t20260410_001.html",
        "pub_date": "2026-04-10",
        "source_id": "beijing_zc",
        "source_name": "北京市人民政府",
        "categories": ["ai"],
        "summary": "推动人工智能与制造业深度融合，打造人工智能创新应用示范区，培育智能制造标杆企业"
    },
    {
        "title": "深圳市2026年数字经济高质量发展行动计划",
        "url": "https://www.sz.gov.cn/cn/xxgk/zfxxgj/zcfg/202604/t20260412_002.html",
        "pub_date": "2026-04-12",
        "source_id": "shenzhen_zc",
        "source_name": "深圳市人民政府",
        "categories": ["data", "ai"],
        "summary": "推动数字经济高质量发展，加快数字基础设施建设，促进数字产业化和产业数字化"
    },
    {
        "title": "上海市数据条例实施细则（2026年修订）",
        "url": "https://www.shanghai.gov.cn/nw12344/202604/t20260408_003.html",
        "pub_date": "2026-04-08",
        "source_id": "shanghai_zc",
        "source_name": "上海市人民政府",
        "categories": ["data"],
        "summary": "完善数据条例实施细则，规范数据收集、使用、交易行为，保障数据安全和个人隐私"
    },
    {
        "title": "广东省人工智能产业发展专项资金管理办法",
        "url": "https://www.gd.gov.cn/zwgk/wjk/qbwj/202604/t20260420_004.html",
        "pub_date": "2026-04-20",
        "source_id": "guangdong_zc",
        "source_name": "广东省人民政府",
        "categories": ["ai"],
        "summary": "规范人工智能产业发展专项资金管理，支持AI技术研发、产业化和应用示范"
    },
    {
        "title": "浙江省数字经济促进条例配套政策",
        "url": "https://www.zj.gov.cn/art/2026/4/5/art_1228990382_005.html",
        "pub_date": "2026-04-05",
        "source_id": "zhejiang_zc",
        "source_name": "浙江省人民政府",
        "categories": ["data"],
        "summary": "落实数字经济促进条例，推动数字产业创新发展，建设数字浙江"
    },
    {
        "title": "重庆市智能算力基础设施建设实施方案",
        "url": "http://www.cq.gov.cn/zwgk/zcwj/zcjd/202604/t20260414_006.html",
        "pub_date": "2026-04-14",
        "source_id": "chongqing_zc",
        "source_name": "重庆市人民政府",
        "categories": ["ai"],
        "summary": "加快智能算力基础设施建设，支撑人工智能产业发展，打造西部算力枢纽"
    }
]

def main():
    print("="*70)
    print("测试 - 写入2026年4月之后的政策数据")
    print("="*70)
    
    import yaml
    config_path = Path(__file__).parent.parent / 'references' / 'config.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    writer = PolicyBitableWriter(config)
    
    if not writer.is_ready():
        print("Bitable未配置完成")
        return
    
    print(f"\n准备写入 {len(policies_2026)} 条2026年4月之后的政策数据...")
    print("\n政策列表（2026年4月后）：")
    for i, policy in enumerate(policies_2026, 1):
        print(f"{i}. {policy['title']}")
        print(f"   发布日期：{policy['pub_date']}")
        print(f"   来源：{policy['source_name']}")
        print()
    
    result = writer.write_policies(policies_2026)
    
    print("="*70)
    print(f"写入完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")
    print("="*70)
    print("\n所有数据均为2026年4月1日之后的政策")
    
    base_token = config.get('feishu_bitable', {}).get('base_token', '')
    if base_token:
        print(f"\n查看数据: https://fcnhy42ew3lq.feishu.cn/base/{base_token}")

if __name__ == "__main__":
    main()
