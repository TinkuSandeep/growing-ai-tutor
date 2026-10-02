from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from .aews import AEWSClient, MockAEWSClient, RuntimeSource
from .config import Settings, load_settings
from .database import SQLServerRepository, load_mock_targets
from .models import RuntimeUpdate, TargetJob
from .transform import latest_runtime_update


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Database-driven AutoSys AEWS runtime ingestion"
    )
    parser.add_argument("--settings", default="config/settings.yaml")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Call the configured target update procedure after every AEWS job passes",
    )
    parser.add_argument(
        "--mock-targets",
        help="Offline JSON replacement for cp_Get_Critical_Batch_Jobs",
    )
    parser.add_argument(
        "--mock-aews",
        help="Offline AEWS JSON fixture",
    )
    return parser.parse_args()


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def _configure_logging(log_path: Path | None) -> logging.Logger:
    logger = logging.getLogger("autosys_sp_ingestion")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    if log_path is not None:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def _job_result(target: TargetJob) -> dict[str, Any]:
    return {
        "job_name": target.job_name,
        "instance_name": target.instance,
        "source": "AEWS",
    }


def _validate_arguments(args: argparse.Namespace) -> None:
    if bool(args.mock_targets) != bool(args.mock_aews):
        raise SystemExit("Offline testing requires both --mock-targets and --mock-aews")
    if args.write and (args.mock_targets or args.mock_aews):
        raise SystemExit("--write cannot be combined with mock data")


