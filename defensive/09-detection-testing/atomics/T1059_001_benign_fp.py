"""False-positive test — a benign admin task that looks suspicious to a naive rule.

A sysadmin legitimately encoding a config blob for transmission. Tests whether
our T1059.001 detection generates false positives on normal admin activity.
"""
import base64
import time


def run():
    # Legitimate: sysadmin base64-encodes a config to pass to a remote host
    config = "host=db.internal;port=5432;dbname=finance"
    encoded = base64.b64encode(config.encode()).decode()
    cmdline = f"echo {encoded} | ssh deploy@10.0.2.10 'base64 -d > /etc/app.conf'"

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "EventID": 1,
        "Image": "/bin/bash",
        "CommandLine": cmdline,
        "ParentImage": "/usr/bin/python3",
        "User": "deploy",
        "technique": None,
        "stdout": "(config deployed)",
        "returncode": 0,
        "_note": "legitimate admin activity — should NOT fire a detection",
    }
