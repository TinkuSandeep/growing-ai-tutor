Read .github/copilot-instructions.md and follow it throughout this task.  
  
Inspect the complete Batch Transformation v1.6 repository, but do not modify  
any files yet.  
  
First:  
  
1. Explain the end-to-end workflow in the current code.  
2. Identify how jobs are retrieved from the database.  
3. Identify how each AEWS/AutoSys instance is called.  
4. Trace how job status, start time and end time are written to the database.  
5. Review post-write database verification.  
6. Review job_eod_date and NULL-handling logic.  
7. Review reset_job_times, source_check, summary_refresh and stream_refresh.  
8. Identify missing tests, especially for source_check and entry-point modules.  
9. Identify security, reliability, logging and concurrency risks.  
10. Check whether failures always produce a non-zero exit code.  
  
Return:  
  
- Findings ranked Critical, High, Medium and Low  
- Evidence with filenames and function names  
- Files you recommend changing  
- Tests that should be added  
- Backward-compatibility risks  
- A phased implementation plan  
  
You may run read-only local inspection and existing unit tests. Do not connect  
to production AEWS or SQL Server. Do not execute stored procedures, modify  
.env, change deployment files, display credentials or edit any files.  
  
Wait for my approval before making changes.  
