# 跨计算机 / 跨项目使用说明

这个 skill 的目标是：**配置一改，到别的电脑、别的项目、别的服务上也能继续用**。

## 默认决策顺序

1. 先看是否已有可用的云端配置
2. 如果没有，就先引导补齐云端配置
3. 只有用户明确要求“本地模型”时，才切到本地模板

推荐优先级：

- 默认优先：`assets/cloud-config.portable.cn.yaml`
- 显式本地：`assets/local-config.portable.cn.yaml`

## 最推荐的使用方式

优先从下面这个模板开始：

- `assets/cloud-config.portable.cn.yaml`

它适合：

- 分享给别人
- 复制到另一个项目里
- 换一台电脑继续用
- 从本地服务切到云端服务

## 使用者必须先改的字段

### 1. `base_url`

这是最重要的字段，改成自己的服务地址：

```yaml
base_url: https://your-ernie-image-domain.example.com
```

### 2. `auth_token_env`

这里填的是**环境变量名**，不是密钥本身：

```yaml
auth_token_env: ERNIE_IMAGE_API_KEY
```

然后在本机设置：

```bash
export ERNIE_IMAGE_API_KEY='你的key'
```

### 3. `mode`

按你的服务协议选：

- `openai_compatible`
- `native_generate`

默认推荐：

```yaml
mode: openai_compatible
```

## 一般不用改的字段

以下字段多数情况下可以保持默认：

- `model: ernie-image`
- `openai_path: /v1/images/generations`
- `native_path: /generate`
- `health_path: /health`
- `model_dir: /opt/ernie-image/model/ERNIE-Image`

## 最推荐的可移植写法

### 权重路径

```yaml
weight_tar_path: ${ERNIE_IMAGE_WEIGHT_TAR_PATH:-}
```

说明：

- 远程服务调用：可以留空
- 本地部署需要记录权重位置时：通过环境变量传入

### 输出目录

```yaml
artifact_dir: ${ERNIE_IMAGE_ARTIFACT_DIR:-./achievement}
```

说明：

- 如果设置了 `ERNIE_IMAGE_ARTIFACT_DIR`，输出到你指定的目录
- 如果没设置，默认输出到**配置文件所在目录旁边的 `achievement/`**
- 这种写法最适合跨项目复用

## 分享给别人时的建议

分享时，优先给对方这几样：

1. `SKILL.md`
2. `scripts/`
3. `assets/cloud-config.portable.cn.yaml`
4. 如果对方明确需要本地模型，再给 `assets/local-config.portable.cn.yaml`

并告诉对方只需要做三步：

```bash
export ERNIE_IMAGE_API_KEY='你的key'
python3 scripts/health_check.py --config assets/cloud-config.portable.cn.yaml
python3 scripts/generate_image.py --config assets/cloud-config.portable.cn.yaml --prompt '一只可爱的橘猫表情包'
```

## 不推荐的做法

不要在分享模板里写死：

- 你的本机绝对路径
- 你的项目私有目录
- 你的真实 API Key
- 只能在某个仓库里成立的输出路径

## 适合不同项目的输出策略

### 方案 A：跟配置文件走

```yaml
artifact_dir: ${ERNIE_IMAGE_ARTIFACT_DIR:-./achievement}
```

适合：

- 临时任务
- 新项目
- 别人拿去直接跑

### 方案 B：项目内固定产物目录

```yaml
artifact_dir: ${ERNIE_IMAGE_ARTIFACT_DIR:-./artifacts/ernie-image}
```

适合：

- 团队项目
- 想统一管理图片产物

### 方案 C：完全由环境变量控制

```yaml
artifact_dir: ${ERNIE_IMAGE_ARTIFACT_DIR}
```

适合：

- CI
- 批量任务
- 多环境切换
