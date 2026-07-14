# Held-out corpus (capstone)

Drop your **held-out** labelled samples here — known-malicious and known-benign events your detection was
**never tuned against**. `eval.ps1` scores the detection over *only* this directory. Do not put tuning
samples here; scoring on the tuning set is a memory test, not a measurement.

Use **real data** where you can: a public `.evtx` corpus like
[EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES), real Sysmon output, or a free
threat feed like [abuse.ch](https://abuse.ch/). Label each sample `malicious` or `benign`. Keep the set
small but honest, and note in your write-up what the corpus size does and does not let the score prove.
