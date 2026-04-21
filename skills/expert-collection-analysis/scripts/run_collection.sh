#!/bin/bash
# 数据采集执行脚本

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "智库专家数据采集"
echo "========================================="
echo ""

# 执行Python采集脚本
python3 "${PROJECT_DIR}/daily_update.py"

echo ""
echo "✓ 采集完成"
