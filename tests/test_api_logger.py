
import json
import tempfile
import unittest

from contextlib import redirect_stderr
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from api_logger import (
    API_BASE_URL,
    ApiLoggerError,
    append_log,
    build_log_entry,
    fetch_repo_data,
    main,
    parse_repository,
    run_once,
)


class ApiLoggerTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.log_path = self.root / "api_log.jsonl"

        self.repo_data = {
            "full_name": "python/cpython",
            "stargazers_count": 12345,
            "open_issues_count": 500,
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_repository_valid(self):
        result = parse_repository("python/cpython")

        self.assertEqual(result, "python/cpython")

    def test_parse_repository_rejects_invalid_format(self):
        with self.assertRaises(ApiLoggerError):
            parse_repository("python")

    @patch("api_logger.requests.get")
    def test_fetch_success(self, mock_get):
        response = Mock()
        response.json.return_value = self.repo_data
        mock_get.return_value = response

        result = fetch_repo_data("python/cpython", timeout=5)

        args, kwargs = mock_get.call_args

        self.assertEqual(
            args[0],
            f"{API_BASE_URL}/python/cpython"
        )
        self.assertEqual(kwargs["timeout"], 5)
        self.assertEqual(result, self.repo_data)

    @patch("api_logger.requests.get")
    def test_fetch_handles_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout

        with self.assertRaisesRegex(
            ApiLoggerError,
            "timed out"
        ):
            fetch_repo_data("python/cpython")

    @patch("api_logger.requests.get")
    def test_fetch_handles_http_404(self, mock_get):
        response = Mock()
        response.status_code = 404

        response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError(
                "404 Not Found",
                response=response,
            )
        )

        mock_get.return_value = response

        with self.assertRaisesRegex(
            ApiLoggerError,
            "Repository not found"
        ):
            fetch_repo_data("python/cpython")

    @patch("api_logger.requests.get")
    def test_fetch_handles_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        with self.assertRaisesRegex(
            ApiLoggerError,
            "request failed"
        ):
            fetch_repo_data("python/cpython")

    @patch("api_logger.requests.get")
    def test_fetch_rejects_invalid_json(self, mock_get):
        response = Mock()
        response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = response

        with self.assertRaisesRegex(
            ApiLoggerError,
            "invalid JSON"
        ):
            fetch_repo_data("python/cpython")

    @patch("api_logger.requests.get")
    def test_fetch_rejects_invalid_response_shape(self, mock_get):
        response = Mock()
        response.json.return_value = {
            "message": "Unexpected response"
        }

        mock_get.return_value = response

        with self.assertRaisesRegex(
            ApiLoggerError,
            "repository name"
        ):
            fetch_repo_data("python/cpython")

    def test_build_log_entry_uses_utc_timestamp(self):
        entry = build_log_entry(self.repo_data)

        timestamp = datetime.fromisoformat(entry["timestamp"])

        self.assertEqual(timestamp.utcoffset().total_seconds(), 0)
        self.assertEqual(entry["repo"], "python/cpython")
        self.assertEqual(entry["stars"], 12345)
        self.assertEqual(entry["open_issues"], 500)

    def test_append_log_writes_json_line(self):
        entry = build_log_entry(self.repo_data)

        append_log(entry, self.log_path)

        lines = self.log_path.read_text(
            encoding="utf-8"
        ).splitlines()

        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0]), entry)

    def test_append_log_creates_parent_directories(self):
        nested_path = self.root / "nested" / "api_log.jsonl"

        append_log(
            build_log_entry(self.repo_data),
            nested_path,
        )

        self.assertTrue(nested_path.exists())

    def test_run_once_uses_injected_fetcher(self):
        fake_fetcher = Mock(return_value=self.repo_data)

        entry = run_once(
            repository="python/cpython",
            output_file=self.log_path,
            timeout=5,
            fetcher=fake_fetcher,
        )

        fake_fetcher.assert_called_once_with(
            "python/cpython",
            5,
        )

        self.assertTrue(self.log_path.exists())
        self.assertEqual(entry["repo"], "python/cpython")

    @patch("api_logger.fetch_repo_data")
    def test_main_success(self, mock_fetch, ):
        mock_fetch.return_value = self.repo_data

        result = main([
            "python/cpython",
            "--output",
            str(self.log_path),
        ])

        self.assertEqual(result, 0)
        self.assertTrue(self.log_path.exists())

    @patch("api_logger.fetch_repo_data")
    def test_main_handles_api_error(self, mock_fetch):
        mock_fetch.side_effect = ApiLoggerError(
            "Simulated API failure"
        )

        error_output = StringIO()

        with redirect_stderr(error_output):
            result = main([
                "python/cpython",
                "--output",
                str(self.log_path),
            ])

        self.assertEqual(result, 1)
        self.assertIn(
            "Simulated API failure",
            error_output.getvalue()
        )


if __name__ == "__main__":
    unittest.main()
