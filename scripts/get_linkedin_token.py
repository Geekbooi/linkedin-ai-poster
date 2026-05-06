"""
LinkedIn OAuth helper — run this once to get your access token.

Steps:
  1. Go to https://www.linkedin.com/developers/ and create an app
  2. Add the "Share on LinkedIn" product (grants w_member_social scope)
  3. Set redirect URI to: http://localhost:8080/callback
  4. Fill in CLIENT_ID and CLIENT_SECRET below or set as env vars
  5. Run: python scripts/get_linkedin_token.py
  6. Visit the printed URL, authorise, then paste the code shown
  7. Copy the printed access token into your .env / GitHub secret
"""

import os
import urllib.parse
import urllib.request
import json
import http.server
import threading
import webbrowser

CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID",     "YOUR_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDIRECT_URI  = "http://localhost:8080/callback"
SCOPE         = "openid profile email w_member_social"

auth_code: list[str] = []   # shared between server thread and main thread


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code   = params.get("code", [None])[0]

        if code:
            auth_code.append(code)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Authorised. You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>Error: no code returned.</h2>")

    def log_message(self, *args):
        pass   # silence request logs


def start_server():
    server = http.server.HTTPServer(("", 8080), CallbackHandler)
    server.handle_request()   # handle exactly one request then stop


def get_auth_url() -> str:
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "scope":         SCOPE,
        "state":         "linkedin_oauth",
    })
    return f"https://www.linkedin.com/oauth/v2/authorization?{params}"


def exchange_code(code: str) -> dict:
    data = urllib.parse.urlencode({
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_person_urn(token: str) -> str:
    req = urllib.request.Request(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return f"urn:li:person:{data['id']}"


def main():
    if CLIENT_ID == "YOUR_CLIENT_ID":
        print("Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET env vars first.")
        return

    # Start local callback server in background
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()

    url = get_auth_url()
    print(f"\nOpening browser for LinkedIn authorisation...\n{url}\n")
    webbrowser.open(url)

    # Wait for callback
    thread.join(timeout=120)

    if not auth_code:
        print("Timed out waiting for authorisation.")
        return

    print("Exchanging code for token...")
    token_data = exchange_code(auth_code[0])
    token      = token_data["access_token"]
    expires_in = token_data.get("expires_in", "unknown")

    urn = get_person_urn(token)

    print("\n" + "=" * 55)
    print("SUCCESS — add these to your .env and GitHub secrets:")
    print("=" * 55)
    print(f"LINKEDIN_ACCESS_TOKEN={token}")
    print(f"LINKEDIN_PERSON_URN={urn}")
    print(f"\nToken expires in: {expires_in} seconds (~60 days)")
    print("=" * 55)


if __name__ == "__main__":
    main()