def _output_paths(
    settings: Settings, started: datetime
) -> tuple[Path | None, Path | None]:
    if not settings.ingestion.file_output_enabled:
        return None, None

    stamp = started.strftime("%Y%m%d_%H%M%S_%f")
    output_dir = Path(settings.ingestion.output_directory)
    log_dir = Path(settings.ingestion.log_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    return (
        output_dir / f"autosys_ingestion_{stamp}.json",
        log_dir / f"autosys_ingestion_{stamp}.log",
    )


def _discover_targets(
    args: argparse.Namespace,
    repository: SQLServerRepository,
    settings: Settings,
) -> list[TargetJob]:
    targets = (
        load_mock_targets(args.mock_targets)
        if args.mock_targets
        else repository.load_targets()
    )
    minimum = settings.ingestion.require_minimum_target_count
    if minimum is not None and len(targets) < minimum:
        raise ValueError(
            f"Discovery returned {len(targets)} jobs; minimum required is {minimum}"
        )
    if not targets:
        raise ValueError("No jobs returned")
    return targets


def _create_runtime_source(
    args: argparse.Namespace, settings: Settings
) -> RuntimeSource:
    return (
        MockAEWSClient(args.mock_aews)
        if args.mock_aews
        else AEWSClient(settings.autosys)
    )


def _collect_runtime_updates(
    targets: list[TargetJob],
    source: RuntimeSource,
    settings: Settings,
    logger: logging.Logger,
) -> tuple[list[dict[str, Any]], list[RuntimeUpdate], int]:
    results: list[dict[str, Any]] = []
    updates: list[RuntimeUpdate] = []
    failed = 0
    for target in targets:
        result = _job_result(target)
        try:
            payload = source.get_job_runs(target)
            update = latest_runtime_update(
                target,
                payload,
                settings.autosys.timezone,
                settings.autosys.store_naive_local_time,
            )
            updates.append(update)
            result.update(
                {
                    "run_number": update.run_number,
                    "job_start_time_et": update.job_start_time,
                    "job_end_time_et": update.job_end_time,
                    "job_status": update.job_status,
                    "result": "PASSED",
                }
            )
            logger.info(
                "PASSED instance=%s job=%s status=%s",
                target.instance,
                target.job_name,
                update.job_status,
            )
        except Exception as exc:
            failed += 1
            result.update({"result": "FAILED", "error": str(exc)})
            logger.error(
                "FAILED instance=%s job=%s error=%s",
                target.instance,
                target.job_name,
                exc,
            )
        results.append(result)
    return results, updates, failed


def _write_target_updates(
    write_enabled: bool,
    failed: int,
    updates: list[RuntimeUpdate],
    repository: SQLServerRepository,
    settings: Settings,
    logger: logging.Logger,
) -> tuple[int, str | None]:
    if not write_enabled:
        return 0, None
    if failed and settings.ingestion.abort_on_job_error:
        message = "Target write blocked because one or more AEWS jobs failed"
        logger.error("TARGET WRITE FAILED error=%s", message)
        return 0, message

    try:
        updated = repository.apply_updates(updates)
        logger.info(
            "Committed %d updates through %s",
            updated,
            settings.database.update_stored_procedure,
        )
        return updated, None
    except Exception as exc:
        logger.error("TARGET WRITE FAILED error=%s", exc)
        return 0, str(exc)


def _overall_result(write_enabled: bool, failed: int, write_error: str | None) -> str:
    outcomes = {
        (False, False): "DRY_RUN_PASSED",
        (False, True): "DRY_RUN_FAILED",
        (True, False): "INGESTION_PASSED",
        (True, True): "INGESTION_FAILED",
    }
    return outcomes[(write_enabled, bool(failed or write_error))]


def _build_report(
    *,
    args: argparse.Namespace,
    settings: Settings,
    started: datetime,
    completed: datetime,
    targets: list[TargetJob],
    results: list[dict[str, Any]],
    failed: int,
    updated: int,
    write_error: str | None,
    api_metrics: dict[str, int],
) -> dict[str, Any]:
    return {
        "version": "1.6.0",
        "result": _overall_result(args.write, failed, write_error),
        "mode": "write" if args.write else "dry_run",
        "job_catalog": (
            "mock" if args.mock_targets else settings.database.discovery_stored_procedure
        ),
        "started_at_et": started,
        "completed_at_et": completed,
        "requested": len(targets),
        "succeeded": len(targets) - failed,
        "failed": failed,
        "target_database_updated": updated > 0,
        "target_rows_updated": updated,
        "target_write_error": write_error,
        **api_metrics,
        "jobs": results,
    }


def _write_report(
    report: dict[str, Any],
    report_path: Path | None,
    log_path: Path | None,
    logger: logging.Logger,
) -> None:
    if report_path is not None:
        report_path.write_text(
            json.dumps(report, indent=2, default=_json_default), encoding="utf-8"
        )
        logger.info("Report written to %s", report_path)
        logger.info("Log written to %s", log_path)


def _print_summary(
    report: dict[str, Any], report_path: Path | None, log_path: Path | None
) -> None:
    report_location = str(report_path) if report_path is not None else None
    log_location = str(log_path) if log_path is not None else None
    print(
        json.dumps(
            {
                "result": report["result"],
                "requested": report["requested"],
                "succeeded": report["succeeded"],
                "failed": report["failed"],
                "target_database_updated": report["target_database_updated"],
                "target_rows_updated": report["target_rows_updated"],
                "target_write_error": report["target_write_error"],
                "api_request_attempts": report["api_request_attempts"],
                "api_retries": report["api_retries"],
                "api_rate_limit_responses": report["api_rate_limit_responses"],
                "report": report_location,
                "log": log_location,
            },
            indent=2,
        )
    )


def _print_failure(result: str, exc: Exception, logger: logging.Logger) -> int:
    logger.error("%s error=%s", result.replace("_", " "), exc)
    print(json.dumps({"result": result, "error": str(exc)}, indent=2))
    return 1


def main() -> int:
    args = _arguments()
    load_dotenv(args.env_file, override=False)
    settings = load_settings(args.settings)
    _validate_arguments(args)

    started = datetime.now(ZoneInfo(settings.autosys.timezone))
    report_path, log_path = _output_paths(settings, started)
    logger = _configure_logging(log_path)
    repository = SQLServerRepository(settings.database)

    try:
        targets = _discover_targets(args, repository, settings)
    except Exception as exc:
        return _print_failure("DISCOVERY_FAILED", exc, logger)

    try:
        source = _create_runtime_source(args, settings)
    except Exception as exc:
        return _print_failure("AEWS_INITIALIZATION_FAILED", exc, logger)

    logger.info(
        "Starting AutoSys-only %s for %d dynamically discovered jobs",
        "collection and target write" if args.write else "dry run",
        len(targets),
    )
    results, updates, failed = _collect_runtime_updates(
        targets, source, settings, logger
    )
    updated, write_error = _write_target_updates(
        args.write, failed, updates, repository, settings, logger
    )
    completed = datetime.now(ZoneInfo(settings.autosys.timezone))
    report = _build_report(
        args=args,
        settings=settings,
        started=started,
        completed=completed,
        targets=targets,
        results=results,
        failed=failed,
        updated=updated,
        write_error=write_error,
        api_metrics=source.metrics(),
    )
    _write_report(report, report_path, log_path, logger)
    _print_summary(report, report_path, log_path)
    return int(bool(failed or write_error))


if __name__ == "__main__":
    raise SystemExit(main())
