# Data/target provenance — 07-web-http

This lab uses two HTTP targets:

## 1. `app/` — the local echo server (custom, legible)

A tiny Flask echo server we ship, used to read raw HTTP byte-for-byte (method, headers, body, the
`Set-Cookie` line, redirects, and the `X-Role` IDOR demo). It is a deliberately minimal teaching
target, now scrubbed of any fictional company naming. Keeping it lets the mechanics steps stay
deterministic and dependency-free.

## 2. OWASP Juice Shop — the REAL intentionally-vulnerable target

For the header/cookie **audit**, the lab points at a real app instead of a toy:

- **Image:** `bkimminich/juice-shop:v17.1.1` (pinned; multi-arch amd64/arm64)
- **Project:** OWASP Juice Shop — an OWASP flagship, "probably the most modern and sophisticated
  insecure web application." <https://owasp.org/www-project-juice-shop/>
- **Why:** its responses carry *genuine* security-header gaps and real `Set-Cookie` behavior — authentic
  artifacts, not hand-authored stand-ins. This satisfies "point the audit at a real intentionally-
  vulnerable app."
- Reachable as `http://juice-shop:3000` (lab container) / `http://localhost:3000` (host).

> Authorization: Juice Shop is *designed* to be attacked and runs locally; this is the sanctioned target.

## RUNNER-VALIDATION NEEDED

The multi-service `docker compose up` (echo-server + Juice Shop) and the header audit against
`http://juice-shop:3000` have **not** been run in the authoring environment. Validate on a runner:
`make up`, then `curl -I http://localhost:3000/` shows Juice Shop's real (missing) security headers, and
the header-audit script flags them. (Juice Shop's first boot takes a few seconds — wait for it to be
healthy before auditing.)
