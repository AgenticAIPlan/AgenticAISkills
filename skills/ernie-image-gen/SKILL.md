---
name: ernie-image-gen
description: Generate images with ERNIE Image through a configurable service endpoint. Use this skill when the user wants Chinese-first text-to-image generation, multilingual text rendering, long-text or multi-region text in images, or when the service base URL, auth token env name, model path, and ERNIE-Image weight tar path must be configurable without code changes.
---

# ERNIE Image Gen

使用 ERNIE Image 做文生图，默认走**服务调用模式**，并支持切换到兼容原生 `/generate` 接口的模式。这个 skill 适合：

- 需要通过配置切换不同 ERNIE Image 服务地址
- 需要保留 `model_dir` / `weight_tar_path` 等部署上下文，但不希望写死本机路径
- 需要中文优先、多语言混合、长文本、多区域文本渲染
- 需要把生成图片和元数据稳定落盘到当前项目或当前任务目录

## 默认逻辑：云端优先，本地显式触发

这个 skill 的默认行为是：

1. **优先采用云端模型服务**
   - 默认优先找云端配置
   - 默认优先使用 `assets/cloud-config.portable.cn.yaml`
   - 默认优先走 `openai_compatible`
2. **如果云端配置还没完成**
   - 不要直接假设本地模型
   - 先引导使用者补齐最少配置：`base_url`、`auth_token_env`、`mode`
   - 配完后先做 `health_check.py`，再生成
3. **只有在用户明确说明要用本地模型时**
   - 才切到本地配置路径
   - 才使用本地权重 / 本地部署上下文
   - 才优先参考 `assets/local-config.portable.cn.yaml`

## 使用者先配置这几项

无论是在另一台电脑、另一个项目，还是分享给别人用，优先检查这 5 项：

1. `base_url`
   - 改成你自己的 ERNIE Image 服务地址
2. `auth_token_env`
   - 填“环境变量名”，不是 API Key 本身
   - 例如：`ERNIE_IMAGE_API_KEY`
3. `mode`
   - OpenAI 兼容接口用 `openai_compatible`
   - 原生接口用 `native_generate`
4. `output.artifact_dir`
   - 推荐保留 `${ERNIE_IMAGE_ARTIFACT_DIR:-./achievement}`
   - 不写死本机绝对路径
5. `weight_tar_path`
   - 如果只是调远程服务，可以留空
   - 只有在你要保留本地部署上下文时才需要填

推荐直接从这两个模板开始：

- 通用英文模板：`assets/cloud-config.portable.yaml`
- 通用中文模板：`assets/cloud-config.portable.cn.yaml`
- 本地模型中文模板：`assets/local-config.portable.cn.yaml`

如果你只是普通云端调用，最常用的动作其实只有两步：

```bash
export ERNIE_IMAGE_API_KEY='你的key'
python3 scripts/generate_image.py --config assets/cloud-config.portable.cn.yaml --prompt '一只可爱的橘猫表情包'
```

## Quick Start

### A. 默认：云端服务调用

1. 优先复制可移植云端模板，而不是项目私有模板：
   - `assets/cloud-config.portable.cn.yaml`
   - 或 `assets/cloud-config.portable.yaml`
2. 按需修改：
   - `mode`: `openai_compatible` 或 `native_generate`
   - `base_url`
   - `auth_token_env`
   - `model_dir`（通常不用改）
   - `weight_tar_path`（可留空，或用环境变量占位）
   - 输出目录 `output.artifact_dir`（推荐相对路径或环境变量）
3. 先做健康检查：

```bash
python3 scripts/health_check.py \
  --config assets/cloud-config.portable.cn.yaml
```

4. 生成图片：

```bash
python3 scripts/generate_image.py \
  --config assets/cloud-config.portable.cn.yaml \
  --prompt "一只戴宇航员头盔的橘猫，电影感打光，超高细节"
```

