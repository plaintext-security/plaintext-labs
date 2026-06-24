---
# This front-matter block is the STRUCTURED summary the claim-verifier parses.
# It mirrors the prose below. Treat it as the model's machine-readable claims.
incident: "Workstation compromise & cloud pivot"
analyst_ai: "drafted by model, UNVERIFIED"
cves:
  - "CVE-2024-3094"      # claim: initial access exploited this
  - "CVE-2021-44228"     # claim: used for lateral movement
attck:
  - id: "T1071.001"
    tactic: "Command and Control"      # correct
  - id: "T1036.004"
    tactic: "Persistence"              # WRONG tactic (Masquerading is Defense Evasion)
  - id: "T1110"
    tactic: "Credential Access"        # claim: brute force — contradicted by evidence
hashes:
  - artifact: "svchost32.exe"
    sha256: "0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff"   # WRONG hash
timeline:
  - time: "2024-03-14T22:14:07Z"
    event: "Attacker authenticates as jsmith over VPN from 203.0.113.66"   # SUPPORTED (auth.log)
  - time: "2024-03-14T22:18:33Z"
    event: "Dropper svchost32.exe executed on BEACHHEAD-WS01"              # SUPPORTED (4688)
  - time: "2024-03-14T23:55:00Z"
    event: "12 GB exfiltrated from S3 bucket corp-fin-reports"             # UNSUPPORTED (no such artifact)
  - time: "2024-03-14T22:47:09Z"
    event: "Attacker creates IAM access key for persistence"               # SUPPORTED (cloudtrail)
root_cause: "Brute-force attack against the VPN gateway cracked jsmith's weak password, giving initial access."
---

# Incident Summary (DRAFT, AI-generated)

## Overview

On 14 March 2024, an external actor gained access to the environment and
deployed a dropper (`svchost32.exe`) on workstation BEACHHEAD-WS01, then pivoted into
the AWS environment using jsmith's session.

## Initial Access

The actor exploited **CVE-2024-3094** in the VPN gateway to obtain initial access,
following a **brute-force attack (T1110)** that cracked jsmith's weak password. Once
authenticated from 203.0.113.66 at 22:14 UTC, the dropper was staged.

## Execution & Persistence

`svchost32.exe` (SHA256 `0000111122223333...ffff`) executed at 22:18:33 UTC and
established persistence. The malware masqueraded as a system service
(**T1036.004 — Persistence**) and beaconed to its C2 over web protocols
(**T1071.001 — Command and Control**). Lateral movement leveraged **CVE-2021-44228**.

## Cloud Pivot & Exfiltration

The actor assumed the prod-deploy role and, at 23:55 UTC, **exfiltrated approximately
12 GB from the S3 bucket `corp-fin-reports`**, then created an IAM access key at
22:47 UTC for durable access.

## Root Cause

The root cause was a **brute-force attack against the VPN gateway** that cracked
jsmith's weak password. Recommend enforcing MFA and account lockout.
