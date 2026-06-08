"""Meridian Financial — employee directory (INTENTIONALLY VULNERABLE).

A deliberately insecure search endpoint for learning SQL injection. The query is
built by string concatenation, so user input crosses straight into the SQL control
plane. Do not copy this pattern into anything real — the lab's whole point is to
exploit it, then fix it with parameterised queries.
"""
import os
import sqlite3

from flask import Flask, jsonify, request

DB = "/app/meridian.db"
app = Flask(__name__)


def init_db():
    """Seed a tiny, deterministic directory plus a juicier table to steal from."""
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("CREATE TABLE employees (name TEXT, username TEXT, role TEXT)")
    cur.executemany(
        "INSERT INTO employees VALUES (?, ?, ?)",
        [
            ("Jane Doe", "jdoe", "Analyst"),
            ("John Smith", "jsmith", "Helpdesk"),
            ("Maria Garcia", "mgarcia", "Finance"),
        ],
    )
    # The prize: credentials the search endpoint should never be able to reach.
    cur.execute("CREATE TABLE users (username TEXT, password TEXT)")
    cur.executemany(
        "INSERT INTO users VALUES (?, ?)",
        [
            ("admin", "S3cr3t-Meridian-Admin!"),
            ("svc_backup", "b@ckup-svc-2026"),
        ],
    )
    con.commit()
    con.close()


@app.route("/search")
def search():
    name = request.args.get("name", "")
    con = sqlite3.connect(DB)
    cur = con.cursor()
    # === THE VULNERABILITY ===
    # User input is concatenated directly into the SQL string. The fix is a
    # parameterised query:  "... WHERE name LIKE ?", ('%' + name + '%',)
    query = "SELECT name, role FROM employees WHERE name LIKE '%" + name + "%'"
    try:
        rows = cur.execute(query).fetchall()
    except sqlite3.Error as exc:
        return jsonify({"query": query, "error": str(exc)}), 400
    finally:
        con.close()
    # Echoing the built query back is a teaching aid (real apps must not) — it
    # lets you *see* how your input rewrote the SQL.
    return jsonify({"query": query, "results": rows})


@app.route("/")
def index():
    return jsonify({"try": "/search?name=Doe", "hint": "the directory is searchable by name"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
