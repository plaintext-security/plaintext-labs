#!/usr/bin/env python3
"""
serve_jwks.py — publish the OIDC provider's public keys (a tiny JWKS endpoint).

A real OIDC provider exposes a discovery document and a JWKS URL so a relying party
(AWS STS) can fetch the public key and verify a token's signature. This serves the
two endpoints AWS would fetch:

    /.well-known/openid-configuration   -> points at the jwks_uri
    /jwks                                -> the JWKS (public keys) written by mint_oidc_token.py

This is included so the OIDC flow is *complete and legible* — you can curl the JWKS the
same way STS would. LocalStack community does not strictly fetch+verify against it (see
lab.md), but a real STS does, and this is what it would read.

Run:  python serve_jwks.py        # listens on 0.0.0.0:8080
"""
import http.server
import json
import os
import socketserver

HERE = os.path.dirname(os.path.abspath(__file__))
JWKS_PATH = os.path.join(HERE, "oidc", "jwks.json")
ISSUER = os.environ.get("OIDC_ISSUER", "http://oidc-provider:8080")
PORT = int(os.environ.get("OIDC_PORT", "8080"))


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, body: bytes, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/.well-known/openid-configuration":
            doc = {
                "issuer": ISSUER,
                "jwks_uri": f"{ISSUER}/jwks",
                "id_token_signing_alg_values_supported": ["RS256"],
            }
            self._send(json.dumps(doc, indent=2).encode())
        elif self.path == "/jwks":
            try:
                with open(JWKS_PATH, "rb") as f:
                    self._send(f.read())
            except FileNotFoundError:
                self._send(b'{"keys": []}', 404)
        else:
            self._send(b'{"error": "not found"}', 404)

    def log_message(self, *args):
        pass  # quiet


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"JWKS server on :{PORT} (issuer {ISSUER})")
        httpd.serve_forever()
