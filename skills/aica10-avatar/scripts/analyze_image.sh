#!/bin/bash
# 图片逆向分析脚本 — 调用星河社区 ERNIE-4.5 多模态 API
# 用法: ./analyze_image.sh <图片路径> [分析提示词文件]

set -e

IMAGE_PATH="$1"
PROMPT_FILE="$2"

if [ -z "$IMAGE_PATH" ]; then
  echo "用法: $0 <图片路径> [分析提示词文件]"
  exit 1
fi

if [ -z "$AISTUDIO_API_KEY" ]; then
  echo "错误: 请先设置 AISTUDIO_API_KEY 环境变量"
  echo "  export AISTUDIO_API_KEY=\"your-key\""
  exit 1
fi

if [ ! -f "$IMAGE_PATH" ]; then
  echo "错误: 文件不存在 — $IMAGE_PATH"
  exit 1
fi

EXT="${IMAGE_PATH##*.}"
EXT_LOWER=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')
case "$EXT_LOWER" in
  png)  MIME="image/png" ;;
  jpg|jpeg) MIME="image/jpeg" ;;
  webp) MIME="image/webp" ;;
  bmp)  MIME="image/bmp" ;;
  *)    echo "错误: 不支持的图片格式 — .$EXT"; exit 1 ;;
esac

BASE64_DATA=$(base64 -i "$IMAGE_PATH" | tr -d '\n')

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PROMPT_FILE="$SCRIPT_DIR/../references/analysis-prompt.md"

if [ -n "$PROMPT_FILE" ] && [ -f "$PROMPT_FILE" ]; then
  ANALYSIS_PROMPT=$(cat "$PROMPT_FILE")
elif [ -f "$DEFAULT_PROMPT_FILE" ]; then
  ANALYSIS_PROMPT=$(cat "$DEFAULT_PROMPT_FILE")
else
  ANALYSIS_PROMPT="请对这张图片进行深度视觉分析，从主体内容、艺术风格、构图视角、色彩基调、光影效果、氛围情绪、文字内容、纹理质感 8 个维度详细描述，并输出适用于 ERNIE-Image 的三个版本提示词（精准复现版/创意改编版/精简核心版）。"
fi

REQUEST_JSON=$(python3 -c "
import json, sys
prompt_text = sys.stdin.read()
payload = {
    'model': 'ernie-4.5-turbo-vl-32k',
    'messages': [{'role': 'user', 'content': [
        {'type': 'image_url', 'image_url': {'url': f'data:$MIME;base64,$BASE64_DATA'}},
        {'type': 'text', 'text': prompt_text}
    ]}],
    'temperature': 0.3,
    'max_tokens': 4096
}
print(json.dumps(payload, ensure_ascii=False))
" <<< "$ANALYSIS_PROMPT")

RESPONSE=$(curl -s https://aistudio.baidu.com/llm/lmapi/v3/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: bearer $AISTUDIO_API_KEY" \
  -d "$REQUEST_JSON")

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'choices' in data and len(data['choices']) > 0:
    print(data['choices'][0]['message']['content'])
elif 'error' in data:
    print(f\"API 错误: {data['error']}\", file=sys.stderr)
    sys.exit(1)
else:
    print(f\"未知响应: {json.dumps(data, ensure_ascii=False)}\", file=sys.stderr)
    sys.exit(1)
"
