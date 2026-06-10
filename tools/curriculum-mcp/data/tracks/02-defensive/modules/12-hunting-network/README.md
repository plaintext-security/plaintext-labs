# Module 12 — Threat Hunting: Network

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *C2 hides in plain sight; beaconing is how you find it.*

## Why this matters
Attackers blend C2 into normal web traffic, but the *rhythm* gives them away — regular, repeated
callbacks (beaconing) that no human browsing produces. Network threat hunting looks for these
statistical tells across connection logs. RITA, working on Zeek logs, automates beacon and
long-connection analysis, and you can hunt real C2 in real malware traffic for free.

## Objective
Hunt for C2 beaconing and other anomalies in Zeek logs from real malicious traffic, using RITA and
your own analysis.

## The core idea
This is the network-side counterpart to endpoint hunting, and it rests on one beautiful fact:
**machines are rhythmic and humans aren't.** An attacker can blend C2 *content* into normal-looking
web traffic, but the implant still calls home on a schedule — beaconing — producing regular, repeated
connections with a tell-tale interval (even with jitter) that no human browsing ever generates. So
network hunting looks for statistical *tells* across connection logs rather than matching signatures.
RITA, running over Zeek's `conn.log`, automates the beacon, long-connection, and rare-destination
maths.

For the network engineer this is the familiar habit of reading flow data for "who talks to whom,"
sharpened into "*how regularly* does this internal host talk to that external one — and is that
rhythm human or mechanical?" Beaconing, abnormally long-lived connections, and rare destinations are
the three classic shapes; DNS gets its own attention because it's so often allowed straight out, which
makes it a favourite tunnelling and exfil channel.

The judgment: this is statistical, not signature — and statistics without a baseline lie. The
textbook false positive is a CDN, NTP source, or telemetry agent that *also* polls on a fixed
interval; RITA will surface it and a model will gladly label it "C2." The actual skill is separating
mechanical-benign from mechanical-malicious, which needs your environment's context — verify every
candidate against the data and the known-bad write-up.

## Learn (~4 hrs)

**The method & tool**
- [Detecting Malware Beacons with Zeek and RITA (video)](https://www.youtube.com/watch?v=eETUi-AZYgc) — beacon hunting end to end.
- [RITA (Real Intelligence Threat Analytics)](https://github.com/activecm/rita) — OSS network-hunt tool: beacons, long connections, rare destinations.

**Concepts**
- [MITRE ATT&CK — Command and Control (TA0011)](https://attack.mitre.org/tactics/TA0011/) — what you're hunting and how it manifests on the wire.

## Key concepts
- Beaconing: regularity as a signal (interval + jitter)
- Long connections and rare destinations
- Hunting in connection logs (Zeek `conn.log`) at scale
- Statistical vs signature approaches
- DNS-based C2 and exfil

## AI acceleration
A model explains a suspicious connection pattern and drafts analysis of Zeek logs — but beaconing
detection is statistical, and the model can't see your baseline; it'll call a CDN's regular polling
"C2." Verify candidates against the data and the known-bad write-up.
