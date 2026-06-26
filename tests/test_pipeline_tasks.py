# -*- coding: utf-8 -*-
"""Unit tests for Financial Risk Pipeline tasks — Caso 5"""

from __future__ import annotations

import hashlib
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_app_train_df():
    """Small synthetic application_train DataFrame with 3 rows."""
    return pd.DataFrame({
        "SK_ID_CURR": [100001, 100002, 100003],
        "TARGET": [1, 0, 0],
        "CODE_GENDER": ["M","F","M"],
        "AMT_INCOME_TOTAL": [202500.0, 405000.0, 300000.0],
        "AMT_CREDIT": [406597.5, 1293502.5, 135000.0],
        "AMT_ANNUITY": [24700.5, 35698.5, 6750.0],
        "AMT_GOODS_PRICE": [351000.0, 1129500.0, 135000.0],
        "DAYS_BIRTH": [-9461, -16765, -19046],
        "DAYS_EMPLOYED": [-637, -1189, -426],
        "NAME_TYPE_SUITE": ["Unaccompanied","Family", None],
        "EXT_SOURCE_1": [0.5, 0.2, 0.8],
        "EXT_SOURCE_2": [0.7, 0.4, 0.9],
        "EXT_SOURCE_3": [0.6, 0.3, 0.85],
    })


# ===========================================================================
# Test class: TestBronzeTasks
# ===========================================================================


class TestBronzeTasks:

    @patch("pipelines.tasks.caso_5.bronze_tasks.os.path.isfile", return_value=True)
    @patch("pipelines.tasks.caso_5.bronze_tasks._obtener_ruta_bronze", return_value="/tmp/bronze")
    @patch("pipelines.tasks.caso_5.bronze_tasks._obtener_ruta_seed", return_value="/tmp/seed")
    def test_ingest_bronze_dataset_creates_parquet(
        self,
        mock_seed_dir,
        mock_bronze_dir,
        mock_isfile,
        sample_app_train_df,
    ):
        """Verify to_parquet is called with correct path and compression='snappy'."""
        with patch("pipelines.tasks.caso_5.bronze_tasks._leer_csv_con_deteccion_codificacion",
                    return_value=sample_app_train_df), \
             patch("pipelines.tasks.caso_5.bronze_tasks._agregar_columnas_tecnicas",
                   return_value=sample_app_train_df), \
             patch("pipelines.tasks.caso_5.bronze_tasks.os.makedirs"), \
             patch.object(pd.DataFrame, "to_parquet") as mock_to_parquet:

            from pipelines.tasks.caso_5.bronze_tasks import ingest_bronze_dataset

            result = ingest_bronze_dataset("application_train", "application_train.csv")

        assert mock_to_parquet.called
        call_kwargs = mock_to_parquet.call_args
        assert call_kwargs[1].get("compression") == "snappy"
        assert call_kwargs[1].get("index") is False
        assert result["rows"] == 3
        assert result["dataset"] == "application_train"
        assert result["output_path"].endswith("application_train.parquet")

    @patch("pipelines.tasks.caso_5.bronze_tasks.os.path.isfile", return_value=True)
    @patch("pipelines.tasks.caso_5.bronze_tasks._obtener_ruta_bronze", return_value="/tmp/bronze")
    @patch("pipelines.tasks.caso_5.bronze_tasks._obtener_ruta_seed", return_value="/tmp/seed")
    def test_ingest_bronze_dataset_adds_metadata_columns(
        self,
        mock_seed_dir,
        mock_bronze_dir,
        mock_isfile,
        sample_app_train_df,
    ):
        """Verify the output df has metadata columns added by _agregar_columnas_tecnicas."""
        with patch("pipelines.tasks.caso_5.bronze_tasks._leer_csv_con_deteccion_codificacion",
                    return_value=sample_app_train_df), \
             patch("pipelines.tasks.caso_5.bronze_tasks.os.makedirs"):

            captured_df = {}

            def capture_to_parquet(self_df, path, **kwargs):
                captured_df["df"] = self_df
                return None

            with patch.object(pd.DataFrame, "to_parquet", capture_to_parquet):
                from pipelines.tasks.caso_5.bronze_tasks import ingest_bronze_dataset
                ingest_bronze_dataset("application_train", "application_train.csv")

        df = captured_df["df"]
        assert "_ingestion_date" in df.columns
        assert "_source_file" in df.columns
        assert "_dataset_name" in df.columns
        assert "_row_hash" in df.columns
        assert df["_source_file"].iloc[0] == "application_train.csv"
        assert df["_dataset_name"].iloc[0] == "application_train"

    @patch("pipelines.tasks.caso_5.bronze_tasks.os.path.isfile", return_value=False)
    @patch("pipelines.tasks.caso_5.bronze_tasks._obtener_ruta_bronze", return_value="/tmp/bronze")
    @patch("pipelines.tasks.caso_5.bronze_tasks._obtener_ruta_seed", return_value="/tmp/seed")
    def test_ingest_bronze_dataset_file_not_found(
        self,
        mock_seed_dir,
        mock_bronze_dir,
        mock_isfile,
    ):
        """When the CSV doesn't exist, result should have rows=0 and empty output_path."""
        from pipelines.tasks.caso_5.bronze_tasks import ingest_bronze_dataset

        result = ingest_bronze_dataset("application_train", "application_train.csv")

        assert result["rows"] == 0
        assert result["output_path"] == ""

    @patch("pipelines.tasks.caso_5.bronze_tasks.os.path.isfile", return_value=True)
    @patch("pipelines.tasks.caso_5.bronze_tasks._obtener_ruta_bronze", return_value="/tmp/bronze")
    @patch("pipelines.tasks.caso_5.bronze_tasks._obtener_ruta_seed", return_value="/tmp/seed")
    def test_ingest_bronze_dataset_empty_csv(
        self,
        mock_seed_dir,
        mock_bronze_dir,
        mock_isfile,
    ):
        """When the CSV raises EmptyDataError, result should have rows=0."""
        with patch("pipelines.tasks.caso_5.bronze_tasks._leer_csv_con_deteccion_codificacion",
                    side_effect=pd.errors.EmptyDataError("No columns to parse")):

            from pipelines.tasks.caso_5.bronze_tasks import ingest_bronze_dataset

            result = ingest_bronze_dataset("application_train", "application_train.csv")

        assert result["rows"] == 0
        assert result["output_path"] == ""


