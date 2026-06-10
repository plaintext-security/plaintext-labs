# Module 11 — Container Escape & Runtime Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *containers are not a security boundary; understand where the walls are and how they break.*

## Why this matters
The phrase "it's just a container" is one of the most dangerous assumptions in cloud security. A developer who deploys `--privileged` because it "fixed the permission error" has handed an attacker a root shell on the node — one pivot away from every other pod on the host, the instance metadata service, and the cloud credential chain. CVE-2019-5736 (runc overwrite), CVE-2020-15257 (Containerd abstract Unix socket), and CVE-2021-30465 (runc symlink race) are real escapes from real container runtimes, each exploited in the wild. Runtime security tooling like Falco exists precisely because scanning and policy can't catch what code does at runtime — only syscall visibility can.

## Objective
Demonstrate a privileged-container host-filesystem escape, then deploy Falco to detect the suspicious syscalls it generates — producing a working detection that would have caught the technique before damage was done.

## The core idea
Containers share the host kernel. What Linux namespaces and cgroups provide is *isolation*, not a hypervisor-grade *boundary*: separate PID and network namespaces, a limited view of the filesystem, and resource caps — but a single shared kernel underneath. A privileged container receives all Linux capabilities (`CAP_SYS_ADMIN`, `CAP_NET_ADMIN`, and 35 others) and most namespace protections are dropped. With `CAP_SYS_ADMIN` you can mount filesystems, load kernel modules, and read raw block devices. `--privileged` is therefore not a "slightly elevated container" — it's effectively a root shell on the host with a thin namespace wrapper. The canonical escape path is: mount the host's root filesystem (accessible because `/dev/sda1` or the underlying block device is visible), `chroot` into it, and read or write anything on the host.

Beyond `--privileged`, several other configuration mistakes narrow or eliminate the isolation. Mounting the Docker socket (`-v /var/run/docker.sock:/var/run/docker.sock`) lets any process in the container issue Docker API calls — including launching a new privileged container. Mounting the host's PID namespace (`--pid=host`) lets a process in the container see and signal host processes. A writable hostPath volume over `/etc` lets a container modify the host's `passwd`, `sudoers`, or `cron`. Each of these is a partial escape vector that doesn't require a kernel CVE — it's just a misconfiguration. This is why Kubernetes admission policies and runtime detection are layered: policy prevents the misconfiguration from deploying; runtime detection catches it if the policy was bypassed or predates the workload.

Runtime security fills the gap that static scanning cannot close. Falco instruments the Linux kernel via eBPF (or its older kernel-module driver) and evaluates a stream of syscall events against a rule set. A rule like "a process in a container wrote to `/etc/passwd`" fires not because the image was scanned, but because `openat(2)` was called on that path at runtime. This catches both known-bad techniques and novel ones that happen to follow suspicious patterns — privilege escalation, reverse shells, unexpected outbound connections, credential file reads. The output is a structured alert with the container ID, image name, PID, and syscall context — enough to identify the workload and begin incident response.

The practitioner's mental model for runtime security is **signal vs. noise tuning**. Default Falco rule sets generate a lot of alerts in a typical cluster because they're written broadly. The skill is suppressing expected benign events (a database process writing to its data directory, a log shipper opening arbitrary files) through `exceptions` or more precise conditions, while keeping the rules that cover real attacker behaviour. A tuned Falco rule set for a known workload is far more actionable than the default set running against an unknown one. That tuning is itself an artifact worth versioning — it's the detection equivalent of writing infrastructure as code.

## Learn (~3 hrs)

**Container isolation internals (~1 hr)**
- [Julia Evans — "A container is just a process" (blog)](https://jvns.ca/blog/2020/04/27/new-zine-how-containers-work/) — the clearest short explanation of how namespaces and cgroups compose to form container isolation; read the blog post (~15 min) before diving deeper.
- [Linux man page: capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html) — skim the capability list (CAP_SYS_ADMIN, CAP_NET_ADMIN, CAP_DAC_OVERRIDE) and understand what each grants; this is the vocabulary behind `--privileged`.

**Container escape techniques (~1 hr)**
- [Trail of Bits — "Understanding Docker container escapes"](https://blog.trailofbits.com/2019/07/19/understanding-docker-container-escapes/) — a technical walkthrough of the `cgroup release_agent` escape technique (CVE-class); step-by-step, with the syscall-level explanation.
- [NVD — CVE-2021-30465](https://nvd.nist.gov/vuln/detail/CVE-2021-30465) — runc symlink-race escape; read the description and CVSS vector to understand the attack surface.
- [MITRE ATT&CK T1611 — Escape to Host](https://attack.mitre.org/techniques/T1611/) — the ATT&CK technique card; note the sub-techniques and the detection guidance.

**Falco runtime detection (~1 hr)**
- [Falco documentation — Rules](https://falco.org/docs/rules/) — the rules language reference; read the "Conditions", "Output", and "Macros" sections. This is the vocabulary you need to write and tune rules.
- [Sysdig blog — "Falco: runtime security for containers"](https://falco.org/docs/concepts/event-sources/) — the conceptual overview of how Falco instruments syscalls via eBPF; a 10-minute read that builds the mental model before the lab.

## Key concepts
- Containers share the host kernel — namespaces provide isolation, not a security boundary
- `--privileged` = all Linux capabilities + most protections disabled = host root access
- Escape vectors beyond kernel CVEs: Docker socket mount, `--pid=host`, writable hostPath `/etc`
- Falco instruments the kernel syscall stream via eBPF to detect runtime behaviour, not just config
- The `release_agent` and block-device-mount escape patterns (CVE-2021-30465 class)
- Signal vs. noise tuning: `exceptions` and precise conditions in Falco rules
- MITRE ATT&CK T1610 (Deploy Container), T1611 (Escape to Host), T1613 (Container and Resource Discovery)

## AI acceleration
Paste a Falco rule YAML into a model and ask it to explain what the rule catches, suggest edge cases it would miss, and propose an `exception` for a specific benign workload. It's reliable on rule syntax and logic — but it cannot tell you whether the rule would actually generate noise in your specific cluster without cluster context. Use it to draft rule variants and `exceptions`; you validate them against real Falco output from `make demo` before promoting to production.
