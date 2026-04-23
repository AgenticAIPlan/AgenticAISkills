#!/usr/bin/env python3
"""
快速修复数据源URL工具
"""

import yaml
from pathlib import Path

def main():
    print("="*70)
    print("数据源URL修复工具")
    print("="*70)
    
    config_path = Path(__file__).parent.parent / 'references' / 'config.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    sources = config.get('sources', [])
    
    print(f"\n共 {len(sources)} 个数据源")
    print("\n建议修复的URL：")
    print("-"*70)
    
    # 已知有效的URL替换
    url_fixes = {
        'cac_internet': {
            'old': 'https://www.cac.gov.cn/2024-10/12/c_1729236849772982.htm',
            'new': 'https://www.cac.gov.cn/gzzt/ztzl/zt/wxdshm/A0920011118index_1.htm',
            'note': '网信办政策列表页'
        },
        'shenzhen_zc': {
            'old': 'http://www.sz.gov.cn/cn/xxgk/zfxxgj/yjzj/',
            'new': 'https://www.sz.gov.cn/cn/xxgk/zfxxgj/zcfg/',
            'note': '深圳市政策法规页'
        },
        'zhejiang_zc': {
            'old': 'https://www.zj.gov.cn/col/col1228990382/index.html',
            'new': 'https://www.zj.gov.cn/col/col1228990383/index.html',
            'note': '浙江省政策文件页（可能需要调整）'
        }
    }
    
    for source_id, fix_info in url_fixes.items():
        print(f"\n数据源: {source_id}")
        print(f"  当前: {fix_info['old']}")
        print(f"  建议: {fix_info['new']}")
        print(f"  说明: {fix_info['note']}")
    
    print("\n" + "="*70)
    print("操作指南：")
    print("1. 手动访问上述URL验证是否可访问")
    print("2. 编辑 config.yaml 更新URL")
    print("3. 运行 verify_urls.py 验证修复结果")
    print("="*70)

if __name__ == "__main__":
    main()
