**Batch Transformation v1.6 — GitHub Copilot Instructions**  
  
**Purpose**  
  
This repository implements the Batch Transformation v1.6 workflow. It retrieves configured AutoSys jobs from SQL Server, collects execution information from the appropriate AEWS/AutoSys scheduler instance, writes verified results to the target database, and runs downstream refresh procedures.  
  
Treat this application as production-support software. Correctness, diagnosability, backward compatibility, and protection of authentication data are more important than minimizing code size.  
  
**Repository scope**  
  
The main Python package is src/autosys_phase1 and includes components such as:  
  
	●	__main__.py  
	●	aews.py  
	●	aews_check.py  
	●	config.py  
	●	database.py  
	●	errors.py  
	●	models.py  
	●	procedure_runner.py  
	●	reset_job_times.py  
	●	source_check.py  
	●	status.py  
	●	stream_refresh.py  
	●	summary_refresh.py  
	●	transform.py  
  
Before proposing changes, inspect the actual repository because filenames and implementations can evolve.  
  
**Copilot working behavior**  
  
When asked to change this repository:  
  
	1.	Inspect the relevant source, tests, configuration, packaging, and deployment entry points before editing.  
	2.	State assumptions and provide a concise implementation plan.  
	3.	Identify the files that will be modified.  
	4.	Wait for approval when the user explicitly requests a review-first workflow.  
	5.	Make focused changes and avoid unrelated rewrites.  
	6.	Preserve existing public functions, command-line arguments, module names, output keys, deployment commands, and stored-procedure contracts unless a breaking change is explicitly approved.  
	7.	Run the relevant tests after editing.  
	8.	Summarize changed files, test results, remaining risks, and local validation commands.  
	9.	Never claim a test passed unless it was actually executed successfully.  
	10.	If a required dependency or environment is unavailable, report that limitation clearly.  
  
**Protected files and data**  
  
Do not read, display, rewrite, or commit sensitive values from:  
  
	●	.env  
	●	environment variables containing authentication values  
	●	Kubernetes or OpenShift Secrets  
	●	service-account credentials  
	●	database connection strings  
	●	AEWS authentication headers, cookies, or tokens  
	●	certificate private keys  
  
Do not place authentication data in source code, tests, logs, reports, fixtures, screenshots, exception messages, or command history.  
  
Configuration examples must use placeholders such as:  
  
${AEWS_USER}  
  
${AEWS_CREDENTIAL}  
  
${DB_USER}  
  
${DB_CREDENTIAL}  
  
**Change boundaries**  
  
Unless explicitly authorized:  
  
	●	Do not modify SQL Server tables, views, stored procedures, schemas, indexes, permissions, or data.  
	●	Do not change stored-procedure names or parameter contracts.  
	●	Do not change Kubernetes/OpenShift deployment resources, ConfigMaps, Secrets, image tags, or AutoSys JIL.  
	●	Do not connect automated tests to live AutoSys, AEWS, SQL Server, OCP, SMTP, or other production services.  
	●	Do not execute force-start, hold, ice, off-hold, off-ice, kill, terminate, update, insert, delete, or other external state-changing operations.  
	●	Do not delete existing diagnostics or compatibility behavior without explaining the replacement.  
  
**Architecture and workflow expectations**  
  
The expected high-level workflow is:  
  
	1.	Load and validate configuration.  
	2.	Generate one unique run_id for the complete execution.  
	3.	Retrieve configured jobs from the source stored procedure.  
	4.	Validate each job target, scheduler instance, and required field.  
	5.	Query the appropriate AEWS instance.  
	6.	Normalize status and timezone-aware timestamps.  
	7.	Attempt the target database update.  
	8.	Verify the committed target values.  
	9.	Produce a truthful per-job outcome and overall result.  
	10.	Run downstream summary/stream refresh only when its prerequisite succeeds.  
	11.	Exit with a meaningful process status.  
  
Never report overall success merely because the AEWS request succeeded or the stored procedure executed without raising an exception.  
  
**Configuration rules**  
  
	●	Keep configuration externalized through YAML and environment variables.  
	●	Do not hard-code job names, scheduler instances, database hosts, usernames, URLs, namespaces, or environment-specific paths.  
	●	Validate configuration at startup and fail before processing jobs if mandatory settings are absent or invalid.  
	●	Error messages may name the missing configuration key but must not print its value.  
	●	Support multiple scheduler instances using the existing mapping/configuration model.  
	●	Preserve the established local and OCP configuration mechanisms.  
	●	Use explicit defaults only when they are safe and documented.  
  
