import re
import time
from calendar import timegm

import feedparser

FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.technologyreview.com/feed/",
    "https://venturebeat.com/ai/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.wired.com/feed/tag/ai/latest/rss",
]

# On a daily schedule, anything older than this isn't "hot" any more.
MAX_AGE_HOURS = 48


def _age_hours(entry) -> float | None:
    """Hours since publication, or None when the feed gives no usable date."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return (time.time() - timegm(parsed)) / 3600


def fetch_stories(max_per_feed: int = 6, max_age_hours: int = MAX_AGE_HOURS) -> list[dict]:
    stories = []
    dropped_stale = 0

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                age = _age_hours(entry)
                if age is not None and age > max_age_hours:
                    dropped_stale += 1
                    continue

                summary = entry.get("summary", entry.get("description", ""))
                summary = re.sub(r"<[^>]+>", "", summary).strip()[:600]

                stories.append({
                    "title":     entry.get("title", "").strip(),
                    "summary":   summary,
                    "link":      entry.get("link", ""),
                    "source":    feed.feed.get("title", url),
                    "published": entry.get("published", ""),
                    "age_hours": round(age, 1) if age is not None else None,
                })
        except Exception as e:
            print(f"[news] Failed to fetch {url}: {e}")

    # Freshest first, undated entries last.
    stories.sort(key=lambda s: s["age_hours"] if s["age_hours"] is not None else 1e9)

    print(
        f"[news] {len(stories)} stories within {max_age_hours}h "
        f"from {len(FEEDS)} feeds ({dropped_stale} older ones skipped)"
    )
    return stories
