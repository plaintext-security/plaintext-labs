# Module 10 — Workload Identity & mTLS (SPIFFE/SPIRE)

*Type 7 · Build-&-Operate — stand up a SPIFFE/SPIRE trust domain, issue each workload a short-lived SVID, and establish identity-keyed mTLS; the deliverable is the running, reviewed system and its verified deny — an unregistered workload gets no identity — not an essay. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *zero trust for humans is identity-aware proxies; zero trust between services is a cryptographic identity every workload can prove — and rotate — on its own.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

The rest of this track makes *human* access zero-trust: an identity-aware proxy checks a user's token
on every request, a mesh checks a device's key, a policy engine decides. But most traffic in a modern
system isn't a human at a browser — it's the checkout service calling the ledger, a batch job reading
the database, one pod talking to another. Ask how those services authenticate to each other and the
honest answer in most shops is *they don't*: a shared API key in an env var, a long-lived service-account
token, or — most often — nothing, because they're "on the same network." That is the exact flat-trust
assumption zero trust exists to kill, and Module 07's network segmentation only narrows it: a label-based
allow rule says *this pod may connect to that pod*, but it never makes the caller **prove who it is**. A
stolen pod identity, a mislabeled workload, or anything that lands inside the allowed segment is trusted.
Workload identity closes that gap — it is the application/workload pillar of NIST SP 800-207, and it's
the part of zero trust the proxy modules don't reach.

## Objective

Stand up a SPIFFE/SPIRE trust domain, register two workloads, and have each **fetch its own
short-lived X.509 SVID at runtime** and use it to establish **mutual TLS** — so the client proves its
identity to the server *and* the server to the client, with no shared secret anywhere. Then **prove the
boundary**: a workload with no registration entry is refused an identity by the agent and cannot complete
the mTLS handshake, demonstrating that identity — not network position — is what grants access.

## The core idea

The move to internalize is that **a workload's identity should be a credential it can prove, not a
secret it holds.** SPIFFE (Secure Production Identity Framework For Everyone) gives every workload a
**SPIFFE ID** — a URI like `spiffe://corp.local/ledger` — and a **SVID** (SPIFFE Verifiable Identity
Document), which is just that ID wrapped in a short-lived X.509 certificate signed by the trust domain's
CA. When the ledger service connects to the database, it presents its SVID; the database presents its
own; each validates the other's certificate against the same trust bundle and reads the peer's SPIFFE ID
out of the cert's SAN. That's **mutual TLS keyed on identity**, and the thing that makes it zero-trust
rather than just "TLS with client certs" is *where the certificate comes from and how long it lives*: the
workload never has a long-lived key sitting in a file to be stolen. It fetches a fresh SVID at startup and
the platform rotates it automatically every few minutes.

SPIRE (the SPIFFE Runtime Environment) is the implementation that issues those SVIDs, and its central
problem is the one that trips up every "just give each service a cert" scheme: **how do you hand a brand-new
workload its first credential without already trusting it?** SPIRE solves it with two layers of
**attestation**. A SPIRE **agent** runs on each node and first proves the *node's* identity to the SPIRE
**server** (node attestation — a cloud instance-identity document, a Kubernetes projected token, or a join
token in a lab). Then, when a local workload calls the agent's Workload API asking for its SVID, the agent
**attests the workload** by inspecting properties it can observe but the workload cannot forge from the
outside — its Unix UID, its Kubernetes service account, its Docker labels or image. The agent matches those
*selectors* against the **registration entries** the operator created (`spiffe://corp.local/ledger` is
issued only to a process whose selectors say `docker:label:com.corp.svc:ledger`) and hands back exactly
the right SVID. No bootstrap secret is ever shipped to the workload — its identity is *derived from what it
demonstrably is*, which is why a workload with no matching entry simply gets nothing.

That reframes the security control from "protect the key" to "**get the attestation right**," and it's
where the judgment lives. Selectors that are too loose — attesting on a Unix UID that every container
shares, or a label any deployment can set — let the wrong workload claim an identity, the workload-identity
equivalent of a wildcard IAM policy. The discipline is to pin each entry to selectors that are genuinely
hard to spoof in your environment (an image digest, a Kubernetes service account bound to a namespace) and
to keep SVID TTLs short so a leaked credential expires in minutes, not months. And note the boundary of what
this gives you: SPIFFE proves *which workload* is calling and encrypts the channel — it is **authentication**,
not **authorization**. Deciding whether `spiffe://corp.local/web` may call `spiffe://corp.local/ledger`
is a policy question, which is exactly the handoff to Module 08: the proxy/mesh authenticates with the SVID,
and OPA evaluates the SPIFFE ID against the access policy. Identity here, decision there.