**Command-line safety**  
  
	●	Use argparse with explicit argument definitions and constrained choices where practical.  
	●	Treat file paths and job names as data, never as shell fragments.  
	●	Do not construct shell commands from unsanitized command-line values.  
	●	Do not invoke commands with shell=True unless explicitly justified and reviewed.  
	●	Validate paths before reading or writing.  
	●	Preserve dry-run behavior when present.  
	●	State-changing behavior must require an explicit option; it must never be the default.  
	●	Return a non-zero exit code for configuration failure, AEWS collection failure, database write failure, verification failure, or downstream procedure failure.  
  
**AEWS/AutoSys client requirements**  
  
**Request handling**  
  
	●	Use a shared requests.Session or the repository’s established client abstraction.  
	●	Apply explicit connect/read timeouts.  
	●	Validate TLS using the configured corporate CA bundle in production.  
	●	Do not disable TLS warnings as a permanent solution.  
	●	Do not log request authorization data.  
	●	Include scheduler instance, HTTP method, sanitized endpoint name, attempt number, duration, and result in diagnostic logs.  
  
**Response handling**  
  
	●	Validate successful HTTP status codes explicitly.  
	●	Distinguish JSON endpoints from plain-text/JIL endpoints.  
	●	For JSON endpoints, reject unexpected non-JSON responses with a clear sanitized error.  
	●	Limit response-body excerpts in errors and ensure they cannot expose credentials.  
	●	Treat an empty successful response according to the documented endpoint contract.  
	●	Preserve server-provided status information needed for diagnosis.  
  
**Retry behavior**  
  
	●	Retry only transient failures such as connection errors, timeouts, HTTP 429, and selected 5xx responses.  
	●	Do not automatically retry HTTP 400, 401, 403, or 404 responses.  
	●	Honor a valid Retry-After header.  
	●	Use bounded exponential backoff with optional jitter.  
	●	Cap both retry count and maximum delay.  
	●	Log each retry without logging authentication data.  
	●	Track request attempts, retries, HTTP 429 responses, failures, and total API duration.  
  
**Status and time normalization**  
  
	●	Preserve the original AEWS status and expose the normalized dashboard status separately when appropriate.  
	●	Use timezone-aware datetime values.  
	●	Do not compare naive and timezone-aware timestamps.  
	●	Record which timezone was used for conversions.  
	●	Handle missing start/end timestamps without manufacturing values.  
	●	A successful status without required timestamps must be explicitly reported as incomplete data when the target requires those timestamps.  
  
**JIL and next-run calculations**  
  
When JIL support is added or used:  
  
	●	Retrieve plain-text JIL without attempting JSON parsing.  
	●	Parse fields such as date_conditions, days_of_week, start_times, run_calendar, exclude_calendar, timezone, condition, and job type.  
	●	Use a timezone database that correctly handles daylight-saving transitions.  
	●	A job with deterministic start_times and days may have a calculated next scheduled time.  
	●	Label locally calculated values as derived from JIL, not as an authoritative AEWS next-run response.  
	●	Do not claim a deterministic next run for jobs driven by predecessors, conditions, events, file watchers, calendars that cannot be resolved, manual actions, or external triggers.  
	●	Report the calculation source and confidence/reason, for example JIL_START_TIMES or NOT_DETERMINISTIC_CONDITION_DRIVEN.  
	●	Hold, ice, scheduler outages, calendar changes, or runtime conditions may prevent a calculated schedule from executing; preserve this distinction.  
  
**Database requirements**  
  
**Connections and transactions**  
  
	●	Use parameterized queries and stored-procedure calls.  
	●	Never build SQL using string concatenation of external values.  
	●	Use explicit transaction boundaries for write operations.  
	●	Commit only after the intended write succeeds.  
	●	Roll back on every database exception.  
	●	Close cursors and connections reliably using context managers or finally blocks.  
	●	Configure database timeouts where supported.  
  
**Stored-procedure handling**  
  
	●	Preserve all existing procedure names, parameter order, parameter types, and result-set expectations.  
	●	Treat procedure execution and data verification as separate stages.  
	●	A procedure returning without exception does not prove that a target row was updated.  
	●	Capture safe return codes, output parameters, row counts, and result-set information when available.  
	●	If several result sets are possible, consume them according to the existing driver contract.  
  
**Post-write verification**  
  
After a write, verify the target using stable identifiers such as scheduler instance and exact job name. Compare the committed database values with the normalized AEWS values.  
  
Use explicit outcomes:  
  
	●	DB_UPDATED  
	●	DB_ALREADY_CORRECT  
	●	DB_MISMATCHED  
	●	DB_TARGET_NOT_FOUND  
	●	DB_DUPLICATE_TARGET  
	●	DB_WRITE_FAILED  
	●	DB_VERIFICATION_FAILED  
  
Verification must safely compare:  
  
	●	scheduler instance  
	●	job name  
	●	job status  
	●	start time  
	●	end time  
	●	applicable end-of-day value  
	●	last-updated metadata when relevant  
  
