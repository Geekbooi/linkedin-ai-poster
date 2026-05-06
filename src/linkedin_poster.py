import os
import requests

ACCESS_TOKEN = os.environ["LINKEDIN_ACCESS_TOKEN"]
PERSON_URN   = os.environ["LINKEDIN_PERSON_URN"]   # urn:li:person:XXXXXXXXXX

HEADERS = {
    "Authorization":             f"Bearer {ACCESS_TOKEN}",
    "Content-Type":              "application/json",
    "X-Restli-Protocol-Version": "2.0.0",
}


def post_to_linkedin(text: str) -> tuple[bool, str]:
    """
    Publish a text post to LinkedIn.
    Returns (success, post_id_or_error_message).
    """
    payload = {
        "author": PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    resp = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )

    if resp.status_code == 201:
        post_id = resp.headers.get("x-restli-id", "unknown")
        return True, post_id

    return False, f"HTTP {resp.status_code}: {resp.text}"
