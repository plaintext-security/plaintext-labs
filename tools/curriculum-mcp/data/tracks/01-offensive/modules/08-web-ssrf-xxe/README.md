# Module 08 — Web Attacks: SSRF, XXE & Deserialization

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *the server-side classes that turn one web bug into cloud compromise.*

## Why this matters
Beyond the client-facing bugs lie the server-side ones — Server-Side Request Forgery, XML
External Entity injection, and insecure deserialization — that let an attacker make the
server itself act on their behalf. SSRF against a cloud metadata endpoint is exactly how the
2019 Capital One breach exposed 100M+ records, which is why these classes matter far more than
their frequency suggests.

## Objective
Identify and exploit SSRF, XXE, and insecure deserialization against deliberately vulnerable
apps, and explain each root cause and fix.

## The core idea
The earlier web modules abused the *client→server* trust; these three abuse the **server's own
position and privileges**. SSRF, XXE, and insecure deserialization share one shape: you trick the
server into acting on your behalf using *its* network access, *its* filesystem, *its* identity — which
is why they punch far above their frequency, because the server can reach what you can't. The headline
case is SSRF against the cloud metadata endpoint (`169.254.169.254`): the server fetches a URL you
control, you aim it at the metadata service, and you walk off with the host's IAM credentials. That is
precisely the 2019 Capital One breach — 100M+ records — from one SSRF.

The unifying mental model is the **confused deputy**: a powerful component — the HTTP fetcher, the XML
parser, the deserializer — acting on attacker input without realising it's been redirected. XXE is
SSRF-plus-file-read through an XML parser that resolves external entities; insecure deserialization is
"rebuild this object from bytes I control," which becomes code execution. Once your question is "where
does the server act on *my* input using *its own* privileges?", you find all three.

The judgment, and the reason this module matters disproportionately: **this is where a web bug becomes
infrastructure compromise** — the pivot from app to cloud account, which is exactly what the cloud
track's IAM and metadata hardening defends. The fixes all amount to "stop the deputy trusting input":
allow-list outbound destinations, disable external entities, sign or avoid deserialization. A model
explains these abstract classes well, but reliable exploitation needs the target's parser, network
position, and trust relationships — which it can't see. Learn the class from it; verify the exploit
against the real app.

## Learn (~4 hrs)

**Hands-on labs**
- [PortSwigger — Server-Side Request Forgery (SSRF)](https://portswigger.net/web-security/ssrf) — including the cloud-metadata pattern behind Capital One.
- [PortSwigger — XXE injection](https://portswigger.net/web-security/xxe) — abusing XML parsers.
- [PortSwigger — Insecure deserialization](https://portswigger.net/web-security/deserialization) — turning serialized objects into code execution.

## Key concepts
- SSRF and the cloud metadata endpoint (`169.254.169.254`)
- XXE: external entities, file read, and SSRF via XML
- Insecure deserialization → remote code execution
- Why these pivot from "web bug" to "infrastructure compromise"
- The fixes: allow-lists, disabling external entities, avoiding/signing deserialization

## AI acceleration
A model explains these abstract classes and drafts payloads well — but exploiting them
reliably needs you to understand the target's parser, network position, and trust
relationships, which the model can't see. Use it to learn the class; verify the exploit
against the actual app.
