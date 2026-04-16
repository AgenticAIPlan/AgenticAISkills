#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专家数据分析脚本
用于对采集的专家数据进行统计分析
"""

import json
import sys
from pathlib import Path

def analyze_expert_data(json_file):
    """分析专家数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    experts = data.get('experts', [])
    speeches = data.get('speeches', [])
    
    print(f"专家总数: {len(experts)}")
    print(f"言论总数: {len(speeches)}")
    
    # 按优先级统计
    priority_stats = {}
    for expert in experts:
        priority = expert.get('priority', '未知')
        priority_stats[priority] = priority_stats.get(priority, 0) + 1
    
    print("\n优先级分布:")
    for priority, count in priority_stats.items():
        print(f"  {priority}: {count}位")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze_experts.py <json文件>")
        sys.exit(1)
    
    analyze_expert_data(sys.argv[1])
