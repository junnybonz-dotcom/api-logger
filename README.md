
# API Logger

[![API Logger CI](https://github.com/junnybonz-dotcom/api-logger/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/junnybonz-dotcom/api-logger/actions/workflows/tests.yml)

A Python command-line application that retrieves public GitHub repository statistics and records them in a JSON Lines file.

The project demonstrates API integration, HTTP error handling, response validation, JSON serialization, file handling, automated testing, and GitHub Actions CI.

## Features

- Retrieves GitHub repository information through the REST API.
- Supports different repositories using command-line arguments.
- Records repository name, star count, and open issue count.
- Generates timezone-aware UTC timestamps.
- Appends records to a JSONL history file.
- Supports configurable output paths.
- Supports configurable request timeouts.
- Handles HTTP errors, timeouts, connection failures, and invalid JSON.
- Validates API response fields before logging.
- Includes automated tests using mocked API responses.

## Requirements

- Python 3.12 or newer
- pip
- requests

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

Run with the default repository:

```bash
python api_logger.py
```

The default repository is `python/cpython`.

Specify another repository:

```bash
python api_logger.py microsoft/vscode
```

Choose an output file:

```bash
python api_logger.py python/cpython --output history/python.jsonl
```

Change the API timeout:

```bash
python api_logger.py python/cpython --timeout 5
```

Display available arguments:

```bash
python api_logger.py --help
```

## JSONL Output

Each successful execution appends one JSON object to the output file.

Example:

```json
{"timestamp":"2026-11-22T13:00:00+00:00","repo":"python/cpython","stars":12345,"open_issues":500}
```

JSON Lines stores one independent JSON record per line, making it convenient to process historical records later with Python or other data tools.

The default output file is `api_log.jsonl` in the project directory.

Generated history files are excluded through `.gitignore`.

## Automated Tests

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

The test suite covers:

- Repository identifier validation
- Successful API responses
- Request timeouts
- HTTP 404 errors
- Connection failures
- Invalid JSON responses
- Invalid response structures
- UTC timestamp generation
- JSONL file creation and appending
- Dependency injection
- Command-line success and error handling

Tests use mocked HTTP responses and temporary files. They do not make real API requests or modify your personal log history.

## Continuous Integration

GitHub Actions automatically runs the test suite on:

- Python 3.12
- Python 3.13
- Python 3.14

The workflow also checks Python syntax through `py_compile`.

## Architecture

```text
CLI arguments
     |
     v
fetch_repo_data()
     |
     v
GitHub REST API
     |
     v
Validate response
     |
     v
build_log_entry()
     |
     v
append_log()
     |
     v
api_log.jsonl
```

## Error Handling

The application handles:

- Request timeouts
- HTTP errors, including missing repositories
- API rate limiting or forbidden responses
- Connection failures
- Invalid JSON
- Unexpected response fields
- Local file-writing failures

The application returns a nonzero exit code when a request or logging operation fails.

## What Broke While Building This

The first version used `response.json()` without checking the HTTP status code first. An unsuccessful response could cause a JSON decoding error instead of a useful message.

This was improved by calling `response.raise_for_status()` before parsing the response.

The second version opened the log file using write mode (`"w"`). This overwrote the previous history each time the script ran.

It was changed to append mode (`"a"`), preserving earlier records.

## Limitations

- The project currently targets public GitHub repositories.
- GitHub API rate limits may affect repeated unauthenticated requests.
- The application records statistics when executed; it does not run continuously by itself.
- It stores historical records locally in JSONL format.

## Skills Demonstrated

- Python functions and exception handling
- HTTP requests and REST API integration
- JSON parsing and serialization
- JSON Lines file handling
- Datetime and UTC timestamps
- Command-line interfaces with argparse
- Dependency injection and mocking
- Automated testing with unittest
- Git and GitHub
- GitHub Actions CI
