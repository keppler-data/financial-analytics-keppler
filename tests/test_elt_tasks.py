"""Unit tests for pipelines/tasks/elt_tasks.py"""

import json
import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pipelines.tasks.elt_tasks import (
    LOG_PATTERN,
    APIIngester,
    CSVIngester,
    LogIngester,
)


class TestAPIIngester:
    """Tests for the APIIngester class."""

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_init_with_explicit_params(self, mock_boto3):
        ingester = APIIngester(base_url="https://custom.api/v2", api_key="test-key-123")
        assert ingester.base_url == "https://custom.api/v2"
        assert ingester.api_key == "test-key-123"
        assert ingester.headers == {"Authorization": "Bearer test-key-123"}
        mock_boto3.client.assert_called_once_with("s3")

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch.dict(os.environ, {"KEPLER_API_URL": "https://env.api/v1", "KEPLER_API_KEY": "env-key"})
    def test_init_from_env_vars(self, mock_boto3):
        ingester = APIIngester()
        assert ingester.base_url == "https://env.api/v1"
        assert ingester.api_key == "env-key"

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch.dict(os.environ, {}, clear=True)
    def test_init_default_base_url(self, mock_boto3):
        os.environ.pop("KEPLER_API_URL", None)
        os.environ.pop("KEPLER_API_KEY", None)
        ingester = APIIngester()
        assert ingester.base_url == "https://api.keplerfintech.local/v1"

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch("pipelines.tasks.elt_tasks.requests")
    def test_fetch_and_upload_with_items_key(self, mock_requests, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{"id": 1, "amount": 100}, {"id": 2, "amount": 200}]
        }
        mock_requests.get.return_value = mock_response

        ingester = APIIngester(base_url="https://api.test/v1", api_key="key123")
        result = ingester.fetch_and_upload("transactions", "2024-06-15")

        assert result == 2
        mock_requests.get.assert_called_once_with(
            "https://api.test/v1/transactions",
            headers={"Authorization": "Bearer key123"},
            params={"date": "2024-06-15", "limit": 10000},
        )
        mock_response.raise_for_status.assert_called_once()

        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "kepler-bronze"
        assert call_kwargs["Key"] == "financial/transactions/year=2024/month=06/day=15/transactions_2024-06-15.json"
        assert call_kwargs["ContentType"] == "application/json"
        assert call_kwargs["Metadata"]["source"] == "transactions"
        assert call_kwargs["Metadata"]["record_count"] == "2"

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch("pipelines.tasks.elt_tasks.requests")
    def test_fetch_and_upload_with_list_response_raises(self, mock_requests, mock_boto3):
        """When the API returns a raw list, the code raises AttributeError
        because list has no .get() method. This documents existing behavior."""
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]
        mock_requests.get.return_value = mock_response

        ingester = APIIngester(base_url="https://api.test/v1", api_key="key")
        with pytest.raises(AttributeError):
            ingester.fetch_and_upload("market_data", "2024-01-10")

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch("pipelines.tasks.elt_tasks.requests")
    def test_fetch_and_upload_with_dict_no_items(self, mock_requests, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "count": 0}
        mock_requests.get.return_value = mock_response

        ingester = APIIngester(base_url="https://api.test/v1", api_key="key")
        result = ingester.fetch_and_upload("endpoint", "2024-03-01")

        # When no 'items' key and data is dict (not list), records = []
        assert result == 0

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch("pipelines.tasks.elt_tasks.requests")
    def test_fetch_and_upload_custom_bucket(self, mock_requests, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [{"id": 1}]}
        mock_requests.get.return_value = mock_response

        ingester = APIIngester(base_url="https://api.test/v1", api_key="key")
        result = ingester.fetch_and_upload("data", "2024-12-25", bucket_name="custom-bucket")

        assert result == 1
        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "custom-bucket"

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch("pipelines.tasks.elt_tasks.requests")
    def test_fetch_and_upload_raises_on_http_error(self, mock_requests, mock_boto3):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_requests.get.return_value = mock_response

        ingester = APIIngester(base_url="https://api.test/v1", api_key="key")
        with pytest.raises(Exception, match="404 Not Found"):
            ingester.fetch_and_upload("bad_endpoint", "2024-01-01")

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch("pipelines.tasks.elt_tasks.requests")
    def test_fetch_and_upload_s3_key_format(self, mock_requests, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_requests.get.return_value = mock_response

        ingester = APIIngester(base_url="https://api.test/v1", api_key="key")
        ingester.fetch_and_upload("loans", "2023-11-05")

        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Key"] == "financial/loans/year=2023/month=11/day=05/loans_2023-11-05.json"


class TestCSVIngester:
    """Tests for the CSVIngester class."""

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_init(self, mock_boto3):
        ingester = CSVIngester()
        mock_boto3.client.assert_called_once_with("s3")
        assert ingester.SUPPORTED_ENCODINGS == ["utf-8", "latin-1", "cp1252"]

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_ingest_csv_success(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col_a,col_b,col_c\n1,hello,3.14\n2,world,2.72\n")
            tmp_path = f.name

        try:
            ingester = CSVIngester()
            result = ingester.ingest_csv(tmp_path, "test_dataset", "2024-07-20")

            assert result == 2
            call_kwargs = mock_s3.put_object.call_args[1]
            assert call_kwargs["Bucket"] == "kepler-bronze"
            assert call_kwargs["Key"] == "financial/test_dataset/year=2024/month=07/day=20/test_dataset_2024-07-20.parquet"
            assert call_kwargs["ContentType"] == "application/x-parquet"
            assert len(call_kwargs["Body"]) > 0
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_ingest_csv_adds_metadata_columns(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,value\nfoo,1\nbar,2\n")
            tmp_path = f.name

        try:
            ingester = CSVIngester()
            ingester.ingest_csv(tmp_path, "dataset", "2024-01-15")

            call_kwargs = mock_s3.put_object.call_args[1]
            parquet_bytes = call_kwargs["Body"]
            df = pd.read_parquet(BytesIO(parquet_bytes))

            assert "_ingestion_source" in df.columns
            assert "_ingestion_date" in df.columns
            assert "_file_name" in df.columns
            assert (df["_ingestion_source"] == "csv").all()
            assert (df["_ingestion_date"] == "2024-01-15").all()
            assert (df["_file_name"] == os.path.basename(tmp_path)).all()
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_ingest_csv_custom_bucket(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("x\n1\n")
            tmp_path = f.name

        try:
            ingester = CSVIngester()
            ingester.ingest_csv(tmp_path, "ds", "2024-02-28", bucket_name="my-bucket")

            call_kwargs = mock_s3.put_object.call_args[1]
            assert call_kwargs["Bucket"] == "my-bucket"
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_ingest_csv_latin1_encoding(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            content = "nombre,ciudad\nJosé,São Paulo\nMaría,Bogotá\n".encode("latin-1")
            f.write(content)
            tmp_path = f.name

        try:
            ingester = CSVIngester()
            result = ingester.ingest_csv(tmp_path, "latam_data", "2024-05-01")
            assert result == 2
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    @patch("pipelines.tasks.elt_tasks.pd.read_csv")
    def test_ingest_csv_raises_on_unsupported_encoding(self, mock_read_csv, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_read_csv.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(b"invalid content")
            tmp_path = f.name

        try:
            ingester = CSVIngester()
            with pytest.raises(ValueError, match="Error al codificar"):
                ingester.ingest_csv(tmp_path, "bad_data", "2024-01-01")
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_ingest_csv_parquet_output_is_valid(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("id,amount,date\n1,100.50,2024-01-01\n2,200.75,2024-01-02\n")
            tmp_path = f.name

        try:
            ingester = CSVIngester()
            ingester.ingest_csv(tmp_path, "payments", "2024-08-10")

            call_kwargs = mock_s3.put_object.call_args[1]
            df = pd.read_parquet(BytesIO(call_kwargs["Body"]))
            assert len(df) == 2
            assert "id" in df.columns
            assert "amount" in df.columns
            assert "date" in df.columns
        finally:
            os.unlink(tmp_path)


class TestLogIngester:
    """Tests for the LogIngester class."""

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_init(self, mock_boto3):
        ingester = LogIngester()
        mock_boto3.client.assert_called_once_with("s3")

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_parse_and_upload_logs_missing_file(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        ingester = LogIngester()
        result = ingester.parse_and_upload_logs("/nonexistent/path/logs.txt", "2024-01-01")

        assert result == 0
        mock_s3.put_object.assert_not_called()

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_parse_and_upload_logs_valid_entries(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        log_content = (
            "2024-06-15T10:30:00 INFO auth User login successful\n"
            "2024-06-15T10:31:00 ERROR payments Payment processing failed\n"
            "2024-06-15T10:32:00 WARN risk High risk score detected for customer\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            tmp_path = f.name

        try:
            ingester = LogIngester()
            result = ingester.parse_and_upload_logs(tmp_path, "2024-06-15")

            assert result == 3
            call_kwargs = mock_s3.put_object.call_args[1]
            assert call_kwargs["Bucket"] == "kepler-bronze"
            assert call_kwargs["Key"] == "financial/app_logs/year=2024/month=06/day=15/app_logs_2024-06-15.json"
            assert call_kwargs["ContentType"] == "application/x-ndjson"
            assert call_kwargs["Metadata"]["source"] == "app_logs"
            assert call_kwargs["Metadata"]["record_count"] == "3"

            body_lines = call_kwargs["Body"].split("\n")
            assert len(body_lines) == 3
            first_event = json.loads(body_lines[0])
            assert first_event["timestamp"] == "2024-06-15T10:30:00"
            assert first_event["level"] == "INFO"
            assert first_event["service"] == "auth"
            assert first_event["message"] == "User login successful"
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_parse_and_upload_logs_no_matching_lines(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        log_content = "This is not a valid log line\nNeither is this\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            tmp_path = f.name

        try:
            ingester = LogIngester()
            result = ingester.parse_and_upload_logs(tmp_path, "2024-01-01")

            assert result == 0
            mock_s3.put_object.assert_not_called()
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_parse_and_upload_logs_mixed_valid_invalid(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        log_content = (
            "2024-06-15T10:30:00 INFO auth Login\n"
            "--- garbage line ---\n"
            "2024-06-15T10:31:00 ERROR db Connection timeout\n"
            "\n"
            "2024-06-15T10:32:00 DEBUG cache Cache miss\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            tmp_path = f.name

        try:
            ingester = LogIngester()
            result = ingester.parse_and_upload_logs(tmp_path, "2024-06-15")

            assert result == 3
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_parse_and_upload_logs_custom_bucket(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        log_content = "2024-01-01T00:00:00 INFO svc Start\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            tmp_path = f.name

        try:
            ingester = LogIngester()
            result = ingester.parse_and_upload_logs(tmp_path, "2024-01-01", bucket_name="logs-bucket")

            assert result == 1
            call_kwargs = mock_s3.put_object.call_args[1]
            assert call_kwargs["Bucket"] == "logs-bucket"
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_parse_and_upload_logs_empty_file(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("")
            tmp_path = f.name

        try:
            ingester = LogIngester()
            result = ingester.parse_and_upload_logs(tmp_path, "2024-01-01")

            assert result == 0
            mock_s3.put_object.assert_not_called()
        finally:
            os.unlink(tmp_path)

    @patch("pipelines.tasks.elt_tasks.boto3")
    def test_parse_and_upload_logs_ndjson_format(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        log_content = (
            "2024-03-10T08:00:00 WARN risk Threshold exceeded\n"
            "2024-03-10T08:01:00 INFO api Request processed\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            tmp_path = f.name

        try:
            ingester = LogIngester()
            ingester.parse_and_upload_logs(tmp_path, "2024-03-10")

            call_kwargs = mock_s3.put_object.call_args[1]
            lines = call_kwargs["Body"].split("\n")
            for line in lines:
                parsed = json.loads(line)
                assert "timestamp" in parsed
                assert "level" in parsed
                assert "service" in parsed
                assert "message" in parsed
        finally:
            os.unlink(tmp_path)


class TestLogPattern:
    """Tests for the LOG_PATTERN regex."""

    def test_matches_standard_log_line(self):
        import re
        line = "2024-06-15T10:30:00 INFO auth User login successful"
        match = re.match(LOG_PATTERN, line)
        assert match is not None
        assert match.group("timestamp") == "2024-06-15T10:30:00"
        assert match.group("level") == "INFO"
        assert match.group("service") == "auth"
        assert match.group("message") == "User login successful"

    def test_matches_error_level(self):
        import re
        line = "2024-01-01T00:00:00 ERROR database Connection refused"
        match = re.match(LOG_PATTERN, line)
        assert match is not None
        assert match.group("level") == "ERROR"
        assert match.group("service") == "database"

    def test_does_not_match_invalid_format(self):
        import re
        line = "This is not a log line"
        match = re.match(LOG_PATTERN, line)
        assert match is None

    def test_does_not_match_partial_timestamp(self):
        import re
        line = "2024-06-15 INFO auth Login"
        match = re.match(LOG_PATTERN, line)
        assert match is None

    def test_matches_multiword_message(self):
        import re
        line = "2024-12-31T23:59:59 WARN alerting Multiple threshold breaches detected in portfolio"
        match = re.match(LOG_PATTERN, line)
        assert match is not None
        assert match.group("message") == "Multiple threshold breaches detected in portfolio"