Do not report INGESTION_PASSED if a required database target is missing, duplicated, mismatched, unverified, or failed.  
  
**NULL and end-of-day handling**  
  
	●	Treat SQL NULL according to business meaning; do not assume it equals a date or empty string.  
	●	New jobs may legitimately begin with job_eod_date IS NULL.  
	●	Avoid SQL predicates where NULL unintentionally produces UNKNOWN and skips eligible rows.  
	●	Distinguish between a new/unprocessed job, a completed job, and a job whose reset did not occur.  
	●	Do not overwrite completed execution data merely because a reset job is delayed.  
	●	Log when a record is excluded due to end-of-day rules.  
	●	Log the target job, current job_eod_date, expected processing date, and exclusion reason without logging unrelated row content.  
  
**Reset-job behavior**  
  
	●	Treat the reset workflow as a separate observable operation.  
	●	Log reset start, completion, duration, affected row count, and failure reason.  
	●	Detect when the reset has not completed by its expected time.  
	●	The ingestion workflow must not silently interpret stale end-of-day values as successful current-day processing.  
	●	If safe fallback behavior exists, make it explicit and tested.  
	●	If reset state makes an update ambiguous, fail or mark the job as skipped with a precise reason rather than manufacturing success.  
  
**Concurrency and overlap protection**  
  
	●	Prevent a new ingestion execution from running concurrently with an active previous execution.  
	●	Prefer the existing AutoSys scheduling controls when available.  
	●	If application-level protection is added, use a safe cross-process mechanism appropriate to the runtime environment.  
	●	Do not rely only on an in-memory flag because different pods/processes cannot share it.  
	●	Log lock acquisition, contention, owner/run identifier, and release.  
	●	A skipped overlapping run must produce a clear outcome and exit behavior.  
	●	Always release locally owned locks in a finally block.  
  
**Logging and observability**  
  
Use structured, searchable logs. Generate one run_id at process start and include it throughout the workflow.  
  
Where applicable, include:  
  
	●	event  
	●	run_id  
	●	component/module  
	●	scheduler instance  
	●	job name  
	●	sanitized procedure name  
	●	attempt number  
	●	elapsed milliseconds  
	●	AEWS status  
	●	expected database values  
	●	actual database values  
	●	outcome/reason code  
	●	requested/processed/succeeded/failed counts  
  
Recommended event names include:  
  
	●	INGESTION_STARTED  
	●	CONFIG_VALIDATED  
	●	SOURCE_JOBS_RETRIEVED  
	●	AEWS_REQUEST_ATTEMPT  
	●	AEWS_REQUEST_RETRY  
	●	AEWS_REQUEST_COMPLETED  
	●	AEWS_JOB_COLLECTED  
	●	DB_UPDATE_ATTEMPT  
	●	DB_UPDATE_COMPLETED  
	●	DB_VERIFY_ALREADY_CORRECT  
	●	DB_VERIFY_MISMATCH  
	●	DB_TARGET_NOT_FOUND  
	●	DB_DUPLICATE_TARGET  
	●	RESET_STARTED  
	●	RESET_COMPLETED  
	●	PROCEDURE_STARTED  
	●	PROCEDURE_COMPLETED  
	●	INGESTION_COMPLETED  
  
Logs must explain why a job did not update. Avoid vague messages such as failed without stage, target, and reason.  
  
Never log:  
  
	●	authentication values  
	●	authorization headers  
	●	cookies or tokens  
	●	complete connection strings  
	●	entire environment dictionaries  
	●	certificate private material  
	●	unrestricted AEWS or database response bodies  
  
**Result and exit semantics**  
  
The final report must accurately distinguish collection from persistence.  
  
Useful aggregate fields include:  
  
	●	result  
	●	run_id  
	●	requested  
	●	api_succeeded  
	●	api_failed  
	●	database_attempted  
	●	database_updated  
	●	database_already_correct  
	●	database_mismatched  
	●	database_not_found  
	●	database_duplicate_targets  
	●	database_failed  
	●	api_request_attempts  
	●	api_retries  
	●	api_rate_limit_responses  
	●	duration_ms  
	●	sanitized error summary  
  
Overall success requires all mandatory stages to succeed and be verified. Partial collection or partial database updates must not be labeled as complete success.  
  
**Downstream refresh procedures**  
  
	●	Run summary/stream refresh only after its configured prerequisite succeeds.  
	●	Do not run a dependent refresh after failed or unverified ingestion unless explicitly configured and documented.  
	●	Log procedure start, completion, duration, and sanitized failure details.  
	●	Return a non-zero process exit code when a mandatory downstream procedure fails.  
	●	Preserve the established AutoSys dependency chain between ingestion and refresh jobs.  
  
