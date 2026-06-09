# ZTNA Architecture Patterns — Structured Comparison

*Seed material for Lab 04. Fictional scenario for Meridian Financial.*

---

## Pattern 1: VPN (Baseline)

### How traffic flows

User device → VPN client → VPN concentrator (TLS tunnel) → Virtual IP assigned → Direct access to
any host in the corporate /20 network. The VPN authenticates the session once at tunnel
establishment; all subsequent traffic is trusted.

```
[User device]
      |
      | (TLS / IPSec tunnel)
      ↓
[VPN concentrator]  ← single choke point; authenticates once
      |
      | (Virtual IP granted on corporate /20)
      ↓
[Any server in 10.10.0.0/20]  ← no per-request evaluation
```

### Trust model

- **Trust anchor:** Network perimeter (VPN concentrator)
- **When trust is evaluated:** Once, at tunnel establishment
- **What is trusted:** Any IP in the virtual subnet = trusted device
- **Identity signal:** Username + password + MFA (at tunnel time only)
- **Device signal:** None (IP in the tunnel range = "corporate device")

### What's needed on the device

VPN client (Cisco AnyConnect, GlobalProtect, etc.). No device certificate required by default.

### Blast radius if compromised

If a credential is stolen and a VPN session is established: full access to all 4096 IPs in the
/20 for the session duration. No application-level segmentation. Lateral movement is unconstrained
within the network segment. Session persists indefinitely with split-tunnel AnyConnect (no idle
timeout by default at Meridian).

### Strengths

- Supports arbitrary TCP/UDP protocols
- Mature, well-understood by operations teams
- Works with any application without modification
- Single authentication event reduces user friction

### Weaknesses

- Network-level trust = maximum blast radius on credential compromise
- No per-application access policy
- No continuous re-evaluation after initial auth
- Cannot enforce device posture without additional tooling (e.g. NAC integration)
- Scales poorly for contractor BYOD (same access as corporate devices)

---

## Pattern 2: Reverse Proxy (Pomerium / BeyondCorp-style)

### How traffic flows

User device → Pomerium authenticate service (OIDC) → Pomerium authorize service (policy check) →
Pomerium proxy → Application upstream. The application is **not exposed** on the network; only the
proxy's listener is reachable. Each request is authenticated and authorized.

```
[User device]
      |
      | (HTTPS — all traffic)
      ↓
[Pomerium Authenticate]  ← OIDC redirect to IdP (Okta/Keycloak)
      |
      ↓
[Pomerium Authorize]     ← evaluates policy: identity + (optional) device posture
      |
      ↓
[Pomerium Proxy]         ← forwards authenticated requests to upstream
      |
      ↓
[Application upstream]   ← only reachable through proxy; not network-accessible
```

### Trust model

- **Trust anchor:** Identity (JWT from IdP) + optional device posture signal
- **When trust is evaluated:** Per request (every HTTP request is evaluated against the policy)
- **What is trusted:** The signed JWT claim (sub, groups, exp) + policy match
- **Identity signal:** OIDC token from Okta/Keycloak; re-validated per session
- **Device signal:** Optional; Pomerium can check a device certificate or a Cloudflare/Tailscale
  device posture signal via a custom claim in the JWT

### What's needed on the device

Browser (for web applications). No VPN client. For mTLS device identity: a client certificate.
For posture-aware access: Cloudflare WARP or a Tailscale node with posture integration.

### Blast radius if compromised

If a user's JWT is stolen: access to only the applications that user is authorized to reach via
proxy policy (not the whole network). If the Pomerium process itself is compromised: access to all
upstream applications behind it. Upstream applications must not be reachable by any other path.

### Strengths

- Per-request access decisions (closest to BeyondCorp original design)
- No lateral movement: application is not network-accessible except through the proxy
- OIDC-native; integrates directly with Okta/Keycloak/Entra ID
- Deployable without replacing applications (transparent to the app)
- Open-source self-hosted option available

### Weaknesses

- HTTP/S only (and gRPC); cannot proxy arbitrary TCP/UDP (SSH, RDP, database protocols)
- Requires DNS and TLS certificate management per application
- Operational complexity scales with number of applications
- Upstream bypass: if an application is also reachable directly (e.g. firewalled but not locked
  to proxy source IP only), the proxy provides no protection

---

## Pattern 3: Network Mesh (Tailscale / headscale / Netbird)

### How traffic flows

Device enrolls with the coordination server (headscale); receives a WireGuard keypair and a mesh
IP. The coordination server distributes other nodes' public keys per the ACL policy. Traffic flows
peer-to-peer over WireGuard tunnels; the coordination server is not in the data path.

```
[Device A]                    [Device B / Service]
    |                               |
    | (WireGuard tunnel — encrypted)
    ↔ ← ← ← ← ← ← ← ← ← ← ← ← → ↔
    |                               |
    |← [headscale coordination] →  |
       (distributes public keys;
        enforces ACL policy;
        NOT in data path)
```

### Trust model

- **Trust anchor:** WireGuard public key registered with coordination server
- **When trust is evaluated:** At mesh enrollment (device identity) + per ACL policy (connection)
- **What is trusted:** A device with a registered keypair that matches the ACL tags for the target
- **Identity signal:** Device keypair (hardware-bound in production with TPM); user identity
  optional via OIDC SSO via Tailscale's user auth
- **Device signal:** Tags assigned at enrollment; posture signals via MDM/EDR integration in
  Tailscale commercial (not headscale OSS)

