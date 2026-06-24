#!/usr/bin/env python3
"""
parse_cloudtrail.py — parses bundled AWS CloudTrail JSON events for the log/cloud forensics lab.
The CloudTrail set is modelled on the public Lunar Spider cloud TTPs (neutral naming).

Usage: python3 parse_cloudtrail.py <cloudtrail_directory>

Prints a chronological timeline of API calls, groups by principal,
and flags suspicious sequences (recon followed by persistence).
"""

import json
import os
import sys
from datetime import datetime, timezone

RECON_EVENTS = {
    "GetCallerIdentity", "ListUsers", "ListRoles", "ListBuckets",
    "DescribeInstances", "GetAccountSummary", "ListAttachedUserPolicies",
    "ListGroupsForUser", "GetUser",
}

PERSISTENCE_EVENTS = {
    "CreateUser", "AttachUserPolicy", "CreateAccessKey", "PutUserPolicy",
    "CreateRole", "AttachRolePolicy", "UpdateAssumeRolePolicy",
    "CreateLoginProfile",
}

LATERAL_EVENTS = {"AssumeRole", "SwitchRole", "GetFederationToken"}


def parse_events(directory):
    events = []
    for fname in os.listdir(directory):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(directory, fname)) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue
            records = data.get("Records", [data]) if isinstance(data, dict) else data
            if isinstance(records, dict):
                records = [records]
            for record in records:
                if not isinstance(record, dict):
                    continue
                events.append(record)
    events.sort(key=lambda e: e.get("eventTime", ""))
    return events


def summarise(events):
    print("=" * 70)
    print("  CloudTrail Event Timeline (modelled on Lunar Spider cloud TTPs)")
    print("=" * 70)
    print()

    by_principal = {}
    for evt in events:
        uid = evt.get("userIdentity", {})
        arn = uid.get("arn") or uid.get("userName") or uid.get("type", "unknown")
        by_principal.setdefault(arn, []).append(evt)

    for principal, evts in by_principal.items():
        print(f"Principal: {principal}")
        print(f"  Total events: {len(evts)}")
        recon_times = []
        persist_times = []
        for e in evts:
            name = e.get("eventName", "")
            ts = e.get("eventTime", "")
            src = e.get("sourceIPAddress", "")
            tag = ""
            if name in RECON_EVENTS:
                tag = "[RECON]"
                recon_times.append(ts)
            elif name in PERSISTENCE_EVENTS:
                tag = "[PERSIST]"
                persist_times.append(ts)
            elif name in LATERAL_EVENTS:
                tag = "[LATERAL]"
            print(f"    {ts}  {name:<40} {src:<22} {tag}")
        print()

        # Flag recon → persistence within 60 minutes
        if recon_times and persist_times:
            first_recon = datetime.fromisoformat(recon_times[0].replace("Z", "+00:00"))
            first_persist = datetime.fromisoformat(persist_times[0].replace("Z", "+00:00"))
            delta = (first_persist - first_recon).total_seconds() / 60
            if 0 <= delta <= 60:
                print(f"  *** FLAG: Recon → Persistence within {delta:.1f} minutes ***")
                print(f"      First recon: {recon_times[0]}")
                print(f"      First persistence: {persist_times[0]}")
                print()

    print("=" * 70)
    print("  SUMMARY")
    total_recon = sum(1 for e in events if e.get("eventName") in RECON_EVENTS)
    total_persist = sum(1 for e in events if e.get("eventName") in PERSISTENCE_EVENTS)
    total_lateral = sum(1 for e in events if e.get("eventName") in LATERAL_EVENTS)
    print(f"  Total events:       {len(events)}")
    print(f"  Recon events:       {total_recon}")
    print(f"  Persistence events: {total_persist}")
    print(f"  Lateral movement:   {total_lateral}")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <cloudtrail_directory>")
        sys.exit(1)
    events = parse_events(sys.argv[1])
    if not events:
        print("No CloudTrail events found.")
        sys.exit(1)
    summarise(events)
