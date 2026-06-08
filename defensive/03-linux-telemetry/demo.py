#!/usr/bin/env python3
"""Linux telemetry demo: parse audit.log + query the live host with osquery.

Two sources, one lesson: the kernel (auditd) and a live SQL query layer (osquery)
both answer questions about host activity — but they ask different questions.
Auditd captures WHAT happened (event history); osquery answers WHAT IS (current state).
"""
import re
import subprocess
import sys
from pathlib import Path

AUDIT_LOG = Path(__file__).parent / "data" / "audit_events.txt"

# ─────────────────────── audit.log parser ─────────────────────────

TIMESTAMP_RE = re.compile(r"msg=audit\((\d+\.\d+):(\d+)\)")
COMM_RE      = re.compile(r'comm="([^"]+)"')
EXE_RE       = re.compile(r'exe="([^"]+)"')
KEY_RE       = re.compile(r'key="([^"]+)"')
PATH_RE      = re.compile(r'name="([^"]+)"')
ARGC_RE      = re.compile(r"argc=(\d+)")
ARG_RE       = re.compile(r'a(\d+)="([^"]+)"')
UID_RE       = re.compile(r"\buid=(\d+)")
EUID_RE      = re.compile(r"\beuid=(\d+)")


def parse_audit_log(path: Path):
    """Group audit records by event ID and extract execve + file-open events."""
    events: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        m = TIMESTAMP_RE.search(line)
        if not m:
            continue
        eid = m.group(2)
        ev = events.setdefault(eid, {"lines": []})
        ev["lines"].append(line)
        if "type=SYSCALL" in line:
            ev.update({
                "comm":  (COMM_RE.search(line) or ["", "?"])[1] if COMM_RE.search(line) else "?",
                "exe":   (EXE_RE.search(line) or ["", "?"])[1] if EXE_RE.search(line) else "?",
                "key":   (KEY_RE.search(line) or ["", ""])[1] if KEY_RE.search(line) else "",
                "uid":   (UID_RE.search(line) or ["", "?"])[1] if UID_RE.search(line) else "?",
                "euid":  (EUID_RE.search(line) or ["", "?"])[1] if EUID_RE.search(line) else "?",
                "ts":    m.group(1),
            })
        if "type=EXECVE" in line:
            args = {int(k): v for k, v in ARG_RE.findall(line)}
            ev["argv"] = [args[i] for i in sorted(args)]
        if "type=PATH" in line:
            pn = PATH_RE.search(line)
            ev.setdefault("paths", []).append(pn.group(1) if pn else "?")
    return events


def print_audit_summary(events: dict) -> None:
    print("── auditd: parsed events ──────────────────────────────────────")
    for eid, ev in sorted(events.items(), key=lambda x: x[1].get("ts", "")):
        key = ev.get("key", "")
        if not key:
            continue
        ts = ev.get("ts", "?")
        exe = ev.get("exe", "?")
        euid = ev.get("euid", "?")
        argv = " ".join(ev.get("argv", []))
        paths = ev.get("paths", [])
        label = "⚠ PRIVESC?" if euid == "0" and ev.get("uid") != "0" else ""
        print(f"  [{eid}] ts={ts}  key={key}  euid={euid}  cmd={argv or exe}  {label}")
        for p in paths:
            print(f"         → file touched: {p}")
    print()


# ─────────────────────── osquery queries ──────────────────────────

QUERIES = [
    ("Running processes (top 10 by pid)",
     "SELECT pid, name, cmdline FROM processes ORDER BY pid LIMIT 10;"),
    ("Current users",
     "SELECT uid, username, description FROM users;"),
    ("OS version",
     "SELECT name, version FROM os_version;"),
]


def run_osquery(sql: str) -> str:
    try:
        result = subprocess.run(
            ["osqueryi", "--csv", sql],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() or result.stderr.strip()
    except FileNotFoundError:
        return "(osqueryi not found — install osquery on your host to run live queries)"
    except subprocess.TimeoutExpired:
        return "(query timed out)"


def print_osquery_section() -> None:
    print("── osquery: live host state ───────────────────────────────────")
    for title, sql in QUERIES:
        print(f"\n  [{title}]")
        print(f"  SQL: {sql}")
        output = run_osquery(sql)
        for line in output.splitlines()[:15]:
            print(f"    {line}")
    print()


# ─────────────────────── main ─────────────────────────────────────

def main() -> int:
    print("=" * 62)
    print("Meridian Financial — Linux Telemetry Demo")
    print("=" * 62)
    print()

    events = parse_audit_log(AUDIT_LOG)
    print_audit_summary(events)

    # Highlight interesting findings
    print("── analyst notes ──────────────────────────────────────────────")
    execve_events = [ev for ev in events.values() if ev.get("key") == "execve_watch"]
    priv_escalations = [
        ev for ev in execve_events
        if ev.get("euid") == "0" and ev.get("uid") not in ("0", "?")
    ]
    sensitive_accesses = [ev for ev in events.values() if ev.get("key") == "sensitive_file"]

    print(f"  Total execve events:           {len(execve_events)}")
    print(f"  Privileged executions (uid→0): {len(priv_escalations)}")
    print(f"  Sensitive file accesses:       {len(sensitive_accesses)}")
    if priv_escalations:
        print("  ⚠  Privilege escalation candidates:")
        for ev in priv_escalations:
            print(f"     cmd={' '.join(ev.get('argv', [ev.get('exe', '?')]))}")
    print()

    print_osquery_section()

    print("Tip: the audit rules that generated this data are in data/audit.rules")
    print("     — deploy them with: auditctl -R data/audit.rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
