import os
import time
import jwt
import requests

def get_github_token(installation_id: int = None) -> str:
    """
    Get a GitHub auth token.
    If GITHUB_APP_ID and GITHUB_PRIVATE_KEY_PATH (or GITHUB_PRIVATE_KEY) are set,
    it performs App authentication and returns the installation access token.
    Otherwise, it falls back to the static GITHUB_TOKEN.
    """
    app_id = os.environ.get("GITHUB_APP_ID")
    private_key_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH")
    private_key_env = os.environ.get("GITHUB_PRIVATE_KEY")
    
    if app_id and (private_key_path or private_key_env) and installation_id:
        try:
            if private_key_path and os.path.exists(private_key_path):
                with open(private_key_path, "r", encoding="utf-8") as f:
                    private_key = f.read()
            elif private_key_env:
                private_key = private_key_env.replace("\\n", "\n")
            else:
                private_key = None

            if private_key:
                payload = {
                    "iat": int(time.time()) - 60,  # backdate a bit for clock drift
                    "exp": int(time.time()) + 540,
                    "iss": int(app_id)
                }
                jwt_token = jwt.encode(payload, private_key, algorithm="RS256")
                
                url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
                headers = {
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json"
                }
                res = requests.post(url, headers=headers)
                res.raise_for_status()
                return res.json()["token"]
        except Exception as e:
            print(f"GitHub App Authentication failed: {e}. Falling back to standard GITHUB_TOKEN.")

    # Fallback to token
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PAT")
    if token:
        return token.strip()
    
    raise ValueError("No GitHub token configured. Please set GITHUB_TOKEN or GitHub App credentials in .env")
