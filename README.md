# 🛡️ PR Sentinel — Autonomous GitHub PR Review Agent

PR Sentinel is an autonomous agent that reviews GitHub Pull Requests the way a senior engineer would. It combines deterministic static analysis (Ruff) with advanced LLM reasoning (Meta LLaMA-3.3 via Groq) to catch code style violations, logical bugs, and security risks. To guarantee reliability, the agent validates all LLM findings against the code diff before posting comments, preventing hallucinations entirely.


---

## 🌟 Key Features

* **Real static analysis (Ruff)**: Automatically analyzes changes for Python styling nits, unused imports, syntax errors, and undefined names.
* **Contextual LLM Reasoning (Groq/LLaMA-3.3)**: Inspects added code for logic flaws, security vulnerabilities (like SQL Injections), and performance bottlenecks.
* **Hallucination Protection (Evidence Check)**: Ensures the LLM quotes the *exact code line* that contains the bug. If the code quoted doesn't exist in the diff, the claim is discarded.
* **PR-scoped Linting**: Filters issues to only report violations on the lines *changed in this PR*, keeping reviews fair to developers.
* **Dual Auth Support**: Works seamlessly with personal accounts (using **Personal Access Tokens**) or public organizations (using **GitHub Apps** with dynamic JWT token generation).
* **Automated Data Retention**: Automatically prunes database review records older than 30 days on server startup to keep the storage clean.
* **Production Ready**: Fully Dockerized and configured with an async background worker model, ready for deployment on platforms like Render or Railway.

---

## 🛠️ Technology Stack

* **Orchestration**: LangGraph (StateGraph)
* **LLM Reasoning**: Groq API (`llama-3.3-70b-versatile`)
* **Static Linting**: Ruff
* **API Framework**: FastAPI & Uvicorn
* **Database**: PostgreSQL (Production) / SQLite (Local) with SQLAlchemy ORM
* **Local Webhook Tunnelling**: Smee.io

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12+
- Node.js (for running the Smee client locally)

### 2. Installation & Setup
Clone the repository, initialize your virtual environment, and install dependencies:
```bash
git clone https://github.com/Kapish7717/PR-SENTINEL.git
cd PR-SENTINEL

# Set up virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# Install packages
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
# Groq LLM API Key
GROQ_API_KEY=your_groq_api_key_here

# GitHub Authentication (Either PAT or App Credentials)
# Option A: Personal Access Token (PAT)
GITHUB_TOKEN=your_github_personal_access_token

# Option B: GitHub App credentials (alternative to GITHUB_TOKEN)
# GITHUB_APP_ID=your_app_id
# GITHUB_PRIVATE_KEY_PATH=github_private_key.pem

# Webhook Secret (Matches GitHub Settings)
GITHUB_WEBHOOK_SECRET=your_custom_webhook_secret_password
```

---

## 💻 Local Execution & Webhook Testing

### Run Unit Tests
Make sure everything is working by running the pytest suite:
```bash
python -m pytest
```

### Run Review Pipeline Locally on a Patch File
You can manually run the pipeline on a local `.patch` diff file without using webhooks:
```bash
python scripts/run_local_review.py --patch sample.patch
```

### Run Real-time GitHub Webhook Pipeline Locally
To test live pull request reviews on your local machine:

1. **Start the Webhook Server**:
   ```bash
   python -m uvicorn webhook:app --reload --port 8000
   ```
2. **Start Smee Proxy**:
   Go to [smee.io](https://smee.io/), click "Start a new channel", and copy the URL. Then start Smee in another terminal:
   ```bash
   npx smee-client --port 8000 --path /webhook --url https://smee.io/your_channel_id
   ```
3. **Configure Repository Webhook**:
   Add a webhook to your GitHub repository pointing to your `https://smee.io/your_channel_id` URL. Choose `application/json` as the content type and select the **"Pull requests"** event.
4. **Push & Open a PR**:
   Push a commit containing a code issue, open a PR, and watch the reviews post instantly inline!

---

## 🐳 Dockerization & Cloud Deployment

This project includes a `Dockerfile` and `.dockerignore` for containerized hosting.

### Building and Running the Docker Container Locally
```bash
docker build -t pr-sentinel .
docker run -p 8000:8000 --env-file .env pr-sentinel

```

### Deploying to Render
1. Go to [Render](https://render.com/) and create a new **Web Service**.
2. Link your GitHub repository. Select **Docker** as the environment.
3. In the **Environment** settings tab, add your `.env` variables.
4. Click **Deploy**. Render will host the service and expose a public URL (e.g., `https://pr-sentinel.onrender.com`).
5. Update your GitHub App or Webhook URL to point to `https://pr-sentinel.onrender.com/webhook`.
