# Module 06 — Network Programming

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *understanding the wire is what separates a script from a tool and a tool from an audit.*

## Why this matters
Security tools that manipulate the network — scanners, banner grabbers, sniffers, honeypot
detectors — are all built on raw socket operations. Understanding how `socket` and `scapy` work
at this level means you can build your own, read the source of existing tools, and understand
exactly what a scanner is doing on the wire when you fire it at a target.

## Objective
Write a port scanner and banner grabber in raw Python `socket`, then use `scapy` to capture and
parse a small packet trace — understanding what is happening at each layer rather than just
reading tool output.

## The core idea
A TCP port scanner is thirty lines of Python. `socket.connect_ex(host, port)` returns `0` on
success and an error code on failure; iterate the port list, record the result, close the
connection. The hard part is not the code — it is the operational discipline: always scan only
targets you own or have written permission to test, set a short timeout (`socket.settimeout(1.0)`)
so the scan doesn't hang indefinitely, and understand that a filtered port (firewall drops the
packet) behaves differently from a closed port (RST returned) — which is information in itself.

Banner grabbing is the step after port enumeration: once you know a port is open, send a probe
and read the first bytes the service returns. Most services announce themselves — SSH says
`SSH-2.0-OpenSSH_8.9`, HTTP says the server header, SMTP says `220 mail.example.com`. You do
not need `nmap` for this; `socket.recv(1024)` and a `.decode("utf-8", errors="replace")` gets
you there. Be aware that some services send nothing until you speak first (`FTP` is prompt-first;
raw `recv` on an HTTPS port returns TLS hello bytes, not plaintext).

`scapy` is the Swiss Army knife of Python networking: it can forge arbitrary packets at any layer,
send them, capture responses, and parse captures. The core mental model is that every packet is
a stack of layers — `Ether / IP / TCP / Raw` — and you can read or set any field at any layer.
`sniff(count=10, filter="tcp port 22")` captures 10 packets matching a BPF filter. `wrpcap()` and
`rdpcap()` read and write `.pcap` files, so `scapy` can post-process captures from Wireshark or
tcpdump. The power and the risk are the same: `scapy` will send what you tell it to send,
including malformed packets — there is no safety net.

The authorization rule matters especially here. A port scanner running against the wrong subnet
is an incident. Every exercise in this module runs against the compose-provided echo server or
loopback — never against external hosts. In the real world, you scan within a defined scope
authorized in writing; everything outside that scope is illegal regardless of intent.

## Learn (~3 hrs)

**Socket programming (~1 hr)**
- [Socket Programming in Python — Real Python](https://realpython.com/python-sockets/) — the definitive walkthrough; read through "TCP Sockets" and "Multi-Connection Client and Server"; skip the async section for now.
- [socket — Low-level networking interface (Python docs)](https://docs.python.org/3/library/socket.html) — reference; focus on `socket()`, `connect_ex()`, `settimeout()`, `recv()`, `sendall()`.

**Scapy (~2 hrs)**
- [Scapy — Official documentation, "Building packets"](https://scapy.readthedocs.io/en/latest/usage.html#generating-sets-of-packets) — the "Quick start" and "Building packets" sections; focus on the layer stack model (`/` operator).

## Key concepts
- `socket.connect_ex()` for non-throwing port probes; `settimeout()` to prevent hangs
- Banner grabbing: recv-first vs probe-first services
- Filtered vs closed vs open: what each TCP response means
- Scapy layer model: `Ether / IP / TCP / Raw`
- BPF filters in `scapy.sniff()` — same syntax as tcpdump
- Authorization: scan only what you own or have written permission for

## AI acceleration
Ask a model to write a port scanner. It will produce a working one. Then ask it to add a
`--timeout` argument and handle the `ConnectionRefusedError`, `TimeoutError`, and
`OSError` cases explicitly. The error handling is where the model's first draft usually
has gaps — and a scanner that crashes on a filtered port is not a scanner.
