# Module 03 — Linux Telemetry

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *servers and containers are Linux; this is how you watch them.*

## Why this matters
Cloud workloads, web servers, and containers run Linux, where default logging tells you little
about *what executed*. auditd and osquery turn a Linux host into a queryable sensor — process
execution, file access, network connections — the visibility the cloud and detection tracks assume.
Without it, a compromised Linux host is a blind spot.

## Objective
Configure Linux audit logging, query host state with osquery, and capture the execution telemetry
detections rely on.

## The core idea
The cloud runs on Linux — your web servers, your containers, your Kubernetes nodes — and Linux's
default logs tell you almost nothing about *what executed*. `/var/log` has auth and syslog, but not
"this binary ran with these arguments and opened this socket." Two tools fill that gap from opposite
directions. **auditd** is the kernel's audit framework: it taps syscalls and streams events as they
happen (`execve`, file access, network) — an always-on firehose. **osquery** flips the model and
exposes the host as a SQL database you *query* (`SELECT … FROM processes`), live or on a schedule.
auditd is the event stream; osquery is the question you ask on demand. You usually want both.

For anyone trained on Windows, the translation is clean: **auditd is your Linux Sysmon** (the
streaming execution sensor) and **osquery is your Linux live-response tool**. The detection lens is
identical to the endpoint module — collect process execution, file, and network activity with the
techniques you care about in mind — only the plumbing differs.

Two gotchas worth front-loading. First, auditd rules are easy to write far too broadly: an
over-eager rule floods you *and* adds real syscall overhead on a busy host, so you scope tightly.
Second, **containers are the modern blind spot** — a process inside a container is just a process on
the host kernel, so host-level auditd/eBPF *can* see it, but only if you've accounted for namespaces
and where the container's own logs go. eBPF-based tooling (Falco, Tetragon) is where this is heading,
and the cloud track builds directly on it.

## Learn (~4 hrs)

**The Linux sensor**
- [osquery documentation](https://osquery.readthedocs.io/en/latest/) — query your host like a database; read "Getting Started" and a few example queries.
- [Linux Audit (auditd) documentation](https://github.com/linux-audit/audit-documentation/wiki) — the kernel audit framework: rules, events, and what to log.

**What to log**
- [MITRE ATT&CK — Data Source: Process](https://attack.mitre.org/datasources/DS0009/) — collect with detection in mind (same lens as the Windows module, Linux side).

## Key concepts
- auditd: rules, syscalls, and the event format
- osquery: host-as-a-database for live and scheduled queries
- Process execution + file + network telemetry on Linux
- eBPF-based tooling (the modern direction)
- Containers: where host telemetry sees — and misses — container activity

## AI acceleration
A model writes auditd rules and osquery SQL quickly — but an over-broad audit rule floods you with
noise and a wrong osquery join misses the event entirely. Test what the rule actually captures
against real activity.
