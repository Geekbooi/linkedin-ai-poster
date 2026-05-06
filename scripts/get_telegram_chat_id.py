"""
Run this once to find your Telegram chat ID.

Steps:
  1. Create a bot at https://t.me/BotFather → /newbot
  2. Copy the bot token
  3. Start a chat with your new bot (send it any message)
  4. Run: TELEGRAM_BOT_TOKEN=your_token python scripts/get_telegram_chat_id.py
"""

import os
import requests

token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    print("Set the TELEGRAM_BOT_TOKEN environment variable first.")
    raise SystemExit(1)

resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
resp.raise_for_status()
updates = resp.json().get("result", [])

if not updates:
    print("No messages found. Send a message to your bot first, then re-run this script.")
    raise SystemExit(1)

seen = set()
for update in updates:
    chat = update.get("message", {}).get("chat", {})
    cid  = chat.get("id")
    name = chat.get("first_name", "") + " " + chat.get("last_name", "")
    if cid and cid not in seen:
        seen.add(cid)
        print(f"Chat ID: {cid}  |  Name: {name.strip()}")

print("\nAdd the correct Chat ID as TELEGRAM_CHAT_ID in your .env and GitHub secrets.")
