from argparse import Namespace
import runpy

import pytest

from autosys_phase1 import aews_check, reset_job_times, stream_refresh, summary_refresh
from autosys_phase1.config import load_settings


@pytest.mark.parametrize(
    ("module", "task_name"),
    [
        (reset_job_times, "reset"),
        (stream_refresh, "stream"),
        (summary_refresh, "summary"),
    ],
)
def test_procedure_entrypoint_delegates_to_named_task(monkeypatch, module, task_name):
    calls = []
    monkeypatch.setattr(module, "run_named_task", lambda name: calls.append(name) or 0)

    assert module.main() == 0
    assert calls == [task_name]


def test_aews_check_main_uses_offline_fixture(monkeypatch, capsys):
    settings = load_settings("config/settings.yaml")
    monkeypatch.setattr(
        aews_check,
        "_arguments",
        lambda: Namespace(
            instance="pb3",
            job="CREEP_CTR_DAILY_LOAD",
            config="config/settings.yaml",
            env_file=".env",
            mock_fixture="config/mock_job_runs.json",
        ),
    )
    monkeypatch.setattr(aews_check, "load_settings", lambda path: settings)

    assert aews_check.main() == 0
    output = capsys.readouterr().out
    assert '"result": "AEWS_TEST_PASSED"' in output
    assert '"instance": "PB3"' in output
    assert '"database_updated": false' in output


def test_package_main_module_exits_with_source_check_result(monkeypatch):
    monkeypatch.setattr("autosys_phase1.source_check.main", lambda: 7)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("autosys_phase1.__main__", run_name="__main__")
    assert exc.value.code == 7

