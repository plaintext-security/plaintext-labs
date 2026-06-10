# Lab 08 — Exploit SSRF and XXE

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/08-web-ssrf-xxe
make up
```

The container runs a minimal Flask app (`app/app.py`) — Meridian Financial's
document portal — with two deliberate server-side bugs. A mock cloud metadata
server runs on `127.0.0.1:5001` inside the container, simulating what the
AWS Instance Metadata Service (169.254.169.254) looks like from an EC2 host.

## Scenario

Meridian's document portal has two features: a URL fetcher (for link previews)
and an XML invoice importer. Both features process server-supplied data without
validating the input source. Neither can be exploited from the UI — but the API
endpoints have no server-side trust boundary.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] Read `app/app.py` and find the two vulnerable functions before running anything.
   For each: what input does the server act on without validating its source, what does
   "confused deputy" mean here, and which `urllib` / `lxml` arguments make it exploitable?
   (`make demo` runs the validated exploit for both — use it afterwards to check what each
   exploit extracts and what the fix is.)

2. [ ] Exploit the SSRF (Bug 1) yourself: get the server to fetch the internal metadata
   endpoint on your behalf and return what only it can reach. (The mock metadata server is
   on `127.0.0.1:5001` inside the container — why can't you hit it directly, and which
   request parameter makes the server do it for you?) In AWS this address is
   `169.254.169.254`; what did Capital One's attacker do once they had the IAM credentials?

3. [ ] Exploit the XXE (Bug 2) yourself: craft an XML body with an external entity that
   reads a file off the server's filesystem, and send it to the importer endpoint. Then
   escalate — read a more sensitive file, and chain it to SSRF by swapping the entity to an
   `http://` URL pointing at the metadata service. (What entity declaration reads a local
   file, and what makes the parser resolve it?)

4. [ ] Apply Bug 1's fix: edit `app/app.py` and add the URL allow-list. Re-run
   `make demo` and confirm the SSRF returns HTTP 403.

5. [ ] Apply Bug 2's fix: harden the XML parser so it no longer resolves external
   entities. Re-run and confirm the XXE returns a parse error (no file read). (Which
   `lxml` parser options disable entity resolution and DTD loading?)

## Success criteria — you're done when

- [ ] You made the server fetch internal credentials via SSRF (simulated IMDSv1).
- [ ] You injected an XXE entity to read a local file from the server's filesystem.
- [ ] You applied both fixes and confirmed each returns the right error.
- [ ] You can explain the "confused deputy" model and how SSRF + XXE share the same root cause.
- [ ] You can describe the IMDSv2 change that mitigates the Capital One-style SSRF.

## Deliverables

`ssrf-xxe.md`: for each bug — the vulnerable code snippet, the exploit payload,
the response that proved it, and the fixed code. One sentence linking SSRF to
the Capital One breach and explaining why IMDSv2's PUT-first flow helps.

## Automate & own it

**Required.** Write `probe.py` that:
- Takes a target URL as an argument
- Probes a list of internal addresses (127.0.0.1, common RFC 1918 ranges, 169.254.x.x)
  via the `/api/fetch?url=` parameter
- Reports which internal addresses responded

AI drafts the probe list and loop; you reason about what the server's network
can actually reach and annotate each result. Commit `probe.py` and `ssrf-xxe.md`.

## AI acceleration

Ask a model to explain why IMDSv2 (PUT request to get a session token first)
makes the Capital One SSRF harder — and then verify by reading the AWS docs.
The model explains the control; you verify the mechanism against the spec.

## Connects forward

SSRF to the metadata service is the bridge from "web pentesting" to cloud
compromise. Track 05 (cloud) picks up from here — IAM privilege escalation,
S3 misconfiguration, and cloud-specific attack paths all start from leaked
credentials or reachable metadata services.

## Marketable proof

> "I exploit SSRF and XXE — the server-side classes behind the Capital One
> breach — and can explain the allow-list and parser-hardening fixes, plus why
> IMDSv2 raises the bar for cloud SSRF."

## Stretch

- Research what the Capital One attacker did after obtaining IAM credentials
  (CVE-2019-5736 is unrelated; look at the 2019 Capital One breach report).
  What S3 permissions did the EC2 role have?
- Chain XXE to SSRF: replace `file:///etc/hostname` with
  `http://127.0.0.1:5001/latest/meta-data/iam/security-credentials/`
  in the entity declaration. Does the XML parser fetch it?
