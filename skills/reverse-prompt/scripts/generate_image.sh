#!/bin/bash
# ERNIE-Image 文生图脚本 — 调用星河社区生图 API
# 用法: ./generate_image.sh "<提示词>" [尺寸] [输出路径]

set -e

PROMPT="$1"
SIZE="${2:-1024x1024}"
OUTPUT="${3:-generated_image.png}"

if [ -z "$PROMPT" ]; then
  echo "用法: $0 \"<提示词>\" [尺寸(默认1024x1024)] [输出路径]"
  exit 1
fi

if [ -z "$AISTUDIO_API_KEY" ]; then
  echo "错误: 请先设置 AISTUDIO_API_KEY 环境变量"
  echo "  export AISTUDIO_API_KEY=\"your-key\""
  exit 1
fi

# 构建请求
REQUEST_JSON=$(python3 -c "
import json, sys
payload = {
    'model': 'Ernie-image-turbo',
    'prompt': sys.argv[1],
    'n': 1,
    'response_format': 'b64_json',
    'size': sys.argv[2],
    'seed': -1
}
print(json.dumps(payload, ensure_ascii=False))
" "$PROMPT" "$SIZE")

echo "正在生成图片..."
echo "  提示词: $PROMPT"
echo "  尺寸: $SIZE"

# 调用 API
RESPONSE=$(curl -s https://aistudio.baidu.com/llm/lmapi/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: bearer $AISTUDIO_API_KEY" \
  -d "$REQUEST_JSON")

# 提取 base64 并保存为图片
python3 -c "
import json, base64, sys
data = json.load(sys.stdin)
if 'data' in data and len(data['data']) > 0:
    b64 = data['data'][0].get('b64_json', '')
    if b64:
        img_bytes = base64.b64decode(b64)
        with open(sys.argv[1], 'wb') as f:
            f.write(img_bytes)
        print(f'图片已保存到: {sys.argv[1]}')
    else:
        print('错误: 响应中无图片数据', file=sys.stderr)
        sys.exit(1)
elif 'error' in data:
    print(f\"API 错误: {data['error']}\", file=sys.stderr)
    sys.exit(1)
else:
    print(f\"未知响应: {json.dumps(data, ensure_ascii=False)}\", file=sys.stderr)
    sys.exit(1)
" "$OUTPUT" <<< "$RESPONSE"
