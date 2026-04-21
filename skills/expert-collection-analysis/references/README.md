# 参考资料

本目录包含智库专家数据采集与分析Skill的详细参考文档和实现说明。

## 📚 文档列表

### 核心文档
- **[ai-scoring-algorithm.md](ai-scoring-algorithm.md)** - AI智能评分算法详解
- **[data-sources.md](data-sources.md)** - 15个权威信息源配置说明
- **[excel-export-format.md](excel-export-format.md)** - Excel输出格式规范

## 🛠️ 实现方式

本Skill采用**模块化设计**，核心功能通过以下方式实现：

### 方式1：使用现有Python脚本（推荐）
适合有Python环境的用户，提供完整的自动化流程：

```bash
# 执行数据采集
cd scripts/
python daily_update.py
```

**核心脚本说明**：
- `daily_update.py` - 主执行脚本（已包含）
- `analyze_experts.py` - 专家分析工具（已包含）
- `run_collection.sh` - 一键执行脚本（已包含）

**依赖模块**（需要用户自行实现或使用现有库）：
- `enhanced_main.py` - 主处理引擎
- `enhanced_crawler.py` - 数据采集器
- `ai_analyzer.py` - AI分析模块
- `baidu_integration.py` - 百度搜索配置
- `excel_exporter.py` - Excel导出
- `feishu_client.py` - 飞书API客户端
- `config.ini` - 配置文件

### 方式2：使用Agent动态实现
适合通过Claude Agent动态执行：

1. **数据采集**: 使用 `baidu-search` skill 搜索权威信息
2. **智能分析**: 通过Claude API进行AI评分
3. **结果导出**: 使用Python库生成Excel文件

**参考实现**：
```python
# 1. 使用baidu-search搜索
from baidu_search import search
results = search("国务院 人工智能 2026")

# 2. AI分析评分
analysis = claude_analyze(results)

# 3. Excel导出
import openpyxl
wb = openpyxl.Workbook()
# ... 导出逻辑
```

## 📊 数据流程

```
采集阶段:
  15个搜索源 → 百度搜索 → 结果爬取 → 数据清洗

分析阶段:
  数据清洗 → 时间过滤 → 去重处理 → AI分析 → 优先级计算

导出阶段:
  优先级结果 → 信息补充 → 专家聚合 → Excel生成 → 报告输出
```

## 🎯 技术栈

- **Python 3.8+**
- **必需依赖**: requests, beautifulsoup4, lxml, openpyxl
- **可选集成**: 飞书Open API, baidu-search skill

## 📝 使用说明

### 快速开始

1. **查看主文档**: 返回上级目录阅读 `SKILL.md`
2. **选择实现方式**: Python脚本 或 Agent动态实现
3. **执行采集**: 运行 `scripts/daily_update.py` 或参考文档手动实现

### 配置说明

详细的配置项和使用方法，请参考：
- [data-sources.md](data-sources.md) - 数据源配置
- [ai-scoring-algorithm.md](ai-scoring-algorithm.md) - 评分算法
- [excel-export-format.md](excel-export-format.md) - 输出格式

## 🔗 相关资源

- **百度搜索集成**: 使用 `baidu-search` skill
- **Claude API**: 用于AI智能分析
- **飞书开放平台**: https://open.feishu.cn

## 📌 注意事项

1. **依赖模块**: 列表中的Python模块需要用户根据实际需求自行实现
2. **数据源**: 15个权威信息源配置见 [data-sources.md](data-sources.md)
3. **权限配置**: 飞书API需要配置相应权限

---

**版本**: v1.0.0  
**最后更新**: 2026-04-16
