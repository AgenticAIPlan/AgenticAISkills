#!/usr/bin/env python3
"""
验证数据源URL可访问性
"""

import requests
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from collector import Collector, test_connection

def verify_url(url, timeout=10):
    """验证URL是否可访问"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, f"[OK] 成功 ({len(response.text)} 字符)"
        else:
            return False, f"[FAIL] HTTP {response.status_code}"
    except requests.Timeout:
        return False, "[FAIL] 超时"
    except requests.ConnectionError:
        return False, "[FAIL] 连接错误"
    except Exception as e:
        return False, f"[FAIL] 错误: {str(e)[:50]}"

def main():
    print("="*70)
    print("验证数据源URL可访问性")
    print("="*70)
    
    # 加载配置
    config_path = Path(__file__).parent.parent / 'references' / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    sources = config.get('sources', [])
    print(f"\n共 {len(sources)} 个数据源需要验证\n")
    
    success_count = 0
    fail_count = 0
    
    for source in sources:
        source_id = source.get('id', 'unknown')
        source_name = source.get('name', '未知')
        url = source.get('url', '')
        
        print(f"检查: {source_name}")
        print(f"  URL: {url}")
        
        success, message = verify_url(url)
        print(f"  结果: {message}\n")
        
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    print("="*70)
    print(f"验证完成: 成功 {success_count}/{len(sources)}, 失败 {fail_count}/{len(sources)}")
    print("="*70)
    
    if fail_count > 0:
        print("\n⚠️  建议：")
        print("1. 访问失败的URL需要手动检查并更新")
        print("2. 部分政府网站可能有反爬虫机制")
        print("3. 建议定期（每月）检查URL有效性")

if __name__ == "__main__":
    main()
