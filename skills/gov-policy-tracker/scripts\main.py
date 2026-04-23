#!/usr/bin/env python3
"""
政策追踪系统 - 主入口
定时抓取政府网站政策，筛选后推送到飞书/钉钉/邮件
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

import yaml

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from collector import Collector, test_connection
from parser import Parser
from processor import Processor


def setup_logging(config: dict):
    """配置日志"""
    log_config = config.get('logging', {})

    # 创建日志目录
    log_file = log_config.get('file', 'logs/policy_tracker.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志格式
    log_format = log_config.get('format',
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s')
    date_format = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=log_config.get('max_bytes', 10 * 1024 * 1024),
                backupCount=log_config.get('backup_count', 5)
            )
        ]
    )

    return logging.getLogger(__name__)


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if config_path is None:
        # 默认查找当前目录或父目录的 config.yaml
        base_dir = Path(__file__).parent.parent
        possible_paths = [
            base_dir / 'references' / 'config.yaml',
            base_dir / 'config.yaml',
        ]

        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break

    if config_path is None or not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    """主函数"""
    # 1. 加载配置
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)

    # 2. 设置日志
    logger = setup_logging(config)
    logger.info("="*50)
    logger.info(f"政策追踪任务开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 3. 测试网络连接
    logger.info("检查网络连接...")
    if not test_connection():
        logger.error("网络连接测试失败，请检查网络")
        sys.exit(1)

    # 4. 初始化各层
    collector = Collector(config)
    parser = Parser(config)
    processor = Processor(config)

    # 5. 执行抓取
    logger.info("="*20 + " 阶段1: 信息采集 " + "="*20)
    sources = config.get('sources', [])
    logger.info(f"数据源数量: {len(sources)}")

    fetch_results = collector.fetch_all(sources)

    # 统计
    success_sources = sum(1 for r in fetch_results if r['success'])
    failed_sources = len(fetch_results) - success_sources
    logger.info(f"采集完成: 成功 {success_sources}/{len(sources)}")

    # 6. 执行解析
    logger.info("="*20 + " 阶段2: 解析与筛选 " + "="*20)
    policies = parser.parse_all(fetch_results)

    ai_count = len(policies['ai'])
    data_count = len(policies['data'])
    total_items = len(policies['all'])
    logger.info(f"筛选完成: AI政策 {ai_count} 条, 数据政策 {data_count} 条")

    # 7. 生成报告
    logger.info("="*20 + " 阶段3: 生成报告 " + "="*20)

    # 查找模板文件
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'references' / 'report.tpl'

    if template_path.exists():
        template_path = str(template_path)
    else:
        template_path = None

    report = processor.generate_report(policies, template_path)
    logger.info(f"报告长度: {len(report)} 字符")

    # 8. 推送报告
    logger.info("="*20 + " 阶段4: 推送报告 " + "="*20)
    if ai_count > 0 or data_count > 0:
        results = processor.distribute(report)
        for target, success in results.items():
            status = "成功" if success else "失败"
            logger.info(f"推送 {target}: {status}")
    else:
        logger.info("无新政策，跳过推送")

    # 9. 写入飞书多维表格
    logger.info("="*20 + " 阶段5: 写入Bitable " + "="*20)
    bitable_result = processor.write_to_bitable(policies)
    if bitable_result['success'] > 0 or bitable_result['failed'] > 0:
        logger.info(f"Bitable写入: 成功 {bitable_result['success']}, 失败 {bitable_result['failed']}")

    # 10. 发送执行摘要
    stats = {
        'total_sources': len(sources),
        'success_sources': success_sources,
        'failed_sources': failed_sources,
        'total_items': total_items,
        'ai_count': ai_count,
        'data_count': data_count
    }
    processor.send_summary(stats)

    logger.info(f"任务完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)


if __name__ == "__main__":
    main()