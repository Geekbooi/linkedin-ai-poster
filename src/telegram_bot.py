import os
import time
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID    = os.environ["TELEGRAM_CHAT_ID"]
BASE_URL   = f"https://api.telegram.org/bot{BOT_TOKEN}"

POLL_INTERVAL  = 20   # seconds between getUpdates calls
APPROVAL_TIMEOUT = 3600  # 1 hour max wait


def _post(endpoint: str, **kwargs) -> dict:
    resp = requests.post(f"{BASE_URL}/{endpoint}", timeout=40, **kwargs)
    resp.raise_for_status()
    return resp.json()


def _get(endpoint: str, **kwargs) -> dict:
    resp = requests.get(f"{BASE_URL}/{endpoint}", timeout=40, **kwargs)
    resp.raise_for_status()
    return resp.json()


def send_message(text: str) -> None:
    _post("sendMessage", json={
        "chat_id":                  CHAT_ID,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True,
    })


def _clear_old_updates() -> int:
    """Drain any backlogged updates and return the next offset to use."""
    data = _get("getUpdates", params={"timeout": 0})
    updates = data.get("result", [])
    if updates:
        return updates[-1]["update_id"] + 1
    return 0


def _get_updates(offset: int) -> list[dict]:
    data = _get("getUpdates", params={
        "offset":          offset,
        "timeout":         POLL_INTERVAL,
        "allowed_updates": ["message"],
    })
    return data.get("result", [])


def send_draft_for_approval(draft: str, story: dict, attempt: int = 1) -> tuple[str, str | None]:
    """
    Send the draft to Telegram and poll for a reply.

    Returns:
        ("approve", None)         — user approved, post it
        ("edit",    "<feedback>") — user wants changes
        ("timeout", None)         — no response within the window
    """
    header = (
        f"📰 <b>Source:</b> {story['source']}\n"
        f"🔗 {story['link']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Draft #{attempt}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{draft}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Reply:\n"
        f"✅ <b>approve</b>\n"
        f"✏️ <b>edit</b> [your instructions]"
    )
    send_message(header)
    return _wait_for_response()


def _wait_for_response() -> tuple[str, str | None]:
    offset   = _clear_old_updates()
    deadline = time.time() + APPROVAL_TIMEOUT

    print(f"[telegram] Polling for response (timeout: {APPROVAL_TIMEOUT // 60} min)...")

    while time.time() < deadline:
        try:
            updates = _get_updates(offset)
        except requests.RequestException as exc:
            print(f"[telegram] Poll error: {exc} — retrying in 15s")
            time.sleep(15)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            text   = update.get("message", {}).get("text", "").strip()

            if not text:
                continue

            lower = text.lower()

            if lower == "approve":
                send_message("✅ Approved! Posting to LinkedIn now...")
                return "approve", None

            if lower.startswith("edit"):
                feedback = text[4:].strip().lstrip(":").strip()
                if not feedback:
                    send_message("❓ Please add your instructions after <b>edit</b>.\nExample: <i>edit make the tone more direct and cut the last paragraph</i>")
                    continue
                send_message(f'✏️ Got it — regenerating with: "<i>{feedback}</i>"')
                return "edit", feedback

            send_message(
                "❓ I didn't understand that.\n\n"
                "Reply with:\n"
                "✅ <b>approve</b>\n"
                "✏️ <b>edit</b> [your instructions]"
            )

    send_message("⏰ Approval window closed (1 hour). Post was <b>not</b> published.")
    return "timeout", None
