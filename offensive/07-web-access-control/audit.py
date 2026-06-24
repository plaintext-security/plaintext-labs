#!/usr/bin/env python3
"""
Broken access control audit — internal order portal.

Demonstrates:
  1. Authentication — confirm login works for two users
  2. IDOR (CWE-639) — jsmith reads bmartin's order by guessing the ID
  3. Vertical escalation (CWE-284) — normal user bypasses admin check via X-Role header
  4. Access-control matrix — all endpoints × all roles
  5. Fix — what the server-side check should look like

Uses Flask's built-in test client (no external HTTP needed).
All code runs inside the container; no live network required.

> Only test systems you own or have explicit written authorisation to test.

Usage:
    python3 audit.py          # full demo
    python3 audit.py --matrix # print access-control matrix only
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "/lab/app")
from app import app as flask_app  # noqa: E402

flask_app.config["TESTING"] = True
DIVIDER = "─" * 64


def login(client, username: str, password: str):
    r = client.post("/api/login", json={"username": username, "password": password})
    return r.status_code, r.get_json()


def get(client, path: str, headers: dict | None = None):
    return client.get(path, headers=headers or {})


def fmt(r) -> str:
    body = r.get_json()
    if body is None:
        return f"HTTP {r.status_code}"
    return f"HTTP {r.status_code}  {json.dumps(body)[:120]}"


def demo() -> int:
    print("=" * 64)
    print("Broken Access Control Audit")
    print("OWASP A01: Broken Access Control (CWE-639 + CWE-284)")
    print("=" * 64)

    # ── Step 1: Authentication ────────────────────────────────────────────
    print("\n[Step 1] Authentication — confirm two users exist")
    print()
    with flask_app.test_client() as c1, flask_app.test_client() as c2:
        sc, body = login(c1, "jsmith", "password")
        print(f"  jsmith   login: HTTP {sc}  role={body.get('role')}")
        sc, body = login(c2, "bmartin", "123456")
        print(f"  bmartin  login: HTTP {sc}  role={body.get('role')}")

    # ── Step 2: Normal access ─────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 2] Baseline — each user accesses their own order")
    print()
    with flask_app.test_client() as c:
        login(c, "jsmith", "password")
        r = get(c, "/api/orders/101")   # jsmith owns order 101
        print(f"  jsmith  GET /api/orders/101 (own order)   → {fmt(r)}")

    # ── Step 3: IDOR ──────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 3] Bug 1 — IDOR: jsmith reads bmartin's order (id=102)")
    print()
    with flask_app.test_client() as c:
        login(c, "jsmith", "password")
        print("  jsmith is authenticated; his orders are 101, 103.")
        print("  Attacker changes the ID in the URL: /api/orders/102")
        print()
        r = get(c, "/api/orders/102")  # bmartin owns order 102
        print(f"  jsmith  GET /api/orders/102 (bmartin's order) → {fmt(r)}")
        if r.status_code == 200:
            order = r.get_json()
            print()
            print(f"  ✓ IDOR confirmed — jsmith read bmartin's order:")
            print(f"    amount:      ${order['amount']:,}")
            print(f"    description: {order['description']}")
            print()
            print("  Root cause: /api/orders/<id> authenticates the caller but never")
            print("  checks whether the caller owns the order (missing object-level auth).")

    # ── Step 4: Vertical escalation ────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 4] Bug 2 — vertical escalation: normal user reaches admin endpoint")
    print()
    with flask_app.test_client() as c:
        login(c, "jsmith", "password")
        r = get(c, "/api/admin/users")
        print(f"  jsmith  GET /api/admin/users (no header)           → {fmt(r)}")

        r = get(c, "/api/admin/users", {"X-Role": "admin"})
        print(f"  jsmith  GET /api/admin/users + X-Role: admin       → {fmt(r)}")
        if r.status_code == 200:
            users = r.get_json()
            print()
            print(f"  ✓ Escalation confirmed — jsmith (role=user) read the user list:")
            for u in users:
                print(f"    id={u['id']}  {u['username']:<12}  role={u['role']}")
            print()
            print("  Root cause: /api/admin/users trusts the X-Role header from the client.")
            print("  Any caller can add X-Role: admin to bypass the role check.")

    # ── Step 5: Access-control matrix ──────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 5] Access-control matrix — all endpoints × all users/roles")
    print()
    endpoints = [
        ("/api/orders/101", None, "jsmith's order"),
        ("/api/orders/102", None, "bmartin's order"),
        ("/api/orders/103", None, "jsmith large order"),
        ("/api/admin/users", None, "admin endpoint (no header)"),
        ("/api/admin/users", {"X-Role": "admin"}, "admin endpoint + X-Role spoof"),
        ("/api/my/orders",  None, "own orders only (correct)"),
    ]
    credentials = [
        ("jsmith",  "password", "user"),
        ("bmartin", "123456",   "user"),
    ]

    print(f"  {'Endpoint (caller)':<48}  Status")
    print(f"  {'─'*48}  {'─'*8}")
    for username, password, role in credentials:
        for path, hdrs, label in endpoints:
            with flask_app.test_client() as c:
                login(c, username, password)
                r = get(c, path, hdrs)
                hdr_note = " [X-Role spoof]" if hdrs else ""
                row = f"{username}({role})  {label}{hdr_note}"
                flag = "  ← VULN" if (
                    (r.status_code == 200 and username == "jsmith" and "bmartin" in label) or
                    (r.status_code == 200 and "admin" in label and role != "admin")
                ) else ""
                print(f"  {row:<48}  HTTP {r.status_code}{flag}")
        print()

    # ── Step 6: Fix ─────────────────────────────────────────────────────────
    print(DIVIDER)
    print("[Step 6] Fix — what the server-side checks should be")
    print()
    print("  Bug 1 (IDOR) — add ownership check to /api/orders/<id>:")
    print()
    print("    order = ORDERS.get(order_id)")
    print("    if not order:")
    print("        return 404")
    print("    if order['user_id'] != user['id']:   # ← ADD THIS")
    print("        return 403                        #")
    print("    return order")
    print()
    print("  Bug 2 (vertical escalation) — remove the X-Role header trust:")
    print()
    print("    # REMOVE:  role = request.headers.get('X-Role', user['role'])")
    print("    role = user['role']   # ← derive from session only")
    print("    if role != 'admin':")
    print("        return 403")
    print()
    print("  General principle: deny by default; enforce on every request;")
    print("  never derive role/identity from client-controlled input.")

    print(f"\n{'=' * 64}")
    print("Audit complete — OWASP A01 broken access control demonstrated")
    print(f"{'=' * 64}\n")
    return 0


if __name__ == "__main__":
    sys.exit(demo())
