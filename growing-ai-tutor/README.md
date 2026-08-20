# 🌱 Growing AI Tutor

A safe, adaptive learning starter for a child that can grow grade-by-grade. V1 includes deterministic Maths and Logical Reasoning quizzes, adaptive progress tracking, an Abacus visualizer, an optional AI teacher, and a parent dashboard.

## Why the architecture is split this way

- **Python owns correctness** for arithmetic and quiz evaluation.
- **AI is optional** and used to explain concepts in child-friendly language.
- **Supervisor logic** recommends learn/practice/challenge based on mastery.
- **Parent dashboard** shows progress without exposing the database directly.
- **Session login** protects student data when deployed.

## Current V1 scope

- Grades 1–12 student profile field (content currently focused on early learning)
- Maths: addition, subtraction, multiplication
- Logical reasoning: patterns, sequences, odd-one-out
- Abacus place-value visualizer up to 9,999
- Adaptive mastery and difficulty
- Parent dashboard
- Optional OpenAI Responses API teacher
- SQLite locally; PostgreSQL supported through `DATABASE_URL`
- Docker + GitHub Actions CI

## Local setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

The default `.env.example` password is only a placeholder. Change it before real use.

## Run tests

```powershell
pytest -q
ruff check app tests
```

## Docker

```powershell
Copy-Item .env.example .env
# Edit .env first
docker compose up --build
```

Open `http://localhost:8000`.

## Production checklist

Set these environment variables in your deployment platform:

```text
APP_ENV=prod
APP_PASSWORD=<strong family password>
SESSION_SECRET=<long random value>
SESSION_HTTPS_ONLY=true
DATABASE_URL=<persistent database URL>
OPENAI_API_KEY=<optional>
OPENAI_MODEL=gpt-5.6-luna
```

For production, prefer a managed PostgreSQL database rather than an ephemeral SQLite filesystem. The app deliberately refuses to start in `prod` if the placeholder password/session secret are still present.

## API

- `GET /health`
- `POST /api/auth/login`
- `GET|POST /api/students`
- `GET /api/curriculum`
- `GET /api/quiz`
- `POST /api/quiz/answer`
- `POST /api/tutor`
- `GET /api/recommendation/{student_id}`
- `POST /api/abacus`
- `GET /api/dashboard/{student_id}`

## Next milestones

1. CBSE/NCERT curriculum ingestion and retrieval layer.
2. Science/EVS and English modules.
3. Interactive draggable abacus and complement techniques.
4. Spaced repetition scheduling.
5. Voice interaction.
6. Parent controls and multiple child profiles.
7. RAG from parent-approved textbooks/worksheets.
8. Evaluation suite for age-appropriateness and factual accuracy.

## Child-safety design

The app does not require a child's email, phone number, location, or social account. Keep internet browsing disabled for the tutor and use only parent-approved learning content when the RAG layer is added.
