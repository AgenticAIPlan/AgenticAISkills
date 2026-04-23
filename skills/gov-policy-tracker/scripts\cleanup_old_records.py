#!/usr/bin/env python3
"""
清理2026年4月之前的旧记录
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from feishu_bitable import FeishuBitableClient
from datetime import datetime, date
import yaml

def main():
    print("="*70)
    print("清理2026年4月之前的旧记录")
    print("="*70)
    
    # 加载配置
    config_path = Path(__file__).parent.parent / 'references' / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    bitable_config = config.get('feishu_bitable', {})
    app_id = bitable_config.get('app_id', '')
    app_secret = bitable_config.get('app_secret', '')
    base_token = bitable_config.get('base_token', '')
    table_id = bitable_config.get('table_id', '')
    
    if not all([app_id, app_secret, base_token, table_id]):
        print("配置不完整")
        return
    
    # 初始化客户端
    client = FeishuBitableClient(app_id, app_secret, base_token)
    client.get_tenant_token()
    
    # 读取所有记录
    print("\n读取所有记录...")
    records = client.read_records(table_id)
    print(f"共找到 {len(records)} 条记录")
    
    # 筛选2026年4月之前的记录
    cutoff_date = date(2026, 4, 1)
    old_records = []
    
    for record in records:
        record_id = record.get('record_id')
        fields = record.get('fields', {})
        
        # 获取政策发布日期
        pub_date_field = fields.get('政策发布日期', 0)
        if isinstance(pub_date_field, int):
            # 时间戳格式
            pub_date = datetime.fromtimestamp(pub_date_field / 1000).date()
        elif isinstance(pub_date_field, str):
            try:
                pub_date = datetime.strptime(pub_date_field, '%Y-%m-%d').date()
            except:
                continue
        else:
            continue
        
        # 检查是否在2026年4月之前
        if pub_date < cutoff_date:
            title = fields.get('政策标题', '无标题')
            old_records.append({
                'record_id': record_id,
                'title': title,
                'pub_date': pub_date.isoformat()
            })
    
    print(f"\n发现 {len(old_records)} 条2026年4月之前的记录：")
    for i, record in enumerate(old_records, 1):
        print(f"{i}. {record['title']} ({record['pub_date']})")
    
    if len(old_records) == 0:
        print("\n没有需要删除的旧记录")
        return
    
    # 删除旧记录
    print(f"\n开始删除 {len(old_records)} 条旧记录...")
    deleted_count = 0
    failed_count = 0
    
    for record in old_records:
        try:
            result = client.delete_record(table_id, record['record_id'])
            if result.get('code') == 0:
                deleted_count += 1
                print(f"[OK] 已删除: {record['title'][:30]}...")
            else:
                failed_count += 1
                print(f"[FAIL] 删除失败: {record['title'][:30]}...")
        except Exception as e:
            failed_count += 1
            print(f"[FAIL] 删除异常: {e}")
    
    print("\n" + "="*70)
    print(f"清理完成: 成功删除 {deleted_count} 条, 失败 {failed_count} 条")
    print("="*70)

if __name__ == "__main__":
    main()
