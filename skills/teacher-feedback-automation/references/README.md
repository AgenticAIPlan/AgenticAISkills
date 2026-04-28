# 参考资料

本目录存放与"定时自动解决教师版用户反馈"技能相关的参考文件和文档。

## 目录结构
```
references/
├── email-templates/         # 邮件回复模板
├── workflow-diagrams/       # 工作流程图
├── system-screenshots/     # 系统操作截图
└── scripts/                # 辅助脚本
```

## 文件说明

### 1. 邮件回复模板
- **permission-request-template.txt**：教师权限申请邮件回复模板
- **usage-question-template.txt**：教师使用问题邮件回复模板
- **computing-power-template.txt**：算力申请邮件回复模板

### 2. 工作流程图
- **overall-workflow.png**：整体工作流程图
- **email-workflow.png**：邮件处理流程图
- **permission-workflow.png**：权限开通流程图

### 3. 系统操作截图
- **login-screenshot.png**：后台系统登录页面截图
- **teacher-management.png**：教师管理页面截图
- **form-filling.png**：表单填写页面截图
- **success-message.png**：成功开通权限提示截图

### 4. 辅助脚本
- **read-csv.py**：读取CSV文件的Python脚本
- **check-teachers.py**：检查教师权限状态的脚本
- **update-records.py**：更新记录文件的脚本

## 使用说明

### 邮件模板使用
```
# 权限申请邮件模板
老师您好！感谢您对百度飞桨星河社区（AI Studio）的关注与支持，开通教师版权限，请您完善AI Studio平台个人中心信息后（https://aistudio.baidu.com/account ），填写如下问卷，https://iwenjuan.baidu.com/?code=dk9b18。我们会在2个工作日内尽快为您开通教师权限。如有问题可以随时联系邮箱aistudio@baidu.com，谢谢！
```

### 工作流程图说明
- 整体工作流程：邮件接收 → 分类处理 → 权限开通 → 结果汇总
- 邮件处理流程：查收邮件 → 分类识别 → 检索答案 → 回复邮件
- 权限开通流程：下载问卷 → 识别新教师 → 登录后台 → 开通权限 → 更新记录

### 系统操作要点
1. **后台系统登录**：使用v_wangqidong账号登录教育版后台
2. **表单填写**：必须使用browser工具的act操作，逐个字段填写
3. **成功确认**：确认显示"保存成员管理成功"提示

### 辅助脚本使用
```bash
# 读取CSV文件
python3 references/scripts/read-csv.py /path/to/csv/file

# 检查教师权限状态
python3 references/scripts/check-teachers.py "王蓉" "浙江传媒学院"

# 更新记录文件
python3 references/scripts/update-records.py add "王蓉" "浙江传媒学院" "19602487"
```

## 更新记录
- 2026-04-09：创建参考资料目录结构
- 2026-04-09：添加文件说明和使用说明