import sys
import os

# Load .env for local runs (no-op in CI where secrets are injected as env vars)
from pathlib import Path
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file)

# Make sibling modules importable when run as `python src/main.py`
sys.path.insert(0, os.path.dirname(__file__))

import history
from news import fetch_stories
from generator import pick_best_story, generate_post
from telegram_bot import send_message, send_draft_for_approval
from linkedin_poster import post_to_linkedin

MAX_EDIT_ROUNDS = 5


def _gather_fresh_stories() -> list[dict]:
    """Fresh stories that haven't been posted before.

    Widens the time window once before giving up, so a quiet news day
    doesn't silently skip the daily post.
    """
    for window in (48, 96):
        stories = fetch_stories(max_age_hours=window)
        unseen  = history.filter_unseen(stories)
        if unseen:
            if window > 48:
                print(f"[main] Nothing new in 48h — widened to {window}h")
            return unseen
    return []


def _announce(story: dict) -> None:
    """Tell Telegram which story was chosen."""
    print(f"      → {story['title']}")
    age = story.get("age_hours")
    age_line = f"\n🕒 {age}h old" if age is not None else ""
    send_message(
        f"🤖 <b>Story selected</b>\n\n"
        f"<b>{story['title']}</b>\n"
        f"Source: {story['source']}{age_line}"
    )


def run() -> None:
    print("=" * 50)
    print("LinkedIn AI Post Pipeline")
    print("=" * 50)

    # 1. Fetch news
    print("\n[1/4] Fetching latest AI news...")
    stories = _gather_fresh_stories()

    if not stories:
        send_message(
            "🈳 <b>No new AI stories today.</b>\n\n"
            "Every fresh headline has already been posted. Nothing was published."
        )
        print("      → No unseen stories. Exiting cleanly.")
        sys.exit(0)

    # 2. Pick best story
    print("\n[2/4] Selecting the best story...")
    story = pick_best_story(stories)
    _announce(story)

    # 3. Generate initial draft
    print("\n[3/4] Generating first draft...")
    draft = generate_post(story)

    # 4. Approval loop
    print("\n[4/4] Waiting for Telegram approval...")
    for attempt in range(1, MAX_EDIT_ROUNDS + 1):
        action, feedback = send_draft_for_approval(draft, story, attempt)

        if action == "approve":
            print("      → Approved. Posting to LinkedIn...")
            success, result = post_to_linkedin(draft, story=story)

            if success:
                history.record(story, result)
                send_message(f"🚀 <b>Posted successfully!</b>\nLinkedIn Post ID: <code>{result}</code>")
                print(f"      → Done! Post ID: {result}")
            else:
                send_message(f"❌ LinkedIn post failed:\n<code>{result}</code>")
                print(f"      → LinkedIn error: {result}")
                sys.exit(1)
            return

        elif action == "edit":
            print(f"      → Edit round {attempt}: {feedback}")
            draft = generate_post(story, feedback=feedback)

        elif action == "skip":
            print(f"      → Skipped: {story['title']}")
            history.record(story, "skipped")
            stories = [s for s in stories if s["link"] != story["link"]]

            if not stories:
                send_message("⏭️ Skipped — and that was the last fresh story today. Nothing published.")
                sys.exit(0)

            story = pick_best_story(stories)
            send_message("⏭️ Skipped. Picking another story...")
            _announce(story)
            draft = generate_post(story)

        elif action == "timeout":
            print("      → Timed out. Exiting.")
            sys.exit(0)

    send_message(
        f"⚠️ Reached the maximum of {MAX_EDIT_ROUNDS} edit rounds.\n"
        "Post was <b>not</b> published. Run the pipeline again to start fresh."
    )
    sys.exit(1)


if __name__ == "__main__":
    run()
