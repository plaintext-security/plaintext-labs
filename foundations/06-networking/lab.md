# Lab 06 — Read the Wire: the Handshake, the Lookup, and the Beacon

*Variant D · skill-first, breach as stakes. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It spins up a tiny HTTP
server and a tool container (`tcpdump`, `dig`, `curl`) on an isolated Docker network — no real network,
no cloud, nothing leaves your machine.

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/06-networking
make up      # start the HTTP server + tool container
make demo    # generate live DNS + HTTP traffic, then walk an annotated capture
make shell   # drop into the tool container (tcpdump, dig, curl)
make down    # stop when done
```

## Scenario
You capture one ordinary HTTP request end to end — the DNS lookup, then the TCP handshake — read by
you, packet by packet. Then you're handed a second capture of otherwise-normal traffic with **one
DNS-based C2 beacon** mixed in (modeled on SUNBURST's `avsvmcloud.com` lookups), and you have to find
it. Same skill, two stakes: read the wire, then read it *adversarially*.

> Capture only on systems/networks you own, or inside this throwaway container. The beacon capture is a
> safe, synthetic stand-in — nothing here contacts a real C2.

## Do
Work the commands out from the Learn resources and `man tcpdump` — that derivation *is* the lab. Each
step feeds the next.

1. [ ] **Capture a live exchange.** Start a packet capture on all interfaces, writing to a file, in the
   background. (Which flags write to a *file* instead of printing? How do you background a command?)
2. [ ] **Generate traffic.** In another shell, produce exactly one DNS lookup and one HTTP request to
   the lab server, then stop the capture cleanly.
3. [ ] **Find the lookup.** From the saved file, isolate just the DNS traffic. Point to the **query**
   and the **answer** — the A record and the IP it returned. (Which port carries DNS?)
4. [ ] **Find the handshake.** Isolate the **SYN**, **SYN-ACK**, and **ACK** that open the TCP
   connection. State the client port, the server port, and the order of the first ~6 packets. (Hint:
   `tcpdump` can filter on TCP flags.)
5. [ ] **Read the whole stream.** Open the capture in Wireshark and "Follow TCP Stream" to see the
   request and response as one conversation — the layers, reassembled.
6. [ ] **Now hunt the beacon.** Open the provided beacon capture. Walk its DNS lookups the way you just
   walked yours, and find the one that's *wrong*. Check your README prediction: what actually gives it
   away — a subdomain no human would type, an unusually long/random name, a repeating interval? Name
   the packet and say, in one sentence, **why** it's the beacon.

## Success criteria — you're done when
- [ ] You can point to the DNS query and the A record it returned in your own capture.
- [ ] You can identify the SYN, SYN-ACK, and ACK, and state the client and server ports.
- [ ] You can name the order of the first ~6 packets and how many flowed before any data did.
- [ ] You've identified the beacon lookup in the second capture and can explain in one sentence what
  made it stand out from the legitimate DNS around it.

## Deliverables
A short `networking.md`: the resolved IP, the annotated SYN/SYN-ACK/ACK packets, how many packets were
exchanged before data flowed, and a one-paragraph verdict on the beacon (which packet, and the tell).
Reference `cap.pcap` — do **not** commit it (see `.gitignore`).

## Automate & own it
**Required.** Turn the manual read into a small reusable tool: a Python script that takes a capture file
and prints (a) the DNS queries and their answers, (b) the SYN/SYN-ACK/ACK of each handshake, and (c)
any DNS lookup that *looks like a beacon* by a rule you choose and can defend — e.g. an unusually long
subdomain, a high-entropy/random-looking name, or a name not on an allowlist. **AI drafts the parser;
you review every line, confirm it flags the real beacon for the right reason, and run it against both
captures to prove it.** Commit the script alongside `networking.md`. (A pcap library like `scapy` or
`dpkt` is the usual path; reading `tcpdump -r` text output is a fine beginner alternative.)

## AI acceleration
Paste any `tcpdump` line you don't understand to a model for a plain-English read of the flags, then
confirm it against your capture and `man tcpdump`. For the beacon, ask the model *why* a given lookup is
suspicious before you decide — it'll propose tells (length, randomness, frequency); your job is to check
each against the actual packets and keep only the ones that hold. The verdict is yours.

## Connects forward
Reading the wire underpins Offensive recon and scanning, Defensive network monitoring (Zeek/Suricata),
and Forensic network reconstruction. The DNS-beacon hunt you just did is the seed of **cloud detection**
— SUNBURST's C2 hid in DNS precisely because cloud and enterprise networks let it out, the exact gap the
Cloud track's logging-and-detection modules close.

## Marketable proof
> "I can take a packet capture cold and walk the DNS lookup and the TCP handshake — and I can spot a
> DNS-based C2 beacon hiding in ordinary traffic and script the triage that flags it."

## Stretch
- Capture an HTTPS request (`curl https://example.com`): you'll see the TLS ClientHello and the SNI, but
  not the payload. Explain *why* the body is opaque — and what a defender can still learn from the
  metadata (the destination, the SNI, the timing) even without decrypting it. This is exactly the
  metadata a DNS/TLS beacon hunt leans on.
