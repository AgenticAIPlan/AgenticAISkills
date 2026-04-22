# 服务配置与接口约定

## 配置文件

建议以单个 YAML 文件管理全部运行参数。

示例见：

- `../assets/cloud-config.portable.cn.yaml`
- `../assets/local-config.portable.cn.yaml`

默认建议：

- 优先使用云端模板
- 只有明确需要本地模型时，才使用本地模板

### 顶层字段

- `mode`: 调用模式
  - `openai_compatible`
  - `native_generate`
- `base_url`: 服务根地址，例如 `http://127.0.0.1:8188`
- `model`: 模型名，默认可用 `ernie-image`
- `auth_token_env`: Bearer Token 所在环境变量名；留空表示不加鉴权头
- `openai_path`: OpenAI 兼容接口路径，默认 `/v1/images/generations`
- `native_path`: 原生接口路径，默认 `/generate`
- `health_path`: 健康检查路径，默认 `/health`
- `model_dir`: 服务使用的模型目录，仅用于记录部署上下文
- `weight_tar_path`: 权重 tar 路径，仅用于记录部署上下文；远程服务调用时可留空
- `request_timeout_sec`: HTTP 超时秒数

### `defaults`

- `width`
- `height`
- `num_inference_steps`
- `guidance_scale`
- `response_format`
  - `b64_json`
  - `url`

### `output`

- `artifact_dir`: 图片与 metadata 默认输出目录，支持相对路径与环境变量展开
- `save_metadata`: 是否保存 JSON 元数据
- `filename_prefix`: 输出文件名前缀

## 推荐的跨机器写法

```yaml
weight_tar_path: ${ERNIE_IMAGE_WEIGHT_TAR_PATH:-}

output:
  artifact_dir: ${ERNIE_IMAGE_ARTIFACT_DIR:-./achievement}
```

说明：

- `${VAR}`：读取环境变量
- `${VAR:-default}`：环境变量不存在时使用默认值
- 相对路径 `./achievement` 会相对配置文件所在目录解析
- 如果你只是调用远程服务，`weight_tar_path` 留空完全没问题

## 请求映射

### 1) `mode: openai_compatible`

发送到：

- `POST {base_url}{openai_path}`

请求体映射：

```json
{
  "model": "ernie-image",
  "prompt": "<prompt>",
  "n": 1,
  "size": "1024x1024",
  "response_format": "b64_json",
  "guidance_scale": 5.0,
  "num_inference_steps": 40,
  "seed": 12345
}
```

说明：

- `size` 由 `width` / `height` 拼接为 `<width>x<height>`
- `response_format=url` 时，脚本会下载返回 URL 指向的图片并落盘

### 2) `mode: native_generate`

发送到：

- `POST {base_url}{native_path}`

请求体映射：

```json
{
  "prompt": "<prompt>",
  "height": 1024,
  "width": 1024,
  "num_inference_steps": 40,
  "guidance_scale": 5.0,
  "seed": 12345,
  "return_base64": true
}
```

说明：

- 若返回字段包含 `image_base64`，直接解码落盘
- 若返回字段包含 URL，也按 URL 下载后落盘

## 健康检查约定

所有生成前默认先请求：

- `GET {base_url}{health_path}`

判定规则：

- 返回状态码不是 `200`：视为失败
- 返回 JSON 里若 `status` 明确为 `ready`：视为就绪
- 返回 JSON 里若 `status` 为 `loading` / `error`：直接失败
- 无 `status` 字段但 HTTP 200：视为可用

## 元数据落盘

默认输出两个文件：

- `*.png`
- `*.json`

metadata JSON 至少包含：

- `timestamp`
- `mode`
- `model`
- `prompt`
- `effective_prompt`
- `request_payload`
- `response_summary`
- `seed`
- `output_file`
- `width`
- `height`
- `num_inference_steps`
- `guidance_scale`