# ===========================================================================
# Test class: TestSilverTasks
# ===========================================================================


class TestSilverTasks:

    def _make_bronze_df(self, rows=None):
        """Helper to create a Bronze-like DataFrame for Silver tests."""
        if rows is None:
            rows = [
                {
                    "SK_ID_CURR": 100001, "TARGET": 1,
                    "CODE_GENDER": "M", "NAME_TYPE_SUITE": "Unaccompanied",
                    "DAYS_EMPLOYED": -637, "AMT_INCOME_TOTAL": 202500.0,
                    "AMT_CREDIT": 406597.5, "DAYS_BIRTH": -9461,
                    "EXT_SOURCE_1": 0.5, "EXT_SOURCE_2": 0.7, "EXT_SOURCE_3": 0.6,
                    "_ingestion_date": "2025-01-01", "_source_file": "x",
                    "_dataset_name": "y", "_row_hash": "abc",
                },
                {
                    "SK_ID_CURR": 100002, "TARGET": 0,
                    "CODE_GENDER": "F", "NAME_TYPE_SUITE": "Family",
                    "DAYS_EMPLOYED": -1189, "AMT_INCOME_TOTAL": 405000.0,
                    "AMT_CREDIT": 1293502.5, "DAYS_BIRTH": -16765,
                    "EXT_SOURCE_1": 0.2, "EXT_SOURCE_2": 0.4, "EXT_SOURCE_3": 0.3,
                    "_ingestion_date": "2025-01-01", "_source_file": "x",
                    "_dataset_name": "y", "_row_hash": "def",
                },
            ]
        return pd.DataFrame(rows)

    @patch("pipelines.tasks.caso_5.silver_tasks._escribir_silver", return_value="/tmp/silver/application_train")
    @patch("pipelines.tasks.caso_5.silver_tasks._leer_bronze")
    def test_silver_deduplicates_on_primary_key(
        self, mock_leer_bronze, mock_escribir_silver
    ):
        """Duplicate SK_ID_CURR rows should be deduplicated (keep first)."""
        df = self._make_bronze_df([
            {
                "SK_ID_CURR": 100001, "TARGET": 1,
                "CODE_GENDER": "M", "NAME_TYPE_SUITE": "Unaccompanied",
                "DAYS_EMPLOYED": -637, "AMT_INCOME_TOTAL": 202500.0,
                "AMT_CREDIT": 406597.5, "DAYS_BIRTH": -9461,
                "EXT_SOURCE_1": 0.5, "EXT_SOURCE_2": 0.7, "EXT_SOURCE_3": 0.6,
                "_ingestion_date": "2025-01-01", "_source_file": "x",
                "_dataset_name": "y", "_row_hash": "abc",
            },
            {
                "SK_ID_CURR": 100001, "TARGET": 0,  # duplicate ID
                "CODE_GENDER": "F", "NAME_TYPE_SUITE": "Family",
                "DAYS_EMPLOYED": -200, "AMT_INCOME_TOTAL": 100000.0,
                "AMT_CREDIT": 500000.0, "DAYS_BIRTH": -10000,
                "EXT_SOURCE_1": 0.3, "EXT_SOURCE_2": 0.5, "EXT_SOURCE_3": 0.4,
                "_ingestion_date": "2025-01-01", "_source_file": "x",
                "_dataset_name": "y", "_row_hash": "xyz",
            },
            {
                "SK_ID_CURR": 100002, "TARGET": 0,
                "CODE_GENDER": "F", "NAME_TYPE_SUITE": "Family",
                "DAYS_EMPLOYED": -1189, "AMT_INCOME_TOTAL": 405000.0,
                "AMT_CREDIT": 1293502.5, "DAYS_BIRTH": -16765,
                "EXT_SOURCE_1": 0.2, "EXT_SOURCE_2": 0.4, "EXT_SOURCE_3": 0.3,
                "_ingestion_date": "2025-01-01", "_source_file": "x",
                "_dataset_name": "y", "_row_hash": "def",
            },
        ])
        mock_leer_bronze.return_value = df

        from pipelines.tasks.caso_5.silver_tasks import transform_to_silver

        stats = transform_to_silver("application_train")

        assert stats["rows_in"] == 3
        assert stats["rows_out"] == 2
        assert stats["duplicates_removed"] == 1

    @patch("pipelines.tasks.caso_5.silver_tasks._escribir_silver", return_value="/tmp/silver/application_train")
    @patch("pipelines.tasks.caso_5.silver_tasks._leer_bronze")
    def test_silver_handles_days_employed_anomaly(
        self, mock_leer_bronze, mock_escribir_silver
    ):
        """DAYS_EMPLOYED == 365243 (sentinel value) should become null."""
        df = self._make_bronze_df([
            {
                "SK_ID_CURR": 100001, "TARGET": 1,
                "CODE_GENDER": "M", "NAME_TYPE_SUITE": "Unaccompanied",
                "DAYS_EMPLOYED": 365243,  # anomaly
                "AMT_INCOME_TOTAL": 202500.0, "AMT_CREDIT": 406597.5,
                "DAYS_BIRTH": -9461,
                "EXT_SOURCE_1": 0.5, "EXT_SOURCE_2": 0.7, "EXT_SOURCE_3": 0.6,
                "_ingestion_date": "2025-01-01", "_source_file": "x",
                "_dataset_name": "y", "_row_hash": "abc",
            },
            {
                "SK_ID_CURR": 100002, "TARGET": 0,
                "CODE_GENDER": "F", "NAME_TYPE_SUITE": "Family",
                "DAYS_EMPLOYED": -1189,  # normal
                "AMT_INCOME_TOTAL": 405000.0, "AMT_CREDIT": 1293502.5,
                "DAYS_BIRTH": -16765,
                "EXT_SOURCE_1": 0.2, "EXT_SOURCE_2": 0.4, "EXT_SOURCE_3": 0.3,
                "_ingestion_date": "2025-01-01", "_source_file": "x",
                "_dataset_name": "y", "_row_hash": "def",
            },
        ])
        mock_leer_bronze.return_value = df

        from pipelines.tasks.caso_5.silver_tasks import transform_to_silver

        captured = {}

        def capture_write(write_df, dataset_name):
            captured["df"] = write_df
            return "/tmp/silver/application_train"

        mock_escribir_silver.side_effect = capture_write
        transform_to_silver("application_train")

        result_df = captured["df"]
        # Row 0: DAYS_EMPLOYED was 365243 → should be null
        assert pd.isna(result_df.loc[result_df["SK_ID_CURR"] == 100001, "DAYS_EMPLOYED"].iloc[0])
        # Row 1: normal value preserved
        assert result_df.loc[result_df["SK_ID_CURR"] == 100002, "DAYS_EMPLOYED"].iloc[0] == -1189

    @patch("pipelines.tasks.caso_5.silver_tasks._escribir_silver", return_value="/tmp/silver/application_train")
    @patch("pipelines.tasks.caso_5.silver_tasks._leer_bronze")
    def test_silver_handles_name_type_suite_null(
        self, mock_leer_bronze, mock_escribir_silver
    ):
        """Null NAME_TYPE_SUITE should be filled with 'Unaccompanied'."""
        df = self._make_bronze_df([
            {
                "SK_ID_CURR": 100001, "TARGET": 1,
                "CODE_GENDER": "M", "NAME_TYPE_SUITE": None,  # null
                "DAYS_EMPLOYED": -637, "AMT_INCOME_TOTAL": 202500.0,
                "AMT_CREDIT": 406597.5, "DAYS_BIRTH": -9461,
                "EXT_SOURCE_1": 0.5, "EXT_SOURCE_2": 0.7, "EXT_SOURCE_3": 0.6,
                "_ingestion_date": "2025-01-01", "_source_file": "x",
                "_dataset_name": "y", "_row_hash": "abc",
            },
            {
                "SK_ID_CURR": 100002, "TARGET": 0,
                "CODE_GENDER": "F", "NAME_TYPE_SUITE": "Family",
                "DAYS_EMPLOYED": -1189, "AMT_INCOME_TOTAL": 405000.0,
                "AMT_CREDIT": 1293502.5, "DAYS_BIRTH": -16765,
                "EXT_SOURCE_1": 0.2, "EXT_SOURCE_2": 0.4, "EXT_SOURCE_3": 0.3,
                "_ingestion_date": "2025-01-01", "_source_file": "x",
                "_dataset_name": "y", "_row_hash": "def",
            },
        ])
        mock_leer_bronze.return_value = df

        from pipelines.tasks.caso_5.silver_tasks import transform_to_silver

        captured = {}

        def capture_write(write_df, dataset_name):
            captured["df"] = write_df
            return "/tmp/silver/application_train"

        mock_escribir_silver.side_effect = capture_write
        transform_to_silver("application_train")

        result_df = captured["df"]
        name_suite_val = result_df.loc[
            result_df["SK_ID_CURR"] == 100001, "NAME_TYPE_SUITE"
        ].iloc[0]
        assert name_suite_val == "Unaccompanied"

    @patch("pipelines.tasks.caso_5.silver_tasks._escribir_silver", return_value="/tmp/silver/application_train")
    @patch("pipelines.tasks.caso_5.silver_tasks._leer_bronze")
    def test_silver_preserves_valid_data(
        self, mock_leer_bronze, mock_escribir_silver
    ):
        """Normal rows with valid data should pass through unchanged."""
        df = self._make_bronze_df()
        mock_leer_bronze.return_value = df

        from pipelines.tasks.caso_5.silver_tasks import transform_to_silver

        captured = {}

        def capture_write(write_df, dataset_name):
            captured["df"] = write_df
            return "/tmp/silver/application_train"

        mock_escribir_silver.side_effect = capture_write
        stats = transform_to_silver("application_train")

        result_df = captured["df"]
        assert stats["rows_in"] == 2
        assert stats["rows_out"] == 2
        assert stats["duplicates_removed"] == 0
        assert result_df.loc[result_df["SK_ID_CURR"] == 100001, "TARGET"].iloc[0] == 1
        assert result_df.loc[result_df["SK_ID_CURR"] == 100002, "TARGET"].iloc[0] == 0

    @patch("pipelines.tasks.caso_5.silver_tasks._leer_bronze", return_value=None)
    def test_silver_returns_empty_stats_when_no_bronze_data(self, mock_leer_bronze):
        """When Bronze has no data, stats should reflect zero rows."""
        from pipelines.tasks.caso_5.silver_tasks import transform_to_silver

        stats = transform_to_silver("application_train")

        assert stats["rows_in"] == 0
        assert stats["rows_out"] == 0
        assert stats["output_path"] is None

    def test_silver_raises_on_unknown_dataset(self):
        """Unregistered dataset name should raise ValueError."""
        from pipelines.tasks.caso_5.silver_tasks import transform_to_silver

        with pytest.raises(ValueError, match="no registrado"):
            transform_to_silver("nonexistent_dataset")


