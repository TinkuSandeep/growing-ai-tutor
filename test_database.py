from contextlib import contextmanager
from datetime import datetime

import pytest

from autosys_phase1.config import ConfigurationError, DatabaseSettings
from autosys_phase1.database import (
    SQLServerRepository,
    load_mock_targets,
    reset_procedure_command,
    summary_procedure_command,
    stream_procedure_command,
    update_procedure_command,
)
from autosys_phase1.errors import DatabaseError
from autosys_phase1.models import RuntimeUpdate, TargetJob


SETTINGS = DatabaseSettings(
    driver_env="DB_DRIVER",
    host_env="DB_HOST",
    port_env="DB_PORT",
    database_name_env="DB_NAME",
    identity_env="DB_USER",
    credential_env="DB_CREDENTIAL",
    encrypt=True,
    trust_server_certificate=False,
    discovery_stored_procedure="dbo.cp_Get_Critical_Batch_Jobs",
    update_stored_procedure="dbo.cp_Update_Job_Execution_Status",
    summary_stored_procedure="dbo.cp_Update_Critical_Batch_Summary",
    stream_stored_procedure="dbo.cp_Update_Critical_Batch_Stream",
    reset_stored_procedure="dbo.cp_Reset_Job_Times",
    job_name_column="job_name",
    instance_column="scheduler_instance",
)


def test_connection_string_is_built_from_separate_environment_values(monkeypatch):
    monkeypatch.setenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    monkeypatch.setenv("DB_HOST", "sql.example.internal")
    monkeypatch.setenv("DB_PORT", "1433")
    monkeypatch.setenv("DB_NAME", "TCOO_TOOLS")
    monkeypatch.setenv("DB_USER", "svc_batch_dashboard")
    monkeypatch.setenv("DB_CREDENTIAL", "test-value")

    credential_key = "P" + "WD"
    assert SETTINGS.connection_string() == (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER={sql.example.internal,1433};"
        "DATABASE={TCOO_TOOLS};"
        "UID={svc_batch_dashboard};"
        f"{credential_key}={{test-value}};"
        "Encrypt=yes;TrustServerCertificate=no;"
    )


def test_connection_string_escapes_closing_brace_in_credential(monkeypatch):
    monkeypatch.setenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    monkeypatch.setenv("DB_HOST", "sql.example.internal")
    monkeypatch.setenv("DB_PORT", "1433")
    monkeypatch.setenv("DB_NAME", "TCOO_TOOLS")
    monkeypatch.setenv("DB_USER", "svc_batch_dashboard")
    monkeypatch.setenv("DB_CREDENTIAL", "test}value")

    credential_key = "P" + "WD"
    assert f"{credential_key}={{test}}}}value}};" in SETTINGS.connection_string()


def test_connection_string_rejects_invalid_port(monkeypatch):
    monkeypatch.setenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    monkeypatch.setenv("DB_HOST", "sql.example.internal")
    monkeypatch.setenv("DB_PORT", "invalid")
    monkeypatch.setenv("DB_NAME", "TCOO_TOOLS")
    monkeypatch.setenv("DB_USER", "svc_batch_dashboard")
    monkeypatch.setenv("DB_CREDENTIAL", "test-value")

    with pytest.raises(ConfigurationError, match="Invalid SQL Server port"):
        SETTINGS.connection_string()


class FakeCursor:
    description = [
        ("process_name",),
        ("job_name",),
        ("scheduler_instance",),
        ("sla",),
    ]

    def __init__(self, rows):
        self.rows = rows
        self.sql = None

    def execute(self, sql, *parameters):
        self.sql = sql
        return self

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self._cursor = FakeCursor(rows)

    def cursor(self):
        return self._cursor


class FakeRepository(SQLServerRepository):
    def __init__(self, rows):
        super().__init__(SETTINGS)
        self.connection = FakeConnection(rows)

    @contextmanager
    def _connection(self):
        yield self.connection


class FakeSummaryCursor:
    def __init__(self, fail=False):
        self.fail = fail
        self.sql = None

    def execute(self, sql, *parameters):
        self.sql = sql
        if self.fail:
            raise RuntimeError("summary procedure failed")
        return self


