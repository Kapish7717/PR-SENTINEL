import os
import sys
import hmac
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from agent.runner import review_pr
from db.session import engine, Base, SessionLocal, cleanup_old_reviews
# Add parent directory of 'agent' to python search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env manually before other imports to prevent KeyError
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create DB tables if they do not exist
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
    db = SessionLocal()
    try:
        cleanup_old_reviews(db)
    finally:
        db.close()
    yield

app = FastAPI(title="PR Sentinel Webhook Service", lifespan=lifespan)


@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    # ── Step 1: verify this actually came from GitHub ──
    webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    if webhook_secret:
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not signature:
            raise HTTPException(status_code=401, detail="X-Hub-Signature-256 header missing")
        expected = "sha256=" + hmac.new(webhook_secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        print("Warning: GITHUB_WEBHOOK_SECRET is not set. Signature verification bypassed.")

    # ── Step 2: parse the event ──
    body = await request.json()
    event = request.headers.get("X-GitHub-Event")
    action = body.get("action")

    # ── Step 3: only care about PR opened or new commit pushed ──
    if event != "pull_request" or action not in ("opened", "synchronize"):
        return {"status": "ignored", "reason": f"Event '{event}' with action '{action}' is not handled."}

    # ── Step 4: extract what we need ──
    try:
        pr_id           = body["pull_request"]["number"]
        repo            = body["repository"]["full_name"]
        commit_sha      = body["pull_request"]["head"]["sha"]
        # Safe extraction of installation_id (only present for GitHub App installs)
        installation_id = body.get("installation", {}).get("id")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing key in payload: {e}")

    # ── Step 5: enqueue background job, respond immediately ──
    background_tasks.add_task(
        review_pr,
        pr_id=pr_id,
        repo=repo,
        commit_sha=commit_sha,
        installation_id=installation_id
    )

    return {"status": "review started"}   # GitHub gets this instantly

@app.get("/health")
def health():
    return {"status": "ok", "db_url": os.environ.get("DATABASE_URL", "sqlite:///./pr_sentinel.db").split("@")[-1]}  # redact auth details