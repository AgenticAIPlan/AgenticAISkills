#!/usr/bin/env python3
"""
自动更新脚本 - 每天采集前一天的政策新闻
"""

import sys
import os
import yaml
import logging
from datetime import date, datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from collector import Collector
from parser import Parser
from feishu_bitable import PolicyBitableWriter


def get_yesterday_str():
    """获取昨天日期字符串"""
    yesterday = date.today() - timedelta(days=1)
    return yesterday.isoformat()


def run_daily_update():
    """执行每日更新"""
    yesterday = get_yesterday_str()
    logger.info("=" * 70)
    logger.info(f"开始自动更新 - 采集 {yesterday} 的政策新闻")
    logger.info("=" * 70)
    
    # 读取配置
    config_path = os.path.join(os.path.dirname(__file__), 'references', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 创建组件
    collector = Collector(config)
    parser = Parser(config)
    writer = PolicyBitableWriter(config)
    
    if not writer.is_ready():
        logger.error("飞书表格未配置，无法写入")
        return
    
    # 采集数据
    sources = config.get('sources', [])
    all_policies = []
    
    for source in sources:
        source_id = source.get('id', 'unknown')
        source_name = source.get('name', source_id)
        
        logger.info(f"\n正在采集: {source_name}")
        
        result = collector.fetch(source)
        
        if not result['success']:
            logger.error(f"  抓取失败: {result.get('error', 'Unknown')}")
            continue
        
        # 解析
        parsed = parser.parse_source(result)
        policies = parsed.get('policies', [])
        
        # 只保留昨天的政策
        yesterday_policies = []
        for p in policies:
            pub_date = p.get('pub_date', '')
            if pub_date == yesterday:
                yesterday_policies.append(p)
        
        if yesterday_policies:
            logger.info(f"  找到 {len(yesterday_policies)} 条 {yesterday} 的政策")
            all_policies.extend(yesterday_policies)
        else:
            logger.info(f"  无 {yesterday} 的政策")
    
    logger.info(f"\n" + "=" * 70)
    logger.info(f"采集完成: 共 {len(all_policies)} 条 {yesterday} 的政策")
    logger.info("=" * 70)
    
    if not all_policies:
        logger.info("没有新数据需要写入")
        return
    
    # 写入飞书表格
    logger.info("\n开始写入飞书表格...")
    result = writer.write_policies(all_policies)
    logger.info(f"写入完成: 成功 {result['success']} 条, 失败 {result['failed']} 条")
    
    base_token = config['feishu_bitable']['base_token']
    logger.info(f"\n查看数据: https://fcnhy42ew3lq.feishu.cn/base/{base_token}")


if __name__ == '__main__':
    run_daily_update()
