from argparse import Namespace
from dataclasses import replace
from datetime import datetime

import pytest

from autosys_phase1.config import load_settings
from autosys_phase1.models import RuntimeUpdate, TargetJob
from autosys_phase1 import source_check


def _args(**overrides):
    values = {
        "settings": "config/settings.yaml",
        "env_file": ".env",
        "write": False,
        "mock_targets": "config/mock_targets.json",
        "mock_aews": "config/mock_job_runs.json",
    }
    values.update(overrides)
    return Namespace(**values)


def test_main_completes_offline_collection(monkeypatch, capsys):
    monkeypatch.setattr(source_check, "_arguments", _args)

    assert source_check.main() == 0

    output = capsys.readouterr().out
    assert '"result": "DRY_RUN_PASSED"' in output
    assert '"requested": 2' in output
    assert '"succeeded": 2' in output


@pytest.mark.parametrize(
    "args",
    [
        _args(mock_aews=None),
        _args(mock_targets=None),
        _args(write=True),
    ],
)
def test_argument_validation_rejects_unsafe_combinations(args):
    with pytest.raises(SystemExit):
        source_check._validate_arguments(args)


def test_json_default_serializes_datetime_and_rejects_other_values():
    value = datetime(2026, 10, 5, 12, 30)
    assert source_check._json_default(value) == "2026-10-05T12:30:00"
    with pytest.raises(TypeError):
        source_check._json_default(object())


def test_output_paths_create_timestamped_files(tmp_path):
    settings = load_settings("config/settings.yaml")
    ingestion = replace(
        settings.ingestion,
        file_output_enabled=True,
        output_directory=str(tmp_path / "reports"),
        log_directory=str(tmp_path / "logs"),
    )
    report_path, log_path = source_check._output_paths(
        replace(settings, ingestion=ingestion), datetime(2026, 10, 5, 1, 2, 3)
    )

    assert report_path.parent.is_dir()
    assert log_path.parent.is_dir()
    assert "20261005_010203" in report_path.name


def test_discovery_rejects_empty_and_below_minimum_results():
    settings = load_settings("config/settings.yaml")

    class Repository:
        def load_targets(self):
            return []

    with pytest.raises(ValueError, match="No jobs returned"):
        source_check._discover_targets(
            _args(mock_targets=None, mock_aews=None), Repository(), settings
        )

    minimum_settings = replace(
        settings,
        ingestion=replace(settings.ingestion, require_minimum_target_count=2),
    )

    class OneTargetRepository:
        def load_targets(self):
            return [TargetJob("JOB_A", "PB3")]

    with pytest.raises(ValueError, match="minimum required is 2"):
        source_check._discover_targets(
            _args(mock_targets=None, mock_aews=None),
            OneTargetRepository(),
            minimum_settings,
        )


def test_collect_runtime_updates_records_success_and_failure():
    settings = load_settings("config/settings.yaml")
    targets = [TargetJob("GOOD_JOB", "PB3"), TargetJob("BAD_JOB", "PC3")]

    class Source:
        def get_job_runs(self, target):
            if target.job_name == "BAD_JOB":
                raise RuntimeError("controlled AEWS failure")
            return {
                "name": target.job_name,
                "runNum": 7,
                "runStartTime": "2026-10-05T10:00:00+00:00",
                "runEndTime": "2026-10-05T10:01:00+00:00",
                "status": 4,
                "strStatus": "SUCCESS",
            }

    logger = source_check._configure_logging(None)
    results, updates, failed = source_check._collect_runtime_updates(
        targets, Source(), settings, logger
    )

    assert failed == 1
    assert len(updates) == 1
    assert results[0]["result"] == "PASSED"
    assert results[1]["result"] == "FAILED"


def test_target_write_paths(monkeypatch):
    settings = load_settings("config/settings.yaml")
    logger = source_check._configure_logging(None)
    update = RuntimeUpdate(
        TargetJob("JOB_A", "PB3"),
        1,
        datetime(2026, 10, 5, 10),
        datetime(2026, 10, 5, 10, 1),
        "SU",
    )

    class Repository:
        def apply_updates(self, updates):
            return len(updates)

    assert source_check._write_target_updates(
        False, 0, [update], Repository(), settings, logger
    ) == (0, None)
    assert source_check._write_target_updates(
        True, 1, [update], Repository(), settings, logger
    )[1] is not None
    assert source_check._write_target_updates(
        True, 0, [update], Repository(), settings, logger
    ) == (1, None)

    class FailingRepository:
        def apply_updates(self, updates):
            raise RuntimeError("controlled write failure")

    assert source_check._write_target_updates(
        True, 0, [update], FailingRepository(), settings, logger
    ) == (0, "controlled write failure")


def test_main_reports_discovery_and_initialization_failures(monkeypatch, capsys):
    monkeypatch.setattr(source_check, "_arguments", _args)
    monkeypatch.setattr(
        source_check,
        "_discover_targets",
        lambda *args: (_ for _ in ()).throw(RuntimeError("discovery unavailable")),
    )
    assert source_check.main() == 1
    assert "DISCOVERY_FAILED" in capsys.readouterr().out

    monkeypatch.setattr(
        source_check,
        "_discover_targets",
        lambda *args: [TargetJob("JOB_A", "PB3")],
    )
    monkeypatch.setattr(
        source_check,
        "_create_runtime_source",
        lambda *args: (_ for _ in ()).throw(RuntimeError("AEWS unavailable")),
    )
    assert source_check.main() == 1
    assert "AEWS_INITIALIZATION_FAILED" in capsys.readouterr().out

