#!/usr/bin/env python3
"""
analyze.py — IAM privilege-escalation graph analyzer.

Loads a pmapper-style graph.json and:
  1. Finds all paths from any non-admin node to any admin node.
  2. Prints each path with the required API calls at each hop.
  3. Outputs a JSON report suitable for a CI gate.
  4. Exits non-zero if any path to admin exists.

Usage:
  python analyze.py data/graph.json
  python analyze.py data/graph.json --json-report report.json
"""

import json
import sys
import argparse
from collections import defaultdict, deque


def load_graph(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def build_adjacency(graph: dict) -> dict[str, list[dict]]:
    """Return {source_arn: [edge, ...]} for all edges in the graph."""
    adj = defaultdict(list)
    for edge in graph.get("edges", []):
        adj[edge["source"]].append(edge)
    return adj


def find_admin_arns(graph: dict) -> set[str]:
    return {n["arn"] for n in graph.get("nodes", []) if n.get("is_admin", False)}


def bfs_paths(start_arn: str, admin_arns: set, adjacency: dict) -> list[list[dict]]:
    """BFS to find all simple paths from start_arn to any admin node.

    visited is tracked per-path (as a frozenset) so multiple distinct paths
    through different intermediate nodes are all discovered.
    """
    found_paths = []
    # Queue items: (current_arn, path_so_far_as_list_of_edges, visited_arns)
    queue = deque([(start_arn, [], frozenset([start_arn]))])

    while queue:
        current, path, visited = queue.popleft()
        if current in admin_arns and path:
            found_paths.append(path)
            continue
        for edge in adjacency.get(current, []):
            dest = edge["destination"]
            if dest not in visited:
                queue.append((dest, path + [edge], visited | {dest}))

    return found_paths


def format_path(path: list[dict]) -> str:
    lines = []
    for i, edge in enumerate(path, 1):
        src_name = edge["source"].split("/")[-1]
        dst_name = edge["destination"].split("/")[-1]
        actions = ", ".join(edge.get("required_actions", [edge.get("edge_type", "?")]))
        lines.append(f"  Hop {i}: {src_name} --> {dst_name}")
        lines.append(f"          Actions: {actions}")
        lines.append(f"          Reason:  {edge.get('reason', 'see graph')}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="IAM attack-path analyzer")
    parser.add_argument("graph", help="Path to graph.json")
    parser.add_argument("--json-report", metavar="FILE", help="Write JSON report to FILE")
    args = parser.parse_args()

    graph = load_graph(args.graph)
    adjacency = build_adjacency(graph)
    admin_arns = find_admin_arns(graph)
    non_admin_nodes = [n for n in graph.get("nodes", []) if not n.get("is_admin", False)]

    all_paths = []
    for node in non_admin_nodes:
        paths = bfs_paths(node["arn"], admin_arns, adjacency)
        for path in paths:
            all_paths.append({
                "source": node["arn"],
                "destination": path[-1]["destination"],
                "hops": len(path),
                "edges": path,
            })

    print(f"Account: {graph.get('account_id', 'unknown')}")
    print(f"Nodes: {len(graph.get('nodes', []))}  |  Edges: {len(graph.get('edges', []))}  |  Admin nodes: {len(admin_arns)}")
    print()

    if not all_paths:
        print("No paths to admin found. Graph is clean.")
        sys.exit(0)

    print(f"FOUND {len(all_paths)} path(s) to admin:\n")
    for i, p in enumerate(all_paths, 1):
        src = p["source"].split("/")[-1]
        dst = p["destination"].split("/")[-1]
        print(f"Path {i}: {src} --> [{p['hops']} hop(s)] --> {dst} (ADMIN)")
        print(format_path(p["edges"]))
        print()

    # Minimum cut-set hint from the graph if present
    cut = graph.get("minimum_cut_set")
    if cut:
        print("Minimum cut-set from graph metadata:")
        print(f"  {cut.get('description', '')}")
        fix = cut.get("cheapest_fix", {})
        if fix:
            print(f"  Cheapest fix ({fix.get('role', '')}):")
            print(f"    Change: {fix.get('change', '')}")
            print(f"    Result: {fix.get('result', '')}")

    if args.json_report:
        report = {
            "account_id": graph.get("account_id"),
            "paths_to_admin": len(all_paths),
            "paths": all_paths,
            "clean": False,
        }
        with open(args.json_report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nJSON report written to: {args.json_report}")

    # Exit non-zero so CI gates fail when paths exist
    sys.exit(1)


if __name__ == "__main__":
    main()
