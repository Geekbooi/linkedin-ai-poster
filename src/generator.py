import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are an expert LinkedIn content creator focused on AI, tech news, cloud computing, and DevOps.

Topics: AI trends, AI agents, LLMs, tech news, cloud, DevOps, and related innovations.

Post structure:
1. Hook — one scroll-stopping opening line that creates curiosity and urgency. No fluff.
2. Body — maximum 2 short paragraphs. Concise, clear, impactful. One useful insight, takeaway, or unique perspective grounded in the news.
3. CTA — end with a question or call-to-action to drive engagement.
4. Hashtags — 3–5 relevant tags on the final line, no more.

Rules:
- 150–250 words maximum
- Simple, direct language — no jargon, no fluff
- Professional but conversational tone
- Rotate between formats: insights, quick tips, breakdowns, opinions, trend analysis
- Never use: "game-changer", "revolutionize", "the future is here", "in today's world"
- Use clean line spacing for readability

Output only the final LinkedIn post, ready to publish."""


def pick_best_story(stories: list[dict]) -> dict:
    stories_text = "\n\n".join(
        f"[{i+1}] {s['title']}\nSource: {s['source']}\nSummary: {s['summary']}"
        for i, s in enumerate(stories)
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": (
                "You are selecting the best AI news story for a LinkedIn post targeting business leaders and tech professionals.\n"
                "Pick the story that is most timely, most impactful, and has the strongest angle for professional opinion.\n"
                "Reply with ONLY the number of the best story.\n\n"
                + stories_text
            ),
        }],
    )

    try:
        idx = int(response.content[0].text.strip()) - 1
        return stories[max(0, min(idx, len(stories) - 1))]
    except (ValueError, IndexError):
        return stories[0]


def generate_post(story: dict, feedback: str | None = None) -> str:
    base_prompt = (
        f"Write a LinkedIn post based on this news story.\n\n"
        f"Title: {story['title']}\n"
        f"Source: {story['source']}\n"
        f"Summary: {story['summary']}\n"
        f"Link: {story['link']}"
    )

    if feedback:
        base_prompt += f"\n\n---\nThe previous draft was rejected. User feedback:\n{feedback}\nIncorporate this feedback while keeping the same news story."

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": base_prompt}],
    )

    return response.content[0].text.strip()
