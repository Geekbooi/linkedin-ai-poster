# LinkedIn AI Post Pipeline

Automatically generates LinkedIn posts from the latest AI news, sends a draft to you on Telegram for approval, and publishes to LinkedIn on your schedule.

## How it works

```
GitHub Actions (every 2 days)
  → Fetch latest AI news from RSS feeds
  → Claude picks the best story + writes a post in your voice
  → Draft sent to you via Telegram
  → You reply: "approve" or "edit [instructions]"
  → Claude regenerates if needed (up to 5 rounds)
  → Approved post goes live on LinkedIn
```

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

The workflow runs automatically every other day at **8:00 AM UTC**.
You can also trigger it manually from the **Actions** tab → **LinkedIn AI Post** → **Run workflow**.

---

## Customising the schedule

Edit `.github/workflows/post.yml`:

```yaml
- cron: "0 8 */2 * *"   # every other day at 8am UTC
```

Use [crontab.guru](https://crontab.guru) to adjust timing.

## Changing the post style

Edit the `SYSTEM_PROMPT` in `src/generator.py` to match your voice more precisely. The more detail you add about your opinions, tone, and audience, the better each post will sound like you.

## Adding or removing news sources

Edit the `FEEDS` list in `src/news.py`.

---

## Project structure

```
├── src/
│   ├── main.py             # Orchestration
│   ├── news.py             # RSS news fetching
│   ├── generator.py        # Claude API — story selection + post generation
│   ├── telegram_bot.py     # Send draft + poll for approval
│   └── linkedin_poster.py  # LinkedIn UGC API posting
├── scripts/
│   ├── get_linkedin_token.py   # OAuth helper (run once)
│   └── get_telegram_chat_id.py # Find your Telegram chat ID
├── .github/workflows/
│   └── post.yml            # GitHub Actions cron job
├── .env.example
└── requirements.txt
```
