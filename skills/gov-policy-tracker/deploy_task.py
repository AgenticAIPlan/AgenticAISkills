#!/usr/bin/env python3
"""
部署定时任务 - 每天早上10点自动更新
"""

import os
import sys
import subprocess

def create_scheduled_task():
    """创建Windows定时任务"""
    
    task_name = "政策追踪自动更新"
    bat_path = r"C:\Users\renmeijing\ComateProjects\comate-zulu-demo\policy-tracker\run_auto_update.bat"
    
    print("=" * 60)
    print("正在部署定时任务...")
    print("=" * 60)
    print()
    
    # 检查批处理文件是否存在
    if not os.path.exists(bat_path):
        print(f"[错误] 找不到文件: {bat_path}")
        return False
    
    # 使用schtasks命令创建任务
    cmd = [
        "schtasks",
        "/Create",
        "/TN", task_name,  # 任务名称
        "/TR", bat_path,   # 执行程序
        "/SC", "DAILY",    # 每天执行
        "/ST", "10:00",    # 开始时间10:00
        "/RL", "HIGHEST",  # 最高权限
        "/F"               # 强制创建（覆盖现有）
    ]
    
    try:
        # 运行命令
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0 or "成功" in result.stdout:
            print(f"[成功] 任务 '{task_name}' 创建成功！")
            print()
            print("任务详情:")
            print(f"  - 任务名称: {task_name}")
            print(f"  - 执行时间: 每天早上 10:00")
            print(f"  - 执行程序: {bat_path}")
            print()
            print("管理命令:")
            print(f"  - 查看任务: schtasks /Query /TN \"{task_name}\"")
            print(f"  - 立即运行: schtasks /Run /TN \"{task_name}\"")
            print(f"  - 删除任务: schtasks /Delete /TN \"{task_name}\" /F")
            return True
        else:
            print(f"[错误] 创建失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[错误] 执行失败: {e}")
        return False

if __name__ == '__main__':
    success = create_scheduled_task()
    
    print()
    print("=" * 60)
    if success:
        print("部署完成！按任意键退出...")
    else:
        print("部署失败，请检查权限或手动设置")
    print("=" * 60)
    
    input()
