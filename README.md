# DocMind AI

An intelligent document workspace powered by **IBM watsonx.ai** foundation models.
Upload PDF, DOCX, PPTX or TXT files and interact with them through natural language —
ask questions, generate summaries, compare documents, and extract AI-powered insights.

---

## Features

| Feature | Description |
|---|---|
| Public landing page | Clean marketing page before login |
| User authentication | Register, login, logout with secure password hashing |
| Account settings | Change username, password, or delete account |
| Dashboard | Stats overview, recent documents, recent conversations |
| Document library | Upload, view, search, download, delete |
| AI Chat | ChatGPT-style Q&A on your documents with conversation history |
| AI Summaries | Short, detailed, or bullet-point styles |
| Document comparison | Side-by-side AI analysis of two documents |
| AI Insights | Keywords, topics, tags, reading time |
| Dark / Light mode | Persisted per-user |
| Rate limiting | Protects login and register endpoints |
| Health check | `/health` endpoint for hosting platforms |
| Error pages | Custom 404, 500, 429 pages |

---

## Local Development

### 1. Clone and set up

```bash
git clone https://github.com/yourname/docmind-ai.git
cd docmind-ai/docmind_ai
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

Edit `.env` and fill in:

```env
SECRET_KEY=any-long-random-string
IBM_API_KEY=your-ibm-cloud-api-key
IBM_PROJECT_ID=your-watsonx-project-id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
FLASK_ENV=development
```

### 3. Run

```bash
python run.py
# → http://localhost:5000
```

---

## Hosting — Railway (recommended)

Railway auto-detects Python and reads `railway.toml`.

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Select your repository
4. Add the following environment variables in the Railway dashboard:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Generate a random string |
| `IBM_API_KEY` | Your IBM Cloud API key |
| `IBM_PROJECT_ID` | Your watsonx.ai project ID |
| `IBM_WATSONX_URL` | Your region URL |
| `FLASK_ENV` | `production` |

5. Railway will build and deploy automatically. Your app will be live at `*.up.railway.app`.

---

## Hosting — Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → **New Web Service** → connect your repo
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2`
4. Add the same environment variables as above

Or use the included `render.yaml` blueprint for one-click deploy.

---

## Hosting — Heroku

```bash
heroku create your-app-name
heroku config:set SECRET_KEY=... IBM_API_KEY=... IBM_PROJECT_ID=... IBM_WATSONX_URL=... FLASK_ENV=production
git push heroku main
```

The `Procfile` is already configured.

> **Note:** Heroku's `postgres://` DATABASE_URL is automatically converted to `postgresql://` by the app.

---

## Project Structure

```
docmind_ai/
├── wsgi.py                     # Production WSGI entry point (gunicorn)
├── run.py                      # Local dev entry point
├── config.py                   # All settings + AGENT_CONFIGURATION
├── requirements.txt
├── Procfile                    # Heroku / Railway / Render
├── railway.toml                # Railway config
├── render.yaml                 # Render blueprint
├── .env.example
└── app/
    ├── __init__.py             # Factory + extensions (SQLAlchemy, Login, Limiter)
    ├── models/                 # User, Document, Conversation, Message
    ├── routes/
    │   ├── misc.py             # Landing page, /health
    │   ├── auth.py             # Register, login, logout (rate-limited)
    │   ├── dashboard.py        # Dashboard stats
    │   ├── documents.py        # Upload, view, delete, download, search
    │   ├── ai.py               # Chat, summary, compare, insights
    │   └── profile.py          # Account settings, change password, delete
    ├── services/
    │   ├── document_service.py # PDF/DOCX/PPTX/TXT text extraction
    │   └── watsonx_service.py  # IBM watsonx.ai API integration
    ├── templates/
    │   ├── landing.html        # Public landing page
    │   ├── base.html           # Sidebar layout
    │   ├── errors/             # 404, 500, 429
    │   ├── auth/               # login, register
    │   ├── dashboard/
    │   ├── documents/
    │   ├── ai/                 # chat, summary, compare, insights
    │   └── profile/            # account settings
    └── static/
        ├── css/main.css        # Full design system, dark/light
        └── js/                 # main, chat, summary, compare, insights, documents
```

---

## AGENT_CONFIGURATION

All AI behaviour is controlled by a single dict in [`config.py`](config.py).
No other code changes needed.

```python
AGENT_CONFIGURATION = {
    "model_id":           "meta-llama/llama-3-3-70b-instruct",
    "personality":        "You are DocMind AI, an expert document analyst...",
    "tone":               "professional",
    "max_new_tokens":     1024,
    "temperature":        0.7,
    "summary_style":      "bullets",
    "safety_instructions":"Do not generate harmful content...",
}
```

---

## Security

- Passwords: PBKDF2-SHA256 via Werkzeug
- Sessions: `HttpOnly`, `SameSite=Lax`, `Secure` in production
- Rate limiting: 20 login attempts / hour, 10 registrations / hour per IP
- Proxy-aware: `ProxyFix` middleware for correct IP detection behind hosting platform load balancers
- API keys: loaded from `.env` only — never hardcoded

---

## Getting IBM Credentials

1. Sign up at [cloud.ibm.com](https://cloud.ibm.com)
2. Create an API key: **IAM → API Keys → Create**
3. Create a watsonx.ai project: [dataplatform.cloud.ibm.com/wx](https://dataplatform.cloud.ibm.com/wx/)
4. Copy the Project ID from **Manage** tab
5. Note your region URL from the list in `.env.example`
