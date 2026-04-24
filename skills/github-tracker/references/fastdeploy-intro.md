# FastDeploy 项目简介

## 项目地址

https://github.com/PaddlePaddle/FastDeploy

## 项目简介

FastDeploy 是飞桨开源的深度学习全场景部署工具，支持多种深度学习框架和硬件平台。

### 核心特性

- **多框架支持**：PaddlePaddle、TensorFlow、PyTorch、ONNX 等
- **多硬件支持**：NVIDIA GPU、昆仑芯、昇腾、寒武纪等
- **高性能**：深度优化的推理引擎
- **易用性**：Python/C++/Go 多语言 API

### 支持的模型类型

- **LLM/VLM**：大语言模型、视觉语言模型
- **CV 模型**：图像分类、检测、分割等
- **语音模型**：ASR、TTS 等
- **NLP 模型**：文本分类、NER 等

### 主要应用场景

- 边缘端部署
- 云端服务
- 多模态推理
- 分布式推理

## 技术亮点

1. **统一接口**：一套 API 支持多框架、多硬件
2. **Speculative Decoding**：支持推测解码加速
3. **多模态 Runner**：优化的多模态推理流程
4. **KV Cache**：高效的 KV Cache 管理
5. **XPU 支持**：国产硬件深度优化

## 支持的推理引擎

- Paddle Inference
- TensorRT
- ONNX Runtime
- OpenVINO
- FastLLM

## 社区活跃度

- GitHub Stars: 3.7k+
- 活跃贡献者: 100+
- 每日 PR 数量: 15-30 个

## 相关项目

- PaddleOCR：OCR 部署
- PaddleNLP：NLP 模型部署
- PaddleSeg：分割模型部署