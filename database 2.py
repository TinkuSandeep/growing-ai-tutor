from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable, Iterator, Protocol
from zoneinfo import ZoneInfo

from .config import AutoSysSettings, DatabaseSettings
from .errors import DatabaseError
from .models import RuntimeUpdate, TargetJob


logger = logging.getLogger(__name__)
ET_ZONE = ZoneInfo("America/New_York")


def _to_sql_datetime(value: datetime | str | None) -> str | None:
    """Return the exact timestamp text expected by the target procedure.

    The stored procedure accepts ``YYYY-MM-DD HH:MM:SS`` successfully when
    executed in SSMS.  Normalize API timestamps to that format, without a
    ``T``, fractional seconds, ``Z``, or UTC offset.  ``None`` remains a real
    SQL NULL when bound by pyodbc.
    """
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip()
        if text.casefold() in {"", "null", "none"}:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DatabaseError(f"Unsupported target timestamp: {value!r}") from exc
    elif isinstance(value, datetime):
        parsed = value
    else:
        raise DatabaseError(
            f"Unsupported target timestamp type: {type(value).__name__}"
        )

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(ET_ZONE).replace(tzinfo=None)

    return parsed.strftime("%Y-%m-%d %H:%M:%S")


class RuntimeRepository(Protocol):
    def load_targets(self, autosys: AutoSysSettings) -> list[TargetJob]: ...
    def apply_updates(self, updates: Iterable[RuntimeUpdate]) -> int: ...


class SQLServerRepository:
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings

    @contextmanager
    def _connection(self) -> Iterator[object]:
        try:
            import pyodbc
        except ImportError as exc:
            raise DatabaseError(
                "pyodbc is required for SQL Server mode; "
                "install requirements-sqlserver.txt"
            ) from exc

        try:
            connection = pyodbc.connect(
                self.settings.connection_string(),
                autocommit=False,
            )
            yield connection
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(f"SQL Server operation failed: {exc}") from exc
        finally:
            if "connection" in locals():
                connection.close()

    def load_targets(self, autosys: AutoSysSettings) -> list[TargetJob]:
        sql = f"""
            SELECT app_id, batch_stream_name, job_name
            FROM {self.settings.quoted_table}
            WHERE scheduler = ?
            ORDER BY batch_stream_name, job_sequence, job_name
        """

        with self._connection() as connection:
            cursor = connection.cursor()
            rows = cursor.execute(sql, self.settings.scheduler_value).fetchall()

        return [
            TargetJob(
                app_id=str(row[0]).strip(),
                batch_stream_name=str(row[1]).strip(),
                job_name=str(row[2]).strip(),
                instance=autosys.instance_for(
                    str(row[0]).strip(),
                    str(row[2]).strip(),
                ),
            )
            for row in rows
        ]

    def apply_updates(self, updates: Iterable[RuntimeUpdate]) -> int:
        values = list(updates)
        if not values:
            return 0

        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                for update in values:
                    start_time = _to_sql_datetime(update.job_start_time)
                    end_time = _to_sql_datetime(update.job_end_time)

                    logger.info(
                        "Target update job=%s start=%r end=%r status=%s",
                        update.target.job_name,
                        start_time,
                        end_time,
                        update.job_status,
                    )

                    if self.settings.write_mode == "stored_procedure":
                        procedure = self.settings.quoted_stored_procedure

                        # Use named procedure parameters so a change in the
                        # procedure's declaration order cannot place status text
                        # into a datetime parameter.
                        sql = f"""
                            EXEC {procedure}
                                @job_name = ?,
                                @job_start_time = ?,
                                @job_end_time = ?,
                                @job_status = ?
                        """
                        parameters = (
                            update.target.job_name,
                            start_time,
                            end_time,
                            update.job_status,
                        )
                    else:
                        audit = ""
                        parameters = [
                            start_time,
                            end_time,
                            update.job_status,
                        ]
                        if self.settings.update_audit_columns:
                            audit = (
                                ", last_updated_date = SYSDATETIME(), "
                                "last_updated_by = ?"
                            )
                            parameters.append(self.settings.updated_by)

                        sql = f"""
                            UPDATE {self.settings.quoted_table}
                            SET job_start_time = ?,
                                job_end_time = ?,
                                job_status = ?
                                {audit}
                            WHERE app_id = ?
                              AND batch_stream_name = ?
                              AND job_name = ?
                        """
                        parameters.extend(
                            (
                                update.target.app_id,
                                update.target.batch_stream_name,
                                update.target.job_name,
                            )
                        )

                    cursor.execute(sql, *parameters)

                    if self.settings.write_mode == "direct" and cursor.rowcount != 1:
                        raise DatabaseError(
                            "Expected exactly one database row for "
                            f"{update.target.app_id}/{update.target.job_name}; "
                            f"got {cursor.rowcount}"
                        )

                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return len(values)


class MemoryRepository:
    def __init__(self, targets: list[TargetJob]):
        self.targets = targets
        self.updates: list[RuntimeUpdate] = []

    def load_targets(self, autosys: AutoSysSettings) -> list[TargetJob]:
        del autosys
        return list(self.targets)

    def apply_updates(self, updates: Iterable[RuntimeUpdate]) -> int:
        values = list(updates)
        self.updates.extend(values)
        return len(values)
