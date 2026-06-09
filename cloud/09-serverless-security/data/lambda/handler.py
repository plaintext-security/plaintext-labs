"""
handler.py — Meridian Financial payment notification processor.
INTENTIONALLY VULNERABLE for security training.

Vulnerabilities present:
1. Event injection: 'command' field passed to subprocess unsanitised (OWASP Serverless #1)
2. Environment variable exposure: sensitive values in env, returned in error responses
3. No input validation on any event fields
"""

import json
import os
import subprocess


def lambda_handler(event, context):
    """Process a payment notification event."""

    account_id = event.get("account_id", "unknown")
    event_type = event.get("event_type", "notification")

    # MISCONFIGURATION 1: 'command' field passed directly to subprocess without validation
    # An attacker who controls the event can inject arbitrary shell commands.
    # Fix: validate command against an explicit allowlist; never shell-execute event input.
    command = event.get("command", "echo 'no command'")
    try:
        result = subprocess.run(
            command,
            shell=True,          # shell=True makes injection trivial
            capture_output=True,
            text=True,
            timeout=5,
        )
        cmd_output = result.stdout + result.stderr
    except Exception as e:
        cmd_output = str(e)

    # MISCONFIGURATION 2: environment variables returned in error path
    # If the function raises an exception, the error response includes os.environ.
    # Fix: never include environment variables in responses; retrieve secrets at runtime from Vault/SSM.
    env_vars = dict(os.environ)  # includes MERIDIAN_API_KEY and any other injected secrets

    response_body = {
        "status": "processed",
        "account_id": account_id,
        "event_type": event_type,
        "command_output": cmd_output,  # attacker sees the output of their injected command
    }

    return {
        "statusCode": 200,
        "body": json.dumps(response_body),
    }
