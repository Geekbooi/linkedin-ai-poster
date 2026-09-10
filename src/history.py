"""Remembers which stories have already been posted, so a daily schedule
never sends the same article twice."""

import json
from datetime import datetime, timezone
from pathlib import Path

HISTORY_FILE = Path(__file__).parent.parent / "data" / "history.json"
KEEP_LAST    = 60   # roughly two months of daily posts


def _normalise(link: str) -> str:
    """Strip tracking params so the same article always hashes the same."""
    return link.split("?")[0].rstrip("/").lower()


def load() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[history] Could not read history ({exc}) — starting fresh")
        return []


def posted_links() -> set[str]:
    return {_normalise(e.get("link", "")) for e in load() if e.get("link")}


def filter_unseen(stories: list[dict]) -> list[dict]:
    """Drop stories already posted, and de-duplicate within this batch."""
    seen = posted_links()
    out  = []
    for s in stories:
        key = _normalise(s.get("link", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(s)
    print(f"[history] {len(out)}/{len(stories)} stories are new")
    return out


def record(story: dict, post_id: str) -> None:
    entry = {
        "link":     story.get("link", ""),
        "title":    story.get("title", ""),
        "source":   story.get("source", ""),
        "post_id":  post_id,
        "posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    entries = load()
    entries.append(entry)
    entries = entries[-KEEP_LAST:]

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(entries, indent=2) + "\n")
    print(f"[history] Recorded: {entry['title'][:60]}")
