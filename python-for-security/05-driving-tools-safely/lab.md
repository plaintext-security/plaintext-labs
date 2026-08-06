# Lab 05 — Wrap a Tool Without Opening a Shell

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/05-driving-tools-safely/`: the `sift` project, the tools to wrap
(`nmap`, `whois`, **`suricata`**, **`tshark`**, **`zeek`**) plus the pinned infection pcap, and a
copilot-generated wrapper with a planted `shell=True` bug for the review beat. `make demo` drives Suricata
over the pcap to produce `eve.json`, then parses it through `sift`'s pydantic union; `make gen-zeek` ships a
second sensor's view (`data/zeek/*.log`) of the *same* capture for the cross-source stretch.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/05-driving-tools-safely
make up
make shell
make demo    # runs the safe wrapper and demonstrates the injection the unsafe one allows
make down
```

Reproducible at zero cost; everything runs locally against targets you control in the lab.

## Scenario

`sift` needs to enrich indicators by driving external tools. You'll build a safe subprocess wrapper into
it — then find and fix the command-injection hole in a copilot-generated version. The only targets are
ones you own inside the lab.

> Only test systems you own or have explicit written permission to test. Scan and shell out only against
> the lab's local targets.

## Do

1. [ ] **Find the planted injection.** You're handed a copilot-generated tool wrapper. Locate the
   `shell=True` command injection, and write down the *tell* that gave it away (the f-string interpolated
   into a shell string).
2. [ ] **Prove it's exploitable.** In the lab, pass an indicator like `x; id` (or `$(id)`) through the
   unsafe wrapper and observe the injected command run. This is why the review matters.
3. [ ] **Rewrite it safe.** Convert the wrapper to `subprocess.run([...], shell=False)` with an argument
   list. Confirm the same malicious indicator is now inert (passed as one literal argument).
4. [ ] **Validate before you shell out.** Add a boundary check (reuse Module 02's approach): an indicator
   derived from a real EVE field (a `src_ip`/`dest_ip`, or a `dns.rrname`/`tls.sni` from the dissectors)
   must match its expected shape (IP/domain) before any tool sees it. Reject the malformed.
5. [ ] **Drive a dissector; parse structured output.** Wrap `suricata -r <pcap> -l <outdir>` behind the
   same safe pattern to produce `eve.json`, then parse *that* structured output — the typed `alert` events
   (`signature`, `severity`, five-tuple) through `sift`'s pydantic union — not scraped stdout text. The
   path you pass Suricata is untrusted input like any other: `shell=False`, list args. (Same move works for
   `tshark -T ek`/`-T json`.)
6. [ ] **Automate & own it.** Commit the safe wrapper and the validation into `sift`, plus a one-line
   trust-checklist entry ("every `subprocess` call: `shell=False`, list args, validated input"). Note in
   the commit what the copilot got wrong and how you caught it.

## Success criteria — you're done when
- [ ] You found the planted `shell=True` injection and demonstrated it running an injected command.
- [ ] The rewritten wrapper uses `shell=False` with a list, and the same payload is now inert.
- [ ] Indicators are validated/allowlisted before any tool is invoked.
- [ ] The wrapper parses structured tool output, not scraped text.

## Deliverables
The updated `sift` repo: the safe tool wrapper, the input validation, the structured-output parser, and a
trust-checklist entry for reviewing `subprocess` calls. Do **not** commit scan output or any target data.

## AI acceleration
The module *is* an AI-review exercise: the vulnerable wrapper is exactly what a copilot ships. The skill
you're proving is catching `shell=True` on sight and reflexively rewriting to the list form — then
encoding that as a checklist so you (and your team) catch the next one. Have the copilot generate the
`nmap` wrapper fresh and check whether it reintroduces the bug; it often does.

## Connects forward
The safe, structured wrapper is what Module 06 exposes through both a `typer` CLI and a `FastAPI` service,
and what Module 08 red-teams once it's reachable by an LLM. The command-injection reflex transfers
directly to the Offensive track's injection modules — same bug, other side.

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
