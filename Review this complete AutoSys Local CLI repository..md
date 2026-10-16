Review this complete AutoSys Local CLI repository.  
  
First inspect the codebase and provide a concise improvement plan. Then implement the approved improvements.  
  
Requirements:  
  
1. Preserve all existing CLI commands and behavior.  
2. Review client.py, cli.py, configuration loading, error handling and tests.  
3. Confirm _request() correctly supports both:  
   - JSON AEWS responses  
   - plain-text JIL responses  
4. Improve HTTP error reporting, timeouts, retry/backoff, rate-limit handling,  
   TLS verification and structured logging.  
5. Never print credentials, tokens, authorization headers or .env values.  
6. Add parsing of JIL schedule fields:  
   date_conditions, days_of_week, start_times, run_calendar,  
   exclude_calendar, timezone and condition.  
7. Add a read-only next-run command that calculates the next scheduled time  
   only when the JIL contains a deterministic schedule.  
8. Clearly report when the next execution cannot be predicted because the job  
   is event-driven, condition-driven, calendar-dependent or a file watcher.  
9. Add unit tests for JSON responses, text/JIL responses, HTTP errors,  
   malformed JSON and schedule parsing.  
10. Do not call a live production AutoSys instance from tests.  
11. Do not execute force-start, hold, ice, off-hold, off-ice, kill or other  
    state-changing actions.  
12. Run the test suite and show me:  
    - files changed  
    - test results  
    - remaining risks  
    - commands for local validation  
  
Before making edits, show the implementation plan and wait for my approval.  
  
  
Proceed with the implementation. Keep every change reviewable and run the  
tests after editing. Do not modify .env or include credentials in output.  
  
# AutoSys Local CLI instructions  
  
- Python code must include type hints.  
- Preserve backward compatibility for existing commands.  
- Never log credentials, tokens, authorization headers or environment values.  
- Never access production AutoSys during automated tests.  
- Mock all AEWS HTTP calls in tests.  
- State-changing AutoSys operations require explicit confirmation.  
- JSON and plain-text JIL responses must be handled separately.  
- Use retry with bounded exponential backoff for transient failures.  
- Treat HTTP 401/403, 404, 429 and 5xx responses distinctly.  
- Use timezone-aware datetime objects.  
- Never claim an event-driven job has a deterministic next-run time.  
- Run formatting, static checks and tests after changes.  
