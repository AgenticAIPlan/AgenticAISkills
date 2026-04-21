---
name: benchmark-model-test
description: 用于批量测试多个大模型对同一组 prompt 的响应，自动化对比不同模型的输出质量并将结果保存到 Excel 表格中。当用户需要对比模型性能、收集测试数据或进行 benchmark 测试时使用。
---

# Benchmark Model Test

自动化测试多个大模型的响应，对比输出质量，并将结果保存到 Excel 表格中。

## 适用场景

当用户需要：
- 批量测试多个模型对同一组 prompt 的响应
- 对比不同大模型的输出质量
- 自动化收集模型测试数据
- 进行 benchmark 测试或模型评估

触发条件：用户提到 "benchmark"、"模型测试"、"模型对比"、"批量测试" 等关键词。

## 输入要求

### Excel 文件

| 列 | 内容 | 说明 |
|----|------|------|
| D (索引3) | prompt | 测试输入文本，必需 |
| G (索引6) | other | 附件文件名，用 `/` 分隔多个文件，可选 |
| H+ (索引7+) | 模型名称 | 表头填写模型名，数据行保存响应结果 |

**表头示例：**

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| 序号 | 任务 | 描述 | prompt | 状态 | 备注 | other | ERNIE-5.0-Thinking | gpt-5.4 | claude-sonnet-4.5 |

### 附件文件（可选）

- 存放在 `other/` 文件夹中
- 支持图片格式：jpg、jpeg、png、gif、webp
- 支持文档格式：txt、pdf、doc、docx、csv、xlsx、xls

## 执行步骤

1. **获取配置**：询问用户模型平台地址
2. **读取配置**：从 Excel 表头 H 列起读取要测试的模型名称
3. **模型匹配**：根据关键字匹配平台上可用的模型
4. **启动浏览器**：打开用户指定的模型平台页面
5. **检查登录**：如需登录，等待用户手动完成
6. **逐行测试**：
   - 创建新对话
   - 选择模型
   - 上传附件（如有）
   - 输入 prompt 并发送
   - 等待响应完成（15秒稳定性检测）
   - 保存结果到对应列
7. **自动保存**：每个模型测试完成后立即保存 Excel

## 输出要求

### Excel 结果

- 模型响应保存在表头对应的列中
- 响应内容完整，无截断
- 错误信息以 `错误:` 前缀保存

### 测试日志

- 显示当前处理行和模型
- 显示响应时间和字符数
- 显示保存位置

## 支持的模型

| 模型名称 | 描述 |
|----------|------|
| ERNIE-5.0-Thinking | 免费创意写作效果好 |
| ERNIE-4.5-Turbo | 免费速度快 |
| seedance-1.5-pro | 音画同步视频生成 |
| seed-2.0 | 免费多模态理解 |
| gpt-5.4 | OpenAI新作 |
| GPT-5.2 | 全能助手 |
| GPT-5.1 | 日常对话 |
| nano-banana-2 | 图像生成 |
| gemini-3-pro-preview | 多模态理解 |
| nano-banana-pro | 图像理解 |
| claude-opus-4.6 | 代码分析 |
| claude-sonnet-4.5 | 长文本分析 |
| DeepSeek-V3.2 | 免费快速通用 |
| Qwen3-235B-Thinking | 免费推理数学 |

## 使用方式

```bash
node scripts/skill.js --file benchmark.xlsx
node scripts/skill.js --file benchmark.xlsx --auto
node scripts/skill.js --file benchmark.xlsx --start-row 2 --timeout 480
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-f, --file` | Excel 文件路径 |
| `-s, --start-row` | 开始行号（默认 2） |
| `-t, --timeout` | 单个模型最长等待时间，秒（默认 480） |
| `--auto` | 自动模式，跳过交互确认 |

## 依赖安装

```bash
npm install playwright xlsx
npx playwright install chromium
```

## 注意事项

- 运行时需要用户输入模型平台地址
- 首次使用需手动登录
- Thinking 模型响应时间较长
- 表头模型名称支持关键字匹配
- 自动模式下需通过环境变量 `PLATFORM_URL` 指定平台地址

## 参考资料

详细的模型配置和高级用法，请参阅 `references/` 目录。