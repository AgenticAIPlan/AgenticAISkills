import requests
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

# 确保同目录下的模块可被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from distribute import distribute_report

load_dotenv()

# --- 核心配置 ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "twitter-api45.p.rapidapi.com"
BOCHA_API_KEY = os.getenv("BOCHA_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

# Twitter List 可通过环境变量自定义，未配置则跳过
X_LIST_URL = os.getenv("X_LIST_URL", "")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_prompt(filename):
    """从 references 目录加载提示词文件"""
    # 优先从 skill 目录结构 (scripts/../references/) 加载
    ref_path = os.path.join(SCRIPT_DIR, "..", "references", filename)
    if os.path.exists(ref_path):
        with open(ref_path, "r", encoding="utf-8") as f:
            return f.read()
    # 兼容扁平项目结构 (prompts/)
    flat_path = os.path.join(SCRIPT_DIR, "..", "prompts", filename)
    if os.path.exists(flat_path):
        with open(flat_path, "r", encoding="utf-8") as f:
            return f.read()
    raise FileNotFoundError(f"找不到提示词文件: {filename}，已搜索 references/ 和 prompts/")

# --- 代理配置 ---
# 从环境变量读取代理配置，解析 PAC，然后清除环境变量
# 避免 requests/httpx 自动走代理导致不需要代理的请求也失败

def _init_proxy():
    """解析代理配置并清除环境变量，返回供被墙站点使用的代理 dict"""
    raw = (os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
           or os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY'))
    # 清除环境变量，防止 requests/httpx 自动走代理
    for k in ('http_proxy', 'HTTP_PROXY', 'https_proxy', 'HTTPS_PROXY'):
        os.environ.pop(k, None)
    if not raw:
        return {}
    # 如果是 PAC URL，解析出真实代理地址
    if '.pac' in raw:
        try:
            resp = requests.get(raw, timeout=5)
            match = re.search(r"PROXY\s+([^;\s]+)", resp.text)
            if match:
                addr = f"http://{match.group(1)}"
                return {'http': addr, 'https': addr}
        except Exception:
            pass
        return {}
    # 普通代理地址
    proxies = {}
    if raw.startswith('http'):
        proxies['http'] = raw
        proxies['https'] = raw
    return proxies

# 仅用于需要翻墙的站点（ArXiv, HuggingFace 等）
PROXY_FOR_BLOCKED = _init_proxy()

def parse_twitter_date(date_str):
    """强大的日期解析器，兼容推特格式与ISO格式"""
    if not date_str: return None
    try:
        return parsedate_to_datetime(date_str) # 尝试解析推特原生格式
    except: pass
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00')) # 尝试解析 ISO 格式
    except: return None

def fetch_twitter_list_data():
    print("🚀 [雷达1] 正在抓取推特精选 List...")
    if not X_LIST_URL:
        print("⚠️ [雷达1] X_LIST_URL 未配置，跳过此雷达。请在 .env 中设置 X_LIST_URL。")
        return []

    list_id = X_LIST_URL.split("/")[-1]
    url = f"https://{RAPIDAPI_HOST}/listtimeline.php"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}
    params = {"list_id": list_id}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        data = res.json().get("timeline", []) if res.status_code == 200 else []
        print(f"✅ [雷达1] 完成，获得原始推文 {len(data)} 条。")
        return data
    except Exception as e:
        print(f"❌ [雷达1] 异常: {e}")
        return []

def fetch_twitter_global_data():
    print("🚀 [雷达2] 正在执行全网 AI 爆款扫描...")
    since_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")

    url = f"https://{RAPIDAPI_HOST}/search.php"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}
    query = f"(LLM OR OpenAI OR Anthropic OR 'Agentic AI' OR DeepSeek OR Kimi OR MiniMax OR 'AI startup' OR 'AI revenue' OR 'AI pricing' OR 'API pricing' OR 'AI ARR' OR 'AI monetization' OR 'Scale AI' OR 'AI agent' OR 'synthetic data' OR 'training data' OR 'Hugging Face leaderboard' OR 'OpenRouter' OR 'LMSYS arena') min_faves:100 -filter:replies lang:en since:{since_date}"
    params = {"query": query, "search_type": "Latest"}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        data = res.json().get("timeline", []) if res.status_code == 200 else []
        print(f"✅ [雷达2] 完成，获得全网爆款 {len(data)} 条。")
        return data
    except Exception as e:
        print(f"❌ [雷达2] 异常: {e}")
        return []

def fetch_hacker_news_data():
    print("🚀 [雷达3] 正在检索 Hacker News 硅谷风向...")
    time_window_ts = int(time.time()) - (48 * 60 * 60)
    query = "AI"
    try:
        res = requests.get("https://hn.algolia.com/api/v1/search", params={
            "query": query,
            "tags": "story",
            "numericFilters": f"created_at_i>{time_window_ts},points>10"
        }, timeout=20)
        data = res.json().get('hits', []) if res.status_code == 200 else []
        print(f"✅ [雷达3] 完成，获得 HN 热帖 {len(data)} 条。")
        return data
    except Exception as e:
        print(f"❌ [雷达3] 异常: {e} (请检查网络代理)")
        return []

