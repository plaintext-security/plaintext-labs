# Lab 06 — Network Programming

*Hands-on lab · [← Back to the module concept](README.md)*

> **Lab environment: real-target rewire — validation deferred.** The scan target is now a real
> intentionally-vulnerable image (Apache Solr 8.11.0, the Vulhub Log4Shell / CVE-2021-44228
> reference) instead of a toy echo server. `make up && make demo && make down` has **not** yet been
> re-run on a clean Linux runner; validate before marking the lab done.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/06-network-programming
make up        # starts the Solr target + student container
make demo      # runs the reference scanner + banner grabber + sniffer
make shell     # interactive shell in student container
make down
```

Two containers: a **real intentionally-vulnerable target** (`target`) — Apache Solr 8.11.0, the
[Vulhub Log4Shell / CVE-2021-44228 reference image](https://github.com/vulhub/vulhub/tree/master/log4j/CVE-2021-44228),
which serves a genuine HTTP/Jetty admin interface on port **8983** and a JDWP debug listener on
port **5005**; and the **student container** with `scapy` and standard library only. Both share a
user-defined bridge network (`lab-net`), so the student container reaches the target by hostname
`target`. No external hosts involved.

> **Authorization note:** Only scan and probe the `target` container in this lab. Never run
> these tools against systems you don't own or lack written permission to test.

## Scenario
You're building a lightweight scanner for internal asset validation — not to replace `nmap`, but
to understand what a scanner does so you can configure and interpret one intelligently. You'll
point it at a real service (a vulnerable Apache Solr instance), write a port scanner, grab banners
from open ports, and capture a small packet trace with `scapy` to verify the TCP handshake is what
you think it is.

## Do
1. [ ] Write `scanner.py` that:
   - Accepts `--host` and `--ports` arguments (e.g., `--ports 8983,5005,9999`).
   - Uses `socket.connect_ex()` to check each port; `settimeout(1.0)`.
   - Prints a table: port, status (OPEN/CLOSED), and banner (if open).
   - For OPEN ports, grabs the banner by `recv(1024)`; handles services that don't send until
     you probe by sending `b"HEAD / HTTP/1.0\r\n\r\n"` for the HTTP port. (Solr's admin HTTP
     listens on **8983**, not 80 — probe that port to draw out the Jetty/Solr banner.)
2. [ ] Run `python scanner.py --host target --ports 8983,5005,9999`. Port **8983** is the Solr
   HTTP admin (OPEN), **5005** is the JDWP debug listener (OPEN if exposed by the image), and
   **9999** is not listening — confirm 9999 shows CLOSED and does not hang.
3. [ ] Write `sniffer.py` using `scapy.sniff()`:
   - Capture 20 packets on the compose network interface while your scanner runs.
   - For each captured TCP packet, print: src IP, dst IP, src port, dst port, TCP flags.
   - Write the capture to `output/scan.pcap`.
4. [ ] Load `output/scan.pcap` with `scapy.rdpcap()` and print the count of SYN, SYN-ACK,
   and RST packets. Verify the counts match what you'd expect from a TCP handshake plus a
   closed-port RST.
5. [ ] **Prove it with a test you wrote (the ownership half).** Don't stop at "the counts make
   sense." Write `test_scanner.py` that imports your scan function and asserts its verdicts against
   the fixed `target` port set:
   - Scanning `target` returns **OPEN** for 8983 (and 5005, if the image exposes JDWP) and
     **CLOSED** for 9999 — assert each.
   - The scan **does not hang** on the closed port (a bounded `settimeout` means the test returns
     promptly).
   - If `scapy` capture runs in your environment, add a check that `rdpcap("output/scan.pcap")`
     yields **≥1 SYN-ACK** (an open port's handshake) and **≥1 RST** (the closed-port reply).

   The socket-level OPEN/CLOSED asserts are the **gating** check — they're deterministic against the
   known target. The pcap SYN-ACK/RST asserts are **optional**: `scapy` raw capture can need
   privileges that aren't available headless, so guard them with a `pytest.mark.skipif` (or a
   try/except skip) rather than letting a capture-permission issue fail the gate. Have a model draft
   the test; read every assert; run `python -m pytest test_scanner.py`.
6. [ ] Run `make demo` and compare your output with the reference.

## Success criteria — you're done when
- [ ] `scanner.py` correctly identifies the open Solr port(s) (8983, and 5005 if exposed) and the
  closed port (9999), with a banner for the HTTP port.
- [ ] `scanner.py` does not hang on a closed or filtered port.
- [ ] `output/scan.pcap` exists and is readable by `rdpcap()`.
- [ ] The SYN/SYN-ACK/RST counts in step 4 make sense given what you scanned.
- [ ] `test_scanner.py` asserts OPEN for 8983 (and 5005 if exposed) and CLOSED for 9999 (plus,
  where `scapy` capture is available, ≥1 SYN-ACK and ≥1 RST), and passes under
  `python -m pytest test_scanner.py`.

## Deliverables
`scanner.py` + `sniffer.py` + `test_scanner.py`. Commit all three. Add `output/` to `.gitignore`.

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
