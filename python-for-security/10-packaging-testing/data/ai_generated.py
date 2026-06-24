"""
ssh-log-analyzer — AI-generated first draft.
DO NOT deploy: this script contains four deliberate security bugs for the lab exercise.

Bugs planted:
1. SQL injection: username parameter concatenated directly into query string
2. Missing error handling: httpx call has no timeout and no try/except
3. Wrong regex: log pattern character class is incorrect (misses some valid lines)
4. Hardcoded credential in module scope
"""

import re
import sqlite3

import httpx

# Bug 4: hardcoded credential (should come from environment variable)
DB_PASSWORD = "sup3r_s3cret_db_pw_2026"

LOG_PATTERN = re.compile(
    # Bug 3: character class [0-9\.] is wrong — the backslash before the dot inside
    # a character class is redundant but worse: it only matches the digits 0-9 and a
    # literal backslash and dot. Should be: r"\d{1,3}(\.\d{1,3}){3}"
    r"Failed password for \S+ from ([0-9\.]+) port \d+"
)


def get_user_logs(username: str, db_path: str = ":memory:") -> list:
    """Fetch log entries for a specific username from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Bug 1: SQL injection — username is concatenated directly
    query = f"SELECT * FROM logs WHERE username = '{username}'"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows


def check_ip_reputation(ip: str) -> dict:
    """Query the threat-intel API for an IP address."""
    # Bug 2: no timeout, no error handling — hangs if API is down, crashes on error
    response = httpx.get(f"https://api.example.com/enrich?ip={ip}")
    return response.json()


def extract_ips_from_log(log_text: str) -> list[str]:
    """Extract source IPs from SSH auth log lines."""
    return LOG_PATTERN.findall(log_text)