The practitioner translation is the cleanest way to hold all of this: **a SVID is to a service what a
short-lived OIDC token is to a user.** Module 02 gave a human a signed, short-lived JWT that travels with
the request and is re-evaluated at each hop; SPIFFE gives a *service* a signed, short-lived certificate that
does the same. Same zero-trust principle — verifiable identity per request, no standing trust, automatic
expiry — applied one layer down, to the east-west traffic that the proxy and the segmentation policy never
actually authenticate.

## Learn (~3.5 hrs)

**SPIFFE/SPIRE concepts (~1.5 hrs)**
- [SPIFFE — Concepts (SPIFFE ID, SVID, trust domain, Workload API)](https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/) — the authoritative model; read "SPIFFE ID," "SVID," and "Workload API." This is the vocabulary the lab makes concrete.
- [SPIRE — Concepts: Agent, Server, Attestation](https://spiffe.io/docs/latest/spire-about/spire-concepts/) — how SPIRE issues identities: node attestation, workload attestation, selectors, and registration entries. Read the attestation sections carefully — that two-layer model is the heart of the lab.

**Why workload identity & mTLS (~1 hr)**
- [SPIFFE — Use cases / "What is SPIFFE and why is it important?"](https://spiffe.io/docs/latest/spiffe-about/overview/) — the problem statement: why shared secrets and network-location trust fail for service-to-service auth, and what an identity-based model replaces them with.
- [Cloudflare — A primer on mutual TLS (mTLS)](https://www.cloudflare.com/learning/access-management/what-is-mutual-tls/) — a short, vendor-neutral explainer of how mutual TLS authenticates *both* sides of a connection. Read this if "both ends present a cert" isn't already second nature.

**Hands-on grounding (~1 hr)**
- [SPIRE — Quickstart (the docker-compose 5-step)](https://spiffe.io/docs/latest/try/getting-started-linux-macos-x/) — the official walkthrough the lab mirrors: start the server, generate a join token, start the agent, create a registration entry, fetch an SVID. Read it once before `make up` so you recognize each step.
- [go-spiffe — X.509-SVID example (mTLS between two workloads)](https://github.com/spiffe/go-spiffe/tree/main/v2/examples/spiffe-tls) — the canonical "two services do mTLS off the Workload API" example; skim the client and server to see how a workload fetches its SVID and validates the peer's SPIFFE ID. Reference for the *Automate & own it* build.

## Key concepts
- SPIFFE ID + SVID: a workload's identity is a URI (`spiffe://trust-domain/path`) carried in a short-lived X.509 cert, not a secret it stores.
- Mutual TLS on identity: both ends present an SVID and validate the peer's SPIFFE ID — no shared key anywhere.
- Two-layer attestation: the agent proves the *node* to the server, then attests each *workload* by unforgeable selectors (UID, k8s SA, docker label/digest).
- Registration entries map selectors → SPIFFE ID — the workload-identity equivalent of an IAM policy; loose selectors are the wildcard-grant failure mode.
- Short TTL + auto-rotation: SVIDs expire in minutes and the agent re-issues them, so a leaked credential is worthless fast — and there's no long-lived key to leak.
- Authentication, not authorization: SPIFFE proves *who* is calling; OPA (Module 08) decides *whether* that caller is allowed — identity here, policy there.
- A SVID is to a service what a short-lived OIDC token (Module 02) is to a user — the same per-request, no-standing-trust model, one layer down.

## AI acceleration

A model is genuinely useful for the *plumbing* here: drafting the SPIRE server/agent config, the
`spire-server entry create` commands, and the go-spiffe mTLS client/server boilerplate — all of which it
writes fluently. Where you own the judgment is **the selectors**, because that is the actual security
decision and the model has no way to know your environment. Ask it to generate a registration entry and it
will happily pick a selector that *works* — `unix:uid:0`, a label any pod can set — without seeing that the
selector is forgeable and would hand your workload's identity to anything that asks. Review every selector
against "could a different workload satisfy this?", prefer image digests / bound service accounts over
shared UIDs and free-form labels, and **prove it** the way the lab does: confirm an unregistered workload is
refused an SVID and the mTLS handshake fails. AI drafts the entry; you make it unforgeable and verify the
deny.
