# Lab 06 — Network Programming

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/06-network-programming
make up        # starts the TCP echo server + student container
make demo      # runs the reference scanner + banner grabber + sniffer
make shell     # interactive shell in student container
make down
```

Two containers: a **TCP echo server** (`target`) that listens on ports 22, 80, 443, and 8080
with simple banners; and the **student container** with `scapy` and standard library only.
Everything runs on the compose network — no external hosts involved.

> **Authorization note:** Only scan and probe the `target` container in this lab. Never run
> these tools against systems you don't own or lack written permission to test.

## Scenario
You're building a lightweight scanner for Meridian's internal asset validation pipeline — not
to replace `nmap`, but to understand what a scanner does so you can configure and interpret one
intelligently. You'll write a port scanner, grab banners from open ports, and capture a small
packet trace with `scapy` to verify the TCP handshake is what you think it is.

## Do
1. [ ] Write `scanner.py` that:
   - Accepts `--host` and `--ports` arguments (e.g., `--ports 22,80,443,8080`).
   - Uses `socket.connect_ex()` to check each port; `settimeout(1.0)`.
   - Prints a table: port, status (OPEN/CLOSED), and banner (if open).
   - For OPEN ports, grabs the banner by `recv(1024)`; handles services that don't send until
     you probe by sending `b"HEAD / HTTP/1.0\r\n\r\n"` for port 80.
2. [ ] Run `python scanner.py --host target --ports 22,80,443,8080,9999`. Port 9999 is not
   listening — confirm it shows CLOSED and does not hang.
3. [ ] Write `sniffer.py` using `scapy.sniff()`:
   - Capture 20 packets on the compose network interface while your scanner runs.
   - For each captured TCP packet, print: src IP, dst IP, src port, dst port, TCP flags.
   - Write the capture to `output/scan.pcap`.
4. [ ] Load `output/scan.pcap` with `scapy.rdpcap()` and print the count of SYN, SYN-ACK,
   and RST packets. Verify the counts match what you'd expect from a TCP handshake plus a
   closed-port RST.
5. [ ] Run `make demo` and compare your output with the reference.

## Success criteria — you're done when
- [ ] `scanner.py` correctly identifies all four open ports and the one closed port, with banners.
- [ ] `scanner.py` does not hang on a closed or filtered port.
- [ ] `output/scan.pcap` exists and is readable by `rdpcap()`.
- [ ] The SYN/SYN-ACK/RST counts in step 4 make sense given what you scanned.

## Deliverables
`scanner.py` + `sniffer.py`. Commit both. Add `output/` to `.gitignore`.

## Automate & own it
**Required.** Add a `--rate-limit` flag to `scanner.py` that enforces a delay (in ms) between
probes. Have a model draft it using `time.sleep()`; verify the delay is per-connection, not
per-port-batch. Commit the updated `scanner.py` with a comment explaining why rate-limiting
matters (avoid triggering IDS rules; don't overwhelm a slow target).

## AI acceleration
Ask a model to write the scapy sniffer. Then ask: "What BPF filter would limit this capture to
only TCP traffic on the compose subnet?" Test its answer — does the filter syntax compile? Does
it correctly exclude non-TCP protocols? The filter string is two words; the reasoning for it
is what you're learning.

## Connects forward
The banner-grabbing pattern reappears in module 07 (web scraping — HTTP is just a text protocol
over a socket). The packet analysis skills connect to Track 02 Defensive (network monitoring) and
Track 03 Forensics (PCAP analysis).

## Marketable proof
> "I've written a port scanner and banner grabber from raw sockets, and I've used scapy to
> verify what's happening on the wire — so when I configure nmap, I know what it's doing."

## Stretch
- Add a UDP scan mode to `scanner.py` using `socket.SOCK_DGRAM` and a probe packet; note the
  difference in how closed UDP ports respond compared to TCP.
- Use `scapy` to send a single crafted TCP SYN packet and receive the response — compare the
  result to what `connect_ex()` reports for the same port.
