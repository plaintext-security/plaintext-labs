"""
Internal order portal (INTENTIONALLY VULNERABLE).

Deliberately vulnerable for educational use:
  Bug 1: /api/orders/<id> — no ownership check (IDOR, CWE-639)
  Bug 2: /api/admin/users — trusts client-supplied X-Role header (vertical escalation, CWE-284)

Fix: enforce authorization server-side on every request; deny-by-default;
     never trust client-supplied role claims.
"""
from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = "dev-insecure-secret"

# --- In-memory "database" ---------------------------------------------------

USERS = {
    1: {"id": 1, "username": "jsmith",  "role": "user",  "password": "password"},
    2: {"id": 2, "username": "bmartin", "role": "user",  "password": "123456"},
    3: {"id": 3, "username": "hradmin", "role": "admin", "password": "admin"},
}

ORDERS = {
    101: {"id": 101, "user_id": 1, "amount": 45000,  "description": "Security audit invoice — Q1"},
    102: {"id": 102, "user_id": 2, "amount": 12000,  "description": "Consulting contract — bmartin"},
    103: {"id": 103, "user_id": 1, "amount": 880000, "description": "Acquisition target financial data"},
    104: {"id": 104, "user_id": 2, "amount": 3500,   "description": "Travel reimbursement"},
}

# ---------------------------------------------------------------------------

def current_user():
    return USERS.get(session.get("user_id"))


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    for u in USERS.values():
        if u["username"] == data.get("username") and u["password"] == data.get("password"):
            session["user_id"] = u["id"]
            return jsonify({"status": "ok", "username": u["username"], "role": u["role"]})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "ok"})


@app.route("/api/orders/<int:order_id>")
def get_order(order_id):
    """
    VULNERABLE — Bug 1: IDOR (CWE-639 / OWASP A01)

    The server authenticates the caller but never checks whether the caller
    *owns* the requested order.  Any authenticated user can read any order
    by guessing the ID.

    Fix: add   `if order["user_id"] != user["id"]: return 403`
    """
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    order = ORDERS.get(order_id)
    if not order:
        return jsonify({"error": "Not found"}), 404

    # BUG: Missing ownership check
    # FIXED:  if order["user_id"] != user["id"]:
    #             return jsonify({"error": "Forbidden"}), 403
    return jsonify(order)


@app.route("/api/admin/users")
def admin_list_users():
    """
    VULNERABLE — Bug 2: vertical privilege escalation (CWE-284 / OWASP A01)

    The server trusts the X-Role header supplied by the client.  Any user can
    add X-Role: admin to their request and bypass the role check.

    This pattern appears in misconfigured reverse proxies that forward internal
    headers to downstream services.

    Fix: derive role exclusively from the server-side session; never from a
         client-controlled header.
    """
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    # BUG: trusts the client-supplied X-Role header
    role = request.headers.get("X-Role", user["role"])
    if role != "admin":
        return jsonify({"error": "Forbidden — admin only"}), 403

    # Strips passwords before returning
    return jsonify([{k: v for k, v in u.items() if k != "password"} for u in USERS.values()])


@app.route("/api/my/orders")
def my_orders():
    """Correct endpoint for comparison: returns only the caller's orders."""
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    mine = [o for o in ORDERS.values() if o["user_id"] == user["id"]]
    return jsonify(mine)
