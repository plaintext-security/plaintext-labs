# Lab 05 — Wrap a Tool Without Opening a Shell

*[← Back to the module concept](README.md)*

> **Hands-on lab.** Environment: `plaintext-labs/python-for-security/05-driving-tools-safely` (a
> container with `nmap`, `whois`, **`suricata`**, **`tshark`**, **`zeek`**, a pinned infection pcap, and
> a copilot-generated wrapper carrying a *planted* `shell=True` bug). Objective: **add safe tool-driving
> to `sift`** — `shell=False` argument-list wrappers, validated input, and structured-output parsing —
> and catch the injection a copilot ships. This is the **same `sift`** you've grown since Module 01; here
> it learns to shell out without opening a hole. Target: **~2–3 hrs.**
> *Intermediate-plus: the steps state objectives; you derive the `subprocess`/`shlex` code (with the copilot).*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **`shell=True` hands your string to `/bin/sh`.** | It interprets `;` `\|` `$()` backticks — the copilot's default, and CWE-78 command injection. |
| 2 | **`shell=False` + an argument list is the whole defense.** | Args go straight to `execve`; there's no shell to inject into. Deleting `shell=True` *is* the fix. |
| 3 | **In a triage tool, the input isn't yours.** | The hostname/URL/hash came from an alert an attacker may have shaped — treat every one as hostile. |
| 4 | **Validate before you shell out.** | Reuse Module 02's boundary: an EVE-derived indicator must match its shape (IP/domain) before any tool sees it. |
| 5 | **Parse *structured* output, don't scrape text.** | Drive `suricata -r` → `eve.json`; parse the typed events through `sift`'s pydantic union, not fragile regex. |
| 6 | **This adds safe tool-driving to `sift`.** | Same tool since M01 — Module 06 exposes this wrapper as a CLI + API; Module 08 red-teams it. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea), the `subprocess` "Security Considerations" section, and
> CVE-2021-21300 (the same bug, shipped for real).

---

## Warm-up — answer before you build (2 min)

1. Exactly why is `subprocess.run(["whois", domain])` safe where `subprocess.run(f"whois {domain}",
   shell=True)` is not, when `domain` is attacker-controlled?
