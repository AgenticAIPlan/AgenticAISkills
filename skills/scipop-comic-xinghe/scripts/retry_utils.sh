#!/bin/bash
# 重试工具函数
# 用法: source retry_utils.sh

# 指数退避重试函数
# 参数: $1 = 最大重试次数, $2 = 要执行的命令
retry_with_backoff() {
    local max_retries=$1
    shift
    local cmd="$@"

    for ((i=1; i<=max_retries; i++)); do
        # 执行命令并捕获退出码
        eval "$cmd"
        exit_code=$?

        if [[ $exit_code -eq 0 ]]; then
            return 0
        fi

        # 计算等待时间（指数退避）
        wait_time=$((i * i))
        echo "⚠️ 第 $i 次尝试失败，${wait_time}s 后重试..."
        sleep $wait_time
    done

    echo "❌ 已重试 $max_retries 次，操作失败"
    return 1
}

# API调用重试函数（带HTTP状态码检查）
# 参数: $1 = 最大重试次数, $2 = curl命令
retry_api_call() {
    local max_retries=$1
    local curl_cmd="$2"
    local response_file="/tmp/api_response_$$.json"

    for ((i=1; i<=max_retries; i++)); do
        # 执行curl并捕获HTTP状态码
        http_code=$(eval "$curl_cmd -s -o $response_file -w '%{http_code}'")

        case $http_code in
            200)
                cat "$response_file"
                rm -f "$response_file"
                return 0
                ;;
            401)
                echo "❌ API Key 认证失败，请检查 AISTUDIO_API_KEY"
                rm -f "$response_file"
                return 1
                ;;
            402)
                echo "❌ 账户余额不足，请登录星河社区控制台充值"
                rm -f "$response_file"
                return 1
                ;;
            429|5*)
                wait_time=$((i * i))
                echo "⚠️ HTTP $http_code，${wait_time}s 后重试..."
                sleep $wait_time
                ;;
            *)
                echo "❌ 未知错误: HTTP $http_code"
                rm -f "$response_file"
                return 1
                ;;
        esac
    done

    echo "❌ API调用失败，已重试 $max_retries 次"
    rm -f "$response_file"
    return 1
}

# 从JSON提取base64并保存为图片
# 参数: $1 = JSON文件, $2 = 输出图片路径
extract_base64_image() {
    local json_file=$1
    local output_path=$2

    # 使用jq提取并解码
    if command -v jq &> /dev/null; then
        local b64_data=$(jq -r '.choices[0].message.content' "$json_file")
        # 去掉data:image/png;base64,前缀
        b64_data=${b64_data#data:image/png;base64,}
        echo "$b64_data" | base64 -d > "$output_path"
    else
        echo "需要安装 jq: brew install jq"
        return 1
    fi
}

# 示例用法
example_usage() {
    # 设置API Key
    export AISTUDIO_API_KEY="your-key"

    # 使用重试函数调用API
    retry_api_call 3 "curl https://aistudio.baidu.com/llm/lmapi/v3/images/generations \n        -H 'Content-Type: application/json' \n        -H 'Authorization: Bearer \$AISTUDIO_API_KEY' \n        -d '{"model": "ernie-image-turbo", "prompt": "测试", "n": 1, "size": "1024x1024"}'"
}

# 如果直接执行此脚本，显示帮助
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "重试工具函数库"
    echo ""
    echo "用法: source retry_utils.sh"
    echo ""
    echo "可用函数:"
    echo "  retry_with_backoff <次数> <命令>  - 指数退避重试"
    echo "  retry_api_call <次数> <curl命令>  - API调用重试"
    echo "  extract_base64_image <json> <png> - 提取base64图片"
fi