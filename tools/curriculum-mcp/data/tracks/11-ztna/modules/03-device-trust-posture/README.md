# Module 03 — Device Trust & Posture

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *identity tells you who is asking; device posture tells you whether to believe the device they're asking from.*

## Why this matters

A stolen credential on a healthy, EDR-enrolled, fully-patched corporate laptop is a serious incident.
The same credential on an unmanaged contractor BYOD device running outdated software, with no
endpoint visibility, is potentially catastrophic — and a model that only verifies identity cannot
tell the difference. Device trust is the second pillar of ZT after identity, and it is the pillar
most organizations handle worst. Getting it right requires a reliable, tamper-resistant signal about
device posture, and a policy engine that factors that signal into every access decision.

## Objective

Deploy headscale (the self-hosted Tailscale coordination server) in Docker, register a device node,
and demonstrate that only enrolled and registered devices can reach the protected service — then map
the fictional Meridian device posture policy to the controls Tailscale ACLs and Cloudflare Access
would enforce in production.

## The core idea

The fundamental challenge of device trust is proving a device's identity in a way that is hard to
fake. The old model used VLAN membership and IP address — if the request came from the corporate
/20, the device was "trusted." IP addresses are trivially spoofed and, in any case, say nothing
about the device's actual security posture. The modern approach uses **cryptographic device
identity**: a private key generated on the device (ideally in a TPM or Secure Enclave, so it cannot
be exported), whose corresponding certificate or public key is registered with a management plane.
Tailscale/WireGuard is the clearest concrete example of this approach: each device generates a
WireGuard keypair, registers the public key with the coordination server (headscale), and all
subsequent traffic is authenticated by that keypair. A device that doesn't have the registered
private key cannot participate in the mesh — IP address doesn't help you.

WireGuard is the protocol that makes Tailscale's device mesh practical. Unlike OpenVPN or
IPSec/IKEv2, WireGuard's cryptographic model is fixed (Noise protocol framework, ChaCha20-Poly1305,
Curve25519 for key exchange) — there are no algorithm negotiation handshakes to exploit and no
legacy cipher suites to misconfigure. Every peer is identified by their 256-bit public key. The
coordination server (Tailscale or headscale) distributes public keys to peers so they can establish
direct encrypted tunnels; it is the configuration plane, not the data plane. Once keys are
exchanged, traffic flows peer-to-peer with no central chokepoint, and access control is expressed
as ACLs on the coordination server that determine which registered devices can reach which others.

Cryptographic identity is necessary but not sufficient for strong device trust. **Posture** is the
second component: even if a device's identity is genuine, its security state matters. A
legitimately enrolled corporate laptop that hasn't received OS patches in 60 days or whose EDR
agent has been disabled presents real risk. Cloudflare Access and Tailscale's ACL system both
support posture-based access decisions: Cloudflare's device posture checks query CrowdStrike's
Zero Trust Assessment score, OS version, disk encryption status, and more, and can gate access to
specific applications on passing a minimum posture threshold. Tailscale's `tagOwner` and group-based
ACLs can restrict which registered devices can reach which services, effectively segmenting "managed
corporate laptop" from "contractor BYOD" even within the same WireGuard mesh. The `data/device-
posture-policy.json` in this lab shows what such a policy looks like in structured form.

FIDO2 and passkeys deserve a specific mention here because they address a different but related
problem: proving human presence at the device during authentication, using cryptographic hardware
that is bound to the specific authenticator (a YubiKey, an Apple Secure Enclave, a Windows Hello
TPM). A FIDO2 assertion proves that the right credential is present on the right device, with the
private key never leaving the hardware boundary. This is complementary to WireGuard-style device
identity: WireGuard proves the device, FIDO2 proves the user on that device. Together they
implement the "verify both the user and the device" principle from NIST 800-207 Tenet 3. Since
FIDO2 hardware is physical, the lab covers it in prose; the interactive demo is at WebAuthn.io.

## Learn (~4 hrs)

**WireGuard and mesh networking (~1.5 hrs)**
- [WireGuard conceptual overview](https://www.wireguard.com/papers/wireguard.pdf) — the original academic paper by Donenfeld; read sections 1–3 (introduction, cryptographic model, protocol). Dense but short; it explains why WireGuard's fixed crypto model is a security advantage over IPSec.
- [Tailscale — How Tailscale Works](https://tailscale.com/blog/how-tailscale-works) — a clear, concrete explanation of the coordination server / data plane separation, NAT traversal, and the ACL model. Read this to understand what headscale is doing.

**headscale (self-hosted coordination server) (~30 min)**
- [headscale documentation](https://headscale.net/stable/) — the self-hosted Tailscale coordination server used in the lab. Read the "Getting started" and "ACLs" sections; the rest is operational reference.

**Device posture and ZT (~1 hr)**
- [Cloudflare Zero Trust — Device Posture](https://developers.cloudflare.com/cloudflare-one/reusable-components/posture-checks/) — Cloudflare's documentation on posture checks: how they query CrowdStrike, Intune, SentinelOne, and OS-level signals. This is what "posture-gated application access" looks like in a production product.
- [Tailscale ACL syntax reference](https://tailscale.com/docs/features/access-control/acls) — how to express "only devices tagged corp-managed can reach service X" in Tailscale's HuJSON policy. Directly applicable to the lab scenario.

**FIDO2 and passkeys (~1 hr)**
- [WebAuthn.io](https://webauthn.io/) — browser-based FIDO2/WebAuthn demo; register and authenticate without hardware, in your browser. Run through it to understand the challenge-response flow before reading the spec.
- [FIDO Alliance — How FIDO Authentication Works](https://fidoalliance.org/passkeys/) — the foundational explainer. Read to understand authenticator binding, user verification, and why the private key never leaves the device.

## Key concepts

- Cryptographic device identity: WireGuard public key as device identity (vs. IP-based trust)
- Coordination server vs. data plane: headscale distributes keys; WireGuard tunnels carry traffic
- Device posture: patch level, EDR enrollment, disk encryption — factors in the access decision
- Posture-gated access: minimum posture score required before token is issued or route allowed
- FIDO2/passkeys: user presence + hardware-bound credential as the human-layer complement to device identity
- Blast radius of a compromised device with vs. without device posture controls

## AI acceleration

Ask a model to generate headscale ACL policies and Tailscale HuJSON configs from a description of
your access requirements — it handles the syntax well. **Your review job** is to verify the policy
actually does what you intend: a policy with an implicit default-allow is the opposite of ZT,
regardless of how syntactically correct it looks. Test by confirming that an *unregistered* device
or an *untagged* device cannot reach the service, not just that a registered one can.
