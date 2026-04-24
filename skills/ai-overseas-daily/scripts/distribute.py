import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

# --- 配置 ---
RULIU_WEBHOOK_URL = os.getenv("RULIU_WEBHOOK_URL")
RULIU_GROUP_ID = os.getenv("RULIU_GROUP_ID")  # 如流群ID（数字）
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
FEISHU_WIKI_SPACE_ID = os.getenv("FEISHU_WIKI_SPACE_ID")
FEISHU_WIKI_PARENT_NODE_TOKEN = os.getenv("FEISHU_WIKI_PARENT_NODE_TOKEN", "")
FEISHU_BASE_URL = os.getenv("FEISHU_BASE_URL", "https://open.feishu.cn")
# 飞书知识库页面的对外访问域名（如 bytedance.feishu.cn / xxx.feishu.cn）
FEISHU_WIKI_DOMAIN = os.getenv("FEISHU_WIKI_DOMAIN", "bytedance.feishu.cn")


# ========== 飞书知识库 ==========

def get_feishu_token():
    """获取飞书 tenant_access_token"""
    resp = requests.post(
        f"{FEISHU_BASE_URL}/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10
    )
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"飞书认证失败: {data}")
    return data["tenant_access_token"]


def create_wiki_node(token, title):
    """在飞书知识库中创建新页面，返回 (document_id, node_token)"""
    body = {
        "obj_type": "docx",
        "node_type": "origin",
        "title": title,
    }
    if FEISHU_WIKI_PARENT_NODE_TOKEN:
        body["parent_node_token"] = FEISHU_WIKI_PARENT_NODE_TOKEN

    resp = requests.post(
        f"{FEISHU_BASE_URL}/open-apis/wiki/v2/spaces/{FEISHU_WIKI_SPACE_ID}/nodes",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=15
    )
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"飞书创建页面失败: {data}")

    node = data["data"]["node"]
    return node["obj_token"], node["node_token"]


def add_blocks_to_doc(token, document_id, blocks):
    """向飞书文档写入 block，每批最多 50 个"""
    url = f"{FEISHU_BASE_URL}/open-apis/docx/v1/documents/{document_id}/blocks/{document_id}/children"
    headers = {"Authorization": f"Bearer {token}"}

    current_index = 0
    for i in range(0, len(blocks), 50):
        batch = blocks[i:i + 50]
        resp = requests.post(url, headers=headers, json={"children": batch, "index": current_index}, timeout=30)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"飞书写入block失败(batch {i // 50}): {data}")
        current_index += len(batch)


def parse_bold_text(text):
    """解析含 **bold** 的文本，返回 TextRun 列表"""
    elements = []
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            elements.append({
                "text_run": {
                    "content": part[2:-2],
                    "text_element_style": {"bold": True}
                }
            })
        else:
            elements.append({
                "text_run": {
                    "content": part,
                    "text_element_style": {}
                }
            })
    return elements


def markdown_to_feishu_blocks(md_content):
    """将 markdown 字符串转为飞书 block 列表"""
    blocks = []
    lines = md_content.split('\n')
    prev_blank = False  # 用于去重连续空行

    for line in lines:
        stripped = line.strip()

        # 空行 → 空段落（保持段落间距），但连续空行只保留一个
        if not stripped:
            if not prev_blank:
                blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": " ", "text_element_style": {}}}]}})
                prev_blank = True
            continue

        prev_blank = False

        # H1 标题
        if stripped.startswith('# ') and not stripped.startswith('## '):
            elements = parse_bold_text(stripped[2:].strip())
            blocks.append({"block_type": 3, "heading1": {"elements": elements}})

        # H2 标题
        elif stripped.startswith('## '):
            elements = parse_bold_text(stripped[3:].strip())
            blocks.append({"block_type": 4, "heading2": {"elements": elements}})

        # H3 标题
        elif stripped.startswith('### '):
            elements = parse_bold_text(stripped[4:].strip())
            blocks.append({"block_type": 5, "heading3": {"elements": elements}})

        # 引用（用斜体文本段落代替，飞书的 quote_container 是容器 block 不便直接创建）
        elif stripped.startswith('> '):
            content = stripped[2:].strip()
            elements = [{"text_run": {"content": content, "text_element_style": {"italic": True}}}]
            blocks.append({"block_type": 2, "text": {"elements": elements}})

        # 无序列表
        elif stripped.startswith('- '):
            elements = parse_bold_text(stripped[2:].strip())
            blocks.append({"block_type": 12, "bullet": {"elements": elements}})

        # 分隔线
        elif stripped in ('---', '***', '___'):
            blocks.append({"block_type": 22, "divider": {}})

        # 缩进续行（列表项的正文，以2个空格开头）
        elif line.startswith('  ') and stripped:
            elements = parse_bold_text(stripped)
            blocks.append({"block_type": 2, "text": {"elements": elements}})

        # 普通段落
        else:
            elements = parse_bold_text(stripped)
            blocks.append({"block_type": 2, "text": {"elements": elements}})

    return blocks


