#!/usr/bin/env python3
"""
魔搭社区数据集更新监控脚本
每次运行时获取最新数据集列表，基于创建时间(GmtCreate)和修改时间(GmtModified)
与上次快照对比，分别统计"新创建"和"有更新"的数据集。
快照文件持久化存储在脚本同级目录的 snapshot.json 中。
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_FILE = os.path.join(SCRIPT_DIR, "snapshot.json")

# 魔搭数据集列表 API（按最近修改排序，无需认证）
API_URL = "https://www.modelscope.cn/api/v1/dolphin/datasets?SortBy=GmtModified&PageSize={page_size}&PageNum={page}"


def ts_to_str(ts):
    """Unix 时间戳转可读字符串"""
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, ValueError):
        return str(ts)


def fetch_datasets(page_size=50, max_pages=3):
    """
    从魔搭 API 获取最新数据集列表。
    返回: list of dict，包含 name, path, gmt_create, gmt_modified 等字段
    """
    all_datasets = []
    seen_paths = set()

    for page in range(1, max_pages + 1):
        url = API_URL.format(page_size=page_size, page=page)
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        req.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"[错误] 请求第 {page} 页失败: {e}", file=sys.stderr)
            break

        if data.get("Code") != 200 or "Data" not in data:
            print(f"[错误] API 返回异常: Code={data.get('Code')}, Message={data.get('Message', 'unknown')}", file=sys.stderr)
            break

        items = data["Data"]
        if not isinstance(items, list) or not items:
            break

        for item in items:
            namespace = item.get("Namespace", "")
            name = item.get("Name", "")
            path = f"{namespace}/{name}" if namespace else name
            if path in seen_paths:
                continue
            seen_paths.add(path)
            all_datasets.append({
                "name": name,
                "path": path,
                "gmt_create": item.get("GmtCreate", 0) or 0,
                "gmt_modified": item.get("GmtModified", 0) or 0,
            })

    return all_datasets


def load_snapshot():
    """加载上次快照"""
    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_snapshot(datasets, timestamp, ts_epoch):
    """保存当前快照"""
    snapshot = {
        "timestamp": timestamp,
        "timestamp_epoch": ts_epoch,
        "dataset_count": len(datasets),
        "datasets": {d["path"]: d for d in datasets},
    }
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    return snapshot


def main():
    import argparse
    parser = argparse.ArgumentParser(description="魔搭社区数据集更新监控")
    parser.add_argument("--pages", type=int, default=3, help="获取页数（默认3页，每页50条）")
    parser.add_argument("--page-size", type=int, default=50, help="每页数量（默认50）")
    parser.add_argument("--dry-run", action="store_true", help="只查看不保存快照")
    parser.add_argument("--reset", action="store_true", help="清除快照重新开始")
    parser.add_argument("--history", action="store_true", help="查看上次快照信息")
    args = parser.parse_args()

    # 查看历史
    if args.history:
        snapshot = load_snapshot()
        if snapshot is None:
            print("暂无历史快照记录。")
        else:
            print(f"上次快照时间: {snapshot['timestamp']}")
            print(f"上次记录数据集数量: {snapshot['dataset_count']}")
            print(f"快照文件: {SNAPSHOT_FILE}")
        return

    # 重置
    if args.reset:
        if os.path.exists(SNAPSHOT_FILE):
            os.remove(SNAPSHOT_FILE)
            print("已清除快照文件。")
        else:
            print("无快照文件需要清除。")
        return

    now_dt = datetime.now()
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    now_epoch = int(now_dt.timestamp())

    print(f"=== 魔搭社区数据集更新监控 ===")
    print(f"当前时间: {now}")
    print(f"正在获取最新数据集（前 {args.pages} 页，每页 {args.page_size} 条）...\n")

    # 获取最新数据集
    new_datasets = fetch_datasets(page_size=args.page_size, max_pages=args.pages)
    if not new_datasets:
        print("[错误] 未能获取到任何数据集，请检查网络。")
        sys.exit(1)

    print(f"本次获取到 {len(new_datasets)} 个数据集。\n")

    # 加载上次快照
    old_snapshot = load_snapshot()

    if old_snapshot is None:
        print("首次运行，无历史快照可对比。")
        print(f"将记录当前 {len(new_datasets)} 个数据集作为基线快照。\n")
    else:
        last_time = old_snapshot.get("timestamp", "未知")
        last_epoch = old_snapshot.get("timestamp_epoch", 0)
        last_count = old_snapshot.get("dataset_count", 0)
        old_datasets = old_snapshot.get("datasets", {})

        print(f"上次快照: {last_time}（{last_count} 个数据集）")

        # 基于时间戳分类
        newly_created = []   # 创建时间在上次检查之后
        recently_modified = []  # 修改时间在上次检查之后，但创建时间在之前
        new_in_list = []     # path 不在旧快照中（可能是新进入前N条的）

        for d in new_datasets:
            path = d["path"]
            gmt_create = d["gmt_create"]
            gmt_modified = d["gmt_modified"]

            if gmt_create > last_epoch:
                newly_created.append(d)
            elif gmt_modified > last_epoch:
                recently_modified.append(d)

            if path not in old_datasets:
                new_in_list.append(d)

        print(f"\n{'='*60}")
        print(f"  对比结果（距上次检查）")
        print(f"{'='*60}")
        print(f"  新创建的数据集:     {len(newly_created)} 个")
        print(f"  有内容更新的数据集: {len(recently_modified)} 个")
        if new_in_list:
            print(f"  新进入列表的数据集: {len(new_in_list)} 个")
        print(f"{'='*60}")

        # 显示新创建的数据集详情
        if newly_created:
            newly_created.sort(key=lambda x: x["gmt_create"], reverse=True)
            print(f"\n--- 新创建的数据集 ---")
            for i, d in enumerate(newly_created, 1):
                print(f"  {i}. {d['path']}")
                print(f"     创建时间: {ts_to_str(d['gmt_create'])}")
                print(f"     链接: https://www.modelscope.cn/datasets/{d['path']}")
                print()

        # 显示有更新的数据集（最多显示20个）
        if recently_modified:
            recently_modified.sort(key=lambda x: x["gmt_modified"], reverse=True)
            show_count = min(len(recently_modified), 20)
            print(f"\n--- 有内容更新的数据集（显示最新 {show_count} 个） ---")
            for i, d in enumerate(recently_modified[:show_count], 1):
                print(f"  {i}. {d['path']}")
                print(f"     最后修改: {ts_to_str(d['gmt_modified'])}")
            if len(recently_modified) > show_count:
                print(f"  ... 还有 {len(recently_modified) - show_count} 个")

        # 计算时间间隔和频率
        try:
            last_dt = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
            delta = now_dt - last_dt
            hours = delta.total_seconds() / 3600
            print(f"\n--- 更新频率估算 ---")
            print(f"距上次检查: {delta.days} 天 {delta.seconds // 3600} 小时 {(delta.seconds % 3600) // 60} 分钟")

            if len(newly_created) > 0 and hours > 0:
                rate = len(newly_created) / hours
                print(f"新数据集创建速率: {rate:.2f} 个/小时（{rate * 24:.1f} 个/天）")
                if rate * 24 > 20:
                    print(f"建议爬取频率: 每天 1-2 次")
                elif rate * 24 > 5:
                    print(f"建议爬取频率: 每 2-3 天 1 次")
                elif rate * 24 > 1:
                    print(f"建议爬取频率: 每周 1-2 次")
                else:
                    print(f"建议爬取频率: 每周 1 次或更低")
            else:
                print(f"该时间段内无新创建的数据集。")

            if len(recently_modified) > 0 and hours > 0:
                mod_rate = len(recently_modified) / hours
                print(f"数据集更新速率: {mod_rate:.2f} 个/小时（{mod_rate * 24:.1f} 个/天）")
        except ValueError:
            pass

    # 保存快照
    if not args.dry_run:
        save_snapshot(new_datasets, now, now_epoch)
        print(f"\n快照已更新保存至: {SNAPSHOT_FILE}")
    else:
        print(f"\n[dry-run] 未保存快照。")


if __name__ == "__main__":
    main()
