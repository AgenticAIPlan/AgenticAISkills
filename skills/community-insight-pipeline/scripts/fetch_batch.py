#!/usr/bin/env python3
"""
Reddit 批量抓取脚本 - 独立可运行版本

依赖：pip install praw
配置：在工作目录创建 .env 文件（见下方配置区说明）

使用前：
  1. 修改下方 TASKS 列表，填入目标产品/话题关键词
  2. 配置 .env 文件（REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / REDDIT_USER_AGENT）
  3. 可选：调整 SUBREDDITS、DB_PATH、GLOBAL_POST_LIMIT
"""

import os
import sys
import time
import sqlite3
from datetime import datetime, date

try:
    import praw
    from praw.models import MoreComments
except ImportError:
    print("Error: praw not installed. Run: pip install praw")
    sys.exit(1)

# ============================================================
# 配置区 - 根据实际需求修改
# ============================================================

# 数据库路径（优先读取环境变量）
DB_PATH = os.getenv("DISCUSSION_DB_PATH", "discussions.db")

# 全局搜索时最多抓取的帖子数
GLOBAL_POST_LIMIT = 100

# 评论展开深度（0 = 全部展开；数字越大抓取越慢）
PRAW_COMMENT_LIMIT = 0

# 子版块列表（mode='subreddits' 时使用，可自行增减）
SUBREDDITS = [
    "LocalLLaMA",
    "ChatGPT",
    "artificial",
    "MachineLearning",
    "deeplearning",
    "learnmachinelearning",
    "ArtificialIntelligence",
    "GPT3",
    "OpenAI",
]

# 任务列表 - 每项格式：(描述, query, mode, include_comments)
#
# query:
#   不加引号 → 宽松匹配，如 'ERNIE' 匹配含该词的帖子
#   加引号   → 精确匹配，如 '"ERNIE-Image"' 只匹配该短语
#
# mode:
#   'global'     → 全站搜索（r/all），覆盖范围广
#   'subreddits' → 仅在上方 SUBREDDITS 列表内搜索，噪音更少
#
# include_comments:
#   True  → 同时抓取帖子下的全部评论（耗时较长）
#   False → 仅抓取帖子

TASKS = [
    # 示例：替换为你的目标产品关键词
    # (描述,               query,        mode,         include_comments)
    ("产品A 全站精确搜索",  '"产品A"',   "global",     True),
    ("产品A 子版块搜索",    "产品A",     "subreddits", True),
]

# ============================================================
# 数据库 Schema（首次运行自动创建）
# ============================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS discussions (
    platform_id     TEXT PRIMARY KEY,
    platform        TEXT    DEFAULT 'reddit',
    content_type    TEXT,           -- 'post' or 'comment'
    title           TEXT,           -- post title (empty for comments)
    content         TEXT,           -- post body or comment text
    url             TEXT,
    author          TEXT,
    subreddit       TEXT,
    score           INTEGER,
    created_at      TEXT,           -- UTC ISO format
    fetched_at      TEXT,           -- UTC ISO format
    search_keywords TEXT,
    image_urls      TEXT,           -- comma-separated image URLs
    depth           INTEGER DEFAULT 0,  -- 0=post, 1+=comment nesting level
    thread_id       TEXT,           -- platform_id of the parent post
    parent_id       TEXT,           -- platform_id of immediate parent
    post_title      TEXT,           -- for comments: title of parent post
    parent_content  TEXT            -- for comments: first 300 chars of parent
);

CREATE TABLE IF NOT EXISTS annotations (
    platform_id     TEXT PRIMARY KEY,
    is_relevant     INTEGER,        -- 1=relevant, 0=not relevant
    summary         TEXT DEFAULT '',
    advantages      TEXT DEFAULT '',
    disadvantages   TEXT DEFAULT '',
    tendency        TEXT DEFAULT '',
    model           TEXT DEFAULT '',
    annotated_at    TEXT,
    FOREIGN KEY (platform_id) REFERENCES discussions(platform_id)
);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def upsert(conn: sqlite3.Connection, row: dict):
    conn.execute(
        """
        INSERT OR REPLACE INTO discussions
          (platform_id, platform, content_type, title, content, url, author,
           subreddit, score, created_at, fetched_at, search_keywords,
           image_urls, depth, thread_id, parent_id, post_title, parent_content)
        VALUES
          (:platform_id, :platform, :content_type, :title, :content, :url, :author,
           :subreddit, :score, :created_at, :fetched_at, :search_keywords,
           :image_urls, :depth, :thread_id, :parent_id, :post_title, :parent_content)
        """,
        row,
    )


# ============================================================
# 工具函数
# ============================================================

def load_dotenv():
    """手动解析 .env 文件，不依赖 python-dotenv"""
    if not os.path.exists(".env"):
        return
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


def load_reddit() -> praw.Reddit:
    load_dotenv()
    for key in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"):
        if not os.environ.get(key):
            print(f"Error: {key} not set. Create a .env file with Reddit API credentials.")
            sys.exit(1)
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "CommunityInsightBot/1.0"),
    )


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def safe_author(obj) -> str:
    try:
        return str(obj.author) if obj.author else "[deleted]"
    except Exception:
        return "[deleted]"