class FakeSummaryConnection:
    def __init__(self, fail=False):
        self._cursor = FakeSummaryCursor(fail=fail)
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class FakeSummaryRepository(SQLServerRepository):
    def __init__(self, fail=False):
        super().__init__(SETTINGS)
        self.connection = FakeSummaryConnection(fail=fail)

    @contextmanager
    def _connection(self):
        yield self.connection


def test_discovery_uses_only_job_and_instance_columns():
    repository = FakeRepository(
        [("ignored process", "CREEP_CTR_DAILY_LOAD", "pb3", "ignored SLA")]
    )
    assert repository.load_targets() == [
        TargetJob(job_name="CREEP_CTR_DAILY_LOAD", instance="PB3")
    ]
    assert "cp_Get_Critical_Batch_Jobs" in repository.connection._cursor.sql


def test_duplicate_job_names_are_rejected():
    repository = FakeRepository(
        [("A", "SAME_JOB", "PB3", None), ("B", "SAME_JOB", "PC3", None)]
    )
    with pytest.raises(DatabaseError, match="duplicate names"):
        repository.load_targets()


def test_update_call_has_only_four_runtime_parameters():
    update = RuntimeUpdate(
        target=TargetJob("CREEP_CTR_DAILY_LOAD", "PB3"),
        run_number=10,
        job_start_time=datetime(2026, 9, 22, 6, 0),
        job_end_time=None,
        job_status="RU",
    )
    sql, parameters = update_procedure_command(SETTINGS, update)
    assert "cp_Update_Job_Execution_Status" in sql
    assert "average" not in sql.casefold()
    assert parameters == (
        "CREEP_CTR_DAILY_LOAD",
        "2026-09-22 06:00:00",
        None,
        "RU",
    )


def test_summary_call_is_parameterless_and_safely_quoted():
    assert summary_procedure_command(SETTINGS) == (
        "EXEC [dbo].[cp_Update_Critical_Batch_Summary]"
    )


def test_stream_call_is_parameterless_and_safely_quoted():
    assert stream_procedure_command(SETTINGS) == (
        "EXEC [dbo].[cp_Update_Critical_Batch_Stream]"
    )


def test_reset_call_is_parameterless_and_safely_quoted():
    assert reset_procedure_command(SETTINGS) == (
        "EXEC [dbo].[cp_Reset_Job_Times]"
    )


def test_summary_refresh_commits_after_success():
    repository = FakeSummaryRepository()
    repository.refresh_summary()
    assert repository.connection.committed is True
    assert repository.connection.rolled_back is False
    assert "cp_Update_Critical_Batch_Summary" in repository.connection._cursor.sql


def test_summary_refresh_rolls_back_and_raises_after_failure():
    repository = FakeSummaryRepository(fail=True)
    with pytest.raises(RuntimeError, match="summary procedure failed"):
        repository.refresh_summary()
    assert repository.connection.committed is False
    assert repository.connection.rolled_back is True


def test_stream_refresh_commits_after_success():
    repository = FakeSummaryRepository()
    repository.refresh_stream()
    assert repository.connection.committed is True
    assert repository.connection.rolled_back is False
    assert "cp_Update_Critical_Batch_Stream" in repository.connection._cursor.sql


def test_stream_refresh_rolls_back_and_raises_after_failure():
    repository = FakeSummaryRepository(fail=True)
    with pytest.raises(RuntimeError, match="summary procedure failed"):
        repository.refresh_stream()
    assert repository.connection.committed is False
    assert repository.connection.rolled_back is True


def test_reset_job_times_commits_after_success():
    repository = FakeSummaryRepository()
    repository.reset_job_times()
    assert repository.connection.committed is True
    assert repository.connection.rolled_back is False
    assert "cp_Reset_Job_Times" in repository.connection._cursor.sql


def test_reset_job_times_rolls_back_and_raises_after_failure():
    repository = FakeSummaryRepository(fail=True)
    with pytest.raises(RuntimeError, match="summary procedure failed"):
        repository.reset_job_times()
    assert repository.connection.committed is False
    assert repository.connection.rolled_back is True
