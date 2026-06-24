# Lab 12 — Pivot Into an Internal Network

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/12-pivoting
make up
```

The compose starts three containers:
- **attacker** — on `dmz` network only; cannot reach `internal-target`
- **pivot** — on both `dmz` and `internal`; this is the host you've "compromised"
- **internal-target** — on `internal` network only; serves a confidential systems inventory

The `internal: true` flag on the Docker network prevents any routing from outside.

You drive the pivot with a **real tunnelling tool**, not a toy. Grab the single
static `chisel` binary from its [releases page](https://github.com/jpillora/chisel/releases)
(Go, one file, no dependencies) onto both the attacker and pivot containers — `make up`
stages it for you. A minimal hand-rolled `relay.py` also ships on the pivot, purely as a
"here's what chisel does under the hood" reference you can read.

## Scenario

You've obtained a shell on `pivot` — the dual-homed DMZ server. The
internal segment (`172.21.x.x`) is not reachable from your machine. You need to
set up a tunnel so your traffic routes through the pivot host to reach internal
systems — and you'll do it with the same OSS tooling a real engagement uses:
**[chisel](https://github.com/jpillora/chisel)** (a fast TCP/UDP tunnel over HTTP,
secured via SSH) as the primary tool, with **[ligolo-ng](https://github.com/nicocha30/ligolo-ng)**
as the alternative.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] Establish the pivot with **chisel**: run a chisel server on the `attacker` box and a
   chisel client (in reverse mode) on the `pivot` host, exposing a SOCKS proxy back through
   the pivot. Then route a request through that proxy to reach and read the confidential
   inventory on `internal-target` — which you cannot reach directly. (Which side runs
   `chisel server --reverse`, which runs `chisel client ... R:socks`, and how do you point a
   client like `curl --socks5` or `proxychains` at the resulting proxy?) `make demo` runs the
   validated pivot end-to-end — run it afterwards to confirm the direct connection fails and
   the tunnelled one succeeds.

2. [ ] Shell into the attacker container and confirm the network isolation:
   ```bash
   make shell
   # From attacker:
   ip addr show     # DMZ IP only
   ip route         # no route to 172.21.x.x
   curl http://internal-target/   # should fail (no DNS/route)
   curl http://pivot:8888/        # should succeed (through relay)
   ```

3. [ ] Shell into the pivot container and examine the dual-homed setup:
   ```bash
   docker compose exec pivot bash
   ip addr show     # two interfaces — DMZ and internal
   ip route         # has route to both 172.20.x.x and 172.21.x.x
   ps aux           # relay.py is running as the tunnel
   ```

4. [ ] **Under the hood:** read the bundled `relay.py` — the minimal version of what chisel
   does. Trace the relay logic:
   - What does it bind to? What does it connect to?
   - How many threads does it use per connection?
   - What does chisel add on top (SSH-secured HTTP transport, SOCKS multiplexing, reverse
     mode) that a raw relay doesn't — and why does that matter on a real engagement?

5. [ ] Map this to real-world pivoting tools — for each, state how you'd configure
   the same `pivot:8888 → internal-target:80` forward:
   - `ssh -L`
   - `socat`
   - `chisel`
   - `ligolo-ng`

6. [ ] Draw the full network topology: subnets, container IPs, the relay, and the
   traffic path. Note which hop each defensive control (firewall, IDS, ZTNA) intercepts.

## Success criteria — you're done when

- [ ] You confirmed the direct connection to `internal-target` fails from the attacker.
- [ ] You reached and read the confidential inventory through a **chisel** SOCKS tunnel via the pivot.
- [ ] You read `relay.py` and can explain what chisel adds over a bare TCP relay.
- [ ] You can configure the same forward using a second tool (SSH `-L`, socat, or ligolo-ng).
- [ ] You can draw the network diagram and name the defensive control that stops each hop.

## Deliverables

`pivoting.md`: network diagram (subnets + container IPs), the chisel tunnel setup
(server + reverse-SOCKS client commands), proof of reaching internal-target (the inventory
page) through the proxy, and one alternative tunnel tool (ligolo-ng / SSH / socat) you'd
use on a real engagement and why.

## Automate & own it

**Required.** Write `setup-pivot.sh` (or a Python script) that:
- Takes `PIVOT_HOST`, `PIVOT_PORT`, `TARGET_HOST`, `TARGET_PORT` as arguments
- Checks the pivot is reachable
- Starts the relay in the background
- Confirms the tunnel is live by making a test connection
- Logs the setup so you can reproduce it later

AI drafts the script; you verify the routing logic before committing. Commit
`setup-pivot.sh` and `pivoting.md`.

## AI acceleration

Ask a model to compare chisel vs ligolo-ng for a real engagement — both do SOCKS
proxying, but their C2 traffic looks different on the wire. Ask it which generates
less anomalous traffic, then verify by reading each tool's documentation.

## Connects forward

Pivoting is the core of lateral movement in Track 06 (Active Directory) — reaching
domain controllers, passing hashes, and spraying credentials all start from being
able to route into the internal segment. The defensive inverse is Track 11 (ZTNA) —
zero-trust architecture removes the "once inside the DMZ, you can reach anything"
assumption that makes pivoting possible.

## Marketable proof

> "I pivot through a compromised host into a segmented network — building a SOCKS tunnel
> with chisel (and knowing ligolo-ng, SSH, and socat as alternatives) — and can explain the
> segmentation and detection controls that limit attacker reach."

## Stretch

- Build a **double pivot**: add a second internal segment (`172.22.x.x`) behind
  the first. Add a second relay on `internal-target` to forward to `internal2-target`.
  Demonstrate the chain: `attacker → pivot → internal-target → internal2-target`.
- Demonstrate why ZTNA collapses this attack: if `internal-target` required mutual
  TLS and identity attestation for every request, what breaks in the pivot chain?
