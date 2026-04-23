# 数据源配置指南

本文件记录爬虫支持的数据源及其配置方法。

## 已支持的数据源

### 1. 机器之心 (jiqizhixin)

- **类型**: AI技术媒体
- **内容特点**: 国内AI领域最新动态，数据集发布新闻较多
- **URL**: https://www.jiqizhixin.com
- **搜索接口**: `https://www.jiqizhixin.com/search?query={关键词}`
- **状态**: ✅ 已启用

### 2. InfoQ (infoq)

- **类型**: 技术资讯平台
- **内容特点**: 技术深度文章，企业技术博客
- **URL**: https://www.infoq.cn
- **状态**: ⚠️ 需要登录/API Key

### 3. 开源中国 (oschina)

- **类型**: 开源项目社区
- **内容特点**: 开源项目发布，GitHub项目推荐
- **URL**: https://www.oschina.net
- **状态**: ✅ 已启用

## 待扩展的数据源

以下数据源可以考虑后续添加：

### 技术博客/企业官方

- **Google AI Blog** - https://ai.googleblog.com
- **OpenAI Blog** - https://openai.com/blog
- **HuggingFace Blog** - https://huggingface.co/blog
- **Papers with Code** - https://paperswithcode.com

### 开源平台

- **GitHub Trending** - 热门数据集仓库
- **Kaggle Datasets** - https://www.kaggle.com/datasets
- **阿里云天池** - https://tianchi.aliyun.com/dataset
- **百度AI Studio** - https://aistudio.baidu.com/dataset

### 学术/研究机构

- **ACL Anthology** - 计算语言学论文及数据集
- **arXiv** - 预印本论文中的数据集
- **Data.gov** - 政府开放数据

## 添加新数据源的步骤

1. 在 `scripts/dataset_crawler.py` 的 `DATA_SOURCES` 字典中添加配置：

```python
'datasource_key': {
    'name': '显示名称',
    'base_url': 'https://example.com',
    'search_url': 'https://example.com/search?q={query}',
    'enabled': True,
}
```

2. 实现对应的爬取方法：

```python
def crawl_datasource_key(self, days: int = 7) -> List[Dict]:
    """爬取新数据源"""
    results = []
    # 实现爬取逻辑
    return results
```

3. 在 `crawl_all()` 方法中添加调用

4. 测试并更新本文档

## 爬虫策略说明

### 请求频率控制

- 默认延迟: 2-5秒随机间隔
- 可通过 `--delay` 参数调整
- 建议遵守目标网站的 robots.txt 规则

### 反爬虫应对

- 使用 User-Agent 轮换
- 支持代理配置（环境变量 `HTTP_PROXY` / `HTTPS_PROXY`）
- 请求失败自动重试（可扩展）

### 数据解析策略

- 使用 BeautifulSoup 解析 HTML
- 优先查找结构化数据（JSON-LD, meta标签）
- 备用方案：正则表达式提取
