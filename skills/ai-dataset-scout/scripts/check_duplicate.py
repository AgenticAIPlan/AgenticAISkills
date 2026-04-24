#!/usr/bin/env python3
"""
数据集去重检查脚本

功能：扫描当前目录下所有任务的CSV文件，检查数据集是否已存在

用法：
    python check_duplicate.py <数据集名称1> [数据集名称2] ...
    python check_duplicate.py --list  # 列出所有已记录的数据集

返回值：
    0 - 所有数据集都是新的
    1 - 有重复数据集（会打印重复列表）
"""

import csv
import glob
import sys
import os


def get_all_dataset_names(base_dir: str) -> dict:
    """
    扫描所有CSV文件，提取数据集名称

    Returns:
        dict: {数据集名称: (csv文件路径, 行号)}
    """
    datasets = {}
    pattern = os.path.join(base_dir, "dataset_scout_*/datasets.csv")

    for csv_file in glob.glob(pattern):
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    if len(row) > 1 and row[1].strip():  # 第2列是数据集名称
                        name = row[1].strip()
                        if name == "数据集名称":
                            continue
                        datasets[name] = (csv_file, row_num)
        except Exception as e:
            print(f"警告: 读取 {csv_file} 失败: {e}", file=sys.stderr)

    return datasets


def check_duplicates(base_dir: str, names_to_check: list) -> tuple:
    """
    检查数据集是否重复

    Returns:
        tuple: (重复列表, 新数据集列表)
    """
    existing = get_all_dataset_names(base_dir)
    duplicates = []
    new_ones = []

    for name in names_to_check:
        name = name.strip()
        if name in existing:
            csv_file, row_num = existing[name]
            rel_path = os.path.relpath(csv_file, base_dir)
            duplicates.append((name, rel_path, row_num))
        else:
            new_ones.append(name)

    return duplicates, new_ones


def list_all_datasets(base_dir: str):
    """列出所有已记录的数据集"""
    datasets = get_all_dataset_names(base_dir)
    if not datasets:
        print("暂无已记录的数据集")
        return

    print(f"共 {len(datasets)} 个已记录的数据集：")
    print("-" * 60)
    for name in sorted(datasets.keys()):
        csv_file, row_num = datasets[name]
        rel_path = os.path.relpath(csv_file, base_dir)
        print(f"  {name} ({rel_path}:{row_num})")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    base_dir = os.getcwd()

    if sys.argv[1] == "--list":
        list_all_datasets(base_dir)
        sys.exit(0)

    names_to_check = sys.argv[1:]
    duplicates, new_ones = check_duplicates(base_dir, names_to_check)

    if duplicates:
        print("=" * 60)
        print("发现重复数据集：")
        print("=" * 60)
        for name, csv_file, row_num in duplicates:
            print(f"  [重复] {name}")
            print(f"         已存在于: {csv_file}:{row_num}")
        print()

    if new_ones:
        print("-" * 60)
        print("新数据集（可添加）：")
        print("-" * 60)
        for name in new_ones:
            print(f"  [新] {name}")
        print()

    print(f"摘要: 检查 {len(names_to_check)} 个, 重复 {len(duplicates)} 个, 新增 {len(new_ones)} 个")

    sys.exit(1 if duplicates else 0)


if __name__ == "__main__":
    main()
