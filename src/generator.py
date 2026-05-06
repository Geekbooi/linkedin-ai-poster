import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You write LinkedIn posts for a thought leader in AI and technology.

Voice & Style:
- Direct, data-backed, occasionally contrarian. Not hype. Not doom.
- Professional but conversational — like a sharp colleague, not a marketer
- First person with strong opinions grounded in the news
- Never use: "game-changer", "revolutionize", "the future is here", "in today's world"

Post structure (follow this strictly):
1. Hook — first line only. A striking stat, fact, or bold claim from the news. No fluff.
2. News anchor — reference the source and story explicitly (1-2 sentences). Builds credibility.
3. Your take — the contrarian or insightful opinion on what it means (2-3 sentences). This is the core value.
4. Practical implication — what should the reader actually do or think about (1-2 sentences).
5. Engagement question — one honest question to spark replies.
6. Hashtags — 3-5 relevant tags on the final line, no more.

Length: 200–280 words exactly.
Tone: Insightful, direct, human. Written to spark a conversation, not to go viral."""


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
