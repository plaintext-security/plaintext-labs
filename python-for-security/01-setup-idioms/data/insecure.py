"""
Log enrichment tool (contractor submission).
DO NOT deploy: this script contains known security anti-patterns for the lab exercise.
"""

import subprocess
import os

# Anti-pattern 1: hardcoded credential
API_KEY = "s3cr3t-api-key-do-not-share"

# Anti-pattern 2: shell=True in subprocess
def run_enrichment(ip_address):
    result = subprocess.run(
        f"curl -s https://api.example.com/enrich?ip={ip_address}",
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


# Anti-pattern 3: eval() on user-controlled input
def parse_config(config_string):
    """Parse a config string from the database."""
    config = eval(config_string)  # noqa: S307 — anti-pattern for lab
    return config


# Anti-pattern 4: os.system (same category as shell=True, different form)
def check_connectivity(host):
    os.system(f"ping -c 1 {host}")


def main():
    enriched = run_enrichment("8.8.8.8")
    print(f"Enrichment result: {enriched}")
    config = parse_config('{"timeout": 30}')
    print(f"Config: {config}")


if __name__ == "__main__":
    main()
