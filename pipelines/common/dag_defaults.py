"""Shared Airflow DAG default_args factory."""

from datetime import datetime, timedelta


DEFAULT_OWNER = "data-team"
DEFAULT_RETRIES = 2
DEFAULT_RETRY_DELAY = timedelta(minutes=5)
DEFAULT_START_DATE = datetime(2024, 1, 1)


def build_default_args(
    owner: str = DEFAULT_OWNER,
    retries: int = DEFAULT_RETRIES,
    retry_delay: timedelta = DEFAULT_RETRY_DELAY,
    start_date: datetime = DEFAULT_START_DATE,
    **extra,
) -> dict:
    """Return a default_args dict for Airflow DAGs.

    Any additional keyword arguments are merged into the result, so
    DAG-specific overrides (``depends_on_past``, ``email_on_failure``,
    etc.) can be passed directly.
    """
    args: dict = {
        "owner": owner,
        "retries": retries,
        "retry_delay": retry_delay,
        "start_date": start_date,
    }
    args.update(extra)
    return args
