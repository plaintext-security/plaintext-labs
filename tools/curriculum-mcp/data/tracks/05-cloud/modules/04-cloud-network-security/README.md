# Module 04 — Cloud Network Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *the cloud network looks like what you know, until it doesn't — and the differences are where attackers hide.*

## Why this matters
Network security is the layer most practitioners feel confident about — until they move to the cloud
and discover that "firewalls," "routing," and "segmentation" all have cloud-specific meanings that
diverge from on-prem in important ways. VPC flow logs catch lateral movement that no host-based tool
sees. Security group drift is one of the most reliable indicators of a mismanaged cloud estate. And
the traffic patterns that flow-log analysis reveals — unexpected cross-account connections, exfiltration
to an unusual IP, a Lambda calling a public endpoint it shouldn't — are increasingly how cloud
intrusions are discovered after the fact. This module builds the network-layer foundation for both
offensive cloud work and cloud incident response.

## Objective
Use `cloudmapper` and VPC flow log analysis to map the network topology of a simulated Meridian
Financial AWS account, identify misconfigured Security Groups and unexpected traffic patterns, and
produce a network security findings report.

## The core idea
The fundamental conceptual shift when moving from on-prem to cloud networking is that **the control
plane and the data plane are separate, programmable objects.** In a traditional data centre, the
firewall is hardware in a rack; the rules live in a database on that appliance, and changing them
means logging into it. In a VPC, the Security Group is a software object — created and modified via
the IAM-controlled API, stored in AWS state, applied dynamically to every network interface attached
to the right resource. This means network security rules are subject to all the IAM attack-path
reasoning from module 03: a role with `ec2:AuthorizeSecurityGroupIngress` can punch a hole in any
Security Group it can reference, regardless of what the security team approved. The firewall and the
identity system are now coupled.

The second shift is the mental model for VPC egress. On-prem, a default-deny perimeter firewall means
nothing gets out unless you explicitly allow it. In a VPC, the default is that all outbound traffic
from any instance is permitted unless a Security Group rule or Network ACL explicitly denies it. This
is an intentional cloud-provider default for developer experience — but it means exfiltration paths
that would be stopped at the perimeter on-prem are open by default in the cloud. The right security
model is to think about *what your workloads legitimately need to reach* and allow only that, using
VPC Endpoints for AWS service traffic (so data to S3 or DynamoDB never leaves the AWS network),
Private Link for third-party services, and restrictive egress Security Group rules for everything else.
PrivateLink is the cloud-native equivalent of the network segmentation principle that everything communicates via an intermediary — and its absence from an architecture is a design risk, not a misconfiguration, but it's one worth flagging.

Flow logs are the network practitioner's primary forensic tool in the cloud. They record the 5-tuple
(source IP, destination IP, source port, destination port, protocol) plus the action (`ACCEPT` or
`REJECT`) for every network flow through the VPC. They don't capture packet contents — this is not
tcpdump — but the metadata is remarkably powerful: you can detect port scans (many flows to different
ports from one source, all REJECT), lateral movement (new east-west flows between hosts that didn't
previously talk), and data exfiltration candidates (a large-transfer flow to an external IP on an
unusual port). The practitioner's skill is knowing what "normal" looks like for a workload and
treating deviations as signal. In Meridian Financial's account, normal means a small set of internal
IPs talking to the application tier, and that tier talking to RDS — anything else warrants investigation.

`cloudmapper` is the tool that turns an AWS account's JSON export (from the `collect` phase) into a
visual graph of the network topology: VPCs, subnets, security groups, and the connections between
resources. The key insight from the graph is which resources are in which trust boundary — a
misconfigured Security Group that exposes a database subnet to `0.0.0.0/0` is immediately visible as
an edge that crosses the boundary incorrectly. The `cloudmapper audit` command surfaces common
misconfiguration patterns without the graph, but the visualisation is what communicates the finding
to engineers and leadership who won't read a findings table.

## Learn (~4 hrs)

**VPC fundamentals (~1.5 hrs)**
- [AWS VPC User Guide — How Amazon VPC works](https://docs.aws.amazon.com/vpc/latest/userguide/how-it-works.html) — the authoritative walkthrough of the VPC components: subnets, route tables, Internet Gateways, NAT, Security Groups, Network ACLs. Read this first; the lab assumes this vocabulary.
- [AWS — VPC Security Groups vs Network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Security.html) — the distinction between stateful (SG) and stateless (NACL) filtering, and when each is the right control.

**VPC flow logs (~1 hr)**
- [AWS — VPC Flow Logs documentation](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html) — the log format, field definitions, and how to enable flow logs. Read the "Flow log records" section carefully; you'll parse these records in the lab.
- [AWS Security Blog — Analyzing VPC Flow Logs with Amazon Athena](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html) — a practical walkthrough of querying flow logs at scale; read the query examples to understand what pattern detection looks like in practice.

**cloudmapper (~1.5 hrs)**
- [cloudmapper GitHub — README](https://github.com/duo-labs/cloudmapper) — Duo Labs' network topology mapper for AWS. Read the `collect`, `prepare`, and `audit` command descriptions. This is what generates the interactive graph from account JSON.

## Key concepts
- VPC as a software-defined network: Security Groups, NACLs, route tables, and Internet Gateways as IAM-controlled objects
- Default-permit egress: why VPCs are not default-deny out of the box
- VPC Endpoints and Private Link for keeping AWS service traffic off the public internet
- Flow log 5-tuple analysis: detecting port scans, lateral movement, and exfiltration candidates
- `cloudmapper collect` → `prepare` → `audit` → `webserver` workflow
- Security Group drift as a common misconfiguration indicator

## AI acceleration
Paste a set of VPC flow log entries into a model and ask it to identify anomalous patterns —
unexpected destination IPs, unusual port combinations, REJECT storms that suggest scanning. The
model will give a reasonable first triage in seconds. Then verify each candidate against the
`data/vpc-flow-logs.log` context: is the flagged destination IP in a known-good range? Is the port
associated with a legitimate service? Is the transfer volume actually large (flow logs include byte
counts)? The model flags candidates; you adjudicate signal from noise. Never include a model-flagged
IP in an incident report without confirming it is not a legitimate AWS service endpoint.