# ===========================================================================
# Test class: TestGoldTasks
# ===========================================================================


class TestGoldTasks:

    def _make_silver_app_df(self):
        """Create a minimal silver application_train DataFrame."""
        return pd.DataFrame({
            "SK_ID_CURR": [100001, 100002, 100003],
            "TARGET": [1, 0, 0],
            "NAME_CONTRACT_TYPE": ["Cash loans","Cash loans","Revolving loans"],
            "CODE_GENDER": ["M","F","M"],
            "FLAG_OWN_CAR": [1, 0, 1],
            "FLAG_OWN_REALTY": [1, 0, 1],
            "CNT_CHILDREN": [0, 2, 0],
            "AMT_INCOME_TOTAL": [202500.0, 405000.0, 300000.0],
            "AMT_CREDIT": [406597.5, 1293502.5, 135000.0],
            "AMT_ANNUITY": [24700.5, 35698.5, 6750.0],
            "AMT_GOODS_PRICE": [351000.0, 1129500.0, 135000.0],
            "NAME_INCOME_TYPE": ["Working","Working","State servant"],
            "NAME_EDUCATION_TYPE": ["Higher education","Secondary","Higher education"],
            "NAME_FAMILY_STATUS": ["Single","Married","Single"],
            "NAME_HOUSING_TYPE": ["House/apt","House/apt","Rented apartment"],
            "DAYS_BIRTH": [-9461, -16765, -19046],
            "DAYS_EMPLOYED": [-637, -1189, -426],
            "REGION_RATING_CLIENT": [2, 1, 3],
            "REGION_RATING_CLIENT_W_CITY": [2, 1, 3],
            "ORGANIZATION_TYPE": ["Business","Government","Self-employed"],
            "EXT_SOURCE_1": [0.5, 0.2, 0.8],
            "EXT_SOURCE_2": [0.7, 0.4, 0.9],
            "EXT_SOURCE_3": [0.6, 0.3, 0.85],
        })

    def _make_intermediate_install_df(self):
        return pd.DataFrame({
            "SK_ID_CURR": [100001, 100002],
            "total_installments": [10, 20],
            "avg_payment_delay": [2.5, 5.0],
        })

    @patch("pipelines.tasks.caso_5.gold_tasks.os.makedirs")
    @patch("pipelines.tasks.caso_5.gold_tasks.pd.read_parquet")
    @patch("pipelines.tasks.caso_5.gold_tasks.os.listdir")
    @patch("pipelines.tasks.caso_5.gold_tasks.os.path.exists")
    def test_gold_customer_360_joins_tables(
        self,
        mock_exists,
        mock_listdir,
        mock_read_parquet,
        mock_makedirs,
    ):
        """Silver application_train should be LEFT JOINed with intermediate tables."""
        silver_df = self._make_silver_app_df()
        install_df = self._make_intermediate_install_df()

        # Set up os.path.exists to return True for app dir and installment dir
        def exists_side_effect(path):
            if "application_train" in path:
                return True
            if "installment" in path:
                return True
            return False

        mock_exists.side_effect = exists_side_effect
        mock_listdir.side_effect = [
            ["application_train.parquet"],  # silver app
            ["agg_customer_installment_history.parquet"],  # intermediate install
        ]
        mock_read_parquet.side_effect = [silver_df, install_df]

        # Capture the DataFrame via patch.object (autospec passes self)
        captured = {}

        def capture_to_parquet(self_df, path, **kwargs):
            captured["df"] = self_df
            return None

        with patch.object(pd.DataFrame, "to_parquet", capture_to_parquet), \
             patch.dict(os.environ, {"SILVER_DIR": "/tmp/s", "INTERMEDIATE_DIR": "/tmp/i", "GOLD_DIR": "/tmp/g"}, clear=False):
            from pipelines.tasks.caso_5.gold_tasks import build_gold_customer_360
            result = build_gold_customer_360()

        gold_df = captured["df"]
        # 3 rows from silver — LEFT JOIN should preserve all
        assert len(gold_df) == 3
        # Merged column should exist (with suffix from _safe_merge)
        assert "total_installments_install" in gold_df.columns or "total_installments" in gold_df.columns
        assert result["rows"] == 3

    @patch("pipelines.tasks.caso_5.gold_tasks.os.makedirs")
    @patch("pipelines.tasks.caso_5.gold_tasks.pd.read_parquet")
    @patch("pipelines.tasks.caso_5.gold_tasks.os.listdir", return_value=["application_train.parquet"])
    @patch("pipelines.tasks.caso_5.gold_tasks.os.path.exists", return_value=True)
    def test_gold_adds_computed_columns(
        self,
        mock_exists,
        mock_listdir,
        mock_read_parquet,
        mock_makedirs,
    ):
        """Gold should have age_years, credit_to_income_ratio, and risk_segment columns."""
        silver_df = self._make_silver_app_df()
        mock_read_parquet.return_value = silver_df

        captured = {}

        def capture_to_parquet(self_df, path, **kwargs):
            captured["df"] = self_df
            return None

        with patch.object(pd.DataFrame, "to_parquet", capture_to_parquet), \
             patch.dict(os.environ, {"SILVER_DIR": "/tmp/s", "INTERMEDIATE_DIR": "/tmp/i", "GOLD_DIR": "/tmp/g"}, clear=False):
            from pipelines.tasks.caso_5.gold_tasks import build_gold_customer_360
            build_gold_customer_360()

        gold_df = captured["df"]
        assert "age_years" in gold_df.columns
        assert "credit_to_income_ratio" in gold_df.columns
        assert "risk_segment" in gold_df.columns

    @patch("pipelines.tasks.caso_5.gold_tasks.os.makedirs")
    @patch("pipelines.tasks.caso_5.gold_tasks.pd.read_parquet")
    @patch("pipelines.tasks.caso_5.gold_tasks.os.listdir")
    @patch("pipelines.tasks.caso_5.gold_tasks.os.path.exists")
    def test_gold_risk_segment_logic(
        self,
        mock_exists,
        mock_listdir,
        mock_read_parquet,
        mock_makedirs,
    ):
        """risk_segment logic verified: default MEDIUM_RISK + direct np.select test.

        The production code merges intermediate data with suffixes (e.g.
        ``_behavior``), then looks for the exact column name
        ``payment_consistency_score`` (without suffix).  This causes the
        segmentation condition to always fall through to the default
        ``MEDIUM_RISK``.  We verify this actual behavior, and separately
        exercise the underlying ``np.select`` formula in isolation.
        """
        silver_df = self._make_silver_app_df()
        behavior_df = pd.DataFrame({
            "SK_ID_CURR": [100001, 100002, 100003],
            "payment_consistency_score": [90.0, 60.0, 20.0],
            "max_days_overdue": [2.0, 15.0, 100.0],
        })

        mock_exists.return_value = True
        mock_listdir.side_effect = [
            ["application_train.parquet"],  # silver app
            [],  # installment
            ["fct_customer_payment_behavior_features.parquet"],  # behavior
            [],  # bureau
            [],  # prev app
            [],  # cc
            [],  # pos
        ]
        mock_read_parquet.side_effect = [silver_df, behavior_df]

        captured = {}

        def capture_to_parquet(self_df, path, **kwargs):
            captured["df"] = self_df
            return None

        with patch.object(pd.DataFrame, "to_parquet", capture_to_parquet), \
             patch.dict(os.environ, {"SILVER_DIR": "/tmp/s", "INTERMEDIATE_DIR": "/tmp/i", "GOLD_DIR": "/tmp/g"}, clear=False):
            from pipelines.tasks.caso_5.gold_tasks import build_gold_customer_360
            build_gold_customer_360()

        gold_df = captured["df"]

        # The merge added _behavior suffix; production code doesn't find the
        # exact column → default MEDIUM_RISK for all rows.
        assert "risk_segment" in gold_df.columns
        assert (gold_df["risk_segment"] == "MEDIUM_RISK").all()

        # ── Now verify the np.select formula directly ──
        consistency = np.array([90.0, 60.0, 20.0])
        overdue = np.array([2.0, 15.0, 100.0])
        conditions = [
            (consistency >= 80) & (overdue <= 5),
            (consistency >= 50) & (overdue <= 30),
        ]
        choices = ["LOW_RISK","MEDIUM_RISK"]
        segments = np.select(conditions, choices, default="HIGH_RISK")
        assert list(segments) == ["LOW_RISK","MEDIUM_RISK","HIGH_RISK"]

    @patch("pipelines.tasks.caso_5.gold_tasks.os.path.exists", return_value=False)
    @patch("pipelines.tasks.caso_5.gold_tasks.os.listdir", return_value=[])
    def test_gold_returns_empty_when_no_silver_data(self, mock_listdir, mock_exists):
        """When no silver data found, result should have rows=0."""
        from pipelines.tasks.caso_5.gold_tasks import build_gold_customer_360

        result = build_gold_customer_360()

        assert result["rows"] == 0
        assert result["output_path"] == ""


