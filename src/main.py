import sys
import os

# Make sibling modules importable when run as `python src/main.py`
sys.path.insert(0, os.path.dirname(__file__))

from news import fetch_stories
from generator import pick_best_story, generate_post
from telegram_bot import send_message, send_draft_for_approval
from linkedin_poster import post_to_linkedin

MAX_EDIT_ROUNDS = 5


def run() -> None:
    print("=" * 50)
    print("LinkedIn AI Post Pipeline")
    print("=" * 50)

    # 1. Fetch news
    print("\n[1/4] Fetching latest AI news...")
    stories = fetch_stories()

    if not stories:
        send_message("❌ Pipeline failed: could not fetch any news stories.")
        sys.exit(1)

    # 2. Pick best story
    print("\n[2/4] Selecting the best story...")
    story = pick_best_story(stories)
    print(f"      → {story['title']}")
    send_message(
        f"🤖 <b>Pipeline started</b>\n\n"
        f"Selected story:\n<b>{story['title']}</b>\n"
        f"Source: {story['source']}"
    )

    # 3. Generate initial draft
    print("\n[3/4] Generating first draft...")
    draft = generate_post(story)

    # 4. Approval loop
    print("\n[4/4] Waiting for Telegram approval...")
    for attempt in range(1, MAX_EDIT_ROUNDS + 1):
        action, feedback = send_draft_for_approval(draft, story, attempt)

        if action == "approve":
            print("      → Approved. Posting to LinkedIn...")
            success, result = post_to_linkedin(draft)

            if success:
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
