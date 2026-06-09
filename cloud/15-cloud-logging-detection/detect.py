#!/usr/bin/env python3
"""
detect.py — simple CloudTrail event matcher for plaintext module 15.

Usage:
    python detect.py [events_file]

Loads a CloudTrail JSON file (the {"Records": [...]} format) and runs a
small set of hard-coded detection rules against it, printing matches.

Rules implemented:
  1. IAM privilege escalation sequence: CreateUser + AttachUserPolicy within 5 min
  2. AssumeRole from unexpected region (not us-east-1 or us-west-2)
  3. S3 GetObject with suspicious user-agent
  4. Root console login without MFA
  5. Security group ingress opened to 0.0.0.0/0
"""
import json
import sys
from datetime import datetime, timezone
from collections import defaultdict

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def parse_time(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def fmt_event(ev: dict) -> str:
    return (
        f"  time={ev.get('eventTime', '?')}  "
        f"name={ev.get('eventName', '?')}  "
        f"user={ev.get('userIdentity', {}).get('arn', '?')}  "
        f"ip={ev.get('sourceIPAddress', '?')}"
    )


# --------------------------------------------------------------------------
# Rule 1: IAM privilege escalation — CreateUser → AttachUserPolicy < 5 min
# --------------------------------------------------------------------------

def rule_iam_privesc(records: list) -> list:
    findings = []
    creates = [
        r for r in records
        if r.get("eventSource") == "iam.amazonaws.com"
        and r.get("eventName") == "CreateUser"
    ]
    attaches = [
        r for r in records
        if r.get("eventSource") == "iam.amazonaws.com"
        and r.get("eventName") == "AttachUserPolicy"
    ]

    admin_policies = {"AdministratorAccess", "PowerUserAccess", "IAMFullAccess"}

    for create in creates:
        created_user = (create.get("requestParameters") or {}).get("userName", "")
        create_time = parse_time(create["eventTime"])
        create_ip = create.get("sourceIPAddress", "")

        for attach in attaches:
            params = attach.get("requestParameters") or {}
            attach_user = params.get("userName", "")
            policy_arn = params.get("policyArn", "")
            attach_time = parse_time(attach["eventTime"])

            if attach_user != created_user:
                continue

            policy_name = policy_arn.split("/")[-1]
            if policy_name not in admin_policies:
                continue

            delta = abs((attach_time - create_time).total_seconds())
            if delta > 300:  # 5-minute window
                continue

            findings.append({
                "rule": "IAM_PRIVESC_CREATEUSER_ATTACHPOLICY",
                "severity": "CRITICAL",
                "technique": "T1098 — Account Manipulation",
                "summary": (
                    f"New IAM user '{created_user}' created and granted '{policy_name}' "
                    f"within {int(delta)}s from IP {create_ip}"
                ),
                "events": [create, attach],
            })
    return findings


# --------------------------------------------------------------------------
# Rule 2: AssumeRole from unexpected region
# --------------------------------------------------------------------------

EXPECTED_REGIONS = {"us-east-1", "us-west-2"}


def rule_assumedrole_unexpected_region(records: list) -> list:
    findings = []
    for r in records:
        if r.get("eventName") != "AssumeRole":
            continue
        region = r.get("awsRegion", "")
        if region not in EXPECTED_REGIONS:
            findings.append({
                "rule": "ASSUMEROLE_UNEXPECTED_REGION",
                "severity": "HIGH",
                "technique": "T1078.004 — Valid Cloud Accounts",
                "summary": (
                    f"AssumeRole called from unexpected region '{region}' "
                    f"by {r.get('userIdentity', {}).get('arn', '?')} "
                    f"from IP {r.get('sourceIPAddress', '?')}"
                ),
                "events": [r],
            })
    return findings


# --------------------------------------------------------------------------
# Rule 3: S3 GetObject with suspicious user-agent
# --------------------------------------------------------------------------

SUSPICIOUS_UA_FRAGMENTS = [
    "Python/2.7",   # EOL Python
    "Boto3/1.9",    # Very old boto3
    "curl/",        # curl accessing S3 directly is unusual
]
SENSITIVE_BUCKETS = {"meridian-financial-reports-prod", "meridian-audit-logs-archive"}


def rule_s3_suspicious_useragent(records: list) -> list:
    findings = []
    for r in records:
        if r.get("eventName") != "GetObject":
            continue
        params = r.get("requestParameters") or {}
        bucket = params.get("bucketName", "")
        if bucket not in SENSITIVE_BUCKETS:
            continue
        ua = r.get("userAgent", "")
        matched = [frag for frag in SUSPICIOUS_UA_FRAGMENTS if frag in ua]
        if matched:
            findings.append({
                "rule": "S3_SENSITIVE_BUCKET_SUSPICIOUS_UA",
                "severity": "HIGH",
                "technique": "T1530 — Data from Cloud Storage",
                "summary": (
                    f"GetObject on sensitive bucket '{bucket}' with suspicious user-agent "
                    f"fragment(s) {matched} from IP {r.get('sourceIPAddress', '?')}"
                ),
                "events": [r],
            })
    return findings


# --------------------------------------------------------------------------
# Rule 4: Root console login without MFA
# --------------------------------------------------------------------------

def rule_root_login_no_mfa(records: list) -> list:
    findings = []
    for r in records:
        if r.get("eventName") != "ConsoleLogin":
            continue
        uid = r.get("userIdentity", {})
        if uid.get("type") != "Root":
            continue
        additional = r.get("additionalEventData") or {}
        if additional.get("MFAUsed", "Yes") != "Yes":
            findings.append({
                "rule": "ROOT_LOGIN_NO_MFA",
                "severity": "CRITICAL",
                "technique": "T1078.004 — Valid Cloud Accounts (Root)",
                "summary": (
                    f"Root account console login without MFA "
                    f"from IP {r.get('sourceIPAddress', '?')}"
                ),
                "events": [r],
            })
    return findings


# --------------------------------------------------------------------------
# Rule 5: Security group opened to 0.0.0.0/0
# --------------------------------------------------------------------------

def rule_sg_open_ingress(records: list) -> list:
    findings = []
    for r in records:
        if r.get("eventName") != "AuthorizeSecurityGroupIngress":
            continue
        params = r.get("requestParameters") or {}
        perms = params.get("ipPermissions", {}).get("items", [])
        for perm in perms:
            for ip_range in perm.get("ipRanges", {}).get("items", []):
                if ip_range.get("cidrIp") == "0.0.0.0/0":
                    findings.append({
                        "rule": "SG_INGRESS_OPEN_TO_ALL",
                        "severity": "HIGH",
                        "technique": "T1562.007 — Disable or Modify Cloud Firewall",
                        "summary": (
                            f"Security group {params.get('groupId', '?')} opened "
                            f"port {perm.get('fromPort', '?')}/{perm.get('ipProtocol', '?')} "
                            f"to 0.0.0.0/0 by {r.get('userIdentity', {}).get('arn', '?')}"
                        ),
                        "events": [r],
                    })
    return findings


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    events_file = sys.argv[1] if len(sys.argv) > 1 else "data/cloudtrail/events.json"

    with open(events_file) as f:
        data = json.load(f)

    records = data.get("Records", data) if isinstance(data, dict) else data
    print(f"Loaded {len(records)} CloudTrail events from {events_file}\n")

    all_rules = [
        rule_iam_privesc,
        rule_assumedrole_unexpected_region,
        rule_s3_suspicious_useragent,
        rule_root_login_no_mfa,
        rule_sg_open_ingress,
    ]

    total_findings = 0
    for rule_fn in all_rules:
        findings = rule_fn(records)
        for f in findings:
            total_findings += 1
            sev = f["severity"]
            bar = "!!!" if sev == "CRITICAL" else "!! "
            print(f"{bar} [{sev}] {f['rule']}")
            print(f"    Technique : {f['technique']}")
            print(f"    Summary   : {f['summary']}")
            for ev in f.get("events", []):
                print(f"    Event     :{fmt_event(ev)}")
            print()

    if total_findings == 0:
        print("No findings. Check that the events file path is correct.")
    else:
        print(f"--- {total_findings} finding(s) total ---")


if __name__ == "__main__":
    main()