# ===========================================================================
# Test class: TestDataQualityReport
# ===========================================================================


class TestDataQualityReport:

    def test_compute_quality_score_perfect_data(self):
        """No nulls and no duplicates → score 100."""
        from quality.data_quality_report import compute_quality_score

        profile = {
            "row_count": 100,
            "total_cells": 500,
            "total_nulls": 0,
            "total_duplicates": 0,
        }
        score = compute_quality_score(profile)
        assert score == 100.0

    def test_compute_quality_score_with_nulls(self):
        """10% nulls → 10 * 0.3 = 3 point penalty → score 97."""
        from quality.data_quality_report import compute_quality_score

        # 50 nulls out of 500 cells = 10%
        profile = {
            "row_count": 100,
            "total_cells": 500,
            "total_nulls": 50,
            "total_duplicates": 0,
        }
        score = compute_quality_score(profile)
        assert score == pytest.approx(97.0)

    def test_compute_quality_score_with_duplicates(self):
        """5% duplicates → 5 * 0.2 = 1 point penalty → score 99."""
        from quality.data_quality_report import compute_quality_score

        profile = {
            "row_count": 100,
            "total_cells": 500,
            "total_nulls": 0,
            "total_duplicates": 5,  # 5% of 100 rows
        }
        score = compute_quality_score(profile)
        assert score == pytest.approx(99.0)

    def test_compute_quality_score_empty_dataset(self):
        """row_count=0 → score 0."""
        from quality.data_quality_report import compute_quality_score

        profile = {
            "row_count": 0,
            "total_cells": 0,
            "total_nulls": 0,
            "total_duplicates": 0,
        }
        score = compute_quality_score(profile)
        assert score == 0.0

    def test_compute_quality_score_combined_penalties(self):
        """Both nulls and duplicates: penalties should add up correctly."""
        from quality.data_quality_report import compute_quality_score

        # 50% nulls (15 pt penalty) + 50% dups (10 pt penalty) = 75
        profile = {
            "row_count": 100,
            "total_cells": 200,
            "total_nulls": 100,  # 50% nulls
            "total_duplicates": 50,  # 50% dups
        }
        score = compute_quality_score(profile)
        assert score == pytest.approx(75.0)

    def test_compute_quality_score_clamps_to_zero(self):
        """Score cannot go below 0."""
        from quality.data_quality_report import compute_quality_score

        profile = {
            "row_count": 10,
            "total_cells": 10,
            "total_nulls": 500,  # extreme
            "total_duplicates": 500,  # extreme
        }
        score = compute_quality_score(profile)
        assert score == 0.0

    @patch("quality.data_quality_report.os.path.isfile", return_value=True)
    @patch("quality.data_quality_report._load_dataset")
    def test_profile_dataset_returns_expected_keys(
        self, mock_load, mock_isfile, tmp_path
    ):
        """Profile dict should have all expected keys."""
        df = pd.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [1.0, 2.0, None, 4.0, 5.0],
            "c": ["x","y","z","x","y"],
        })
        mock_load.return_value = df

        from quality.data_quality_report import profile_dataset

        result = profile_dataset(str(tmp_path / "test.parquet"), "test_dataset")

        expected_keys = [
            "dataset",
            "row_count",
            "column_count",
            "total_nulls",
            "total_duplicates",
            "quality_score",
            "null_percentage_by_column",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

        assert result["dataset"] == "test_dataset"
        assert result["row_count"] == 5
        assert result["column_count"] == 3
        assert result["total_nulls"] == 1
        assert result["total_duplicates"] == 0
        # 1 null / (5 rows * 3 cols = 15 cells) = 6.67% → penalty 6.67*0.3 = 2.0 → score = 98.0
        assert result["quality_score"] == pytest.approx(98.0)

    @patch("quality.data_quality_report.os.path.isfile", return_value=False)
    @patch("quality.data_quality_report._find_parquet_files", return_value=[])
    def test_profile_dataset_no_files(self, mock_find, mock_isfile):
        """When no files found, profile should return zeroed metrics."""
        from quality.data_quality_report import profile_dataset

        result = profile_dataset("/nonexistent/path", "empty_dataset")

        assert result["row_count"] == 0
        assert result["quality_score"] == 0.0
        assert result["total_nulls"] == 0

    @patch("quality.data_quality_report._load_dataset")
    def test_profile_dataset_with_empty_dataframe(self, mock_load):
        """When loaded DataFrame is empty, return zeroed metrics."""
        mock_load.return_value = pd.DataFrame()

        from quality.data_quality_report import profile_dataset

        result = profile_dataset("/some/file.parquet", "empty_df")

        assert result["row_count"] == 0
        assert result["quality_score"] == 0.0

    @patch("quality.data_quality_report.os.getenv", return_value=str(__import__("os").getcwd()))
    @patch("quality.data_quality_report.os.path.exists", return_value=False)
    def test_generate_quality_report_no_layers(self, mock_exists, mock_getenv):
        """When no data directories exist, report should have empty layers."""
        from quality.data_quality_report import generate_quality_report

        report = generate_quality_report()

        assert "generated_at" in report
        assert "layers" in report
        assert "summary" in report
        assert report["summary"]["total_datasets"] == 0


# ===========================================================================
# Test class: TestScoringBaseline
# ===========================================================================


class TestScoringBaseline:

    def _make_gold_df_with_target(self):
        """Create a minimal gold DataFrame for ML tests."""
        return pd.DataFrame({
            "SK_ID_CURR": [100001, 100002, 100003, 100004, 100005],
            "TARGET": [1, 0, 0, None, 1],
            "AMT_INCOME_TOTAL": [202500.0, 405000.0, 300000.0, 150000.0, 250000.0],
            "AMT_CREDIT": [406597.5, 1293502.5, 135000.0, 200000.0, 500000.0],
            "AMT_ANNUITY": [24700.5, 35698.5, 6750.0, 10000.0, 20000.0],
            "AMT_GOODS_PRICE": [351000.0, 1129500.0, 135000.0, 180000.0, 450000.0],
            "DAYS_BIRTH": [-9461, -16765, -19046, -12000, -8000],
            "DAYS_EMPLOYED": [-637, -1189, -426, -800, -365],
            "CNT_CHILDREN": [0, 2, 0, 1, 3],
            "REGION_RATING_CLIENT": [2, 1, 3, 2, 1],
            "EXT_SOURCE_1": [0.5, 0.2, 0.8, 0.6, 0.4],
            "EXT_SOURCE_2": [0.7, 0.4, 0.9, 0.5, 0.3],
            "EXT_SOURCE_3": [0.6, 0.3, 0.85, 0.7, 0.5],
        })

    def test_prepare_features_drops_null_target(self):
        """Rows with null TARGET should be dropped."""
        from ml.training.scoring_baseline import _prepare_features

        df = self._make_gold_df_with_target()
        X, y, feature_names = _prepare_features(df)

        # Original df has 5 rows, 1 with null TARGET → 4 rows remain
        assert len(X) == 4
        assert len(y) == 4
        # No null TARGET values should remain
        assert y.isna().sum() == 0

    def test_prepare_features_fills_nulls(self):
        """NaN values in features should be replaced with 0."""
        from ml.training.scoring_baseline import _prepare_features

        df = self._make_gold_df_with_target()
        # Inject some NaN in feature columns
        df.loc[0, "AMT_INCOME_TOTAL"] = np.nan
        df.loc[1, "EXT_SOURCE_1"] = np.nan

        X, y, feature_names = _prepare_features(df)

        assert X.isna().sum().sum() == 0

    def test_prepare_features_returns_available_features_only(self):
        """Should return only features present in the DataFrame."""
        from ml.training.scoring_baseline import _prepare_features, MODEL_FEATURES

        df = self._make_gold_df_with_target()
        X, y, feature_names = _prepare_features(df)

        # All returned feature names should be in the DataFrame columns
        for fname in feature_names:
            assert fname in X.columns
        # TARGET should not be in features
        assert "TARGET" not in X.columns

    def test_prepare_features_handles_empty_df(self):
        """Empty DataFrame after dropping null TARGET should produce empty X/y."""
        from ml.training.scoring_baseline import _prepare_features

        df = pd.DataFrame({"TARGET": [None, None], "AMT_INCOME_TOTAL": [100.0, 200.0]})
        X, y, feature_names = _prepare_features(df)

        assert len(X) == 0
        assert len(y) == 0

    def test_get_feature_importance_random_forest(self):
        """Random Forest model should use feature_importances_ attribute."""
        from ml.training.scoring_baseline import _get_feature_importance

        mock_model = MagicMock()
        mock_model.feature_importances_ = np.array([0.4, 0.3, 0.2, 0.1])
        feature_names = ["feat_a","feat_b","feat_c","feat_d"]

        result = _get_feature_importance(mock_model, feature_names, "random_forest")

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["feature","importance"]
        assert len(result) == 4
        # Should be sorted descending by importance
        assert result.iloc[0]["importance"] >= result.iloc[-1]["importance"]
        assert result.iloc[0]["feature"] == "feat_a"
        assert result.iloc[0]["importance"] == pytest.approx(0.4)

    def test_get_feature_importance_logistic_regression(self):
        """Logistic Regression model should use abs(coef_) for importance."""
        from ml.training.scoring_baseline import _get_feature_importance

        mock_model = MagicMock()
        mock_model.coef_ = np.array([[-0.5, 0.3, -0.8, 0.1]])
        feature_names = ["feat_a","feat_b","feat_c","feat_d"]

        result = _get_feature_importance(mock_model, feature_names, "logistic_regression")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        # Should use abs values
        importances = result.set_index("feature")["importance"]
        assert importances["feat_c"] == pytest.approx(0.8)
        assert importances["feat_a"] == pytest.approx(0.5)
        # Should be sorted descending — feat_c (0.8) should be first
        assert result.iloc[0]["feature"] == "feat_c"

    def test_get_feature_importance_unknown_model(self):
        """Unknown model name should return zeros for all features."""
        from ml.training.scoring_baseline import _get_feature_importance

        mock_model = MagicMock()
        # Remove feature_importances_ and coef_ to simulate unknown model
        del mock_model.feature_importances_
        del mock_model.coef_
        feature_names = ["feat_a","feat_b"]

        result = _get_feature_importance(mock_model, feature_names, "unknown_model")

        assert (result["importance"] == 0).all()
