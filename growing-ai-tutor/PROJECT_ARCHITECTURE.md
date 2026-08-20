# Project Architecture

```text
Browser / Tablet
      |
      v
FastAPI + Session Auth
      |
      +--> Student API --------> SQLAlchemy ------> SQLite/PostgreSQL
      |
      +--> Quiz Engine (deterministic correctness)
      |
      +--> Abacus Engine
      |
      +--> Progress Engine -----> mastery + difficulty
      |
      +--> Supervisor ----------> learn / practice / challenge
      |
      +--> Tutor Service -------> Optional LLM explanation
      |
      +--> Parent Dashboard
```

## Agentic growth path

V1 uses an explicit Python supervisor rather than a heavyweight multi-agent framework. This makes decisions observable and testable. Later, the supervisor can orchestrate Tutor, Quiz, Reasoning, RAG, Evaluation, and Revision agents while retaining deterministic tools for scoring and arithmetic.