def fetch_reddit_data():
    print("🚀 [雷达4] 正在潜入 Reddit 硬核社区...")
    subs = ["LocalLLaMA", "MachineLearning", "artificial", "singularity", "MLOps", "datascience"]
    results = []
    reddit_host = "reddit34.p.rapidapi.com"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": reddit_host}

    for sub in subs:
        url = f"https://{reddit_host}/getPostsBySubreddit"
        params = {"subreddit": sub, "sort": "hot"}
        try:
            res = requests.get(url, headers=headers, params=params, timeout=30)
            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    posts = data.get("data", {}).get("posts", [])
                    for p in posts[:8]:
                        d = p.get("data", {})
                        results.append({"source": f"Reddit r/{sub}", "author": d.get("author"), "content": d.get("title")})
        except Exception: continue

    print(f"✅ [雷达4] 完成，获得 Reddit 讨论 {len(results)} 条。")
    return results

def fetch_producthunt_data():
    print("🚀 [雷达5] 正在扫描 Product Hunt AI 新产品...")
    ph_host = "product-hunt-scraper-api.p.rapidapi.com"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": ph_host}
    results = []
    try:
        res = requests.get(f"https://{ph_host}/producthunt/daily-top", headers=headers, timeout=30)
        if res.status_code == 200:
            products = res.json().get("data", {}).get("products", [])
            for p in products:
                topics = [t.get("name", "") for t in p.get("topics", [])]
                # 筛选 AI 相关产品
                is_ai = any(kw in " ".join(topics).lower() for kw in ["artificial intelligence", "ai", "machine learning", "developer tools"])
                if is_ai:
                    results.append({
                        "source": "Product Hunt",
                        "author": "",
                        "content": f"[#{p.get('daily_rank', '')}] {p.get('name', '')}: {p.get('tagline', '')} (topics: {', '.join(topics)})"
                    })
        print(f"✅ [雷达5] 完成，获得 PH AI 新产品 {len(results)} 条。")
    except Exception as e:
        print(f"❌ [雷达5] 异常: {e}")
    return results

def fetch_bocha_data():
    print("🚀 [雷达6] 正在检索博查中文 AI 资讯...")
    if not BOCHA_API_KEY:
        print("⚠️ [雷达6] BOCHA_API_KEY 未配置，跳过。")
        return []

    url = "https://api.bochaai.com/v1/web-search"
    headers = {"Authorization": f"Bearer {BOCHA_API_KEY}", "Content-Type": "application/json"}
    queries = [
        "大模型 数据工程 训练数据 合成数据 Scale AI",
        "AI大模型 出海 海外市场 DeepSeek Kimi MiniMax",
        "大模型 商业化 营收 API定价 创业融资",
        "AI model revenue pricing API enterprise customers 2026",
        "synthetic data training data curation RLHF Scale AI Labelbox",
        "Hugging Face leaderboard OpenRouter model ranking",
    ]
    results = []
    for q in queries:
        try:
            res = requests.post(url, headers=headers, json={
                "query": q,
                "freshness": "oneWeek",
                "summary": True,
                "count": 5
            }, timeout=20)
            if res.status_code == 200:
                data = res.json()
                web_pages = data.get("data", {}).get("webPages", {}).get("value", [])
                for page in web_pages:
                    results.append({
                        "source": f"博查/{page.get('siteName', '网络')}",
                        "author": page.get("siteName", ""),
                        "content": f"{page.get('name', '')}: {page.get('summary') or page.get('snippet', '')}"
                    })
        except Exception as e:
            print(f"  ⚠️ 博查查询 '{q[:15]}...' 异常: {e}")
            continue

    print(f"✅ [雷达6] 完成，获得中文资讯 {len(results)} 条。")
    return results

