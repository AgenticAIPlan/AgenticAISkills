#!/usr/bin/env python3
"""
读取问卷CSV文件的辅助脚本
注意：问卷导出的CSV文件使用GBK编码
"""

import csv
import sys
import os

def read_questionnaire_csv(file_path):
    """
    读取问卷CSV文件
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        list: 教师信息列表，每个元素是一个字典
    """
    try:
        # 问卷CSV文件使用GBK编码
        with open(file_path, 'r', encoding='gbk') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # CSV字段顺序
        # 0: 是否提交（\t1）
        # 1: 序号（\t1045）
        # 2: wj_uid（\t5224）
        # 3: 开始时间（2026-03-24 14:02:18）
        # 4: 提交时间（2026-03-24 14:03:35）
        # 5: IP地址（220.181.3.174）
        # 6: 来源地址（可能为空）
        # 7: 姓名（孙宇萌）
        # 8: 学校（北京大学）
        # 9: 学院（现代农学院）
        # 10: 专业（经济管理）
        # 11: 职称（无）
        # 12: 手机号（\t17756987901，注意前面有制表符）
        # 13: 邮箱（sunyumeng04@baidu.com）
        # 14: UID（\t16886555，注意前面有制表符）
        # 15-19: 其他字段
        # 20: 备注
        
        teachers = []
        for row in rows[1:]:  # 跳过标题行
            if len(row) >= 15:
                teacher = {
                    '姓名': row[7].strip() if len(row) > 7 else '',
                    '学校': row[8].strip() if len(row) > 8 else '',
                    '学院': row[9].strip() if len(row) > 9 else '',
                    '专业': row[10].strip() if len(row) > 10 else '',
                    '职称': row[11].strip() if len(row) > 11 else '',
                    '手机号': row[12].strip().replace('\t', '') if len(row) > 12 else '',
                    '邮箱': row[13].strip() if len(row) > 13 else '',
                    'UID': row[14].strip().replace('\t', '') if len(row) > 14 else '',
                    '提交时间': row[4].strip() if len(row) > 4 else '',
                    '备注': row[20].strip() if len(row) > 20 else ''
                }
                teachers.append(teacher)
        
        return teachers
        
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return []

def find_new_teachers(csv_file_path, processed_file_path):
    """
    从CSV文件中找到新增的老师
    
    Args:
        csv_file_path: 问卷CSV文件路径
        processed_file_path: 已处理记录文件路径
        
    Returns:
        list: 新增的老师列表
    """
    # 读取CSV文件
    all_teachers = read_questionnaire_csv(csv_file_path)
    print(f"问卷中共有 {len(all_teachers)} 位老师")
    
    # 读取已处理的老师记录
    processed_uids = set()
    if os.path.exists(processed_file_path):
        try:
            with open(processed_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'UID：' in line:
                        uid = line.split('UID：')[1].strip()
                        processed_uids.add(uid)
        except Exception as e:
            print(f"读取已处理记录失败: {e}")
    
    print(f"已处理 {len(processed_uids)} 位老师")
    
    # 从最后一行往前检查，找到新增的老师
    new_teachers = []
    for teacher in reversed(all_teachers):
        if teacher['UID'] and teacher['UID'] not in processed_uids:
            new_teachers.append(teacher)
        else:
            # 遇到已处理的老师就停止
            break
    
    print(f"找到 {len(new_teachers)} 位新增老师")
    return new_teachers

def update_processed_records(processed_file_path, teacher):
    """
    更新已处理记录文件
    
    Args:
        processed_file_path: 记录文件路径
        teacher: 老师信息字典
    """
    record = f"""
### {teacher['姓名']} - {teacher['学校']}
- UID：{teacher['UID']}
- 手机号：{teacher['手机号']}
- 学院：{teacher['学院']}
- 专业：{teacher['专业']}
- 职称：{teacher['职称']}
- 开通时间：{teacher['提交时间']}
- 开通状态：✅ 成功
"""
    
    with open(processed_file_path, 'a', encoding='utf-8') as f:
        f.write(record)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python3 read-csv.py <csv文件路径>")
        print("示例: python3 read-csv.py /tmp/playwright-artifacts-abc123/questionnaire.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    processed_file = os.path.expanduser("~/.openclaw/workspace/memory/teacher-permission-records.md")
    
    # 查找新增老师
    new_teachers = find_new_teachers(csv_file, processed_file)
    
    if new_teachers:
        print("\n新增老师列表:")
        for i, teacher in enumerate(new_teachers, 1):
            print(f"{i}. {teacher['姓名']} - {teacher['学校']} - UID: {teacher['UID']}")
    else:
        print("没有找到新增的老师")