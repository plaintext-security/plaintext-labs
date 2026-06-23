# Lab 11 — Reproduce the runc Breakout, Then Detect It

*Variant D · build-first. [← Back to the module concept](README.md)*

## Setup
This lab has **two halves**, both one command away.

**Half A — the real CVE.** You reproduce **CVE-2019-5736** against a *pinned vulnerable runc* using
[Vulhub](https://github.com/vulhub/vulhub)'s environment. This is the genuine exploit — the host
`runc` binary is actually overwritten from inside the container — not a simulation.

```bash
git clone https://github.com/vulhub/vulhub
cd vulhub/runc/CVE-2019-5736     # pinned vulnerable runc + a target container
docker compose up -d --build     # bring up the vulnerable runtime  <!-- VALIDATE compose vs docker-compose path -->
```

**Half B — detection.** You deploy and tune Falco using the companion reference environment in
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs), which ships a privileged
container, a co-located target, and a Falco sensor:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/11-container-escape-runtime
make up           # privileged attacker + target + Falco sensor
make logs-falco   # (second terminal) tail Falco's JSON alerts
make shell        # shell into the attacker container
make demo         # run escape + detection end-to-end
make down         # stop and clean up
```

**Be honest about what's real.** Half A overwrites a host binary — run it on a disposable
VM you own, never a machine you care about, and `docker compose down` after. Half B's `--privileged`
escape is also real (it mounts and reads a host-side path); the two halves are split only because
pinning vulnerable runc and running Falco's eBPF probe have different host requirements.

> Only test systems you own or have explicit written permission to test. Everything here runs locally
> against disposable containers and targets you launch yourself.

## Scenario
The target account's platform team got a Dependabot alert: a data-processing job pulled a base image
with a vulnerable runc, and a *second* job in the same cluster runs `--privileged` "because it fixed a
permissions error." You are both halves of the response. **Red team:** reproduce the host-level escape
so the risk is undeniable, not theoretical. **Detection engineer:** stand up Falco, prove it catches
the behavior, and tune one false positive out so the rule is something the SOC will actually keep on.

## Do

**Half A — Reproduce CVE-2019-5736 (the real escape)**

1. [ ] Bring up Vulhub's vulnerable-runc environment and confirm the runc version is in the affected
   range (cross-check against the [NVD record](https://nvd.nist.gov/vuln/detail/CVE-2019-5736)).
   *Hint: the README in the Vulhub directory names the exploit steps; follow them.*

2. [ ] Run the exploit: place the malicious payload inside the container so that when the operator (you,
   playing the admin) `exec`s in, the `/proc/self/exe` race overwrites the **host** `runc`. Confirm the
   escape: the payload you control executes **on the host as root** on the next container operation.
   *Hint: the published PoC works by replacing the container's entrypoint with a `/proc/self/exe`
   symlink and racing the open; the Vulhub README points to a working PoC.*

3. [ ] **Record the chain.** In your report, write the hop in the module's mental-model language:
   which **shared resource** was abused (the host `runc` binary the runtime reaches in with), and why
   no namespace, cgroup, or capability stopped it — *the kernel and that host binary were shared.*

**Half B — Deploy and tune Falco**

4. [ ] `make up`, then `make logs-falco` in a second terminal. `make shell` into the privileged
   attacker. Confirm you're a container PID 1 (`cat /proc/1/cgroup` shows the container ID).

5. [ ] **Trigger the escape behavior and watch Falco fire.** From the attacker shell, write to a
   host-binary-class path / `/etc/passwd` and read the host-side secret
   (`make demo` does both deterministically). In the Falco terminal you'll see CRITICAL/WARNING JSON
   alerts carrying `container`, `image`, `pid`, and the rule name. Copy the alert text into your report.

6. [ ] **Settle the prediction.** Open `data/falco-rules.yaml`. Compare the rule that fires on the
   **write to the sensitive file** (low-noise: nothing benign writes a host binary) against the rule
   that fires on **`mount(2)` inside a container** (Rule 3). Note which one you'd build the detection
   around — and why `mount` is the one that will generate your false positive.

7. [ ] **Force the false positive.** A legitimate workload mounts a volume at runtime (or a DB writes a
   path that matches a broad rule). Reproduce *one* benign event that trips a rule — e.g. a non-attack
   `mount` from an allowed process, or a benign write under a data dir matched too broadly. Capture the
   spurious alert.

8. [ ] **Tune it out.** Edit the rule (add an `exception`, or tighten the `condition` — e.g. exclude the
   known image/process/path for the benign case) so it **no longer fires on the benign event but still
   fires on the escape.** Re-run both the benign action and `make demo` and show the alert flips: silent
   on benign, CRITICAL on the attack. Save the result as `falco-rules-tuned.yaml`.

## Success criteria — you're done when
- [ ] You reproduced **CVE-2019-5736**: a payload you control executed on the host as root, originating
  from inside the container (real exploit, not a description).
- [ ] You can state the escape in the module's terms: the **shared host resource** abused, and why
  namespaces/caps didn't stop it.
- [ ] You have a Falco alert (JSON) for the escape behavior showing container, image, pid, and rule.
- [ ] You produced **one** benign false positive and then **tuned it out** — your `falco-rules-tuned.yaml`
  is silent on the benign event and still CRITICAL on the escape, demonstrated by re-running both.

## Deliverables
- `escape-report.md` — the CVE-2019-5736 reproduction (steps, commands, the host-root proof), the
  shared-resource explanation, and the Falco alert text.
- `falco-rules-tuned.yaml` — the tuned rule with your `exception`/tightened `condition`, plus a one-line
  comment per change saying which false positive it removes and why it still catches the attack.

Commit these two. Container/runtime state, the overwritten `runc`, host artifacts, and any captured
secrets stay out of the commit.

## Automate & own it
**Required — the guardrail is the tuned detection itself.** Your judgment ("`mount` is noisy; the
write-to-host-binary is the sharp signal; here is the one benign case to except") is encoded in
`falco-rules-tuned.yaml` as **detection-as-code** — a rule that *fails the bad state and passes the
fix*: it fires on the escape and stays silent on the benign workload. Prove the flip in CI-style: a
small script (or `make demo`) that runs the benign action **and** the escape and asserts the tuned rule
alerted on exactly one. Have a model draft rule variants and the `exception`; you read every line and
confirm each variant still fires on the real escape before keeping it — a rule tuned until it's silent
on *everything* is worse than no rule. (Optional: also ship `audit-privileged.sh` — `docker inspect`
across running containers flagging `Privileged: true`, `/dev` mounts, or `docker.sock` mounts — the
prevention companion to the detection.)

## AI acceleration
Feed the escape's Falco alert JSON to a model and ask it to reconstruct the kill chain: technique, ATT&CK
ID, likely next move. It writes a solid triage narrative — validate it against the actual rule
`condition` and the [T1611](https://attack.mitre.org/techniques/T1611/) card. Then paste your tuned rule
and ask it to find an attack variant that now sneaks past your `exception`. If it finds one, your
exception is too broad — tighten it. That adversarial loop is the whole skill.

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
