# 参考资料

本目录包含智库专家数据采集与分析Skill的详细参考文档。

## 文档列表

- **快速开始** - 快速上手指南和基本用法
- **系统架构** - 技术实现细节和模块说明
- **数据源配置** - 15个权威信息源的详细说明
- **API集成** - 飞书多维表格集成指南

## 使用说明

这些文档提供了补充信息，主要的使用说明请参考上级目录的 `SKILL.md`。

## 核心文件

当前目录的核心功能文件应在实际使用时根据需要补充：

- `enhanced_main.py` - 主处理引擎
- `enhanced_crawler.py` - 数据采集器  
- `ai_analyzer.py` - AI分析模块
- `baidu_integration.py` - 百度搜索配置
- `excel_exporter.py` - Excel导出
- `daily_update.py` - 定时更新脚本
- `config.ini` - 配置文件

## 技术栈

- Python 3.8+
- 必需依赖: requests, beautifulsoup4, lxml, openpyxl
- 可选集成: 飞书Open API, baidu-search skill

## 版本信息

- 当前版本: v1.0.0
- 最后更新: 2026-04-15
