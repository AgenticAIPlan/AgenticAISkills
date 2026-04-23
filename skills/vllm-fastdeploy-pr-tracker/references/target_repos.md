# 监控目标仓库列表

本文档列出需要监控的 GitHub 仓库目标。

## 推理工具类

| 项目名 | 仓库 | 描述 | 监控重点 |
|--------|------|------|----------|
| vLLM | vllm-project/vllm | 高性能 LLM 推理引擎 | 新模型支持、量化方法、调度优化 |
| FastDeploy | PaddlePaddle/FastDeploy | 端到端推理部署方案 | 新模型支持、推理优化、部署能力 |
| TensorRT-LLM | NVIDIA/TensorRT-LLM | NVIDIA 高性能 LLM 推理 | 新模型、核优化、多卡支持 |
| llama.cpp | ggerganov/llama.cpp | 纯 CPU/GPU 推理 | 量化方法、推理速度 |
| Ollama | ollama/ollama | 本地 LLM 运行框架 | 新模型支持、易用性 |

## 添加新仓库

在下方添加新条目：

```markdown
| 项目名 | owner/repo | 描述 | 监控重点 |
|--------|------------|------|----------|
```