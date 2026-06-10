# Foundations capstone — grading rubric

Self/peer/reviewer rubric for the Track 00 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Packet-capture walk-through** | Capture exists but layers aren't separated; DNS/TCP/TLS conflated | DNS lookup, the three-way handshake, and the TLS hello each identified by packet number and explained in your own words | Adds the *why* — SNI, encrypted vs. cleartext after ClientHello, one security-relevant header — tied to the relevant RFC |
| **Decoding the blob** | One layer peeled; tool used as a black box | All layers decoded to plaintext, with the order and each encoding (base64/hex/URL) named | Decoded by a committed script, with a note on how you recognised each layer |
| **STRIDE model** | Lists assets only, or generic threats | One page mapping trust boundaries to STRIDE with a concrete threat per relevant category | Threats ranked, each with a mitigation, referencing components you built |
| **Secret & git hygiene** | Artifacts (`.pcap`, keys) committed, or history dirty | No captures/keys/secrets in history; `.gitignore` present; clean commits | Pre-commit secret scan wired in; commits tell the build story |
| **Reproducibility** | Steps not written down | A reader can follow your write-up and reproduce each result | One `make`/script rebuilds the lab and re-runs the decode from zero |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] No live target is attacked here; you capture your own traffic to a host you control.
