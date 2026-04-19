# 运行时与导出

本文件只回答模型应落到哪类运行时、是否需要导出，以及导出后需要自行承担哪些工程责任。

本文件不负责判断目标平台边界，也不负责决定原生或跨端宿主接入方式。

## 1. 默认路径

默认先在 PaddlePaddle 栈上完成 PaddleOCR 的基线验证。

这里的“基线验证”是为了确认模型、前后处理和效果口径，不等于承诺最终产品形态一定采用官方栈。

PaddleOCR 提供 Python 和 C++ SDK。对于其他语言，无法直接支持。

只有在用户明确提出以下约束时，才偏离默认路径：

- 目标环境不能承载 PaddleOCR 官方栈。
- 需要更明确的多后端或加速能力。
- 需要将导出的模型接入厂商推理 SDK 或其他目标运行时。

## 2. 高性能推理（HPI）

PaddleOCR 提供高性能推理（High-Performance Inference，HPI）功能，支持根据环境智能选择 ONNX Runtime、OpenVINO、TensorRT、Paddle Inference、Paddle TensorRT 子图引擎等多种推理后端。HPI 方案本身可以处理 ONNX 格式模型，也可能把 Paddle 模型自动转成 ONNX 参与推理。HPI 只在 PaddleOCR 的 Python 推理包中提供。

适合考虑 HPI 的前提：

- 用户仍能接受 PaddleOCR 相关依赖。
- 问题重点是加速、后端选择或官方栈内的高性能推理。

- 依赖安装：`paddleocr install_hpi_deps {cpu|gpu}`
- 典型入口：`enable_hpi=True`（Python API） 或 `--enable_hpi True`（CLI）

## 3. ONNX 导出与第三方运行时接入

更适合以下情况：

- 目标环境不能直接承载 PaddleOCR 官方栈。
- 设备侧已有厂商推理 SDK、NPU 工具链或其他可接入导出模型的第三方运行时。
- 用户明确接受自行维护推理链路。

可以参考 PaddleOCR 官方文档，使用 `paddlex paddle2onnx` 命令导出 ONNX 格式模型。导出成功不等于端到端链路可用。用户需要自行编写前处理、后处理和模型串联逻辑，以适配目标运行时。必要时还应补充端到端一致性验证。
