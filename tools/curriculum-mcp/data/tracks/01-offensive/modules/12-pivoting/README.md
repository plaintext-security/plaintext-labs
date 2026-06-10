# Module 12 — Pivoting & Lateral Movement

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *one foothold is rarely the goal; this is how access spreads through a network.*

## Why this matters
Real targets are segmented: the host you compromise can usually reach internal systems you
can't touch directly. Pivoting — routing your traffic *through* a foothold — and lateral
movement are how a single foothold becomes domain-wide compromise, and they're exactly what
defenders segment and hunt against. Understanding the attacker's tunnel is also how you argue
for network segmentation.

## Objective
Pivot through a compromised host to reach an internal network you can't reach directly, and
move laterally to a second target in your lab.

## The core idea
One foothold is a beachhead, not the objective. Real networks are segmented: the box you popped can
reach internal systems you can't touch from outside. **Pivoting** is routing *your* traffic *through*
that foothold so the internal network treats you as if you were sitting inside it. The mental model is
a ladder of increasing reach: a single **port-forward** (reach one internal service), a **SOCKS proxy**
(reach many, via proxychains), or a full **tunnel interface** (ligolo-ng gives your machine an actual
route into the internal subnet). You climb that ladder as you need more.

For the network engineer this is the offensive mirror of segmentation: every pivot defeats a boundary
someone deliberately drew — and understanding the tunnel is exactly how you argue for the segmentation
that *would* have contained you. A double pivot (through segment A to reach segment B) is just the same
move stacked, and it's how a single foothold becomes domain-wide compromise.

The judgment: pivoting is unforgiving. A wrong route, a mistyped subnet, or a routing loop can sever the
very foothold you're tunnelling through and end the engagement. So you **map the network first** — which
subnets exist, which host can reach what — *before* you build the tunnel. A model will generate the
tunnel commands, but it can't see your topology; understand each hop yourself, because losing the
foothold is expensive to recover.

## Learn (~4 hrs)

**Tunneling & pivoting**
- [Pivoting Made Easy with Ligolo-ng (video)](https://www.youtube.com/watch?v=txFnX5NPqKc) — the modern, clean way to tunnel into an internal network.
- [Ligolo-ng (project + README)](https://github.com/nicocha30/ligolo-ng) and [Chisel](https://github.com/jpillora/chisel) — the two tools you'll reach for; read their usage.

**Where it sits**
- [MITRE ATT&CK — Lateral Movement (TA0008)](https://attack.mitre.org/tactics/TA0008/) — the techniques and how they're detected.

## Key concepts
- Network segmentation and why a foothold matters
- Port forwarding vs SOCKS proxying vs a tunnel interface
- Pivoting tools (ligolo-ng, chisel) and proxychains
- Lateral movement techniques (and their telemetry)
- Double pivots through multiple segments

## AI acceleration
A model explains a tunneling setup and generates the commands — but pivoting is unforgiving of
a wrong route or a misread subnet, and you can lose your foothold. Map the network yourself and
understand each hop before you build the tunnel.
