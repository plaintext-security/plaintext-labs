"""
HTTP echo server — shows every header, body, and cookie the client sends.
A more reliable alternative to httpbin for teaching HTTP mechanics.
"""
from flask import Flask, request, make_response, redirect, jsonify
import json

app = Flask(__name__)


@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def echo():
    """Echo back method, headers, body, and cookies."""
    return jsonify({
        "method": request.method,
        "url": request.url,
        "headers": dict(request.headers),
        "args": dict(request.args),
        "form": dict(request.form),
        "data": request.get_data(as_text=True),
        "cookies": dict(request.cookies),
        "remote_addr": request.remote_addr,
    })


@app.route("/redirect-me")
def redir():
    """Returns a 301 redirect to /after-redirect."""
    return redirect("/after-redirect", code=301)


@app.route("/after-redirect")
def after_redirect():
    return jsonify({"message": "You followed the redirect!", "url": request.url})


@app.route("/set-cookie")
def set_cookie():
    """Sets a session cookie."""
    resp = make_response(jsonify({"message": "Cookie set — send it back on the next request"}))
    resp.set_cookie("session_token", "meridian-abc123", httponly=True)
    return resp


@app.route("/cookie-echo")
def cookie_echo():
    """Shows what cookies the client sent."""
    return jsonify({
        "cookies_received": dict(request.cookies),
        "note": (
            "The session_token cookie was carried here from /set-cookie. "
            "This is how a server recognises a returning client across "
            "stateless HTTP requests."
        )
    })


@app.route("/role-check")
def role_check():
    """Demonstrates why trusting a client-supplied header is dangerous."""
    role = request.headers.get("X-Role", "user")
    if role == "admin":
        return jsonify({
            "role": role,
            "data": "SECRET: quarterly financials for Meridian Financial",
            "warning": "IDOR! The server trusted the X-Role header from the client."
        }), 200
    return jsonify({"role": role, "data": "Public data only"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
