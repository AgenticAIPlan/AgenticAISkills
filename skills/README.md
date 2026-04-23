# 飞桨星河社区项目评审专家Skill

基于大语言模型的飞桨星河社区（AI Studio）项目评审专家，负责项目评审、打分、提供修改建议，帮助开发者打磨项目到加精水平。

## 功能特性

- ✅ 多维度项目评审（创新性、技术深度、文档质量、可复现性、社区价值）
- ✅ AI生成内容检测与减分
- ✅ 快速筛选水文和低质量项目
- ✅ 具体的修改建议和资源指引
- ✅ 三种评审结论（建议加精、改一版能加精、建议放弃）
- ✅ 用户成长建议（PPDE申请、算力申领、激励计划）

## 快速开始

### 安装

```bash
# 克隆或下载本项目
cd comate-zulu-demo
```

### 使用方法

#### 1. 使用Python脚本

```bash
# 完整评审
python run_review.py --project_url https://aistudio.baidu.com/projectdetail/123456

# 快速筛选
python run_review.py --project_url https://aistudio.baidu.com/projectdetail/123456 --focus quick

# 带项目描述的评审
python run_review.py --project_url https://aistudio.baidu.com/projectdetail/123456 \n                    --description "基于ResNet50的图像分类项目"

# 保存结果到文件
python run_review.py --project_url https://aistudio.baidu.com/projectdetail/123456 \n                    --output review_result.txt
```

#### 2. 集成到其他系统

参考 `aistudio-project-reviewer.skill.json` 中的 `system_prompt` 和 `input_schema`，将此skill集成到你的聊天机器人或评审系统中。

### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `--project_url` | string | 是 | AI Studio项目链接 |
| `--description` | string | 否 | 项目描述或摘要 |
| `--focus` | enum | 否 | 评审深度：full（完整评审，默认）、quick（快速筛选）、specific（针对特定问题） |
| `--output` | string | 否 | 输出文件路径 |
| `--skill` | string | 否 | Skill配置文件路径（默认aistudio-project-reviewer.skill.json） |

## 项目结构

```
comate-zulu-demo/
├── aistudio-project-reviewer.skill.json  # 主skill配置文件
├── run_review.py                       # 可执行评审脚本
├── DESIGN.md                           # 详细设计文档
├── README.md                           # 本文件
├── templates/                          # 模板资源
│   ├──评分标准模板.md                  # 详细评分参考
│   ├──回复模板库.md                    # 各种场景的回复模板
│   └──快速检查清单.md                  # 项目评审快速检查清单
└── tests/                              # 测试文件
    └── test_reviewer.py                # 单元测试
```

## 评审标准

### 五个维度（满分100分）

1. **创新性（25分）**：选题、技术路线、独特思考
2. **技术深度（25分）**：API使用、模型调优、代码质量
3. **文档质量（20分）**：README清晰度、说明完整性
4. **可复现性（20分）**：环境依赖、数据集、一键运行
5. **社区价值（10分）**：对其他开发者的参考价值

### AI生成内容检测与减分

| 判定结果 | 特征描述 | 减分规则 |
|---------|---------|---------|
| 明显AI生成 | 高疑似特征≥3个，且无任何个人化内容 | 创新性-10，技术深度-5，文档质量-5（共-20分） |
| 疑似AI生成 | 高疑似特征1-2个，或中等疑似特征≥3个 | 创新性-5，技术深度-3（共-8分） |
| 部分AI辅助 | 有AI生成痕迹，但有明显的个人修改和补充 | 创新性-3，文档质量-2（共-5分） |
| 无明显AI痕迹 | 无上述特征，或AI仅用于翻译/格式化等辅助用途 | 不减分 |

### 加精底线

- 公开项目，必须使用飞桨或文心大模型技术
- README清晰易懂，内容充实
- 代码在AI Studio环境可运行
- 明显灌水或洗稿的不予加精
- 完全AI生成且无个人化内容的项目不建议加精

## 评审流程

1. **快速扫一眼**：看标题、技术栈、README前三行
2. **AI生成检测**：扫描README和代码注释的AI生成特征
3. **心里打分**：按五个维度评分，考虑AI生成减分
4. **给出结论**：建议加精 / 改一版能加精 / 建议放弃
5. **成长建议**（可选）：PPDE申请、算力申领等

## 回复风格

- 接地气的同事语气，不是机器人
- 具体评价，避免空话
- 直接指路，提供参考链接
- 禁用大段emoji、夸张赞美、生硬编号列表

## 资源库

### 官方资源
- **精品项目撰写指南**：在AI Studio搜索"精品项目撰写指南"
- **PaddleX文档第3章**：https://paddlex.readthedocs.io/zh_CN/develop/（代码生成工具）
- **飞桨API文档**：https://www.paddlepaddle.org.cn/documentation/docs/zh/api/index_cn.html
- **AI Studio使用指南**：https://aistudio.baidu.com/aistudio/course/introduce

### 数据集资源
- 百度AI Studio数据集：https://aistudio.baidu.com/aistudio/dataset
- 飞桨模型库：https://www.paddlepaddle.org.cn/model/

## 加精奖励

- 项目加精奖励：200元京东卡
- 写项目可申请算力（联系社区小助手）
- 参与激励计划可获得更多福利

## 开发和测试

### 运行测试

```bash
# 运行单元测试
python -m pytest tests/
```

## 扩展和定制

### 修改评审标准

编辑 `aistudio-project-reviewer.skill.json` 中的 `system_prompt` 部分，调整评审维度、评分标准或AI生成检测规则。

### 添加回复模板

在 `templates/回复模板库.md` 中添加新的场景和回复模板，然后在 `system_prompt` 中引用。

### 自定义输出格式

修改 `run_review.py` 中的 `review` 方法，或集成到你的系统中自定义输出格式。

## 常见问题

### Q: 如何处理无法访问的项目链接？

A: 提示用户检查链接是否正确，如果是私有项目，建议改为公开或直接提供项目内容。

### Q: AI生成检测准确吗？

A: 检测基于多个特征的综合判断，不是100%准确。如果开发者主动标注了AI辅助，会从轻处理。重点在于是否有个人化内容和真实经验。

### Q: 如何提高项目评审效率？

A: 使用 `--focus quick` 参数进行快速筛选，只检查关键问题。对于明显的水文或环境配置错误的项目，可以快速给出反馈。

## 贡献

欢迎提交Issue和Pull Request来改进这个skill。

## 许可证

MIT License

## 联系方式

- 飞桨星河社区：https://aistudio.baidu.com/
- 社区小助手：AI Studio内置功能

---

**提示**：这是一个辅助评审工具，最终评审结果建议由人工复核，特别是涉及加精奖励的项目。