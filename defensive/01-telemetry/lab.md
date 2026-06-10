# Lab 01 — Stand Up a Log Pipeline

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/01-telemetry
make up
```

This drops you into a Python container with `pipeline.py` and a bundled
sshd log sample (`data/ssh_auth.txt`, loghub-format). Run `make demo` to
walk all three pipeline stages: raw ingest → structured records (NL-JSON)
→ four analyst queries → gap analysis. The lab's `pipeline.py` is the
starting point for your own ingest script.

For the full Elasticsearch + Kibana path described in step 3, spin those
up separately and point them at the NL-JSON the script writes to
`/tmp/pipeline_output.ndjson`; or swap in a Fluent Bit config to forward
to your chosen backend. The pipeline concepts are the same regardless of
backend.

## Scenario
Build the searchable log store the rest of the track depends on, and load real logs into it.

## Do
1. [ ] Stand up Elasticsearch + Kibana and confirm both are reachable.
2. [ ] Ingest a real log dataset (a loghub sample, or your own host's auth/syslog).
3. [ ] In Kibana, search the data — find a specific event and filter on a field. (Can you find the
   failed logins?)
4. [ ] Identify one telemetry *gap*: what attacker activity would these logs miss?

## Success criteria — you're done when
- [ ] Real logs are searchable in Kibana.
- [ ] You can find a specific event and filter by a field.
- [ ] You can name one thing this telemetry would not catch.

## Deliverables
`telemetry.md`: what you ingested, a couple of useful searches, and the gap you identified.

## AI acceleration
Have a model draft the ingest/parse config — then verify the fields actually land correctly in the
index. A mis-parsed log is invisible to every later detection.

## Connects forward
This pipeline is the substrate for every later Defensive module — detections (08), hunting (11–12),
and response (13–15) all query it.

## Marketable proof
> "I stand up a central log pipeline (Elastic) and ingest real telemetry — and I reason about
> collection gaps before writing a single detection."

## Automate & own it
**Required.** Capture the whole pipeline as a `docker-compose` + ingest config that stands up from
zero and loads the data; AI drafts it, you verify what lands in the index; commit it.

## Stretch
- Add a second log source (network, or a second host) and normalise both into a common field set
  (a preview of module 07).