2. You "need a pipe" between two tools — how do you do it *without* `shell=True`?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/05-driving-tools-safely
make up       # build the container (nmap, whois, suricata, tshark, zeek + the pcap)
make shell    # drop into sift with the copilot-generated wrapper to review
make demo     # shell=True wrapper EXECUTES an injected command; shell=False + validated refuses it
make down
```

> **Authorization note.** Everything runs locally in the lab container against bundled sample data and
> targets you control — only test systems you own or have explicit written permission to test.

---

## Build it — objective, then a signal (intermediate-plus: you drive the code)

### Step 1 — Find the planted injection (the review beat)

**Concept (30 sec):** Flight-card #1. You're handed a copilot-generated tool wrapper. The tell is an
f-string interpolated into a `subprocess` call with `shell=True`.

**Do:** locate the `shell=True` command injection in the handed wrapper; write down the *tell* that gave
it away in under five seconds.

> **▸ On track if:** you can point to the exact line and name *why* it's exploitable — the interpolated
> input reaches `/bin/sh`, not just the tool.

### Step 2 — Prove it's exploitable

**Concept (30 sec):** Flight-card #3. The input isn't yours; demonstrate what a shaped indicator does.
`make demo` shows this end-to-end.

**Do:** pass an indicator like `x; id` (or `$(id)`) through the unsafe wrapper and observe the injected
command actually run.

> **▸ On track if:** you see `id` (a command you never asked for) execute — concrete proof of why the
> review in Step 1 mattered.

### Step 3 — Rewrite it safe

**Concept (30 sec):** Flight-card #2. Convert to `subprocess.run([...], shell=False)` with a list; the
list form removes the shell entirely.

**Do:** rewrite the wrapper to an argument list and re-run the same malicious indicator.

> **▸ On track if:** the arg-list wrapper runs the tool while a shell-metachar payload in the input is
> treated as **data, not a command** — passed as one literal argument the tool simply rejects as malformed.

### Step 4 — Validate before you shell out

**Concept (30 sec):** Flight-card #4. Defense in depth — reuse Module 02's boundary. A well-formed
argument has a smaller attack surface than a trusted one.

**Do:** add a shape check on an indicator derived from a real EVE field (a `src_ip`/`dest_ip`, or a
`dns.rrname`/`tls.sni`): it must match its expected shape (IP/domain) before any tool is invoked. Reject
the malformed.

> **▸ On track if:** a validated `dest_ip` reaches the tool while a garbage/oversized indicator is
> rejected *at the boundary* — before `subprocess` is ever called.

### Step 5 — Drive a dissector; parse structured output

**Concept (30 sec):** Flight-card #5. The path you pass Suricata is untrusted input like any other —
`shell=False`, list args — and you parse the *structured* result, not scraped stdout.

**Do:** wrap `suricata -r <pcap> -l <outdir>` behind the safe pattern to produce `eve.json`, then feed
the typed `alert` events (`signature`, `severity`, five-tuple) through `sift`'s pydantic union. (Same
move works for `tshark -T ek`/`-T json`.)

> **▸ On track if:** `sift` triages from *parsed* EVE events (not regex over text), and the Suricata
> invocation is a `shell=False` argument list over a path you control.

---

## Prove the control (your finish line)

Commit the safe wrapper into `sift` and confirm the control holds — **both halves**: the would-be
injection is neutralised, *and* the review catches the planted hole.

- [ ] You found the planted `shell=True` injection and demonstrated it running an injected command.
- [ ] The rewritten wrapper uses `shell=False` with a list, and the same payload is now **inert** (one
      literal argument, not a command).
- [ ] Indicators are validated/allowlisted before any tool is invoked.
- [ ] The wrapper parses **structured** tool output (EVE JSON through the pydantic union), not scraped text.
- [ ] A trust-checklist entry exists: *every `subprocess` call — `shell=False`, list args, validated input.*

---

## Recall check — close the doc, answer from memory (3 min)

1. What's the tell that lets you spot command injection in a code review in under five seconds?
2. Why is the same shell-metachar payload RCE under `shell=True` but inert under `shell=False` + a list?
3. Where does validation sit relative to the `subprocess` call, and what does it add on top of `shell=False`?

---

## Deliverables

The updated **`sift`** repo: the safe tool wrapper, the input validation, the structured-output parser,
and a trust-checklist entry for reviewing `subprocess` calls. Do **not** commit scan output or any target
data — lab artifacts (captures, `eve.json`, dumps) stay out of commits.

## Automate & own it

**Required.** Commit the safe wrapper and the validation into `sift`, plus the one-line trust-checklist
entry ("every `subprocess` call: `shell=False`, list args, validated input"). In the commit/PR, note
exactly what the copilot got wrong (the f-string into `shell=True`) and how you caught it. Then have the
copilot generate the `nmap` wrapper *fresh* and check whether it reintroduces the bug — it often does;
that's the point.

## Definition of done (`driving-tools-safely` ✅)

- [ ] The safe, validated, structured-output wrapper is committed into `sift`.
- [ ] You demonstrated the injection running *and* the rewritten wrapper rendering the same payload inert.
- [ ] The trust-checklist entry is in the repo, and you can explain all six flight-card facts cold.

## Connects forward

The safe, structured wrapper is what **Module 06** exposes through both a `typer` CLI and a `FastAPI`
service, and what **Module 08** red-teams once it's reachable by an LLM. The command-injection reflex
transfers directly to the Offensive track's injection modules — same bug, other side.

## Marketable proof

> "I wrap external security tools from Python without command-injection risk — `shell=False`, list args,
> validated input, structured-output parsing — and I catch the `shell=True` holes an AI copilot ships."

## Stretch (optional)

- Add a `bandit` (or `ruff` security-rule) CI check that fails the build on `shell=True`, so the class
  can't come back in.
- Wrap a second tool (`pymisp` or a VirusTotal query) behind the same safe pattern and share the
  validation.
- **Dissector: `flow` + `fileinfo` (and reconcile against `tshark`).** Grow `sift`'s discriminated union
  with two more event types from the same driven-tool output: `FlowEvent` (`event_type:"flow"`, the
  connection summary) and `FileinfoEvent` (`event_type:"fileinfo"`, with `fileinfo.filename` and
  `fileinfo.sha256` for files carved from the traffic). This continues the growing union you started in
  M02 (`dns`), M03 (`http`), and M04 (`tls`); anything still unhandled stays quarantined, never fatal.
  Then — tying the dissector to *this* module's drive-a-tool skill — drive `tshark -T ek` over the same
  pcap and reconcile its dissection against Suricata's: do the two tools agree on the flows and the
  carved-file hashes?
  *Acceptance:* every line of `eve.json` validates to a known event type (`alert`/`flow`/`fileinfo`/…) or
  is quarantined; the `fileinfo` records surface `filename` + `sha256`; and you report where Suricata's
  and `tshark`'s views of the same pcap agree or diverge.
- **Second sensor: reconcile Zeek against Suricata (a genuinely *different* source).** Everything so far
  parses one tool's output — Suricata EVE JSON. Now run **Zeek** over the *same* pcap (`make gen-zeek` ships
  `data/zeek/{conn,dns,http,ssl}.log`) and teach `sift` a different *schema*: Zeek's native **TSV** logs
  with their `#fields`/`#types` header — not JSON, so a different parser entirely, and the real test of
  whether your domain model is source-agnostic. Drive Zeek the same safe way (list-form args, no
  `shell=True`), parse the TSV into `sift`'s domain model, and **reconcile the two sensors**: the STRRAT C2
  `141.98.10.79` that Suricata *alerts* on appears in Zeek's `conn.log` as a bare connection with no
  verdict, and the RAT's `ip-api.com` recon shows in both. Suricata is opinionated (detection), Zeek is
  descriptive (facts) — the lesson is that your typed boundary normalizes both into one model.
  *Acceptance:* `sift` ingests Zeek TSV (correctly reading the `#fields` header) *and* Suricata EVE into the
  **same** domain type; the same triage runs against either source; and you report one indicator (e.g. the
  C2) as seen by both sensors, noting what each view adds that the other doesn't.
- **Third sensor: endpoint telemetry (Sysmon EVTX) — the host side.** Network sensors see a C2 *IP*; they
  can't see which **process** made the call. That's the endpoint's job. `make gen-sysmon` fetches a real
  **Sysmon** EventID 3 (network-connection) sample (Bousseaden's EVTX-ATTACK-SAMPLES — GPL, so *fetched, not
  bundled*), a *third* schema: binary **EVTX** → XML `EventData`, neither JSON nor TSV. Parse it with
  `python-evtx` into `sift`'s domain model and **join host to wire**: a Sysmon EID 3 record ties an
  outbound `DestinationIp` to the `Image` (process) that opened it — so a C2 IP the network sensors flagged
  can be attributed to a process on the host. (Host logs for the STRRAT capture aren't public, so this is a
  separate real incident — the point is that `sift` absorbs endpoint telemetry too, not just packets.)
  *Acceptance:* `sift` parses the Sysmon EVTX into the same domain type as EVE/Zeek; you surface at least
  one EID 3 record as `(process Image, DestinationIp, DestinationPort)`; and you explain the join that turns
  a network-only IOC into a host-attributed one.
