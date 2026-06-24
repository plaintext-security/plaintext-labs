# Lab 13 — Run a C2 Framework

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/13-c2-postex
make up
```

You'll operate **Sliver** as the real C2. Install it on your operator box
(`curl https://sliver.sh/install | sudo bash`, or grab a release from the
[Sliver repo](https://github.com/BishopFox/sliver)), then start the server, generate an
implant, and catch a session against the lab `target` container.

The compose also ships a **minimal Flask C2** as an annotated reference (not the main tool):
- **c2-server** — Flask-based C2 server (session manager + task queue)
- **target** — host you point a Sliver implant at; also runs the minimal reference beacon
- **operator** — operator console

The reference implant beacons every 5 seconds (±1s jitter) — read it to see the
check-in/task/result loop a framework like Sliver implements at scale.

## Scenario

You've deployed an implant on the target application server. Operate a **real
open-source C2 framework — [Sliver](https://github.com/BishopFox/sliver)** (Bishop Fox,
GPLv3) — to maintain access, enumerate the host, and establish persistence. Then switch
hats: analyze what you left on the wire and how a defender would detect it. The minimal
Flask C2 that ships with this lab stays as an annotated reference for the session/task/result
API a real C2 implements under the hood.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] **Operate Sliver (primary).** Start the Sliver server, generate an implant for the
   `target` (an HTTP or mTLS beacon), run it on the target, and catch the session/beacon in
   your Sliver console. (Which Sliver command generates an implant? How do you switch between
   a long-poll `session` and an interval `beacon`? See the Sliver docs at
   [sliver.sh](https://sliver.sh/docs).) Confirm you have an active callback before moving on.

2. [ ] **Run post-ex through Sliver.** From the session/beacon, run at least three post-ex
   commands — host enumeration (`whoami`, `ls`, `info`), a file `download`, and one more of
   your choice — and note what the operator sees vs. what crosses the wire. Then establish a
   persistence mechanism and record the artifact it leaves.

3. [ ] **Reference C2 — read the API under the hood.** Read the bundled `implant/beacon.py`
   and `server/c2_server.py` to see the minimal version of what Sliver does:
   - What data does each check-in POST? How does the implant apply jitter, and why?
   - How does the server track sessions and run the task queue (FIFO push/pop)?
   - What does the operator see vs. what the implant sends?
   (`make demo` runs this minimal reference C2 end-to-end so you can watch the lifecycle.)

4. [ ] **Optional — drive the reference C2 by hand** to feel the raw API the framework hides:
   ```bash
   make shell
   curl http://c2-server:5000/api/sessions
   curl -X POST http://c2-server:5000/api/task \
     -H 'Content-Type: application/json' \
     -d '{"sid":"<SID>","cmd":"id"}'
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

- [ ] You generated a Sliver implant and caught an active session/beacon against the target.
- [ ] You ran at least three post-ex commands through Sliver and established persistence.
- [ ] You can explain the beacon interval, jitter, and why both matter for detection.
- [ ] You read the minimal reference C2 and can map its session/task/result API onto what Sliver does.

## Deliverables

`c2-notes.md`: your Sliver session details, three post-ex outputs, the persistence artifact,
and a comparison of the minimal reference C2 vs. Sliver — what does a real C2 add on protocol
(mTLS/DNS/WireGuard), evasion, and post-ex modules?

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

> "I operate a real open-source C2 framework (Sliver) — generate implants, establish
> sessions, run post-ex modules, plant persistence — and can explain the beaconing artifacts
> and detection techniques that surface it in a SOC."

## Stretch

- Modify `implant/beacon.py` to add randomised User-Agent headers. Run RITA-style
  beacon scoring from module 12 against the Zeek conn.log. Does the score change?
- Replace the HTTP transport with HTTPS (self-signed cert). What changes in the
  detection picture?