def extract_image_urls(submission) -> str:
    urls = []
    url = getattr(submission, "url", "") or ""
    if any(url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        urls.append(url)
    try:
        for img in (getattr(submission, "preview", {}) or {}).get("images", []):
            src = img.get("source", {}).get("url", "")
            if src:
                urls.append(src.replace("&amp;", "&"))
    except Exception:
        pass
    seen, result = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return ",".join(result)


def post_to_row(submission, search_keywords: str) -> dict:
    return {
        "platform_id":     f"reddit__{submission.id}",
        "platform":        "reddit",
        "content_type":    "post",
        "title":           submission.title or "",
        "content":         submission.selftext or "",
        "url":             f"https://reddit.com{submission.permalink}",
        "author":          safe_author(submission),
        "subreddit":       str(submission.subreddit),
        "score":           submission.score,
        "created_at":      datetime.utcfromtimestamp(submission.created_utc).isoformat(),
        "fetched_at":      now_iso(),
        "search_keywords": search_keywords,
        "image_urls":      extract_image_urls(submission),
        "depth":           0,
        "thread_id":       None,
        "parent_id":       None,
        "post_title":      submission.title or "",
        "parent_content":  "",
    }


def comment_to_row(comment, submission, search_keywords: str,
                   depth: int, parent_content: str) -> dict:
    raw_parent = getattr(comment, "parent_id", "") or ""
    parent_suffix = raw_parent.split("_", 1)[-1] if "_" in raw_parent else raw_parent
    return {
        "platform_id":     f"reddit__{comment.id}",
        "platform":        "reddit",
        "content_type":    "comment",
        "title":           "",
        "content":         comment.body or "",
        "url":             f"https://reddit.com{comment.permalink}",
        "author":          safe_author(comment),
        "subreddit":       str(submission.subreddit),
        "score":           comment.score,
        "created_at":      datetime.utcfromtimestamp(comment.created_utc).isoformat(),
        "fetched_at":      now_iso(),
        "search_keywords": search_keywords,
        "image_urls":      "",
        "depth":           depth,
        "thread_id":       f"reddit__{submission.id}",
        "parent_id":       f"reddit__{parent_suffix}" if parent_suffix else None,
        "post_title":      submission.title or "",
        "parent_content":  (parent_content or "")[:300],
    }


def fetch_comments(submission, conn: sqlite3.Connection, search_keywords: str) -> int:
    try:
        submission.comments.replace_more(limit=PRAW_COMMENT_LIMIT)
    except Exception as e:
        print(f"    Warning: replace_more failed: {e}")

    post_content = submission.selftext or ""
    count = 0

    def walk(comment_list, depth):
        nonlocal count
        for c in comment_list:
            if isinstance(c, MoreComments):
                continue
            raw_parent = getattr(c, "parent_id", "") or ""
            parent_content = post_content if raw_parent.startswith("t3_") else ""
            upsert(conn, comment_to_row(c, submission, search_keywords, depth, parent_content))
            count += 1
            walk(c.replies, depth + 1)

    walk(submission.comments, 1)
    conn.commit()
    return count


def already_fetched_today(conn: sqlite3.Connection) -> set:
    today = date.today().isoformat()
    rows = conn.execute(
        "SELECT DISTINCT thread_id FROM discussions "
        "WHERE thread_id IS NOT NULL AND depth > 0 AND fetched_at LIKE ?",
        (f"{today}%",),
    ).fetchall()
    return {r[0] for r in rows}


# ============================================================
# 任务执行
# ============================================================

def run_task(label: str, query: str, mode: str, include_comments: bool,
             reddit: praw.Reddit, conn: sqlite3.Connection):
    print(f"\n{'=' * 60}")
    print(f"Task: {label}  |  query={query}  |  mode={mode}")
    print(f"{'=' * 60}")
    t0 = time.time()
    posts = []

    try:
        if mode == "global":
            target = reddit.subreddit("all")
        elif mode == "subreddits":
            target = reddit.subreddit("+".join(SUBREDDITS))
        else:
            print(f"  Unknown mode: {mode}, skipping")
            return

        for submission in target.search(query, limit=GLOBAL_POST_LIMIT, sort="relevance"):
            posts.append(submission)
            upsert(conn, post_to_row(submission, query))
        conn.commit()
        print(f"  Posts saved: {len(posts)}")

        if include_comments and posts:
            fetched_today = already_fetched_today(conn)
            total_comments, skipped = 0, 0
            for idx, submission in enumerate(posts, 1):
                thread_id = f"reddit__{submission.id}"
                if thread_id in fetched_today:
                    print(f"  [{idx}/{len(posts)}] skip (fetched today): {submission.title[:40]}")
                    skipped += 1
                    continue
                print(f"  [{idx}/{len(posts)}] fetching comments: {submission.title[:50]}")
                n = fetch_comments(submission, conn, query)
                total_comments += n
                time.sleep(0.5)
            print(f"  Comments saved: {total_comments}  (skipped {skipped})")

    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()

    print(f"  Done in {time.time() - t0:.0f}s")


def main():
    print(f"Fetch start  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"DB: {DB_PATH}")
    conn = init_db(DB_PATH)
    reddit = load_reddit()
    for label, query, mode, include_comments in TASKS:
        run_task(label, query, mode, include_comments, reddit, conn)
    conn.close()
    print(f"\nAll done  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
