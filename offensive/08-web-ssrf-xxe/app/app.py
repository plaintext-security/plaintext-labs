"""
Document processing portal (INTENTIONALLY VULNERABLE).

Deliberately vulnerable for educational use:
  Bug 1: /api/fetch  — SSRF (CWE-918): fetches any URL the user supplies.
  Bug 2: /api/import — XXE (CWE-611): parses XML with external entities enabled.

Fix: Bug 1 — validate against an explicit allow-list of external domains.
     Bug 2 — use defusedxml or etree.XMLParser(resolve_entities=False, load_dtd=False).
"""
import urllib.request
import urllib.error
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Document Portal v2.1"})


@app.route("/api/fetch")
def ssrf_fetch():
    """
    VULNERABLE — Bug 1: SSRF (CWE-918 / OWASP A10)

    The server fetches a URL supplied by the caller with no validation.
    An attacker can aim this at internal services — including the cloud
    metadata endpoint (169.254.169.254) — that the attacker's own IP
    cannot reach directly.

    Real-world pattern: the 2019 Capital One breach was a single SSRF
    against the AWS IMDSv1 endpoint, which returned IAM role credentials,
    giving the attacker S3 access to 100M+ records.

    Fix: allow-list outbound URLs to known external domains; block
         169.254.x.x, 10.x.x.x, 172.16-31.x.x, 127.x.x.x.
    """
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "url parameter required"}), 400

    # BUG: no URL validation — fetches any address the server can reach
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            body = r.read(2000).decode(errors="replace")
        return jsonify({"status": r.status, "body": body})
    except urllib.error.URLError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/import-invoice", methods=["POST"])
def xxe_import():
    """
    VULNERABLE — Bug 2: XXE injection (CWE-611 / OWASP A05)

    The XML parser is configured with external entities enabled.
    An attacker can inject a DOCTYPE entity that references a file:// or
    http:// URI, causing the parser to include its contents in the output.

    Fix: use defusedxml.ElementTree, or lxml with
         etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True).
    """
    xml_data = request.data
    if not xml_data:
        return jsonify({"error": "XML body required"}), 400

    try:
        from lxml import etree
        # BUG: external entity resolution is on
        parser = etree.XMLParser(
            resolve_entities=True,   # unsafe — allows file:// / http:// entities
            load_dtd=True,           # unsafe — loads external DTDs
            no_network=False,        # unsafe — allows remote entity fetches
        )
        tree = etree.fromstring(xml_data, parser=parser)
        invoice_id = tree.findtext("id") or "(none)"
        amount     = tree.findtext("amount") or "(none)"
        return jsonify({"invoice_id": invoice_id, "amount": amount})
    except etree.XMLSyntaxError as e:
        return jsonify({"error": f"XML parse error: {e}"}), 400
