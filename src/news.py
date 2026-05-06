import feedparser
import os

FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.technologyreview.com/feed/",
    "https://venturebeat.com/ai/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.wired.com/feed/tag/ai/latest/rss",
]

def fetch_stories(max_per_feed: int = 4) -> list[dict]:
    stories = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                summary = entry.get("summary", entry.get("description", ""))
                # Strip HTML tags simply
                import re
                summary = re.sub(r"<[^>]+>", "", summary).strip()[:600]
                stories.append({
                    "title":     entry.get("title", "").strip(),
                    "summary":   summary,
                    "link":      entry.get("link", ""),
                    "source":    feed.feed.get("title", url),
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"[news] Failed to fetch {url}: {e}")

    print(f"[news] Fetched {len(stories)} stories from {len(FEEDS)} feeds")
    return stories
