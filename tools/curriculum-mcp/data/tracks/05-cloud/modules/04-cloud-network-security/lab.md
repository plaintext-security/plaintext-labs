# Lab 04 — Network Topology Mapping & Flow Log Analysis

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo.
The environment runs `cloudmapper` against bundled AWS account JSON and provides a set of
realistic VPC flow log entries for manual analysis.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/04-cloud-network-security
make up        # build the container with cloudmapper
make demo      # run the cloudmapper audit + flow log analysis
make shell     # drop into the container to work interactively
make down      # stop when done
```

The container includes `cloudmapper` and its dependencies. Two data sets are bundled:
- `data/account/` — a realistic AWS account JSON snapshot (the output of `cloudmapper collect`) representing Meridian Financial's VPC topology.
- `data/vpc-flow-logs.log` — 50 representative flow log entries including normal traffic, a scanning pattern, and a suspicious large-transfer event.

> Everything runs locally against bundled data you own. No real AWS account needed.

## Scenario
Meridian Financial's infrastructure team has handed you an account JSON export and a week's worth
of VPC flow log samples from their production VPC. They've had two recent security incidents —
an unexpected outbound connection flagged by a third-party threat feed, and a compliance finding
about Security Groups with `0.0.0.0/0` ingress. Your job: map the topology, confirm the misconfigured
Security Groups, and find the flow log evidence of the suspicious connection.

## Do
1. [ ] **Run the cloudmapper audit.** Execute `cloudmapper audit --account meridian` against the
   bundled account data. Hint: `cloudmapper --config data/config.json audit --account meridian`.
   How many Security Groups have ingress from `0.0.0.0/0`? Which ports are exposed?

2. [ ] **Inspect the Security Group findings.** For each Security Group that the audit flags,
   identify which resource it's attached to (web tier, app tier, or database tier) and whether
   the exposure is intentional (a public ALB) or a misconfiguration (a database port open to the
   internet).

3. [ ] **Analyse the flow logs for the port scan.** Open `data/vpc-flow-logs.log` and find the
   entries that indicate a port scan — many `REJECT` flows from a single source IP to multiple
   destination ports within a short time window. What source IP, and what destination IP was
   being scanned?

4. [ ] **Find the suspicious large-transfer event.** One flow log entry shows a large byte count
   (over 50 MB) to an external IP on port 443. Identify the source internal IP, the destination
   external IP, and the byte count. Is the destination IP in a known AWS range, or is it an
   external party? (The `data/vpc-flow-logs.log` file has a comment line marking the suspicious
   entry — find it, then remove the comment and confirm you can identify it from the raw data
   alone.)

5. [ ] **Cross-reference the Security Group and flow log findings.** The source IP of the large
   transfer — which Security Group is its instance attached to? Is egress to port 443 explicitly
   allowed, or is it open by default? Write this in `findings.md`.

6. [ ] **Run `make demo`** and compare the worked output to your manual analysis.

## Success criteria — you're done when
- [ ] You've listed every Security Group that `cloudmapper audit` flags, with the attached resource
  and the specific misconfiguration.
- [ ] You've identified the port-scan source and target from the flow logs.
- [ ] You've identified the suspicious large-transfer event and its external destination.
- [ ] You've linked at least one flow log event to a specific Security Group misconfiguration.
- [ ] Your `findings.md` has a network findings table with severity ratings.

## Deliverables
`findings.md` — a network security findings report: topology findings (misconfigured Security Groups),
flow log findings (scan, large transfer), and a recommended control for each. Commit this file.
Do not commit real credentials, real account IDs, or real IP addresses from live infrastructure.

## Automate & own it
**Required.** Write a Python script (`analyze_flows.py`) that reads `data/vpc-flow-logs.log` and
outputs:
  - A list of `REJECT`-storm source IPs (more than 10 REJECT flows from one source in the log).
  - A list of flows with byte counts over 10 MB to external (non-RFC-1918) destinations.

Have a model draft the parsing logic from the [flow log field spec](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html#flow-logs-fields);
you review every line, run it against the bundled log, and confirm it surfaces the scan and
large-transfer findings. This is the skeleton of a flow-log anomaly detector.

## AI acceleration
Paste the full `data/vpc-flow-logs.log` content into a model and ask: "Which entries indicate
a port scan and which indicate potential data exfiltration? Explain the indicators." Compare its
answer to what your `analyze_flows.py` finds. Note any entries the model flags that your script
misses (false negatives) and any entries the model overlooks (false negatives). Calibrating your
automated detector against model judgment is a useful debugging technique.

## Connects forward
The Security Group misconfigurations found here are exactly what module 05 (Posture & Misconfiguration
Auditing) would catch with `prowler check aws_ec2_securitygroup_allow_ingress_from_internet_to_any_port`.
The flow log analysis skills reappear in module 16 (Cloud Incident Response) where you'll correlate
flow log evidence with CloudTrail API calls to reconstruct an attack timeline.

## Marketable proof
> "I can map a cloud network topology with cloudmapper, audit Security Groups for misconfiguration,
> and analyse VPC flow logs to identify scanning and exfiltration candidates — core skills for cloud
> security assessment and incident response."

## Stretch
- Run `cloudmapper webserver` inside the container and open the interactive graph in a browser
  (forward port 8000). Explore the visual topology and find which subnet is directly internet-routable.
- Extend `analyze_flows.py` to enrich the external IPs it flags by checking them against the AWS
  IP range JSON (`https://ip-ranges.amazonaws.com/ip-ranges.json` — download it once to
  `data/aws-ip-ranges.json`) and noting which ones are AWS-owned vs. truly external.
