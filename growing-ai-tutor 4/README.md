# 🌱 Growing AI Tutor — Family Beta

A bilingual, child-friendly learning beta for Indian families. The current release supports English, Telugu, and natural Telugu+English mixed teaching.

## Family Beta goals

This build is meant for a small group of families, friends and colleagues to validate whether the product is genuinely useful before adding subscriptions and more languages.

### Included
- Maths: addition, subtraction, multiplication
- Science: plants, animals, our body
- Logical reasoning: patterns, sequences, odd-one-out
- Abacus place-value visualizer
- Adaptive mastery and next-topic recommendations
- English / తెలుగు / bilingual teaching preference
- Anonymous beta tester IDs per child profile
- Parent dashboard
- Structured beta feedback and willingness-to-pay signals
- Optional OpenAI-powered teaching; deterministic fallback works without an API key

## Local run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Vercel

When importing this GitHub repository, set the Vercel Root Directory to
`growing-ai-tutor 4`. Vercel otherwise builds the repository root and produces
an empty deployment that reports `READY` but returns HTTP 404.

The included `vercel.json` configures `api/index.py` as the Python function
entry point and routes requests to the FastAPI application in `app/main.py`.

Recommended production environment variables:

```text
APP_ENV=prod
APP_PASSWORD=<private beta family password>
SESSION_SECRET=<long random secret>
SESSION_HTTPS_ONLY=true
BETA_INVITE_CODES=<comma-separated one-time family invite codes>
DATABASE_URL=<pooled managed PostgreSQL URL; required in production>
OPENAI_API_KEY=<optional>
OPENAI_MODEL=gpt-5.4-mini
```

Do not use local SQLite for real multi-family beta data on serverless production. Use managed PostgreSQL before collecting meaningful tester progress/feedback.

Parents create their own account with a one-time invite code. Passwords are
hashed with Argon2, and each signed-in parent can access only their own child
profiles. `APP_PASSWORD` is retained only for backwards-compatible local
configuration and is no longer used by the parent login flow.

## Privacy

Do not collect unnecessary personal information from children. Keep the beta private/shared only with invited families until authentication, privacy terms, data retention and parental-consent flows are production-ready.
