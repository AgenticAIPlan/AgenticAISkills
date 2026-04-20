# 数据源配置完整列表

## RSS 数据源

```javascript
const RSS_SOURCES = [
    {
        vendorName: 'Hugging Face Blog',
        url: 'https://huggingface.co/blog/feed.xml'
    },
    {
        vendorName: 'NVIDIA Developer News',
        url: 'https://developer.nvidia.com/blog/feed/'
    }
];
```

## HTML 数据源

```javascript
const HTML_SOURCES = [
    {
        vendorName: "华为昇腾",
        listUrls: [
            "https://www.hiascend.com/zh/news",
            "https://www.hiascend.com/zh/"
        ],
        linkPatterns: [/hiascend\.com\/zh\/news\/detail\/\d+/i]
    },
    {
        vendorName: "寒武纪",
        listUrls: ["https://www.cambricon.com/index.php?a=lists&catid=7&m=content"],
        linkPatterns: [/index\.php\?a=show&catid=\d+&id=\d+&m=content/i]
    },
    {
        vendorName: "壁仞科技",
        listUrls: ["https://www.birentech.com/news"],
        linkPatterns: [/birentech\.com\/news\/(?!$)/i]
    },
    {
        vendorName: "昆仑芯科技",
        listUrls: ["https://www.kunlunxin.com/news"],
        linkPatterns: [/kunlunxin\.com\/news\/(?!$)/i],
        containerSelector: '.left .main'
    },
    {
        vendorName: "沐曦",
        listUrls: ["https://www.metax-tech.com/news"],
        linkPatterns: [/metax-tech\.com\/ndetail\/\d+\.html/i]
    },
    {
        vendorName: "海光信息",
        listUrls: [
            "https://www.hygon.cn/news",
            "https://www.hygon.cn/"
        ],
        linkPatterns: [/hygon\.cn\/(news|information|dynamic|article|detail|infodetails|press)[^"' ]*/i]
    },
    {
        vendorName: "燧原科技",
        listUrls: [
            "https://www.enflame-tech.com/news",
            "https://www.enflame-tech.com/"
        ],
        linkPatterns: [/enflame-tech\.com\/(news|newsdetail|detail|article|press)[^"' ]*/i]
    },
    {
        vendorName: "Intel Newsroom",
        listUrls: ["https://newsroom.intel.com/"],
        linkPatterns: [/newsroom\.intel\.com\/(news|press-kit)\/[^"' ]+/i]
    },
    {
        vendorName: "安谋科技",
        listUrls: [
            "https://www.armchina.com/index/",
            "https://www.armchina.com/"
        ],
        linkPatterns: [/armchina\.com\/infodetails\?id=\d+/i]
    }
];
```

## 新增数据源指南

### 步骤 1：分析目标网站结构

1. 找到新闻列表页 URL
2. 找到详情页 URL 的 URL pattern
3. 确定标题和日期的 CSS 选择器

### 步骤 2：编写配置

```javascript
{
    vendorName: "新厂商名称",
    listUrls: ["https://www.example.com/news"],
    linkPatterns: [/example\.com\/news\/\d+\.html/i],
    containerSelector: ".news-container" // 可选
}
```

### 步骤 3：验证正则

在浏览器 Console 测试：

```javascript
const url = "https://www.example.com/news/12345.html";
/example\.com\/news\/\d+\.html/i.test(url); // 应返回 true
```

### 步骤 4：添加到 HTML_SOURCES

1. 打开 `scripts/fetch-news.js`
2. 在 `HTML_SOURCES` 数组末尾添加新配置
3. 运行 `npm run fetch-news` 测试

## 请求头配置

```javascript
const REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
};
```

## 超时配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| HTTP 请求超时 | 5000ms | 详情页正文穿透 |
| 列表页请求超时 | 10000ms | HTML 列表页抓取 |
| AI 请求超时 | 30s | Gemini/智谱调用 |
