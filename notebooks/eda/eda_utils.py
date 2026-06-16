"""Shared EDA helpers used across all exploratory notebooks.

Import this module at the top of every EDA notebook to avoid copy-pasting
the same setup/analysis blocks.

    from eda_utils import setup_display, load_and_summarize, ...
"""

from __future__ import annotations

from typing import Sequence

import pandas as pd


# ---------------------------------------------------------------------------
# Display setup
# ---------------------------------------------------------------------------

def setup_display(max_columns: int | None = None, max_rows: int = 200) -> None:
    """Configure pandas display options used by every EDA notebook."""
    pd.set_option("display.max_columns", max_columns)
    pd.set_option("display.max_rows", max_rows)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_and_summarize(filepath: str) -> pd.DataFrame:
    """Read a CSV into a DataFrame and print row/column counts."""
    df = pd.read_csv(filepath)
    print(f"Filas: {df.shape[0]}")
    print(f"Columnas: {df.shape[1]}")
    return df


# ---------------------------------------------------------------------------
# Null analysis
# ---------------------------------------------------------------------------

def compute_null_percentages(df: pd.DataFrame) -> pd.Series:
    """Return column-wise null percentages sorted descending."""
    return (
        df.isnull()
        .mean()
        .mul(100)
        .sort_values(ascending=False)
    )


def categorize_nulls(
    null_pct: pd.Series,
    high_threshold: float = 50.0,
    medium_threshold: float = 20.0,
) -> dict[str, pd.Series]:
    """Split null percentages into high / medium / low buckets.

    Returns a dict with keys ``"high"``, ``"medium"``, ``"low"``
    and prints a summary.
    """
    high = null_pct[null_pct > high_threshold]
    medium = null_pct[(null_pct > medium_threshold) & (null_pct <= high_threshold)]
    low = null_pct[(null_pct > 0) & (null_pct <= medium_threshold)]

    print(f"Columnas > {high_threshold}%: {len(high)}")
    print(f"Columnas entre {medium_threshold}%-{high_threshold}%: {len(medium)}")
    print(f"Columnas < {medium_threshold}%: {len(low)}")

    return {"high": high, "medium": medium, "low": low}


# ---------------------------------------------------------------------------
# Uniqueness / duplicates
# ---------------------------------------------------------------------------

def print_key_stats(df: pd.DataFrame, key_columns: Sequence[str]) -> None:
    """Print unique counts and duplicates for the given key columns."""
    for col in key_columns:
        n_unique = df[col].nunique()
        n_dups = df[col].duplicated().sum()
        print(f"{col}  \u2014  únicos: {n_unique}, duplicados: {n_dups}")


# ---------------------------------------------------------------------------
# Categorical profiling
# ---------------------------------------------------------------------------

def list_categorical_columns(df: pd.DataFrame) -> list[str]:
    """Return names of object/string-dtype columns."""
    return df.select_dtypes(include=["object", "string"]).columns.tolist()


def print_categorical_uniques(df: pd.DataFrame) -> None:
    """Print the number of unique values for each categorical column."""
    for col in list_categorical_columns(df):
        print(f"{col}: {df[col].nunique()}")