### What's needed on the device

Tailscale or headscale client (WireGuard-based; available for all major OS). In headscale: no SaaS
dependency; self-hosted coordination server. In Tailscale commercial: WARP-style agent.

### Blast radius if compromised

If a device's private key is compromised: access to whatever resources that device's ACL tags
allow — typically scoped to specific services. The default-deny ACL model limits lateral movement
to the tagged service set. If the coordination server (headscale) is compromised: attacker could
distribute malicious public keys and hijack routing.

### Strengths

- Supports arbitrary TCP/UDP protocols (SSH, RDP, databases, proprietary protocols)
- Cryptographic device identity (vs. IP-based)
- ACL model naturally implements micro-segmentation
- No central data-path chokepoint (peer-to-peer)
- Open-source self-hosted option (headscale) avoids vendor dependency

### Weaknesses

- Device posture integration requires additional tooling (MDM/EDR integration; not in headscale OSS)
- ACL management complexity grows with number of tags and services
- No threat inspection of traffic content (encrypted peer-to-peer; no DPI)
- Requires client installation on every device (harder for BYOD)
- Not SASE: no SaaS visibility, no DNS filtering, no browser isolation

---

## Pattern 4: Cloud Edge (Cloudflare Zero Trust / Zscaler / Netskope)

### How traffic flows

Device runs the vendor agent (Cloudflare WARP). All traffic (or selected traffic per split-tunnel
policy) routes to the nearest vendor PoP. At the PoP, identity and posture are evaluated, policies
are applied (DNS filtering, threat inspection, Zero Trust Network Access), and traffic is forwarded
to the destination — either the public internet or a private application via a Cloudflare Tunnel.

```
[Device + WARP agent]
      |
      | (WireGuard to nearest Cloudflare PoP)
      ↓
[Cloudflare Edge PoP]  ← identity check, device posture, DNS filter, threat inspect
      |
      ├─→ [Public internet / SaaS apps]  (via Cloudflare edge)
      |
      └─→ [Private app via cloudflared tunnel]
              ↑
         [cloudflared daemon on private network — outbound-only, no inbound ports]
```

### Trust model

- **Trust anchor:** Cloudflare Access policy (identity + device posture + IP risk score + tenant check)
- **When trust is evaluated:** Per session; continuous re-evaluation via the WARP agent
- **What is trusted:** Identity (Okta/Entra ID OIDC), device posture (CrowdStrike ZTA, OS version,
  disk encryption), and network context (IP reputation, geo, time-of-day)
- **Identity signal:** OIDC from enterprise IdP
- **Device signal:** CrowdStrike ZTA score, Intune compliance, OS build, disk encryption — checked
  by the WARP agent and reported to the Access policy engine

### What's needed on the device

Cloudflare WARP client. For Zero Trust tunnels: `cloudflared` daemon on the server side (outbound
only — no inbound firewall rules needed). Browser-only access available without WARP for specific
applications (useful for BYOD / contractors).

### Blast radius if compromised

If a user's identity provider credentials are stolen: Cloudflare Access evaluates posture on the
device; a stolen credential on an unregistered or low-posture device is blocked. If Cloudflare's
edge is compromised: all traffic in the data path is exposed. Vendor dependency is the primary risk.

### Strengths

- Single policy plane for SaaS, on-prem, and cloud applications
- Built-in threat inspection, DNS filtering, browser isolation
- No inbound firewall rules needed (cloudflared is outbound-only)
- Best-in-class BYOD support (browser-based access without WARP for external users)
- Globally distributed — low latency for remote users
- Integrates posture signals from CrowdStrike, Intune, and others natively

### Weaknesses

- Vendor dependency: Cloudflare is in your data path; their SLA is your SLA
- Subscription cost scales with users (free tier limited to 50 users)
- Configuration surface area is large; misconfiguration can create bypass paths
- Limited self-hosting: Cloudflare Tunnel is open-source; the Access/Gateway control plane is not
- Privacy considerations: vendor can observe all DNS and (with inspection) TLS traffic

---

## Summary comparison table

| Dimension | VPN | Reverse Proxy | Network Mesh | Cloud Edge |
|---|---|---|---|---|
| **Protocol support** | Any TCP/UDP | HTTP/S, gRPC | Any TCP/UDP | Any (with WARP) |
| **Trust evaluated** | Once (network perimeter) | Per request | Per connection (ACL) | Per session (continuous) |
| **Device posture** | None by default | Optional (cert/claim) | Tags only (headscale OSS) | Native (CrowdStrike, Intune) |
| **Blast radius (credential)** | Full network | Authorized apps only | Tagged services only | Policy-scoped |
| **Blast radius (infra)** | VPN concentrator | Proxy host | Coordination server | Cloudflare PoP |
| **BYOD support** | Poor (same network grant) | Good (browser-based) | Fair (client required) | Excellent (browser option) |
| **Operational complexity** | Low (familiar) | Medium (per-app config) | Medium (ACL management) | Low-Medium (SaaS managed) |
| **Self-hosted option** | Yes | Yes (Pomerium) | Yes (headscale) | Partial (cloudflared) |
| **SaaS visibility** | None | None | None | Yes (DNS + proxy) |
| **Audit per request** | No | Yes | ACL level | Yes |
| **Cost** | Infrastructure | Infrastructure + ops | Infrastructure + ops | Per-user subscription |
