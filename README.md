# LinkedIn AI Post Pipeline

Automatically generates LinkedIn posts from the latest AI news, sends a draft to you on Telegram for approval, and publishes to LinkedIn on your schedule.

## How it works

```
GitHub Actions (daily, 9:00 AM America/Detroit)
  → Fetch AI news published in the last 48 hours
  → Drop anything already posted (data/history.json)
  → Claude picks the best story + writes a post in your voice
  → Draft sent to you via Telegram
  → You reply: "approve" / "edit [instructions]" / "skip"
  → Claude regenerates or moves to another story (up to 5 rounds)
  → Approved post goes live on LinkedIn, and the story is recorded
```

### Replying on Telegram

| Reply | What happens |
|---|---|
| `approve` | Publishes the draft to LinkedIn |
| `edit <instructions>` | Claude rewrites the post with your notes, same story |
| `skip` | Drops this story for good and drafts the next-best one |
| *(no reply)* | After 1 hour the run closes without posting |

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/linkedin-ai-poster
cd linkedin-ai-poster
pip install -r requirements.txt
```

### 2. Get your credentials

**Anthropic API Key**
- Go to https://console.anthropic.com/
- Create an API key

**Telegram Bot**
```bash
# 1. Message @BotFather on Telegram → /newbot → copy the token
# 2. Start a chat with your new bot (send it any message)
# 3. Run:
TELEGRAM_BOT_TOKEN=your_token python scripts/get_telegram_chat_id.py
```

**LinkedIn Access Token**
```bash
# 1. Create an app at https://www.linkedin.com/developers/
# 2. Add the "Share on LinkedIn" product
# 3. Set redirect URI to: http://localhost:8080/callback
# 4. Run:
LINKEDIN_CLIENT_ID=xxx LINKEDIN_CLIENT_SECRET=yyy python scripts/get_linkedin_token.py
```
This opens your browser, you authorise, and the script prints your token and person URN.

> ⚠️ LinkedIn tokens expire after **60 days**. Re-run the script to refresh.

### 3. Configure environment

```bash
cp .env.example .env
# Fill in all five values
```

### 4. Test locally

```bash
python src/main.py
```

The pipeline runs immediately. You will receive a Telegram message with the draft.

### 5. Deploy to GitHub Actions

Add each variable from `.env` as a **Repository Secret** in:
`GitHub → Your repo → Settings → Secrets and variables → Actions → New repository secret`

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `TELEGRAM_BOT_TOKEN` | Your bot token |
| `TELEGRAM_CHAT_ID` | Your chat ID |
| `LINKEDIN_ACCESS_TOKEN` | OAuth access token |
| `LINKEDIN_PERSON_URN` | `urn:li:person:XXXXXXXXXX` |

The workflow runs automatically **every day at 9:00 AM America/Detroit**.
You can also trigger it manually from the **Actions** tab → **LinkedIn AI Post** → **Run workflow**.

---

## Customising the schedule

GitHub's cron runs on UTC and does **not** follow daylight saving, so the
workflow registers both possible UTC times for 9 AM Eastern and a guard step
drops whichever one isn't 9 AM locally today:

```yaml
- cron: "0 13 * * *"   # 09:00 EDT (Mar–Nov)
- cron: "0 14 * * *"   # 09:00 EST (Nov–Mar)
```

To move the hour, shift both crons **and** the `TZ=America/Detroit` hour check
in the *"Skip if it is not 9am"* step, or the guard will cancel every run.

Set `APPROVAL_TIMEOUT_SECONDS` to change how long it waits for your reply
(default 3600). Keep `timeout-minutes` in the workflow above that value.

> GitHub also delays scheduled runs when its queue is busy — 9:05–9:20 AM is
> normal. The guard allows the whole 9 AM hour.

## Changing the post style

Edit the `SYSTEM_PROMPT` in `src/generator.py` to match your voice more precisely. The more detail you add about your opinions, tone, and audience, the better each post will sound like you.

## Adding or removing news sources

Edit the `FEEDS` list in `src/news.py`. `MAX_AGE_HOURS` in the same file
controls how old a story may be (default 48h); if nothing fresh is left
unposted, the pipeline widens to 96h once before standing down for the day.

## Posted-story history

`data/history.json` holds the last 60 stories that were posted or skipped, so a
daily schedule never repeats an article. GitHub Actions commits it back to the
repo after each run. Delete the file to reset.

---

## Project structure

```
├── src/
│   ├── main.py             # Orchestration
│   ├── news.py             # RSS news fetching + freshness filter
│   ├── history.py          # Remembers posted stories (no repeats)
│   ├── generator.py        # Claude API — story selection + post generation
│   ├── telegram_bot.py     # Send draft + poll for approval
│   └── linkedin_poster.py  # LinkedIn UGC API posting
├── scripts/
│   ├── get_linkedin_token.py   # OAuth helper (run once)
│   └── get_telegram_chat_id.py # Find your Telegram chat ID
├── .github/workflows/
│   └── post.yml            # GitHub Actions cron job
├── data/history.json       # Posted-story log (auto-committed by CI)
├── .env.example
└── requirements.txt
```
