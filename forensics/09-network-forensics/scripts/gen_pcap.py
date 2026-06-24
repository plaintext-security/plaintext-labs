#!/usr/bin/env python3
"""
gen_pcap.py — OFFLINE FALLBACK generator of a tiny synthetic PCAP for the network
forensics lab. The PREFERRED artifact is the real Redline Stealer infection capture
fetched via `make fetch-data` (Malware-Traffic-Analysis.net, 2024-10-23). Use this
generator only when you cannot reach that site — it reproduces the analysis workflow
(suspicious DNS lookup + HTTP binary transfer) without any real malware.

Produces capture.pcap containing:
  - Normal HTTPS traffic (simulated TLS ClientHello to 93.184.216.34 / example.com)
  - A DNS query for workspacin.cloud resolving to 198.51.100.42
  - A brief HTTP GET /update.bin to 198.51.100.42:80
  - A small binary payload in the HTTP response

All IPs are either RFC 5737 documentation addresses (198.51.100.x) or well-known
public addresses. No real malware content is included.
"""

from scapy.all import (
    Ether, IP, TCP, UDP, DNS, DNSQR, DNSRR, Raw,
    wrpcap, RandShort
)
import struct

CLIENT = "10.0.0.50"
DNS_SRV = "10.0.0.1"
LEGIT_SRV = "93.184.216.34"   # example.com
C2_SRV = "198.51.100.42"

pkts = []
seq = 1000

def eth(src="aa:bb:cc:dd:ee:01", dst="aa:bb:cc:dd:ee:02"):
    return Ether(src=src, dst=dst)

# --- DNS query for workspacin.cloud ---
dns_query = (
    eth() /
    IP(src=CLIENT, dst=DNS_SRV) /
    UDP(sport=54321, dport=53) /
    DNS(rd=1, qd=DNSQR(qname="workspacin.cloud"))
)
pkts.append(dns_query)

dns_response = (
    eth(src="aa:bb:cc:dd:ee:02", dst="aa:bb:cc:dd:ee:01") /
    IP(src=DNS_SRV, dst=CLIENT) /
    UDP(sport=53, dport=54321) /
    DNS(qr=1, aa=1, rd=1, ra=1,
        qd=DNSQR(qname="workspacin.cloud"),
        an=DNSRR(rrname="workspacin.cloud", ttl=300, rdata=C2_SRV))
)
pkts.append(dns_response)

# --- DNS query for example.com (benign) ---
dns_q2 = (
    eth() /
    IP(src=CLIENT, dst=DNS_SRV) /
    UDP(sport=54322, dport=53) /
    DNS(rd=1, qd=DNSQR(qname="example.com"))
)
pkts.append(dns_q2)
dns_r2 = (
    eth(src="aa:bb:cc:dd:ee:02", dst="aa:bb:cc:dd:ee:01") /
    IP(src=DNS_SRV, dst=CLIENT) /
    UDP(sport=53, dport=54322) /
    DNS(qr=1, aa=1, rd=1, ra=1,
        qd=DNSQR(qname="example.com"),
        an=DNSRR(rrname="example.com", ttl=300, rdata=LEGIT_SRV))
)
pkts.append(dns_r2)

# --- Simulated TLS ClientHello to example.com (normal HTTPS) ---
# Simplified: just SYN + a raw byte payload shaped like TLS record
tls_syn = eth() / IP(src=CLIENT, dst=LEGIT_SRV) / TCP(sport=54400, dport=443, flags="S", seq=1000)
tls_synack = eth(src="aa:bb:cc:dd:ee:02", dst="aa:bb:cc:dd:ee:01") / IP(src=LEGIT_SRV, dst=CLIENT) / TCP(sport=443, dport=54400, flags="SA", seq=2000, ack=1001)
tls_ack = eth() / IP(src=CLIENT, dst=LEGIT_SRV) / TCP(sport=54400, dport=443, flags="A", seq=1001, ack=2001)
# Minimal TLS ClientHello record header (content type 0x16 = handshake)
client_hello_payload = bytes([
    0x16, 0x03, 0x01, 0x00, 0x7a,  # TLS 1.0 handshake record
    0x01, 0x00, 0x00, 0x76,          # ClientHello
    0x03, 0x03,                       # TLS 1.2
]) + b'\x00' * 100
tls_hello = eth() / IP(src=CLIENT, dst=LEGIT_SRV) / TCP(sport=54400, dport=443, flags="PA", seq=1001, ack=2001) / Raw(load=client_hello_payload)
pkts.extend([tls_syn, tls_synack, tls_ack, tls_hello])

# --- HTTP GET to C2 server ---
http_syn = eth() / IP(src=CLIENT, dst=C2_SRV) / TCP(sport=54500, dport=80, flags="S", seq=3000)
http_synack = eth(src="aa:bb:cc:dd:ee:02", dst="aa:bb:cc:dd:ee:01") / IP(src=C2_SRV, dst=CLIENT) / TCP(sport=80, dport=54500, flags="SA", seq=4000, ack=3001)
http_ack = eth() / IP(src=CLIENT, dst=C2_SRV) / TCP(sport=54500, dport=80, flags="A", seq=3001, ack=4001)

http_req = (
    b"GET /update.bin HTTP/1.1\r\n"
    b"Host: workspacin.cloud\r\n"
    b"User-Agent: Mozilla/5.0\r\n"
    b"Connection: close\r\n\r\n"
)
http_get = eth() / IP(src=CLIENT, dst=C2_SRV) / TCP(sport=54500, dport=80, flags="PA", seq=3001, ack=4001) / Raw(load=http_req)

# Small benign binary payload (200 bytes of padding — NOT malware)
payload = b"PK\x03\x04" + b"\x00" * 196  # fake ZIP header + padding
http_resp = (
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Type: application/octet-stream\r\n"
    b"Content-Length: 200\r\n"
    b"Connection: close\r\n\r\n"
) + payload
http_response = eth(src="aa:bb:cc:dd:ee:02", dst="aa:bb:cc:dd:ee:01") / IP(src=C2_SRV, dst=CLIENT) / TCP(sport=80, dport=54500, flags="PA", seq=4001, ack=3001+len(http_req)) / Raw(load=http_resp)

pkts.extend([http_syn, http_synack, http_ack, http_get, http_response])

output = "/data/capture.pcap"
wrpcap(output, pkts)
print(f"Written {len(pkts)} packets to {output} ({sum(len(bytes(p)) for p in pkts)} bytes)")
