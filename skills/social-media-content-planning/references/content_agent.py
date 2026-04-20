#!/usr/bin/env python3
"""
Daily Content Planner - generates daily social-media post drafts.

Workflow:
    materials library -> extract content -> plan topic -> draft post -> independent review

Usage:
    python content_agent.py                  # Normal run using next unused material
    python content_agent.py --trending       # Force trending-topics mode (skip materials)
    python content_agent.py --material FILE  # Use a specific PDF or URL

Requires config.py (see config.example.py).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

import config


# ---------------------------------------------------------------------------
# Materials Library
# ---------------------------------------------------------------------------

class MaterialsLibrary:
    """Manages the pool of input materials and tracks usage."""

    def __init__(self, base_dir: str = config.MATERIALS_DIR):
        self.base_dir = Path(base_dir)
        self.pdfs_dir = self.base_dir / "pdfs"
        self.links_file = self.base_dir / "links.txt"
        self.used_file = self.base_dir / "used_materials.json"
        self._used = self._load_used()

    def _load_used(self) -> set:
        if self.used_file.exists():
            return set(json.loads(self.used_file.read_text()))
        return set()

    def _save_used(self):
        self.used_file.write_text(
            json.dumps(sorted(self._used), ensure_ascii=False, indent=2)
        )

    def mark_used(self, key: str):
        self._used.add(key)
        self._save_used()

    def get_all_pdfs(self) -> list[dict]:
        if not self.pdfs_dir.exists():
            return []
        return [
            {"type": "pdf", "path": str(p), "key": p.name}
            for p in sorted(self.pdfs_dir.glob("*.pdf"))
            if p.name not in self._used
        ]

    def get_all_links(self) -> list[dict]:
        if not self.links_file.exists():
            return []
        links = []
        for line in self.links_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and line not in self._used:
                links.append({"type": "url", "url": line, "key": line})
        return links

    def get_next_material(self) -> dict | None:
        """Return the next unused material (PDFs first, then links)."""
        for m in self.get_all_pdfs():
            return m
        for m in self.get_all_links():
            return m
        return None

    def get_specific(self, path_or_url: str) -> dict:
        """Wrap a user-specified path or URL as a material dict."""
        if path_or_url.startswith("http"):
            return {"type": "url", "url": path_or_url, "key": path_or_url}
        return {"type": "pdf", "path": path_or_url, "key": Path(path_or_url).name}


# ---------------------------------------------------------------------------
# Content Extractor
# ---------------------------------------------------------------------------

class ContentExtractor:
    """Extracts text content from PDFs and web pages."""

    MAX_CHARS = 6000  # truncation limit for LLM input

    @classmethod
    def extract(cls, material: dict) -> str:
        if material["type"] == "pdf":
            return cls.extract_pdf(material["path"])
        if material["type"] == "url":
            return cls.extract_url(material["url"])
        return ""

    @classmethod
    def extract_pdf(cls, path: str) -> str:
        if PdfReader is None:
            return "[Error] PyPDF2 not installed. Run: pip install PyPDF2"
        try:
            reader = PdfReader(path)
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            full_text = "\n\n".join(pages_text)
            if not full_text.strip():
                return "[Warning] PDF appears to be scanned images with no extractable text."
            return full_text[:cls.MAX_CHARS]
        except Exception as e:
            return f"[Error] Failed to read PDF: {e}"

    @classmethod
    def extract_url(cls, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")

            # WeChat article special handling
            if "mp.weixin.qq.com" in url:
                content_div = soup.find(id="js_content")
                if content_div:
                    text = content_div.get_text(separator="\n", strip=True)
                    return text[:cls.MAX_CHARS]

            # Generic: try <article>, then <main>, then <body>
            for selector in ["article", "main", "body"]:
                el = soup.find(selector)
                if el:
                    for tag in el.find_all(["script", "style", "nav", "footer"]):
                        tag.decompose()
                    text = el.get_text(separator="\n", strip=True)
                    if len(text) > 200:
                        return text[:cls.MAX_CHARS]

            return soup.get_text(separator="\n", strip=True)[:cls.MAX_CHARS]
        except Exception as e:
            return f"[Error] Failed to fetch URL: {e}"


# ---------------------------------------------------------------------------
# Trending Search
# ---------------------------------------------------------------------------

class TrendingSearch:
    """Finds trending topics related to the account's niche when no materials are available."""

    def __init__(self, client: OpenAI):
        self.client = client

    def search(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        resp = self.client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[{
                "role": "user",
                "content": f"""Today is {today}. You are an industry analyst for the niche below.

ACCOUNT: {config.ACCOUNT_NAME}
AUDIENCE: {config.TARGET_AUDIENCE}
CONTENT STYLE: {config.CONTENT_STYLE}

List 5 current trending topics / recent developments in this niche that could
become a social post today. For each topic, provide:
1. The topic/trend (one line)
2. Why it's relevant now (one line)
3. The angle that ties it back to the account's focus (one line)

Focus on what the audience would actually find interesting and discussion-worthy."""
            }],
            temperature=0.8,
            max_tokens=1500,
        )
        return _extract_reply(resp)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_reply(resp) -> str:
    """Extract text from API response, handling models that use reasoning_content."""
    msg = resp.choices[0].message
    content = msg.content or ""
    # Some reasoning models (e.g. deepseek-r1) put output in reasoning_content
    if not content.strip() and hasattr(msg, "reasoning_content") and msg.reasoning_content:
        content = msg.reasoning_content
    return content.strip() or "[No content returned by model]"


