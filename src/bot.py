"""
Long-running Telegram bot — trigger the LinkedIn pipeline with /run.

Usage:
    python3 src/bot.py

Then send /run in Telegram anytime to start the pipeline.
"""

import sys
import os
import time
import requests

sys.path.insert(0, os.path.dirname(__file__))

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID   = str(os.environ["TELEGRAM_CHAT_ID"])
BASE_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}"

from telegram_bot import send_message
import main as pipeline


def _get_updates(offset: int) -> list[dict]:
    try:
        resp = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30, "allowed_updates": ["message"]},
            timeout=40,
        )
        return resp.json().get("result", [])
    except Exception as e:
        print(f"[bot] Poll error: {e}")
        time.sleep(5)
        return []


def run():
    # Drain any backlogged messages so old commands don't trigger on startup
    updates = _get_updates(0)
    offset  = (updates[-1]["update_id"] + 1) if updates else 0

    send_message(
        "🤖 <b>LinkedIn Bot is online!</b>\n\n"
        "Send /run to generate and post to LinkedIn.\n"
        "Send /status to check if a pipeline is running."
    )
    print("[bot] Listening... Send /run in Telegram to trigger the pipeline.")

    running = False

    while True:
        updates = _get_updates(offset)

        for update in updates:
            offset  = update["update_id"] + 1
            msg     = update.get("message", {})
            text    = msg.get("text", "").strip()
            chat_id = str(msg.get("chat", {}).get("id", ""))

            if chat_id != CHAT_ID:
                continue

            if text == "/run":
                if running:
                    send_message("⚠️ A pipeline is already running. Wait for it to finish.")
                    continue

                running = True
                try:
                    pipeline.run()
                except SystemExit as e:
                    if e.code and e.code != 0:
                        send_message("❌ Pipeline exited with an error.")
                except Exception as e:
                    send_message(f"❌ Unexpected error: <code>{e}</code>")
                    print(f"[bot] Unexpected error: {e}")
                finally:
                    running = False
                    send_message("📬 Send /run anytime to start a new pipeline.")

            elif text == "/status":
                if running:
                    send_message("⚙️ Pipeline is currently <b>running</b>.")
                else:
                    send_message("💤 No pipeline running. Send /run to start one.")


if __name__ == "__main__":
    run()
