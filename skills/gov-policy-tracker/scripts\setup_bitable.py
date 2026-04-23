#!/usr/bin/env python3
"""
飞书多维表格配置向导
引导用户完成Bitable配置
"""

import os
import sys
import yaml
from pathlib import Path


def print_step(step_num, title):
    """打印步骤标题"""
    print("\n" + "="*60)
    print("步骤 {}: {}".format(step_num, title))
    print("="*60)


def get_input(prompt, default=None):
    """获取用户输入"""
    if default:
        prompt = "{} [{}]: ".format(prompt, default)
    else:
        prompt = "{}: ".format(prompt)
    value = input(prompt).strip()
    return value if value else default


def main():
    print("""
==============================================================
                                                              
         飞书多维表格配置向导 - 政策追踪系统                    
                                                              
==============================================================

本向导将帮助您配置飞书多维表格，用于存储政策数据。
""")

    # 步骤1: 创建飞书应用
    print_step(1, "创建飞书应用")
    print("""
请按以下步骤操作：

1. 访问飞书开放平台：
   https://open.feishu.cn/app/cli_a96d81e056f85cb6/baseinfo
   
2. 点击左侧菜单"凭证与基础信息"
   
3. 复制 App Secret（点击显示后复制）
   
""")
    
    app_id = "cli_a96d81e056f85cb6"
    print("App ID: {}".format(app_id))
    app_secret = get_input("请输入 App Secret")
    
    if not app_secret:
        print("未提供 App Secret，退出配置")
        return

    # 步骤2: 开启权限
    print_step(2, "开启权限")
    print("""
在同一页面，点击左侧"权限管理"，添加以下权限：

[x] bitable:app - 读取多维表格应用信息
[x] bitable:record - 读取和修改记录  
[x] bitable:field - 读取字段信息

添加后点击"批量开通"
""")
    
    input("完成权限开通后，按回车继续...")

    # 步骤3: 发布应用
    print_step(3, "发布应用")
    print("""
1. 点击左侧"版本管理与发布"
2. 点击"创建版本"
3. 填写版本号（如 1.0.0）和更新说明
4. 点击"保存"
5. 点击"申请发布"
""")
    
    input("完成发布后，按回车继续...")

    # 步骤4: 创建多维表格
    print_step(4, "创建多维表格")
    print("""
1. 在飞书中搜索"多维表格"，创建新表格
2. 命名表格（如"政策追踪数据"）
3. 添加数据表，按以下字段创建：

   字段列表：
   +------------------+------------+
   | 抓取日期         | 日期       |
   | 政策发布日期     | 日期       |
   | 来源部门         | 文本       |
   | 地区             | 文本       |
   | 政策标题         | 文本       |
   | 政策摘要         | 文本       |
   | 原文链接         | 超链接     |
   | 文件原名         | 文本       |
   | 政策类型         | 单选       |
   | 关键词标签       | 多选       |
   | 优先级           | 单选       |
   | 处理状态         | 单选       |
   | 相关政策         | 文本       |
   | 备注             | 文本       |
   +------------------+------------+
""")
    
    input("创建完表格后，按回车继续...")

    # 步骤5: 获取表格信息
    print_step(5, "获取表格Token")
    print("""
1. 在浏览器中打开刚创建的多维表格
2. 复制URL中的base_token部分：
   
   示例URL：https://xxx.feishu.cn/base/UEECbOMyhaSa6vsxPvgcbe5bnFd
                                           ^^ 这是 base_token
   
   提示：表格创建时飞书会提供App Token，就是base_token
""")
    
    base_token = get_input("请输入 base_token (App Token)")
    
    if not base_token:
        print("未提供 base_token，退出配置")
        return

    # 步骤6: 获取数据表ID
    print_step(6, "获取数据表ID")
    print("""
获取 table_id 的方法：

方法1（推荐）：
1. 点击左下角数据表名称（默认"数据表1"）
2. 选择"复制链接"
3. 从链接中提取 table_id

方法2：
1. 查看浏览器URL，table_id 通常在 base_token 之后
   格式如：tblXXXXXXXXXXXXX
""")
    
    table_id = get_input("请输入 table_id")
    
    if not table_id:
        print("未提供 table_id，退出配置")
        return

    # 步骤7: 保存配置
    print_step(7, "保存配置")
    
    config_path = Path(__file__).parent.parent / 'references' / 'config.yaml'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 更新Bitable配置
        config['feishu_bitable'] = {
            'enabled': True,
            'app_id': app_id,
            'app_secret': app_secret,
            'base_token': base_token,
            'table_id': table_id
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        
        print("配置已保存到: {}".format(config_path))
        
    except Exception as e:
        print("保存配置失败: {}".format(e))
        return

    # 完成
    print("""
==============================================================
                                                              
              配置完成！                                     
                                                              
==============================================================

现在可以运行政策追踪系统：

   cd scripts
   python main.py

系统将自动把抓取到的政策数据写入飞书多维表格！

""")


if __name__ == "__main__":
    main()