# ---------------------------------------------------------------------------
# Post Generator
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are the content strategist for the social account "{config.ACCOUNT_NAME}".

TARGET AUDIENCE: {config.TARGET_AUDIENCE}
LANGUAGE: {config.LANGUAGE}
CONTENT STYLE: {config.CONTENT_STYLE}
BRAND VOICE: Knowledgeable, approachable, audience-friendly. Confident but not arrogant.

CONTENT GUIDELINES:
- Depth: Reference concrete capabilities, benchmarks, APIs, or use cases — show, don't tell
- Engagement: Ask questions, invite discussion, or include a clear CTA
- Hashtags: Include 1-3 relevant hashtags
- Tone: "Smart practitioner sharing insights" not "corporate marketing"

FORMAT OPTIONS:
- Single post: Under 280 characters (tight, punchy)
- Thread: 3-5 numbered tweets for deeper content (each under 280 chars)
- Choose the best format based on the content depth"""


class PostGenerator:
    """Two-step generation: topic planning -> draft writing."""

    def __init__(self, client: OpenAI):
        self.client = client

    def plan_topic(self, source_content: str, source_label: str) -> str:
        resp = self.client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"""Based on the following source material, propose 3 different angles
for today's post. For each angle, give:
- Angle title (one line)
- Why this angle works for our audience (one line)
- Suggested format: single post or thread (one line)

SOURCE ({source_label}):
\"\"\"
{source_content}
\"\"\""""},
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return _extract_reply(resp)

    def generate_drafts(self, topic_plan: str, source_content: str) -> str:
        resp = self.client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"""Based on the topic planning below, write 2 complete draft variations
for today's post.

TOPIC PLAN:
\"\"\"
{topic_plan}
\"\"\"

SOURCE MATERIAL:
\"\"\"
{source_content[:4000]}
\"\"\"

For each draft:
1. Pick the best angle from the plan
2. Write the full post (single post or thread)
3. Include hashtags
4. Add a brief note on the best posting time (in the audience's timezone)

Mark drafts clearly as [DRAFT A] and [DRAFT B]."""},
            ],
            temperature=0.8,
            max_tokens=2000,
        )
        return _extract_reply(resp)


# ---------------------------------------------------------------------------
# Draft Reviewer (uses REVIEWER_MODEL — deliberately different from MODEL_NAME)
# ---------------------------------------------------------------------------

REVIEWER_PROMPT = f"""You are a senior content reviewer for the social account "{config.ACCOUNT_NAME}".
Target audience: {config.TARGET_AUDIENCE}. Language: {config.LANGUAGE}.

Your job is to review draft posts and provide a critical assessment. You must check:

1. **Tone & Voice**: Is the tone appropriate for the audience? Too salesy? Too casual? Too corporate?
2. **Ambiguity**: Any sentence that could be misunderstood or misinterpreted?
3. **Absolute Claims**: Flag overly absolute statements ("the best", "the only", "always", "never") that could undermine credibility.
4. **Factual Accuracy**: Cross-check against the source material. Flag any factual errors, exaggerations, or unsupported claims.
5. **Cultural Sensitivity**: Anything that might not translate well for the target audience's culture?
6. **Platform Fit**: Does each post fit within 280 characters? Is the thread structure logical?

OUTPUT FORMAT:
For each draft, provide:
- ✅ What works well (1-2 points)
- ⚠️ Issues found (list each with specific quote and suggested fix)
- 📝 Overall verdict: READY / NEEDS MINOR EDITS / NEEDS REWRITE

Finally, provide a **Revised Version** for any draft that has issues, with the problems fixed.
Respond in both English and Chinese (中英双语)."""