### B. 仅当用户明确要求：本地模型调用

1. 复制本地模板：
   - `assets/local-config.portable.cn.yaml`
2. 重点修改：
   - `base_url`
   - `mode`
   - `model_dir`
   - `weight_tar_path`
   - `output.artifact_dir`
3. 再执行：

```bash
python3 scripts/health_check.py \
  --config assets/local-config.portable.cn.yaml
```

```bash
python3 scripts/generate_image.py \
  --config assets/local-config.portable.cn.yaml \
  --prompt "一只戴宇航员头盔的橘猫，电影感打光，超高细节"
```

更详细的跨机器/跨项目使用方式见：

- `references/portable-usage.md`

## Mode Decision

### 默认：`openai_compatible`

优先调用：

- `GET /health`
- `POST /v1/images/generations`

适合：

- 已有 OpenAI 兼容图片接口
- 想用统一的 `size` / `response_format`
- 后续希望无缝切到兼容网关
- 默认云端服务优先时，优先选这个

### 兼容：`native_generate`

调用：

- `GET /health`
- `POST /generate`

适合：

- 直接对接你现有的 `ernie-image-siliconflow` 原生接口
- 需要显式传 `height` / `width` / `num_inference_steps` / `guidance_scale`
- 用户明确说明要走本地模型 / 本地部署时，优先检查这个模式

## Prompt Workflow

1. 先明确画面主体、场景、风格、构图
2. 如果图里有文字，必须把**逐字文本**单独列出来
3. 如果是多语言或长文本，明确：
   - 语言种类
   - 每块文本的相对位置
   - 是否需要海报/标牌/包装排版
4. 默认保留显式参数覆盖入口：
   - `seed`
   - `width`
   - `height`
   - `num_inference_steps`
   - `guidance_scale`

详细模板见：

- `references/prompting.md`

## Artifact Policy

- 默认先执行健康检查，不健康直接失败
- 生成成功后，把图片保存到 `output.artifact_dir`
- 默认同时保存 metadata JSON：
  - prompt
  - effective_prompt
  - seed
  - width / height
  - num_inference_steps
  - guidance_scale
  - mode
  - model
  - output file path
  - response summary

## Config Contract

统一配置文件为 YAML，核心字段：

- `mode`
- `base_url`
- `model`
- `auth_token_env`
- `openai_path`
- `native_path`
- `health_path`
- `model_dir`
- `weight_tar_path`
- `defaults.width`
- `defaults.height`
- `defaults.num_inference_steps`
- `defaults.guidance_scale`
- `defaults.response_format`
- `output.artifact_dir`
- `output.save_metadata`

跨机器复用建议：

- `weight_tar_path` 推荐写成 `${ERNIE_IMAGE_WEIGHT_TAR_PATH:-}`
- `output.artifact_dir` 推荐写成 `${ERNIE_IMAGE_ARTIFACT_DIR:-./achievement}` 或项目内相对目录
- 相对 `artifact_dir` 会相对**配置文件所在目录**解析

字段说明见：

- `references/service-config-and-api.md`
- `references/portable-usage.md`

## Local Deployment / Existing Service

如果你要直接适配**你自己的**本地部署项目、容器服务或云函数服务，也可以继续用这个 skill。  
skill 本身只关心接口与配置，不绑定某个固定项目目录。

注意：

- 没有明确“本地模型”诉求时，默认不要走本地路径
- 只有用户明确说“使用本地模型 / 本地权重 / 本地服务”时，才切换到本地配置模板
- 如果云端配置缺失，优先做的是**提示补配置**，而不是自动切本地

部署与联调说明见：

- `references/local-deploy.md`

## Scripts

- `scripts/validate_config.py`：校验 YAML 配置
- `scripts/health_check.py`：健康检查
- `scripts/generate_image.py`：统一生成入口

当需要稳定行为时，优先直接运行这些脚本，而不是让 agent 临时拼 HTTP 请求。
