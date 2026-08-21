# Growing AI Tutor — Family Beta Architecture

```text
Child / Parent Browser
        |
        v
FastAPI + Session Login
        |
        +-- Student Profile
        |      +-- Grade
        |      +-- Language preference
        |      +-- Beta tester ID
        |
        +-- Learning Engine
        |      +-- Maths
        |      +-- Science
        |      +-- Logical Reasoning
        |      +-- Abacus
        |
        +-- Tutor Layer
        |      +-- Deterministic fallback
        |      +-- Optional OpenAI explanation
        |
        +-- Progress / Adaptive Supervisor
        |
        +-- Parent Dashboard
        |
        +-- Structured Beta Feedback
        |
        v
SQLite (local only) / PostgreSQL (shared beta)
```

## Beta success signals
- children return without being forced
- parents report explanations are useful
- language preference: English / Telugu / Both
- top requested next features
- regular-use intent
- willingness-to-pay distribution
