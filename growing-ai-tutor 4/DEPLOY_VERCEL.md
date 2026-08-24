# Growing AI Tutor — Vercel Release

## 1. Push the release to GitHub

Do not commit `.env`.

```bash
git check-ignore .env
git status
git add .
git commit -m "release: Growing AI Tutor family beta for Vercel"
git push origin main
```

## 2. Import the repository in Vercel

Import the GitHub repository that contains this folder. If these files are at the
repository root, leave **Root Directory** empty. If they are inside a subfolder,
set Root Directory to that subfolder.

FastAPI Vercel entrypoint: `api/index.py` (imports `app.main:app`)

## 3. Required Vercel environment variables

Set these for Production (and Preview if desired):

- `APP_ENV=prod`
- `APP_NAME=Growing AI Tutor`
- `APP_PASSWORD=<your beta password>`
- `SESSION_SECRET=<a long random secret>`
- `SESSION_HTTPS_ONLY=true`
- `BETA_INVITE_CODES=<comma-separated one-time family invite codes>`

Optional:

- `OPENAI_API_KEY=<your key>`
- `OPENAI_MODEL=<model you want to use>`

## 4. Database

Production requires `DATABASE_URL`; the app intentionally refuses to start with
SQLite so family accounts, progress, and feedback cannot be silently lost. Use
a pooled managed PostgreSQL connection such as Neon:
it will use SQLite under `/tmp`. **That storage is temporary and may reset.**

Before inviting family/friends for meaningful testing, set a persistent Postgres URL:

`DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require`

The schema is created automatically on startup for this beta.

## 5. Smoke test after deployment

- `/health` returns `{"status":"ok",...}`
- Family login works
- Add a student
- English / Telugu / bilingual selector works
- New Question -> answer -> Check shows green/red feedback
- Parent dashboard updates
- Feedback form submits
