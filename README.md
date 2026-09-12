# API Logger

A small script that calls the GitHub API for a given repo and appends
a timestamped summary (stars, open issues) to `api_log.jsonl`.

## Usage
    python api_logger.py

Each run appends one line to `api_log.jsonl` — run it repeatedly
(e.g. via cron) to build a history over time.

## What broke while building this
- First version used `response.json()` without checking the status
  code first — a 404 or 500 response isn't always valid JSON, and
  the script crashed with a JSONDecodeError instead of a clean message.
  Fixed by calling `response.raise_for_status()` before parsing.
- Second version used `open(LOG_FILE, "w")` — this overwrote the whole
  log on every run instead of building history. Switched to `"a"`.