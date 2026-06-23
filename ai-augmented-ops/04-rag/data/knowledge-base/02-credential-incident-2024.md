# LastPass Breach — Stage 1: Development Environment Compromise (August 2022)
**Document type:** Public post-mortem detail | **Source:** LastPass disclosure (Aug 25, 2022)

## Summary
In August 2022, an unauthorized party gained access to portions of the LastPass **development
environment** through a **single compromised developer account**. The attacker took portions of
source code and some proprietary LastPass technical information.

## Initial access vector
The entry point was **one developer's account**. The attacker impersonated that developer once the
account was authenticated to the development environment. LastPass's investigation found the activity
was confined to the development environment.

## What was and was not accessed
- **Accessed:** portions of source code and proprietary technical information.
- **Not accessed (stage 1):** no customer data, and no encrypted password vaults. The development
  environment was physically separated from the production environment and contained no customer
  data.

## Why stage 1 mattered later
LastPass later confirmed that the information stolen in this first incident was **reused by the same
threat actor** to carry out the second, far more damaging incident. The source code and technical
details gave the attacker the knowledge needed to target a specific employee and the cloud backup
infrastructure. Stage 1 looked contained; it was actually reconnaissance for stage 2.

## Key facts
- Single compromised **developer** account.
- **Development** environment only — separated from production.
- Source code + technical information taken; **no** customer/vault data in this stage.
- Disclosed **August 25, 2022**.

## Source
- LastPass, "Notice of Recent Security Incident": https://blog.lastpass.com/posts/notice-of-recent-security-incident
