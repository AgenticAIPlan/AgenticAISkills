# Policy Tracker - 使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install requests beautifulsoup4 lxml pyyaml jinja2 python-dateutil
```

### 2. 配置数据源

编辑 `references/config.yaml`：

```yaml
sources:
  - id: miit_wj
    name: 工信部政策
    url: https://www.miit.gov.cn/zwgk/zcwj/index.html
    parser:
      list_selector: "ul.news-list li"
      title_selector: "a::text"
      link_selector: "a::attr(href)"
      date_selector: "span.date::text"
```

**选择器配置说明**：
- `list_selector`: 政策列表容器选择器
- `title_selector`: 标题选择器
- `link_selector`: 链接选择器
- `date_selector`: 日期选择器

### 3. 配置关键词

```yaml
keywords:
  ai:
    - 人工智能
    - AI
    - 大模型
  data:
    - 数据要素
    - 数据安全
```

### 4. 配置推送

飞书机器人配置：
1. 在飞书群聊中添加群机器人
2. 获取Webhook地址
3. 填入配置：

```yaml
targets:
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

### 5. 运行

```bash
cd scripts
python main.py
```

### 6. 定时任务

**Windows任务计划程序**：
```
python main.py 每日 09:00 执行
```

**Cron (Linux/Mac)**：
```bash
0 9 * * * cd /path/to/scripts && python main.py
```

## 文件结构

```
policy-tracker/
├── SKILL.md                 # Skill定义
├── references/
│   ├── config.yaml         # 配置文件
│   └── report.tpl          # 报告模板
└── scripts/
    ├── main.py             # 主入口
    ├── collector.py        # 采集层
    ├── parser.py           # 解析层
    └── processor.py        # 处理层
```

## 故障排查

### 解析失败
检查配置的选择器是否匹配目标网站。可使用浏览器开发者工具检查HTML结构。

### 推送失败
- 确认Webhook地址正确
- 检查飞书/钉钉机器人是否有发送消息权限

### 网络超时
调整 `collector.timeout_connect` 和 `collector.timeout_read` 参数。