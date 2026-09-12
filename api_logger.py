#!/usr/bin/env python3
"""
api_logger.py — calls a public API and appends a timestamped
summary of the response to a local log file.
"""

import requests
import json
import datetime
import sys

API_URL = "https://api.github.com/repos/python/cpython"
LOG_FILE = "api_log.jsonl"  # one JSON object per line


def fetch_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # raises an exception on 4xx/5xx
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except json.JSONDecodeError:
        print("Response wasn't valid JSON.")
        return None


def log_result(data):
    if data is None:
        return
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "repo": data.get("full_name"),
        "stars": data.get("stargazers_count"),
        "open_issues": data.get("open_issues_count")
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Logged: {entry}")


if __name__ == "__main__":
    data = fetch_data(API_URL)
    log_result(data)