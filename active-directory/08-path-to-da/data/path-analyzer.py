#!/usr/bin/env python3
"""
path-analyzer.py — Corp attack path analyser.
Reads bloodhound-attack-paths.json and prints a structured report.

Usage: python3 path-analyzer.py bloodhound-attack-paths.json
"""
import json
import sys


def print_separator(char="=", width=70):
    print(char * width)


def analyse(data: dict) -> None:
    print_separator()
    print("CORP — ATTACK PATH ANALYSIS")
    print(f"Domain: {data['meta']['domain']}")
    print(f"Total paths found: {data['meta']['total_paths']}")
    print_separator()

    for path in data["paths"]:
        print()
        print(f"PATH {path['id']}: {path['name']}")
        print(f"  Length: {path['length']} hops | Feasibility: {path['feasibility']} | Stealth: {path['stealth']}")
        print()

        techniques_used = []
        for hop in path["hops"]:
            src = hop["from"]["name"]
            tgt = hop["to"]["name"]
            edge = hop["edge"]
            tid = hop["attck_technique"]
            tname = hop["attck_name"]
            diff = hop["detection_difficulty"]
            events = ", ".join(hop["events_generated"]) if hop["events_generated"] else "None"

            print(f"  Step {hop['step']}: {src}")
            print(f"    --> [{edge}] --> {tgt}")
            print(f"    ATT&CK:   {tid} — {tname}")
            print(f"    Action:   {hop['action'][:90]}{'...' if len(hop['action']) > 90 else ''}")
            print(f"    Events:   {events}")
            print(f"    Detect:   {diff}")
            print()
            techniques_used.append(f"{tid} ({tname})")

        print(f"  Unique techniques: {len(set(techniques_used))}")
        print_separator("-")

    print()
    print_separator()
    print("PRIORITISED MITIGATIONS")
    print_separator()
    print()

    for m in data["mitigations"]:
        print(f"[{m['effort']} effort] {m['control']}")
        print(f"  Breaks: {', '.join(m['paths_broken'])}")
        print(f"  Impact: {m['impact']}")
        print(f"  Action: {m['recommended_action']}")
        print()

    # Highest-leverage fix
    path_breaks = {}
    for m in data["mitigations"]:
        for pb in m["paths_broken"]:
            path_breaks[m["id"]] = path_breaks.get(m["id"], 0) + 1

    if path_breaks:
        best = max(path_breaks, key=path_breaks.get)
        best_m = next(m for m in data["mitigations"] if m["id"] == best)
        print_separator()
        print("HIGHEST-LEVERAGE SINGLE FIX")
        print(f"  {best_m['control']}")
        print(f"  Effort: {best_m['effort']} | Breaks {path_breaks[best]} path segment(s)")
        print_separator()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: path-analyzer.py <bloodhound-attack-paths.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    analyse(data)
