
#!/usr/bin/env python3

import argparse
import json
import re
import sys

from datetime import datetime, timezone
from pathlib import Path

import requests


API_BASE_URL = "https://api.github.com/repos"
DEFAULT_REPOSITORY = "python/cpython"
DEFAULT_LOG_FILE = Path(__file__).resolve().with_name("api_log.jsonl")
DEFAULT_TIMEOUT = 10.0


class ApiLoggerError(Exception):
    """Raised when an API request or logging operation fails."""


def parse_repository(repository):
    """Validate and return an owner/repository identifier."""
    repository = repository.strip()

    if not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
        repository,
    ):
        raise ApiLoggerError(
            "Repository must use owner/repository format, "
            "for example python/cpython."
        )

    return repository


def fetch_repo_data(repository, timeout=DEFAULT_TIMEOUT):
    """Fetch repository information from the GitHub API."""
    repository = parse_repository(repository)
    url = f"{API_BASE_URL}/{repository}"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
        )

        response.raise_for_status()

    except requests.exceptions.Timeout as exc:
        raise ApiLoggerError(
            f"GitHub API request timed out after {timeout} seconds."
        ) from exc

    except requests.exceptions.HTTPError as exc:
        status = (
            exc.response.status_code
            if exc.response is not None
            else None
        )

        if status == 404:
            message = f"Repository not found: {repository}."

        elif status == 403:
            message = (
                "GitHub API access was forbidden or rate-limited. "
                "Try again later."
            )

        else:
            message = f"GitHub API returned HTTP {status}."

        raise ApiLoggerError(message) from exc

    except requests.exceptions.RequestException as exc:
        raise ApiLoggerError(
            f"GitHub API request failed: {exc}"
        ) from exc

    try:
        data = response.json()

    except ValueError as exc:
        raise ApiLoggerError(
            "GitHub API returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise ApiLoggerError(
            "GitHub API returned an unexpected response."
        )

    if not isinstance(data.get("full_name"), str):
        raise ApiLoggerError(
            "API response is missing a valid repository name."
        )

    for field in ("stargazers_count", "open_issues_count"):
        value = data.get(field)

        if type(value) is not int or value < 0:
            raise ApiLoggerError(
                f"API response contains an invalid {field} value."
            )

    return data


def build_log_entry(data):
    """Create a clean, timestamped log record."""
    if not isinstance(data, dict):
        raise ApiLoggerError("Repository data must be a dictionary.")

    full_name = data.get("full_name")
    stars = data.get("stargazers_count")
    open_issues = data.get("open_issues_count")

    if not isinstance(full_name, str) or not full_name:
        raise ApiLoggerError("Repository name is missing.")

    if type(stars) is not int or stars < 0:
        raise ApiLoggerError("Invalid repository star count.")

    if type(open_issues) is not int or open_issues < 0:
        raise ApiLoggerError("Invalid open issue count.")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ),
        "repo": full_name,
        "stars": stars,
        "open_issues": open_issues,
    }


def append_log(entry, log_file=DEFAULT_LOG_FILE):
    """Append one JSON record to the log file."""
    path = Path(log_file)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(entry, ensure_ascii=False) + "\n"
            )

    except OSError as exc:
        raise ApiLoggerError(
            f"Could not write to log file {path}: {exc}"
        ) from exc


def run_once(
    repository=DEFAULT_REPOSITORY,
    output_file=DEFAULT_LOG_FILE,
    timeout=DEFAULT_TIMEOUT,
    fetcher=None,
):
    """Fetch repository data and append one log record."""
    if fetcher is None:
        fetcher = fetch_repo_data

    data = fetcher(repository, timeout)
    entry = build_log_entry(data)
    append_log(entry, output_file)

    return entry


def positive_float(value):
    """Validate a positive timeout argument."""
    try:
        number = float(value)

    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Timeout must be a positive number."
        ) from exc

    if number <= 0:
        raise argparse.ArgumentTypeError(
            "Timeout must be greater than zero."
        )

    return number


def build_parser():
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Fetch GitHub repository statistics and log them."
    )

    parser.add_argument(
        "repository",
        nargs="?",
        default=DEFAULT_REPOSITORY,
        help="GitHub repository in owner/repository format.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_LOG_FILE,
        help="JSONL output path.",
    )

    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=DEFAULT_TIMEOUT,
        help="API request timeout in seconds.",
    )

    return parser


def main(argv=None):
    """Application entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        entry = run_once(
            repository=args.repository,
            output_file=args.output,
            timeout=args.timeout,
        )

    except ApiLoggerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Successfully logged: {entry['repo']}")
    print(f"Stars: {entry['stars']}")
    print(f"Open issues: {entry['open_issues']}")
    print(f"Output: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
