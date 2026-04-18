# PaddleOCR 能力与接口依赖说明

本 Skill 使用 PaddleOCR 文档解析能力，将本地论文 PDF 转换为 Markdown 文本，并将解析结果中的图片资源下载到同名目录。

飞桨星河社区的 PaddleOCR 页面说明其覆盖文档解析、智能文字识别、API 调用和 MCP 服务等能力，适合作为论文处理、文档整理和结构化提取场景的底层能力来源：

<https://aistudio.baidu.com/paddleocr>

## 本 Skill 使用的能力

- 通过文档解析接口读取本地 PDF。
- 获取每页 Markdown 正文。
- 获取每页图片资源映射。
- 将图片资源下载到本地同名目录。
- 将 Markdown 中的图片引用改写为可迁移的相对路径。

## 运行环境要求

运行环境必须提供：

- `PADDLEOCR_DOC_PARSING_API_URL`
- `PADDLEOCR_ACCESS_TOKEN`
- 可选：`PADDLEOCR_DOC_PARSING_TIMEOUT`

密钥只能通过环境变量提供，不能写入 Skill 文件、PR 描述、提交记录或路径清单。

## 依赖边界

本 Skill 不负责申请 PaddleOCR 服务、创建 token 或托管接口。若接口鉴权失败、限流、超时或返回结构变化，脚本会将错误写入 JSON 摘要并返回非零退出码。

如需要更换 OCR 服务，应创建另一个 Skill 或显式修改脚本实现；当前 Skill 不在失败时自动切换到其他 OCR 流程。
