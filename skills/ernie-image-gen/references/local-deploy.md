# 本地部署与联调说明

本 skill 默认优先适配以下现有工程：

- `/Users/lixiaobai/.codex/超级个体项目孵化/ernie-image-siliconflow`

已确认该工程包含：

- `POST /generate`
- `POST /v1/images/generations`
- `GET /health`

以及以下本地权重包：

- `/Users/lixiaobai/.codex/超级个体项目孵化/ernie-image-siliconflow/ERNIE-Image.tar`

## 已确认的部署要点

根据附件 `Diffusers PR(8).pdf` 与本地工程：

- pipeline 为 `ErnieImagePipeline`
- 权重目录结构符合 diffusers `from_pretrained()` 读取方式
- 服务默认端口为 `8188`
- 本地启动命令为：

```bash
docker run --rm --gpus all -p 8188:8188 ernie-image:latest
```

双 4090 示例环境变量：

```bash
docker run --rm --gpus all -p 8188:8188 \
  -e ERNIE_IMAGE_PROFILE=dual_4090_balanced \
  -e ERNIE_IMAGE_TORCH_DTYPE=float16 \
  -e ERNIE_IMAGE_DEFAULT_HEIGHT=1024 \
  -e ERNIE_IMAGE_DEFAULT_WIDTH=1024 \
  -e ERNIE_IMAGE_DEFAULT_STEPS=40 \
  -e ERNIE_IMAGE_DEVICE_MAP_MODE=balanced \
  ernie-image:latest
```

## 推荐联调顺序

1. 先确认容器已启动
2. 调用 `/health`
3. 用本 skill 的配置模板把 `base_url` 指向 `http://127.0.0.1:8188`
4. 首次联调用 `response_format: b64_json`
5. 生成成功后检查 `achievement/` 中是否同时存在 PNG 与 metadata JSON

## 推荐的本地配置值

```yaml
mode: openai_compatible
base_url: http://127.0.0.1:8188
model: ernie-image
auth_token_env: ""
openai_path: /v1/images/generations
native_path: /generate
health_path: /health
model_dir: /opt/ernie-image/model/ERNIE-Image
weight_tar_path: ${ERNIE_IMAGE_WEIGHT_TAR_PATH:-./ERNIE-Image.tar}
output:
  artifact_dir: ${ERNIE_IMAGE_ARTIFACT_DIR:-./achievement}
```

在另一台电脑上，你只需要按实际情况设置：

```bash
export ERNIE_IMAGE_WEIGHT_TAR_PATH='/your/path/to/ERNIE-Image.tar'
export ERNIE_IMAGE_ARTIFACT_DIR='/your/output/dir'
```

如果不设置：

- `weight_tar_path` 默认留空或使用相对默认值
- `artifact_dir` 默认落到配置文件旁边的 `achievement/`

## 本 skill 不做的事

- 不在 skill 内重新实现服务端
- 不强制耦合某个云平台
- 不默认替你启动 Docker / 云函数

skill 的职责是：**以稳定的配置+脚本调用你已经有的 ERNIE Image 服务，并把结果规范归档。**
