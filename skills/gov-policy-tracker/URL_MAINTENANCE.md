# 数据源URL维护指南

## 当前URL验证结果

### 成功的URL (8个)
1. ✅ 工信部 - https://www.miit.gov.cn/zwgk/zcwj/wjfb/tz/
2. ✅ 科技部 - https://www.most.gov.cn/kjbgz/
3. ✅ 发改委 - https://www.ndrc.gov.cn/xxgk/zcfb/tz/
4. ✅ 财政部 - https://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/
5. ✅ 北京市 - https://www.beijing.gov.cn/zhengce/zhengcefagui/
6. ✅ 上海市 - https://www.shanghai.gov.cn/nw12344/
7. ✅ 广东省 - https://www.gd.gov.cn/zwgk/wjk/qbwj/
8. ✅ 江苏省 - http://www.jiangsu.gov.cn/col/col46147/index.html

### 需要修复的URL (8个)
1. ❌ 网信办 - 需要找到正确的政策列表页
2. ❌ 深圳 - 已更新为 https://www.sz.gov.cn/cn/xxgk/zfxxgj/zcfg/
3. ❌ 浙江 - 需要找到正确的政策列表页
4. ❌ 湖北 - 返回412错误，可能需要特殊请求头
5. ❌ 四川 - 返回403错误，可能被阻止
6. ❌ 福建 - 404错误
7. ❌ 厦门 - 404错误
8. ❌ 重庆 - 404错误

## 如何找到正确的URL

### 方法1：使用浏览器的开发者工具
1. 打开目标政府网站
2. 找到政策/文件栏目
3. 按F12打开开发者工具
4. 刷新页面，查看Network标签
5. 找到请求政策列表的URL

### 方法2：使用web search skill
```
搜索: site:域名 政策 2024
例如: site:zj.gov.cn 政策 人工智能
```

### 方法3：手动检查常见路径
- /zwgk/zcwj/ (政务公开/政策文件)
- /xxgk/zcfb/ (信息公开/政策发布)
- /zhengce/zhengcefagui/ (政策/政策法规)
- /art/年份/月份/ (文章/时间路径)

## 使用建议

### 对于无法访问的URL
1. **暂时禁用**：在config.yaml中将enabled设为false
2. **定期检查**：每月运行verify_urls.py检查一次
3. **手动补充**：对于重要数据源，可以手动导入数据

### 对于链接打不开的问题
政府网站经常：
- 更换域名或路径
- 增加反爬虫机制
- 需要特定的User-Agent
- 需要Referer头

## 推荐的Skill

### 1. web-search
用于搜索正确的URL：
```bash
搜索: site:政府域名 政策文件
```

### 2. web-fetch
用于验证URL可访问性：
```python
import requests
response = requests.get(url, headers={'User-Agent': '...'})
```

### 3. lark-cli
用于管理飞书表格字段：
```bash
lark-cli base +field-list --base-token xxx --table-id xxx
```

## 定期维护建议

### 每周
- 运行main.py检查数据源状态
- 查看日志中的失败记录

### 每月
- 运行verify_urls.py验证所有URL
- 更新失效的URL
- 检查是否有新数据源需要添加

### 每季度
- 评估数据源质量
- 调整关键词匹配规则
- 优化解析器选择器

## 联系支持

如果遇到技术问题：
1. 查看scripts/目录下的日志文件
2. 运行verify_urls.py获取详细的错误信息
3. 检查config.yaml配置是否正确
