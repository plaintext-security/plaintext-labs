# Lab 11 — Reproduce the runc Breakout, Then Detect It

> **Hands-on lab.** Environment: `plaintext-labs/cloud/11-container-escape-runtime` (a `--privileged`
> attacker container + co-located target + a **Falco** eBPF sensor), plus a Vulhub half for the *real*
> CVE. Objective: **reproduce a container escape end-to-end, then write and tune the Falco rule that
> catches it** — silent on benign work, CRITICAL on the escape. Target: **~90 min**, one finish line.
> [← Back to the module concept](https://plaintext-security.github.io/plaintext/05-cloud/modules/11-container-escape-runtime/)

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **A container is a host process in a costume — same kernel, no hypervisor.** | There is no box to break out of. Every escape abuses a resource both sides touch. |
| 2 | **CVE-2019-5736 overwrites the host `runc` binary from inside the container.** | The runtime reaches *into* the container; a `/proc/self/exe` race turns that reach around → root on host. |
| 3 | **`--privileged` + `/dev` is a full escape with no CVE at all.** | Same shared-kernel hallway, a different door — just a permissive config. This is what the local lab reproduces. |
| 4 | **Static scan reads the image; admission reads the spec; neither sees behavior.** | The escape is a *sequence of syscalls at runtime* — only a runtime sensor (Falco) can see it. |
| 5 | **The sharp signal is the write to a host binary / `/etc/passwd`; `mount(2)` is the noisy one.** | Nothing benign writes a host binary; plenty of workloads `mount`. Pick the low-noise rule; tune the noisy one. |
| 6 | **A tuned rule is detection-as-code: fails the bad state, passes the fix.** | It fires on the escape and stays silent on the one benign workload you engineer around — the artifact a SOC keeps on. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [mental model](https://plaintext-security.github.io/plaintext/05-cloud/modules/11-container-escape-runtime/#the-mental-model-the-wall-is-the-kernel)
> and [the gap runtime detection fills](https://plaintext-security.github.io/plaintext/05-cloud/modules/11-container-escape-runtime/#the-gap-that-runtime-detection-fills);
> the [Falco Rules docs](https://falco.org/docs/rules/) for the `condition`/`exception` grammar.

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A container shares the host's kernel and has no hypervisor boundary. So what *is* a container "escape" —
   what does it actually abuse?
2. The image scans clean and the pod spec is legal, yet the escape still runs. Why can't scanning or
   admission control catch it, and what reads the event instead?

---

## Setup

This lab has **two halves**, both one command away.

**Half A — the real CVE (Vulhub).** You reproduce **CVE-2019-5736** against a *pinned vulnerable runc*
using [Vulhub](https://github.com/vulhub/vulhub). This is the genuine exploit — the host `runc` binary is
actually overwritten from inside the container — not a simulation.

```bash
git clone https://github.com/vulhub/vulhub
cd vulhub/runc/CVE-2019-5736     # pinned vulnerable runc + a target container
docker compose up -d --build     # bring up the vulnerable runtime
```

**Half B — detection (this environment).** You deploy and tune Falco using the reference environment here:
a `--privileged` attacker, a co-located target on a shared host path, and a Falco sensor.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/11-container-escape-runtime
make up           # privileged attacker + target + Falco sensor
make logs-falco   # (second terminal) tail Falco's JSON alerts
make shell        # shell into the attacker container
make demo         # run escape + detection end-to-end
make down         # stop and clean up
```

> **▸ On track if:** `make up` starts three services (`attacker`, `target`, `falco`); `make logs-falco`
> streams Falco's startup then goes quiet until an event fires. The environment is live.

> **Authorization note.** Only run the escape in the shipped local lab (or a disposable VM) you own —
> only ever test systems you own or have explicit written permission to test. Half A **overwrites a host
> binary**: run it on a throwaway VM, never a machine you care about, and `docker compose down` after.
> Half B's `--privileged` escape is also real (it reads a host-side path via a bind mount). The two
> halves are split only because pinning vulnerable runc and running Falco's eBPF probe have different host
> requirements — nothing here touches a system you don't control.

---

## Scenario

The platform team got a Dependabot alert: a data-processing job pulled a base image with a vulnerable
runc, and a *second* job in the same cluster runs `--privileged` "because it fixed a permissions error."
You are both halves of the response. **Red team:** reproduce the host-level escape so the risk is
undeniable, not theoretical. **Detection engineer:** stand up Falco, prove it catches the behavior, and
tune one false positive out so the rule is something the SOC will actually keep on. Each step runs the
same rhythm: **Predict → Do → Reveal → Record.**

---

## Build it — read a little, do a little

### Step 1 — Half A: reproduce CVE-2019-5736 (the real escape)

**Concept (30 sec):** Flight-card #2. `runc` is a host binary that reaches *into* the container to
`exec`. Because the attacker controls the container filesystem, a `/proc/self/exe` symlink race lets the
host's own `runc` be opened for writing and overwritten — the next container operation runs attacker code
on the host as root.

**Do it:** bring up Vulhub's vulnerable-runc environment and confirm the runc version is in the affected
range (cross-check the [NVD record](https://nvd.nist.gov/vuln/detail/CVE-2019-5736)). Then run the
published PoC: it replaces the container's entrypoint with the `/proc/self/exe` symlink and races the
open; when you (playing the admin) `exec` in, the host `runc` is overwritten.
*Hint: the README in the Vulhub directory names the exploit steps and points to a working PoC — follow them.*

> **▸ On track if:** the payload you control **executes on the host as root** on the next container
> operation — e.g. it drops a host marker file or a reverse shell that lands **outside** any container
> namespace (verify with `cat /proc/1/cgroup` on the host: no container ID). That host-root execution
> **is** the breakout. **Record:** the shared resource abused = the host `runc` binary the runtime reaches
> in with; no namespace/cgroup/capability stopped it because *the kernel and that binary were shared*.

### Step 2 — Half B: bring up the sensor and confirm your foothold

**Concept (30 sec):** Flight-card #3. The local escape needs no CVE — `--privileged` + a mounted `/dev`
and host path *is* the door. Falco watches the syscalls either door produces.

**Do it:** `make up`, then `make logs-falco` in a second terminal, then `make shell` into the attacker.
Confirm you're a container PID 1.

> **▸ On track if:** `cat /proc/1/cgroup` inside the shell shows a **container ID** (a long hex path),
> and `make logs-falco` is streaming (quiet, waiting for events). You're inside the privileged workload
> with the sensor watching.

### Step 3 — Trigger the escape behavior and watch Falco fire

**Concept (30 sec):** Flight-card #4. The write and the host-secret read are the escape's *behavior* —
exactly what a static scan and admission control never see.

**Do it:** run `make demo`. It writes to `/etc/passwd` and reads the host-side secret deterministically,
then tails Falco.

> **▸ On track if:** `make demo` prints `Written to /etc/passwd`, then the seeded secret
> (`DB_PASSWORD=S3cr3tToken-PROD-4829` / `API_KEY=mrd-prod-api-8f3a2c9e1b4d7f6a`), and the Falco tail
> emits a **`CRITICAL`** JSON line naming the rule **`Write /etc/passwd in Container`** with
> `container`, `image`, `pid`, and `cmdline` fields. (You'll also see a **`WARNING`** for
> `Read Sensitive File in Container`.) Copy the alert text into your report.

### Step 4 — Settle the prediction: which syscall is the sharp signal?

**Concept (30 sec):** Flight-card #5. The module asked you to predict; now compare the rules directly.

**Do it:** open `data/falco-rules.yaml`. Compare **Rule 1** (`Write /etc/passwd in Container`, fires on
the write) against **Rule 3** (`Container Mounts Host Filesystem`, fires on any `mount(2)`).

> **▸ On track if:** you can state that Rule 1 is the low-noise signal (nothing benign writes a host
> binary / `/etc/passwd`) and Rule 3 is the one that will generate your false positive (legitimate
> workloads `mount` volumes all the time). **Record:** build the detection around the write; expect to
> *tune* the mount rule.

### Step 5 — Force the false positive, then tune it out

**Concept (30 sec):** Flight-card #6. A rule that's silent on the escape is useless; a rule that screams
on every benign `mount` gets muted by the SOC. The craft is the exception that removes *only* the benign
case.

**Do it:** reproduce **one** benign event that trips a broad rule — e.g. a non-attack `mount` from an
allowed process, or a benign write under a data dir a rule matched too broadly. Capture the spurious
alert. Then edit the rule (add an `exception`, or tighten the `condition` to exclude the known
image/process/path) so it **no longer fires on the benign event but still fires on the escape.** Save the
result as `falco-rules-tuned.yaml` (mount it in place of `data/falco-rules.yaml`, or drop it in
`rules.d/` and `make down && make up`).

> **▸ On track if:** re-running the benign action produces **no alert**, and re-running `make demo` still
> produces the **`CRITICAL`** escape alert. The rule flipped: silent on benign, loud on the attack.

---

## Prove the control (your finish line)

**The escape you ran is caught by the rule you tuned — and *only* the escape.** Demonstrate the flip in
one pass: run your benign action (no alert) and then `make demo` (CRITICAL alert naming your rule),
against `falco-rules-tuned.yaml`. If your rule stays silent on the escape, or still screams on the benign
event, it isn't done — tune until it fires on exactly the attack. That flip is detection-as-code: your
judgment, encoded, that a SOC would keep enabled.

Then score your module prediction (which syscall is the sharp signal?) against Step 4 — note whether you
picked the write or, like most people, the `mount`.

---

## Recall check — close the doc, answer from memory (3 min)

1. In the module's terms, what shared resource did CVE-2019-5736 abuse, and why did no namespace, cgroup,
   or capability stop it?
2. Why is the write-to-host-binary the sharper detection signal than `mount(2)`?
3. What makes a Falco rule "detection-as-code," and what does "fails the bad state, passes the fix" mean
   for your tuned rule?

---

## Success criteria — you're done when

- [ ] You reproduced **CVE-2019-5736**: a payload you control executed on the host as root, originating
  from inside the container (real exploit, not a description).
- [ ] You can state the escape in the module's terms: the **shared host resource** abused, and why
  namespaces/caps didn't stop it.
- [ ] `make demo` produced a Falco **`CRITICAL`** alert (JSON) for the escape behavior showing container,
  image, pid, and rule name.
- [ ] You produced **one** benign false positive and then **tuned it out** — `falco-rules-tuned.yaml` is
  silent on the benign event and still CRITICAL on the escape, demonstrated by re-running both.

---

## Deliverables

- `escape-report.md` — the CVE-2019-5736 reproduction (steps, commands, the host-root proof), the
  shared-resource explanation in the module's mental-model language, and the Falco alert text from
  `make demo`.
- `falco-rules-tuned.yaml` — the tuned rule with your `exception`/tightened `condition`, plus a one-line
  comment per change saying which false positive it removes and why it still catches the attack.

Commit these two. Container/runtime state, the overwritten `runc`, host artifacts, and any captured
secrets (the seeded `DB_PASSWORD`/`API_KEY`) stay out of the commit.

## Automate & own it

**Required — the guardrail *is* the tuned detection.** Your judgment ("`mount` is noisy; the
write-to-host-binary is the sharp signal; here is the one benign case to except") is encoded in
`falco-rules-tuned.yaml` as **detection-as-code** — a rule that *fails the bad state and passes the fix*:
it fires on the escape and stays silent on the benign workload. Prove the flip in CI-style: a small script
(or `make demo`) that runs the benign action **and** the escape and asserts the tuned rule alerted on
exactly one. Have a model draft rule variants and the `exception`; you read every line and confirm each
variant still fires on the real escape before keeping it — a rule tuned until it's silent on *everything*
is worse than no rule. (Optional: also ship `audit-privileged.sh` — `docker inspect` across running
containers flagging `Privileged: true`, `/dev` mounts, or `docker.sock` mounts — the prevention companion
to the detection.)

## AI acceleration

Feed the escape's Falco alert JSON to a model and ask it to reconstruct the kill chain: technique, ATT&CK
ID, likely next move. It writes a solid triage narrative — validate it against the actual rule
`condition` and the [T1611](https://attack.mitre.org/techniques/T1611/) card. Then paste your tuned rule
and ask it to find an attack variant that now sneaks past your `exception`. If it finds one, your
exception is too broad — tighten it. That adversarial loop is the whole skill.

## Definition of done (`container-escape-runtime` ✅)

- [ ] Half A: CVE-2019-5736 reproduced — attacker payload ran on the host as root.
- [ ] Half B: `make demo` fired a CRITICAL Falco alert on the escape behavior, captured in the report.
- [ ] `escape-report.md` explains the shared-resource mechanism and carries the alert text.
- [ ] `falco-rules-tuned.yaml` is silent on one engineered benign event and still CRITICAL on the escape.
- [ ] You can explain all six flight-card facts cold, and why the write beats `mount` as the signal.

## Connects forward

- **Module 13 (K8s admission & runtime)** moves this exact problem into Kubernetes: `--privileged`
  becomes a pod-spec field a **Kyverno admission policy** blocks before it ever runs — prevention in
  front of the Falco detection you wrote here, which catches what slips past.
- **Module 15 (cloud logging & detection)** generalizes the move: today you tuned a Falco rule against
  benign syscalls; there you'll tune a Sigma rule against benign CloudTrail. Same signal-vs-noise craft,
  different log source.

## Marketable proof

> "I reproduced CVE-2019-5736 — the runc host-binary breakout — end to end, can explain why a container's
> shared kernel makes it a process-in-a-jail and not a VM, and I deployed and *tuned* a Falco rule that
> fires on the escape but stays silent on a benign workload I had to engineer around."

## Stretch

- Reproduce a **configuration** escape with no CVE: in a container with `/var/run/docker.sock` mounted,
  `docker run --privileged -v /:/host alpine chroot /host` for host root — and write the Falco rule that
  catches a container talking to the Docker socket.
- Read [CVE-2021-30465](https://nvd.nist.gov/vuln/detail/CVE-2021-30465) (runc symlink race) and explain,
  in your report, how it reaches a host filesystem write *without* `--privileged` — a different door,
  same shared-kernel hallway.
