# LastPass Breach — The Home-Computer / Third-Party Media Software Vector
**Document type:** Public post-mortem detail | **Source:** LastPass second-incident write-up

## The unusual entry point of stage 2
LastPass's detailed write-up of the second incident describes a notable attack vector: the threat
actor targeted **one of only four DevOps engineers** who had access to the decryption keys needed to
access the cloud storage service. The attacker compromised that engineer's **personal/home
computer**.

## How the home computer was compromised
According to LastPass's account, the attacker **exploited a vulnerable third-party media-server
software package** running on the DevOps engineer's home computer. Exploiting that software enabled
remote code execution, which let the attacker implant a **keylogger**.

## From keylogger to corporate vault
With the keylogger in place, the attacker captured the engineer's **master password** as it was
entered — after the engineer authenticated with MFA — and thereby gained access to the engineer's
**corporate LastPass vault**. That vault contained the credentials and keys that ultimately unlocked
the cloud backup storage described in document 03.

## Why this vector matters
- It crossed the **work/home boundary**: a personal machine, outside corporate endpoint controls,
  became the foothold into highly privileged corporate access.
- It shows the limit of MFA alone: MFA was satisfied, but a keylogger on a trusted endpoint captured
  the master password directly.
- It explains why only a **small number of engineers** held the keys — and why compromising **one**
  of them was sufficient.

## Key facts
- Target: a **DevOps engineer** with access to storage decryption keys (one of four).
- Vector: **vulnerable third-party media-server software on the engineer's home computer** → RCE →
  **keylogger**.
- Result: captured **master password** → access to the engineer's **corporate vault** → storage keys.

## Source
- LastPass, "Notice of Recent Security Incident": https://blog.lastpass.com/posts/notice-of-recent-security-incident
