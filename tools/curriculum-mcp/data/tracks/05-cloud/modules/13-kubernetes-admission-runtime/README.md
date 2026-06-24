# Module 13 — Kubernetes: Admission & Runtime

*Variant D · breach-driven, build-first ("encode the bouncer, then watch the room"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *a worm that spread through doors nobody guarded; admission control is the guard you write once and it holds for every pod after.*

<!-- module-meta -->
**Difficulty:** Advanced &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 12 — RBAC & NetworkPolicy](../12-kubernetes-rbac-network/README.md)

{ .module-meta }

## The case

In October 2019, Palo Alto's Unit 42 published
[Graboid](https://unit42.paloaltonetworks.com/graboid-first-ever-cryptojacking-worm-found-in-images-on-docker-hub/),
the first known cryptojacking *worm* to spread through containers. It needed no exploit and no
zero-day. It found **Docker Engine daemons exposed to the internet with no authentication**, used the
open API to **pull a malicious image from Docker Hub and run it**, and from each newly infected host
repeated the move against the next. It mined Monero on the side. Unit 42 watched it reach roughly
**2,000 unsecured hosts in about an hour.** The same shape — an unauthenticated container/orchestration
endpoint that will happily *admit and run whatever it's handed* — is what a year earlier let attackers
deploy cryptominers through Tesla's open Kubernetes dashboard, and it is the open door this module
closes.

There was nothing clever in Graboid. The entire breach is that **a container ran that should never have
been allowed to start.** Nobody decided to run it; nothing stopped it from running. So this module turns
on a single operational question:

> **At the moment a pod spec hits the API server — before any container starts — what should refuse to
> admit it, and what watches for the bad behavior of the things that got admitted anyway?**

## Your job

By the end of this module you'll have built the two layers that Graboid walked straight through.
First, **admission control as code**: write Kyverno `ClusterPolicy` documents that *deny at the door*
the pod specs that should never run in production — privileged containers, host mounts, host
namespaces, root users — and prove they block a non-compliant pod while admitting a compliant one.
Then, **runtime detection** for what slips past: deploy Falco and write a rule that fires on the
behavior a policy can't see — an `exec` into a running pod, a process spawning from `/tmp`. The
deliverable is the prevention-as-code policy set plus one runtime rule: judgment encoded so the bad
state can't recur, and a camera for the gaps where it still might.

## Call it before you build

This module leads with the build, not a quiz — but commit to one call first, because the wrong instinct
here is *load-bearing.* Below are four pod specs a developer might submit. Mark the ones that **should
never be admitted to a production cluster**, and for each, name the single field that damns it.

> **A.** `securityContext: { privileged: true }`
> **B.** a `volumes` entry with `hostPath: { path: "/" }` mounted into the container
> **C.** `hostNetwork: true` and `hostPID: true` on the pod
> **D.** no `securityContext` at all (so the container runs as **root**, UID 0, by default)

The instructive part isn't *which* are dangerous — it's seeing that **the answer is all four**, and
that each is a different way of erasing the boundary between the container and the node it runs on.
`privileged: true` hands the container the host's devices and capabilities; `hostPath: /` mounts the
node's entire filesystem (read `/etc/shadow`, write a cron job, you own the box); `hostNetwork`/`hostPID`
drop the container into the node's network and process namespace; and **the most common one — `D`,
nothing set at all** — runs your workload as root, which is the default and the reason "the default is
not secure" is as true in Kubernetes as it was in S3. Graboid didn't need any of A–C; it just needed a
door that would run *anything.* Each of these is a Kyverno policy you'll write, and the point of calling
it first is to feel that **"obviously dangerous" and "actually blocked" are two different states** —
prevention only exists if someone *encoded* the verdict. That encoding is the module.

## The model: the bouncer and the camera

Hold those four against this. There are two distinct controls and you need both, because each is blind
to exactly what the other catches.

**Admission control is the bouncer at the door.** The Kubernetes API server runs a webhook chain on
every `CREATE`/`UPDATE`: before a pod is persisted or scheduled, registered admission controllers get
to **validate** (allow/deny) or **mutate** (default fields) the manifest. Kyverno registers as both. A
`ClusterPolicy` is declarative YAML — a pattern the manifest must match or must not match, plus an
action — that lives in git and applies with `kubectl apply`. This is **prevention, and it is cheap**:
the check runs once, against the *spec*, *before* any code executes. A ten-line policy the security team
owns replaces "please remember to set `runAsNonRoot`" in every code review forever. The operational
catch worth memorizing: roll out in **`Audit`** first (log violations, don't block), watch the Policy
Reports for how many existing workloads would fail, remediate, *then* flip to **`Enforce`**. Jumping
straight to `Enforce` on a live cluster is how a CronJob can't start at 2 AM.

**Runtime detection is the camera inside.** The bouncer reads the *spec*; it cannot see what an admitted
container *does*. A pod that passed every policy can still be `exec`'d into, can still spawn a shell from
`/tmp`, can still read a credential file — and an image that was already running before you wrote the
policy never went through the door at all. Falco is the camera: a DaemonSet that watches syscalls on
each node and fires on behavior, with Kubernetes context attached. The honest framing — and the whole
reason this is one module, not two — is that **prevention without detection is blind to its own gaps.**
Admission tells you what *could* run; it cannot tell you that the one thing that slipped past is, right
now, reading `/etc/shadow`. You write the policy to make the door narrow, and the Falco rule to watch
the gap the door can't close.

## Learn (~3 hrs)

*Build-first module: the spine is the lab, so Learn is the reference you reach for *while* writing
policy, not a lecture to read first. Skim, then write — return when a `deny` condition won't behave.*

**Admission control — the mechanism (~45 min)**
- [Kubernetes docs — Admission Controllers Reference](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/) (~20 min) — read the intro and "Why do I need admission controllers?"; this is the webhook chain Kyverno plugs into, stated by the source.
- [Kubernetes docs — Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) (~25 min) — the *built-in* controller and the `baseline`/`restricted` profiles. Read this to see exactly which of your four pod specs the standard profiles already forbid — your Kyverno policies are the same verdicts, made explicit and extensible.

**Kyverno — the tool you're writing in (~1 hr)**
- [Kyverno docs — Writing Policies / Validate Rules](https://kyverno.io/docs/policy-types/cluster-policy/validate/) (~30 min) — the primary reference for `validate`, `deny`, patterns, and `validationFailureAction`. This is the vocabulary for every policy in the lab.
- [Kyverno policy library — Pod Security](https://kyverno.io/policies/?policytypes=Pod+Security+Standards+(Baseline)) (~30 min) — browsable community policies. Read "Disallow Privileged Containers," "Disallow Host Path," and "Require Run As Non-Root": they are the worked answers to your four predictions. Read them to learn the *shape*, then write your own — don't copy-paste blind.

**Runtime — the camera (~45 min)**
- [Falco docs — Kubernetes deployment](https://falco.org/docs/setup/kubernetes/) (~20 min) — the DaemonSet model and how alerts carry Kubernetes metadata.
- [Falco docs — Rules / writing a custom rule](https://falco.org/docs/concepts/rules/) (~25 min) — `condition`, `output`, `priority`, and the default `Terminal shell in container` / `Read sensitive file` rules. You'll tune one of these for the runtime gap.

## Key concepts
- Admission control runs on the spec *before* the pod starts (prevention, cheap); runtime detection watches behavior *after* it starts (detection, for the gap) — you need both
- The four "never admit" patterns each erase the container↔node boundary: `privileged`, `hostPath: /`, `hostNetwork`/`hostPID`, and the silent default — **runAsRoot**
- Kyverno `ClusterPolicy`: `validate`/`deny` vs. `mutate`; `Audit` → understand → remediate → `Enforce` is the only safe rollout order
- Policy-as-code is *judgment made un-recurrable*: the verdict "this should never run" lives in git, applies with `kubectl apply`, and blocks every future pod, not just this one
- Falco fires on behavior (exec into a pod, exec from `/tmp`, sensitive-file read) that the manifest never reveals
- MITRE ATT&CK: T1610 (Deploy Container), T1611 (Escape to Host), T1525 (Implant Internal Image) — the Graboid pattern

## AI acceleration
Hand a model a pod spec and ask which of your policies would deny it and why — it's strong at reading
`securityContext` and matching it to the "never admit" patterns, and a fine first-draft author of a
Kyverno `ClusterPolicy`. But it sees the YAML, not your cluster: it can't tell you whether that policy is
in `Audit` or `Enforce` mode (`kubectl get clusterpolicy` does), and it will confidently write a `deny`
condition whose path is subtly wrong so the policy *admits the bad pod while looking correct*. That
silent failure is the danger — a policy that doesn't block is worse than none, because you trust it. So
**AI drafts the policy; you prove it** by applying the bad pod and watching the API server reject it for
the *right* field. Same for the Falco rule: the model drafts the `condition`, you confirm it fires on the
exec and not on every benign process. You direct it; you own the door.
