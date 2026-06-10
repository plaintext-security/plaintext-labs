# Module 08 — Triage & Live Response

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *get the right data off the right hosts in minutes, before the attacker cleans up or the machine reboots.*

## Why this matters

The first hour of an incident is the most volatile. Processes die, network connections drop, and
an attacker who knows they've been detected may begin wiping. Disk imaging takes hours; live
response takes minutes. A practitioner who can push a purpose-built collector to dozens of endpoints
simultaneously and pull back structured data without touching disk images is an asset in a crisis.
Velociraptor is the tool that makes this real — it ships as a single binary, runs a built-in query
language against live host state, and scales to enterprises of tens of thousands of endpoints.

## Objective

Deploy a Velociraptor server and endpoint agent in a local Docker environment, collect running
processes, active network connections, and recently modified files via VQL, and interpret the
output in the context of the Meridian Financial investigation.

## The core idea

Live response sits in a tension that trips up new responders: you want to capture volatile state
(memory, open connections, running processes) before it's gone, but every action you take on a live
system changes it. The answer is *collection-first, analysis-second* — run a read-only agent that
queries the OS through kernel APIs, pulls the results over the wire, and leaves the live system
otherwise untouched. You're not sitting at the keyboard running commands; you're issuing queries
that execute in parallel across a fleet.

The querying primitive Velociraptor uses is **VQL** (Velociraptor Query Language), which is SQL
shaped around OS artifacts: process tables, file system journals, Windows event logs, registry
hives. A VQL artifact is a named, parameterised query — `Windows.System.Pslist` or
`Linux.Sys.BashHistory` — that the agent executes locally and ships the results back. An analyst
who knows a handful of these artifacts can answer "which accounts are logged in right now?", "what
process opened this port?", and "was anything written to this path in the last 24 hours?" in
seconds, across every enrolled endpoint simultaneously.

The key mental shift is: **triage is not forensics.** Triage is rapid prioritisation — you collect
just enough to say "this host is in scope; image it and move on" or "this host is clean; stand
down." Full forensic acquisition (module 02) comes later for the in-scope hosts. Getting that
triage wrong in either direction is expensive: miss a host and lose the evidence; image everything
and drown in data for weeks. VQL artifacts let you ask crisp questions — persistence mechanisms,
scheduled tasks, suspicious parent-child process relationships — and stop when you have enough to
triage, not when you've collected everything.

In the Meridian investigation, the compromised developer account triggered alerts on one endpoint,
but the IR team needs to know whether the attacker moved laterally. Live response can answer that
question across fifty hosts in ten minutes; disk imaging those fifty hosts would take two days. The
answers shape every subsequent step: which hosts go into the imaging queue, which users get password
resets, and whether the incident is still active.

## Learn (~3 hrs)

**Velociraptor fundamentals (~1.5 hrs)**
- [Velociraptor Docs — Quick Start](https://docs.velociraptor.app/docs/overview/) — the architecture overview: server, client, GUI, and VQL. Read the "Deployment" and "Artifacts" sections to understand how queries flow to endpoints.

**VQL & artifacts (~1 hr)**
- [VQL Reference](https://docs.velociraptor.app/vql_reference/) — the built-in functions and plugins. Focus on the `Process`, `Network`, and `Filesystem` categories — those cover the core triage questions.
- [Exchange Artifact Repository](https://docs.velociraptor.app/exchange/) — the community library of contributed artifacts. Browse the Incident Response category to see what real analysts collect.

**Triage decision-making (~0.5 hrs)**
- [SANS FOR508 Triage Cheat Sheet (PDF)](https://www.sans.org/posters/hunt-evil/) — free one-page poster: the baseline of "what normal looks like" on a Windows endpoint. Use it as the checklist when reviewing Velociraptor output; anything outside the norm is a priority.

## Key concepts
- Live response collects volatile state (processes, connections, open files) read-only via kernel APIs
- VQL is SQL for endpoint artifacts: named, parameterised, runs in parallel across the fleet
- Triage ≠ imaging — collect enough to scope, then image only in-scope hosts
- Hunt vs. query: a hunt pushes the same artifact to all enrolled endpoints simultaneously
- Collection priority: running processes → network connections → persistence mechanisms → recent file writes

## AI acceleration

A model is excellent at writing VQL from a description: "give me a VQL query for all processes whose parent is explorer.exe but whose image path is outside C:\Windows" is faster to describe than write. Use it to draft artifact queries, then review the generated VQL against the reference docs before running it in production — VQL that selects from the wrong table or joins on the wrong key will silently return empty results and miss the threat. The other AI move: paste a process list or connection table into a chat session and ask "anything anomalous here?" as a *triage lead generator*, not as a verdict. You confirm every flagged item against the artifact yourself.