def publish_to_feishu(title, md_content):
    """发布报告到飞书知识库，返回页面 URL"""
    if not all([FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_WIKI_SPACE_ID]):
        print("  [飞书] 配置不完整，跳过发布。")
        return None

    token = get_feishu_token()
    document_id, node_token = create_wiki_node(token, title)
    blocks = markdown_to_feishu_blocks(md_content)

    if blocks:
        add_blocks_to_doc(token, document_id, blocks)

    page_url = f"https://{FEISHU_WIKI_DOMAIN}/wiki/{node_token}"
    return page_url


# ========== 如流群消息 ==========

def extract_summary(md_content):
    """从完整报告中提取精简摘要：板块标题 + 每条新闻（**标题加粗** + 子弹句不加粗）
    格式规范：只保留标题和关键子弹句，不写入选理由/介绍等详情"""
    lines = md_content.split('\n')
    summary_parts = []

    for line in lines:
        stripped = line.strip()

        # 收集板块标题
        if stripped.startswith('## '):
            summary_parts.append(f"\n{stripped}")

        # 格式1：「- **标题**：子弹句」
        elif stripped.startswith('- **') and '**' in stripped[4:]:
            match = re.match(r'- \*\*(.+?)\*\*[:：]?\s*(.*)', stripped)
            if match:
                title = match.group(1)
                bullet = match.group(2).strip()
                summary_parts.append(f"- **{title}**")
                if bullet:
                    summary_parts.append(f"  {bullet}")
            else:
                summary_parts.append(stripped)

        # 格式2：「### N. **标题**」→ 提取标题
        elif stripped.startswith('### ') and '**' in stripped:
            bold = re.search(r'\*\*(.+?)\*\*', stripped)
            if bold:
                summary_parts.append(f"- **{bold.group(1)}**")

        # 格式3：「**一句话说清发生了什么**：子弹句」→ 提取子弹句
        elif '**一句话说清发生了什么**' in stripped:
            match = re.search(r'\*\*一句话说清发生了什么\*\*[:：]\s*(.+)', stripped)
            if match:
                bullet = match.group(1).strip()
                if bullet:
                    summary_parts.append(f"  {bullet}")

    return '\n'.join(summary_parts).strip()


def send_to_ruliu(title, md_content, feishu_url=None):
    """发送精简摘要到如流群"""
    if not RULIU_WEBHOOK_URL:
        print("  [如流] RULIU_WEBHOOK_URL 未配置，跳过发送。")
        return
    if not RULIU_GROUP_ID:
        print("  [如流] RULIU_GROUP_ID 未配置，跳过发送。")
        return

    summary = extract_summary(md_content)

    # 拼接消息
    text = f"## {title}\n\n{summary}"
    if feishu_url:
        text += f"\n\n---\n查看完整日报: {feishu_url}"

    # 如流 groupmsgsend API 格式：header.toid + body 数组
    # MD 类型支持 markdown 渲染，限制 2K 字符；超长降级为 TEXT
    msg_type = "MD" if len(text) <= 2000 else "TEXT"
    payload = {
        "message": {
            "header": {
                "toid": [int(RULIU_GROUP_ID)]
            },
            "body": [
                {
                    "type": msg_type,
                    "content": text
                }
            ]
        }
    }

    resp = requests.post(RULIU_WEBHOOK_URL, json=payload, timeout=10)
    data = resp.json()
    print(f"  [如流] API 返回: {data}")
    err = data.get("errcode") or 0
    if err != 0:
        raise Exception(f"如流发送失败: {data}")
    fail = data.get("data", {}).get("fail", {})
    if fail:
        raise Exception(f"如流部分发送失败: {fail}")


# ========== 统一入口 ==========

def distribute_report(title, md_content):
    """分发报告：飞书先发（拿链接）→ 如流后发（带链接）"""
    print("-" * 30)
    print("📤 开始分发报告...")

    feishu_url = None

    # 1. 飞书知识库
    try:
        feishu_url = publish_to_feishu(title, md_content)
        if feishu_url:
            print(f"✅ [飞书] 知识库页面发布成功: {feishu_url}")
    except Exception as e:
        print(f"❌ [飞书] 发布失败: {e}")

    # 2. 如流群消息
    try:
        send_to_ruliu(title, md_content, feishu_url)
        print("✅ [如流] 群消息发送成功")
    except Exception as e:
        print(f"❌ [如流] 发送失败: {e}")


if __name__ == "__main__":
    # 单独测试用：读取最近的报告文件并分发
    import glob
    files = sorted(glob.glob("*-Overseas-LLM-Insight.md"), reverse=True)
    if files:
        with open(files[0], "r", encoding="utf-8") as f:
            content = f.read()
        title_line = content.split('\n')[0].lstrip('# ').strip()
        # 去掉标题行，只传正文给分发
        body = '\n'.join(content.split('\n')[1:]).strip()
        distribute_report(title_line, body)
    else:
        print("未找到报告文件，请先运行 daily_report.py 生成报告。")