**Error handling**  
  
	●	Use specific repository exception types rather than broad unclassified exceptions.  
	●	Preserve the original exception as the cause when wrapping errors.  
	●	Do not suppress exceptions that should change the process result.  
	●	Catch errors at boundaries where context can be added or cleanup is required.  
	●	Error messages must identify the failed stage and target without exposing sensitive values.  
	●	Categorize configuration, authentication, authorization, rate-limit, network, response-format, database, verification, and downstream-procedure failures separately.  
  
**Testing requirements**  
  
Tests must be deterministic and isolated from external systems.  
  
**Required coverage**  
  
	●	configuration validation  
	●	status normalization  
	●	timestamp parsing and timezone conversion  
	●	JSON AEWS responses  
	●	plain-text JIL responses  
	●	empty responses  
	●	malformed JSON  
	●	timeouts and connection failures  
	●	HTTP 400/401/403/404/429/5xx handling  
	●	retry and Retry-After behavior  
	●	source job discovery  
	●	multiple scheduler instances  
	●	successful database update  
	●	already-correct database values  
	●	target not found  
	●	duplicate target  
	●	database mismatch  
	●	transaction rollback  
	●	job_eod_date IS NULL  
	●	stale end-of-day/reset scenarios  
	●	summary and stream refresh success/failure  
	●	command-line validation  
	●	non-zero exit codes  
	●	sensitive-value redaction  
	●	overlap protection  
  
**Entry-point coverage**  
  
Ensure tests exist for executable modules, including:  
  
	●	__main__.py  
	●	aews_check.py  
	●	reset_job_times.py  
	●	source_check.py  
	●	stream_refresh.py  
	●	summary_refresh.py  
	●	procedure_runner.py  
  
**Test isolation**  
  
	●	Mock all HTTP interactions.  
	●	Mock all database connections and cursors.  
	●	Mock time/sleep behavior for retry tests.  
	●	Never load real .env values.  
	●	Never call a live AEWS endpoint or production database.  
	●	Verify both returned results and emitted safe diagnostics.  
  
**Code-quality expectations**  
  
	●	Use Python type hints for public and internal functions where practical.  
	●	Prefer small functions with one responsibility.  
	●	Use dataclasses or existing typed models for structured data.  
	●	Avoid Any when a stable type can be defined without excessive complexity.  
	●	Keep I/O at application boundaries and business logic testable without external services.  
	●	Use pathlib.Path for filesystem paths.  
	●	Follow the repository’s formatter, linter, and test configuration.  
	●	Avoid adding a dependency when the standard library or an existing dependency is sufficient.  
	●	Document non-obvious business rules, especially end-of-day and verification behavior.  
  
**Review checklist**  
  
Before declaring work complete, confirm:  
  
	●	Existing commands remain compatible.  
	●	Stored-procedure contracts were not changed.  
	●	No sensitive value was added to code, tests, output, or logs.  
	●	JSON and text/JIL responses are handled correctly.  
	●	Retry behavior is bounded and safe.  
	●	Database writes use explicit commit/rollback behavior.  
	●	Database results are verified after writing.  
	●	NULL/end-of-day rules are tested.  
	●	Reset delay scenarios are observable.  
	●	Overlapping runs are prevented or clearly controlled.  
	●	Failed mandatory work returns a non-zero exit code.  
	●	All relevant tests were executed.  
	●	The final summary states what was and was not verified.  
  
**Standard review-first prompt**  
  
When the user asks for a complete review, follow this workflow:  
  
Inspect the entire Batch Transformation v1.6 repository. Do not edit files yet.  
  
Review architecture, AEWS calls, configuration, database writes, stored-procedure  
  
handling, post-write verification, NULL/end-of-day logic, reset behavior,  
  
concurrency protection, logs, exit codes, tests, packaging and deployment entry  
  
points.  
  
Return:  
  
1. Findings ranked by severity.  
  
2. Evidence with file and function names.  
  
3. Proposed files to change.  
  
4. Proposed tests.  
  
5. Backward-compatibility and operational risks.  
  
Do not access production services, execute stored procedures, modify .env,  
  
display credentials, or perform state-changing AutoSys operations. Wait for  
  
approval before editing files.  
  
**Standard implementation prompt**  
  
After the review plan is approved, follow this workflow:  
  
Implement only the approved Batch Transformation v1.6 changes.  
  
Preserve existing CLI commands, module entry points, database schemas,  
  
stored-procedure contracts and deployment behavior. Add or improve structured  
  
diagnostics, run_id correlation, truthful result classification, explicit  
  
commit/rollback behavior, post-write verification, safe argument validation,  
  
bounded retry handling and missing entry-point tests.  
  
Mock AEWS and SQL Server in all automated tests. Do not access production,  
  
modify .env, expose authentication values or perform state-changing AutoSys  
  
operations.  
  
Run the relevant test suite and report changed files, test results, local  
  
validation commands and remaining risks.  
