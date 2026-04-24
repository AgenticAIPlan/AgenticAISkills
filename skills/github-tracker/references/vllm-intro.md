# vLLM 项目简介

## 项目地址

https://github.com/vllm-project/vllm

## 项目简介

vLLM 是一个快速且易于使用的大语言模型（LLM）推理服务库，具有以下特点：

### 核心特性

- **高性能**：PagedAttention 技术，高效管理 KV Cache
- **高吞吐量**：连续批处理和优化的 CUDA 内核
- **易用性**：与 Hugging Face 模型无缝集成
- **灵活部署**：支持多种硬件（NVIDIA、AMD、Intel 等）

### 支持的模型类别

- **主流模型**：LLaMA、GPT、Qwen、DeepSeek 等
- **多模态模型**：LLaVA、mLLaMA 等
- **MoE 模型**：Mixtral、DeepSeek-MoE 等
- **量化模型**：FP8、INT8、INT4、AWQ、GPTQ 等

### 主要应用场景

- 在线推理服务
- 大规模模型部署
- 多模型并发服务
- 低延迟推理

## 技术亮点

1. **PagedAttention**：解决 KV Cache 内存碎片问题
2. **连续批处理**：动态调度请求，提升吞吐量
3. **CUDA 优化**：深度优化的推理内核
4. **分布式推理**：支持张量并行和流水线并行

## 社区活跃度

- GitHub Stars: 50k+
- 活跃贡献者: 500+
- 每日 PR 数量: 10-20 个