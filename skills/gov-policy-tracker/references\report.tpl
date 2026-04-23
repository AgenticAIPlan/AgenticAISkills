{% if ai_policies or data_policies %}
## 📋 政策追踪日报

**{{ gen_date }}**

---

{% if ai_policies %}
### 🤖 人工智能政策

{% for item in ai_policies %}
* **[{{ item.source_name }}]** {{ item.title }}
  * {{ item.summary }}
  * 发布日期：{{ item.pub_date }} | [原文链接]({{ item.url }})
{% endfor %}
{% else %}
* 暂无更新
{% endif %}

---

{% if data_policies %}
### 📊 数据要素政策

{% for item in data_policies %}
* **[{{ item.source_name }}]** {{ item.title }}
  * {{ item.summary }}
  * 发布日期：{{ item.pub_date }} | [原文链接]({{ item.url }})
{% endfor %}
{% else %}
* 暂无更新
{% endif %}

---

_以上信息由AI自动生成，引用前请核对原文。_
{% else %}
## 📋 政策追踪日报

**{{ gen_date }}**

今日暂无符合关键词的政策更新。

---
_政策追踪系统 · {{ gen_time }}_
{% endif %}