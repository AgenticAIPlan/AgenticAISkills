# Excel导出格式说明

## 工作表结构

生成的Excel文件包含2个工作表：

### 工作表1：专家档案

| 列名 | 数据类型 | 说明 | 示例 |
|------|---------|------|------|
| 专家姓名 | 文本 | 专家完整姓名 | 邬贺铨 |
| 最新单位 | 文本 | 当前工作机构 | 中国工程院 |
| 最新职务 | 文本 | 当前职务 | 院士 |
| 简介 | 长文本 | 专家背景介绍 | 中国工程院院士，网络与通信技术专家... |
| 发言统计 | 数字 | 采集到的言论总数 | 3 |
| 优先级 | 文本 | 高/中/低 | 高 |
| AI数据相关度 | 数字 | 0-100评分 | 85 |

### 工作表2：专家言论

| 列名 | 数据类型 | 说明 | 示例 |
|------|---------|------|------|
| 链接 | 超链接 | 百度搜索URL | https://www.baidu.com/s?wd=... |
| 时间 | 日期 | 发布日期 | 2026-04-01 |
| 专家姓名 | 文本 | 发言专家 | 邬贺铨 |
| 正文 | 长文本 | 言论完整内容 | 在数字经济时代... |
| 发言主题 | 文本 | 核心话题 | 人工智能 |
| 发言要点 | 长文本 | 关键观点提炼 | 1. 加强算力建设 2. 推动数据共享... |
| 活动背景 | 文本 | 发言场合 | 2026年全国两会 |

## 编码规范

### UTF-8 with BOM

**使用原因：**
- Windows Excel默认使用GBK编码
- UTF-8 BOM头让Excel自动识别UTF-8编码
- 完美支持中文字符显示

**技术实现：**
```python
import openpyxl

# 创建工作簿时自动使用UTF-8编码
workbook = openpyxl.Workbook()
workbook.save('专家分析报告.xlsx')
```

### 列宽自动调整

```python
from openpyxl.utils import get_column_letter

for col_idx in range(1, sheet.max_column + 1):
    column_letter = get_column_letter(col_idx)
    max_length = 0
    for cell in sheet[column_letter]:
        if cell.value:
            max_length = max(max_length, len(str(cell.value)))
    sheet.column_dimensions[column_letter].width = min(max_length + 2, 50)
```

## 样式设置

### 表头样式
- 背景色: 浅蓝色 (#4472C4)
- 字体: 粗体, 白色
- 对齐: 居中
- 边框: 全边框

### 数据行样式
- 奇数行: 白色背景
- 偶数行: 浅灰色背景 (#F2F2F2)
- 字体: 常规, 黑色
- 对齐: 左对齐（文本），居中（数字）
- 边框: 细边框

## 导出文件命名

格式: `专家分析报告_YYYYMMDD_HHMMSS.xlsx`

示例: `专家分析报告_20260415_093012.xlsx`

## 与飞书表格的兼容性

导出的Excel格式完全兼容飞书多维表格导入功能：
1. 打开飞书多维表格
2. 点击"导入" → 选择Excel文件
3. 飞书自动识别工作表和字段类型
4. 确认导入即可

**注意事项：**
- 超链接字段在飞书中显示为可点击链接
- 日期字段自动转换为飞书日期格式
- 长文本字段支持多行显示
