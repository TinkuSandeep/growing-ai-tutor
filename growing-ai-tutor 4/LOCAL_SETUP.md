# Run Growing AI Tutor V4 locally

## Windows PowerShell

```powershell
cd "growing-ai-tutor-v4"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:BETA_INVITE_CODES="FAMILY-BETA,FRIENDS-BETA"
$env:SESSION_SECRET="local-development-secret-change-this"
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>, choose **Create a family account**, enter one of
the invitation codes, and create your own password.

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Optional OpenAI teaching

Set these before starting Uvicorn:

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="gpt-5.4-mini"
```

The application still works with deterministic teaching content when no API
key is configured.

## Run tests

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```

Local progress is stored in `data/tutor.db`. Do not commit `.env`, database
files, passwords, session secrets, or API keys.