def fetch_arxiv_data():
    print("🚀 [雷达7] 正在检索 ArXiv 数据工程前沿论文...")
    # ArXiv API 免费，无需 API key
    # 搜索 cs.CL/cs.AI/cs.LG 中与数据工程、合成数据、训练数据相关的论文
    query = 'all:"training data" OR all:"synthetic data" OR all:"data curation" OR all:"RLHF" OR all:"preference data" OR all:"data quality" OR all:"data pipeline"'
    results = []
    try:
        res = requests.get("http://export.arxiv.org/api/query", params={
            "search_query": f"({query}) AND (cat:cs.CL OR cat:cs.AI OR cat:cs.LG)",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 15
        }, timeout=20, proxies=PROXY_FOR_BLOCKED)
        if res.status_code == 200:
            root = ET.fromstring(res.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")[:300]
                authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
                results.append({
                    "src": "ArXiv",
                    "auth": ", ".join(authors[:3]),
                    "content": f"{title}: {summary}"
                })
        print(f"✅ [雷达7] 完成，获得 ArXiv 论文 {len(results)} 篇。")
    except Exception as e:
        print(f"❌ [雷达7] 异常: {e} (请检查网络代理)")
    return results

def fetch_hf_papers_data():
    print("🚀 [雷达8] 正在抓取 HuggingFace Daily Papers...")
    # HF Daily Papers API 免费，无需 API key
    results = []
    try:
        res = requests.get("https://huggingface.co/api/daily_papers", timeout=20, proxies=PROXY_FOR_BLOCKED)
        if res.status_code == 200:
            papers = res.json()
            for p in papers[:15]:
                paper = p.get("paper", {})
                title = paper.get("title", "")
                summary = paper.get("summary", "")[:300]
                authors = [a.get("name", "") for a in paper.get("authors", [])[:3]]
                upvotes = p.get("paper", {}).get("upvotes", 0)
                results.append({
                    "src": "HuggingFace Papers",
                    "auth": ", ".join(authors),
                    "content": f"[{upvotes} upvotes] {title}: {summary}"
                })
        print(f"✅ [雷达8] 完成，获得 HF 热门论文 {len(results)} 篇。")
    except Exception as e:
        print(f"❌ [雷达8] 异常: {e} (请检查网络代理)")
    return results

def process_and_generate_report(t_list, t_global, hn_data, reddit_data, ph_data, arxiv_data, hf_data, skip_distribute=False):
    print("-" * 30)
    print("⏳ 正在跨源清洗数据并进行深度思考...")

    combined_info = []
    now = datetime.now(timezone.utc)
    time_window = now - timedelta(hours=48)

    dropped_old = 0
    dropped_empty = 0

    # 清洗推特数据（适配 twitter-api45 返回格式）
    for t in (t_list + t_global):
        text = t.get("text") or ""

        if not text:
            dropped_empty += 1
            continue

        author = t.get("screen_name") or t.get("author", {}).get("screen_name") or "Unknown"
        date_str = t.get("created_at") or t.get("createdAt")

        # 精准时间比对
        parsed_date = parse_twitter_date(date_str)
        if parsed_date and parsed_date < time_window:
            dropped_old += 1
            continue

        combined_info.append({"src": "Twitter", "auth": author, "content": text[:500]})

    # 清洗 HN 数据
    for h in hn_data:
        combined_info.append({"src": "Hacker News", "auth": h.get("author"), "content": h.get("title")})

    # 清洗 Reddit 数据
    combined_info.extend(reddit_data)

    # 清洗 Product Hunt 数据
    for p in ph_data:
        combined_info.append({"src": p.get("source", "Product Hunt"), "auth": p.get("author", ""), "content": p.get("content", "")})

    # ArXiv 和 HF Papers 数据已预清洗，直接合入
    combined_info.extend(arxiv_data)
    combined_info.extend(hf_data)

    # 打印验尸官日志
    print(f"🔍 清洗报告：丢弃了 {dropped_old} 条过期老推文，丢弃了 {dropped_empty} 条无法读取正文的数据。")
    print(f"🧠 最终汇聚有效情报 {len(combined_info)} 条。")

    if not combined_info:
        print("⚠️ 警告：全网静默，无任何有效数据可供总结。流程终止。")
        return

    # --- 大脑指令 ---
    system_prompt = load_prompt("system_prompt.md")

    print(f"🤖 正在调用 {LLM_MODEL} 进行情报加工...")
    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"今日多源情报流：\n{json.dumps(combined_info, ensure_ascii=False)}"}
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.2,
                extra_body={"stream": False}
            )

            report_content = response.choices[0].message.content
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{date_str}-Overseas-LLM-Insight.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# 海外大模型每日情报观察 ({date_str})\n\n{report_content}")
            print("-" * 30)
            print(f"✅ 成功！情报已萃取完毕，文件保存在：{filename}")

            # 自动分发到飞书和如流
            if not skip_distribute:
                report_title = f"海外大模型每日情报观察 ({date_str})"
                distribute_report(report_title, report_content)
            else:
                print("⏭️  跳过分发（--no-distribute）")
            return

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg and attempt < max_retries - 1:
                wait = (attempt + 1) * 30
                print(f"⏳ API 限流(429)，第 {attempt+1} 次重试，等待 {wait} 秒...")
                time.sleep(wait)
            else:
                print(f"\n❌ 大模型调用失败: {error_msg}")
                return

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-distribute", action="store_true", help="仅生成报告，不分发到飞书/如流")
    args = parser.parse_args()

    print("=" * 40)
    t_list = fetch_twitter_list_data()
    t_global = fetch_twitter_global_data()
    hn = fetch_hacker_news_data()
    reddit = fetch_reddit_data()
    ph = fetch_producthunt_data()
    arxiv = fetch_arxiv_data()
    hf = fetch_hf_papers_data()

    process_and_generate_report(t_list, t_global, hn, reddit, ph, arxiv, hf,
                                skip_distribute=args.no_distribute)