class DraftReviewer:
    """Reviews drafts for tone, accuracy, ambiguity, and absolute claims."""

    def __init__(self, client: OpenAI):
        self.client = client

    def review(self, drafts: str, source_content: str) -> str:
        resp = self.client.chat.completions.create(
            model=config.REVIEWER_MODEL,
            messages=[
                {"role": "system", "content": REVIEWER_PROMPT},
                {"role": "user", "content": f"""Please review the following post drafts.

DRAFTS TO REVIEW:
\"\"\"
{drafts}
\"\"\"

ORIGINAL SOURCE MATERIAL (for fact-checking):
\"\"\"
{source_content[:4000]}
\"\"\"

Provide your detailed review with issues and suggested fixes."""},
            ],
            temperature=0.3,
            max_tokens=2500,
        )
        return _extract_reply(resp)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate daily social post drafts")
    parser.add_argument("--trending", action="store_true", help="Force trending topics mode")
    parser.add_argument("--material", type=str, help="Specify a PDF path or URL to use")
    args = parser.parse_args()

    if config.LLM_API_KEY == "your-api-key-here":
        print("ERROR: Please set your API key in config.py first.")
        sys.exit(1)

    client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)
    library = MaterialsLibrary()
    generator = PostGenerator(client)

    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(config.OUTPUT_DIR) / today
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"  Daily Content Planner — {today}")
    print(f"{'='*50}\n")

    # Step 1: Choose source
    if args.material:
        material = library.get_specific(args.material)
        source_label = f"Specified: {args.material}"
        print(f"[Source] Using specified material: {args.material}")
    elif args.trending:
        material = None
        source_label = "Trending topics"
        print("[Source] Forced trending mode")
    else:
        material = library.get_next_material()
        if material:
            source_label = f"Material: {material['key']}"
            print(f"[Source] Using material: {material['key']}")
        else:
            material = None
            source_label = "Trending topics"
            print("[Source] No unused materials found, switching to trending topics")

    if material:
        print("[Extract] Reading content...")
        source_content = ContentExtractor.extract(material)
        if source_content.startswith("[Error]") or source_content.startswith("[Warning]"):
            print(f"  {source_content}")
            print("  Falling back to trending topics...")
            source_content = TrendingSearch(client).search()
            source_label = "Trending topics (fallback)"
        else:
            library.mark_used(material["key"])
            print(f"  Extracted {len(source_content)} characters")
    else:
        print("[Trending] Searching for trending topics...")
        source_content = TrendingSearch(client).search()

    # Step 2: Topic planning
    print("[Plan] Generating topic angles...")
    topic_plan = generator.plan_topic(source_content, source_label)
    topic_file = output_dir / "topic.md"
    topic_file.write_text(
        f"# Topic Plan — {today}\n\n"
        f"**Source:** {source_label}\n\n"
        f"---\n\n{topic_plan}\n",
        encoding="utf-8",
    )
    print(f"  Saved to {topic_file}")

    # Step 3: Draft generation
    print("[Draft] Writing post drafts...")
    drafts = generator.generate_drafts(topic_plan, source_content)
    draft_file = output_dir / "draft.md"
    draft_file.write_text(
        f"# Post Drafts — {today}\n\n"
        f"**Account:** {config.ACCOUNT_NAME}\n"
        f"**Source:** {source_label}\n\n"
        f"---\n\n{drafts}\n",
        encoding="utf-8",
    )
    print(f"  Saved to {draft_file}")

    # Step 4: Independent review (different model)
    print(f"[Review] Reviewing drafts with {config.REVIEWER_MODEL}...")
    reviewer = DraftReviewer(client)
    review_result = reviewer.review(drafts, source_content)
    review_file = output_dir / "review.md"
    review_file.write_text(
        f"# Draft Review — {today}\n\n"
        f"**Reviewer Model:** {config.REVIEWER_MODEL}\n\n"
        f"---\n\n{review_result}\n",
        encoding="utf-8",
    )
    print(f"  Saved to {review_file}")

    print(f"\n{'='*50}")
    print(f"  Done! Review your drafts:")
    print(f"  - Topic plan: {topic_file}")
    print(f"  - Post drafts: {draft_file}")
    print(f"  - Draft review: {review_file}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
