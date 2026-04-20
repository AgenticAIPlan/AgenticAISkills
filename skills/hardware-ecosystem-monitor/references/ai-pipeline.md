# AI 清洗流程详解

## 处理流水线

```
原始新闻 → 关键词初筛 → 正文穿透 → AI 清洗 → 结果输出
                              ↓
                    Gemini 2.5 Flash
                          ↓ (失败)
                    智谱 GLM-4-Flash
                          ↓ (失败)
                    兜底占位文本
```

## 系统 Prompt

```
你是我司的大模型与多硬件生态监控专家。请阅读以下新闻标题和原始摘要。判断该新闻是否实质性涉及'大模型(LLM)、深度学习框架在特定硬件(GPU/NPU)上的适配、训练优化、推理部署或硬核生态合作'。如果是普通的商业公关稿、线下活动（如训练营、大赛、全国行）或无关更新，严格仅输出单词：REJECT。如果相关，请用不超过30个字的精炼中文总结其核心业务价值。注意：如果输入没有摘要，强行用原标题推测业务价值即可，绝对不准回复'未提供摘要'等聊天内容，直接交出总结或抛出REJECT，输出不得包含任何多余文字。
```

## 判断标准

### ✅ 生态相关（输出摘要）

- 大模型在国产芯片上的适配进展
- 推理性能优化、吞吐量提升
- 训练框架与硬件的深度集成
- 生态合作签约、联合发布
- 技术突破、算力创新

### ❌ 非生态相关（输出 REJECT）

- 线下活动：训练营、大赛、城市峰会
- 商业合作：普通签约、无技术细节
- 人事变动：高管任命、组织调整
- 无关新闻：财报、收购、政策

## 正文穿透机制

在调用 AI 之前，系统会尝试获取新闻详情页的正文内容：

```javascript
async function fetchArticleContent(targetUrl, defaultSummary) {
    try {
        const response = await axios.get(targetUrl, { timeout: 5000 });
        const $ = cheerio.load(response.data);
        let content = '';
        $('p').each((i, el) => {
            content += $(el).text() + ' ';
        });
        // 截取前 1500 字
        return content.substring(0, 1500);
    } catch (err) {
        return defaultSummary; // 失败时回退
    }
}
```

## 双引擎容灾

### Plan A: Gemini 2.5 Flash

```javascript
const response = await geminiClient.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: prompt,
    config: { systemInstruction: SYSTEM_PROMPT }
});
```

### Plan B: 智谱 GLM-4-Flash

```javascript
const response = await zhipuClient.chat.completions.create({
    model: "glm-4-flash",
    messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: prompt }
    ]
});
```

### Plan C: 兜底

```javascript
newsItem.summary = "暂无智能摘要（双引擎均超时）";
return newsItem;
```

## 输出示例

### 相关新闻

**输入**：
```
标题：壁仞科技完成MiniMax M2.5、智谱GLM-5等多款SOTA模型高效适配
正文：壁仞科技近日宣布...
```

**输出**：
```
壁仞科技硬核适配国产大模型，实现高效推理部署。
```

### 无关新闻

**输入**：
```
标题：某头部银行基于昆仑芯2的风控大模型全栈国产化替代
正文：近日，某头部银行...
```

**输出**：
```
REJECT
```

（金融行业应用案例，不属于硬件厂商新闻）

## 性能优化

1. **串行处理**：避免 API 并发限制
2. **滑动窗口**：仅保留最新 100 条
3. **关键词预筛**：减少 AI 调用次数
4. **正文截断**：限制输入长度（1500 字）
