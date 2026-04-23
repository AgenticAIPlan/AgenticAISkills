# 输入数据字段规范

## 用途

用这份规范统一 AI 硬件生态监测中的样本字段、格式示例和填写要求，保证不同来源的数据可以进入同一套分析流程。

## 推荐字段

| 字段 | 必填 | 说明 |
|------|------|------|
| platform | 是 | 平台名称，如 news / reddit / github / weibo |
| title | 是 | 标题；没有标题时可截取正文前 40-80 字 |
| content | 是 | 正文、摘要、评论或公告内容 |
| author | 否 | 作者、媒体名、机构名或账号名 |
| url | 否 | 原始链接 |
| published_at | 是 | 发布时间，推荐 ISO 8601 或 `YYYY-MM-DD HH:MM:SS` |
| likes | 否 | 点赞数 |
| comments | 否 | 评论数 |
| shares | 否 | 转发 / 分享数 |
| views | 否 | 阅读 / 播放 / 浏览数 |
| followers | 否 | 作者粉丝数 / 订阅数 |
| source_type | 否 | media / official / forum / social / policy / finance |
| entity_layer | 否 | upstream / midstream / downstream / model_vendor / external |
| company_type | 否 | chip_vendor / cloud_vendor / model_vendor / odm / media 等 |
| component_type | 否 | gpu / hbm / server / optics / cooling / sdk 等 |
| brand | 否 | 命中的品牌或厂商 |
| product | 否 | 命中的产品线或型号 |
| model_vendor | 否 | 命中的模型厂商名称 |
| region | 否 | 涉及区域 |
| tags | 否 | 预标注标签，数组或逗号分隔字符串 |
| raw_engagement | 否 | 若原平台指标难拆分，可用总互动量补充 |

## CSV 示例

```csv
platform,title,content,author,url,published_at,source_type,entity_layer,company_type,component_type,brand,product,model_vendor
news,HBM 供给持续紧张,多家媒体提到 AI 训练需求继续拉动 HBM 价格,行业媒体A,https://example.com/a,2026-04-20 09:30:00,media,upstream,memory_vendor,hbm,SK hynix,,
official,OpenAI expands compute partnership,OpenAI announces deeper infrastructure cooperation with cloud partners,OpenAI,https://example.com/b,2026-04-20 11:00:00,official,model_vendor,model_vendor,compute_service,,,
```

## JSON 示例

```json
[
  {
    "platform": "reddit",
    "title": "New rack-scale deployment points to stronger liquid-cooling demand",
    "content": "Commenters expect rack density to keep rising in new AI clusters.",
    "author": "infra_forum",
    "url": "https://example.com/c",
    "published_at": "2026-04-20T12:30:00",
    "entity_layer": "midstream",
    "component_type": "liquid_cooling"
  }
]
```

## 填写要求

样本入库前至少确认：

- 统一时间时区；跨地区项目建议保留原时区并附带标准化时间
- 对官方公告、媒体报道、论坛讨论和传闻类内容标明来源类型
- 对价格、交付、产能和资本开支信息尽量补充核验状态
- 对模型厂商相关样本补充关联硬件、云厂商或部署对象
