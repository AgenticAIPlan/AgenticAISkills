#!/usr/bin/env python3
"""
测试脚本 - 向飞书多维表格写入示例政策数据
用于演示系统功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from feishu_bitable import PolicyBitableWriter
from datetime import datetime, timedelta

# 示例政策数据（上周至今 - 真实URL格式）
sample_policies = [
    {
        "title": "关于加快人工智能产业发展的指导意见",
        "url": "https://www.miit.gov.cn/jgsj/kjs/wjfb/art/2024/art_7d9b241f5d3844e8b8b9c3d8e2a1f0c5.html",
        "pub_date": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
        "source_id": "miit_wj",
        "source_name": "中华人民共和国工业和信息化部",
        "categories": ["ai"],
        "summary": "推动人工智能与实体经济深度融合，支持大模型研发应用，促进AI技术在各行业的创新应用"
    },
    {
        "title": "北京市数字经济促进条例",
        "url": "https://www.beijing.gov.cn/zhengce/zhengcefagui/202311/t20231130_12345.html",
        "pub_date": (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
        "source_id": "beijing_zc", 
        "source_name": "北京市人民政府",
        "categories": ["data"],
        "summary": "促进北京数字经济高质量发展，推动数据要素市场化配置，培育数字经济新业态新模式"
    },
    {
        "title": "深圳市人工智能产业发展扶持办法",
        "url": "http://www.sz.gov.cn/cn/xxgk/zfxxgj/yjzj/content/post_11234567.html",
        "pub_date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        "source_id": "shenzhen_zc",
        "source_name": "深圳市人民政府",
        "categories": ["ai"],
        "summary": "支持深圳人工智能产业发展，加大财政资金支持力度，培育人工智能创新生态"
    },
    {
        "title": "浙江省数据要素市场化配置改革总体方案",
        "url": "https://www.zj.gov.cn/art/2024/3/4/art_1228990382_58925199.html",
        "pub_date": (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d'),
        "source_id": "zhejiang_zc",
        "source_name": "浙江省人民政府",
        "categories": ["data"],
        "summary": "推进浙江数据要素市场化配置改革，构建数据要素交易流通体系，释放数据要素价值"
    },
    {
        "title": "大模型算法备案管理暂行办法",
        "url": "https://www.most.gov.cn/kjbgz/202404/t20240415_12345678.html",
        "pub_date": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        "source_id": "most_kj",
        "source_name": "中华人民共和国科学技术部",
        "categories": ["ai", "data"],
        "summary": "加强生成式AI服务算法备案管理，规范大模型研发和应用，保障算法安全可控"
    },
    {
        "title": "上海市促进人工智能产业发展条例",
        "url": "https://www.shanghai.gov.cn/nw12344/202403/t20240315_12345.html",
        "pub_date": (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'),
        "source_id": "shanghai_zc",
        "source_name": "上海市人民政府",
        "categories": ["ai"],
        "summary": "促进上海人工智能产业高质量发展，打造人工智能创新高地，推动AI技术产业化应用"
    },
    {
        "title": "重庆市数据条例",
        "url": "http://www.cq.gov.cn/zwgk/zcwj/zcjd/202404/t20240410_12345.html",
        "pub_date": (datetime.now() - timedelta(days=9)).strftime('%Y-%m-%d'),
        "source_id": "chongqing_zc",
        "source_name": "重庆市人民政府",
        "categories": ["data"],
        "summary": "规范重庆市数据收集、存储、使用、加工、传输、提供、公开等处理活动，保障数据安全"
    },
    {
        "title": "广东省数据要素市场化配置改革行动方案",
        "url": "https://www.gd.gov.cn/zwgk/wjk/qbwj/yfb/content/post_3000831.html",
        "pub_date": (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'),
        "source_id": "guangdong_zc",
        "source_name": "广东省人民政府",
        "categories": ["data"],
        "summary": "推进广东数据要素市场化配置改革，建设粤港澳大湾区数据要素交易市场"
    }
]

def main():
    print("="*60)
    print("测试 - 向飞书多维表格写入示例数据")
    print("="*60)
    
    # 加载配置
    import yaml
    config_path = Path(__file__).parent.parent / 'references' / 'config.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 初始化Bitable写入器
    writer = PolicyBitableWriter(config)
    
    if not writer.is_ready():
        print("Bitable未配置完成，请检查config.yaml")
        return
    
    print(f"\n准备写入 {len(sample_policies)} 条示例政策数据...\n")
    
    # 写入数据
    result = writer.write_policies(sample_policies)
    
    print("\n" + "="*60)
    print(f"写入完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")
    print("="*60)
    
    # 显示访问链接
    base_token = config.get('feishu_bitable', {}).get('base_token', '')
    if base_token:
        print(f"\n查看数据: https://fcnhy42ew3lq.feishu.cn/base/{base_token}")

if __name__ == "__main__":
    main()
