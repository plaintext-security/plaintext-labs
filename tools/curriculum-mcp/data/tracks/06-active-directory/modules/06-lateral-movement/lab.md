# Lab 06 — Lateral Movement

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/06-lateral-movement
make up      # start DC + two workstation containers + attacker
make demo    # enumerate hosts, check SMB signing, lateral movement demo
make shell   # attacker shell
make down
```

The environment provides:
- `samba-dc` (10.10.0.10) — Meridian DC
- `ws-fin-01` (10.10.0.101) — Finance workstation running a minimal SMB service
- `ws-it-01` (10.10.0.102) — IT workstation running a minimal SMB service
- `attacker` (10.10.0.20) — Debian container with `netexec`, impacket

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Scenario

You now have credentials for `jsmith` (Finance) and have obtained `tallen`'s NT hash from module 04. Your goal: map the live hosts on the 10.10.0.0/24 subnet, identify which hosts have SMB signing disabled, and achieve code execution on two different hosts using three different impacket techniques — noting the different artefact profile of each.

## Do

1. [ ] **Enumerate the subnet.** Sweep the `10.10.0.0/24` range for live SMB hosts and record, per host: hostname, OS, domain, and SMB signing status. Which hosts require signing and which don't?

2. [ ] **Authenticate and enumerate with PTH.** Replay the captured NT hash across every host. Which hosts report local-admin access for that credential, and how does the tool signal it?

3. [ ] **psexec lateral movement.** Get a shell on a Finance workstation by passing the hash. Confirm your privilege level. (What account do you land as, and why?)

4. [ ] **smbexec lateral movement.** Get execution on an IT workstation the same way but via smbexec. Compare the shell quality to psexec.

5. [ ] **wmiexec lateral movement.** Get execution on a host via wmiexec. How does its output behaviour differ from psexec/smbexec, and what does that tell you about how it returns command results?

6. [ ] **Compare artefact profiles.** For each technique, write down:
   - What Windows Event IDs are generated on the target?
   - Is a file written to disk on the target?
   - Is a service created on the target?
   - Which technique is "quietest" if a defender is watching for service creation (Event 7045)?

7. [ ] **SMB signing impact.** Identify a host with SMB signing required. Try passing-the-hash to it. Does it succeed? What error do you see if signing is enforced but you're not signing?

## Success criteria — you're done when

- [ ] You have identified all live hosts and their SMB signing status via netexec.
- [ ] You have executed code on two hosts using at least two different impacket techniques.
- [ ] You have documented the event ID profile for each technique.
- [ ] You can explain why SMB signing prevents NTLM relay but not PTH.

## Deliverables

`lateral-movement-report.md` — the host enumeration results, the credentials used for each hop (hash, not plaintext — never commit credentials), the technique used, the event IDs generated, and a table comparing the artefact profile of psexec vs. smbexec vs. wmiexec. Commit it.

## Automate & own it

**Required.** Write `sweep.sh` — a netexec wrapper that: takes a CIDR range and credential (username + hash), enumerates live hosts, filters for hosts where signing is False, and for each host runs a command (`whoami`) via wmiexec. Have a model draft it; you add error handling for unreachable hosts and ensure the output is clean and parseable. This simulates the lateral movement sweep an attacker runs to map their access quickly. Commit it.

## AI acceleration

Ask a model to write the Sigma rules that would detect each of the three lateral movement techniques (psexec, smbexec, wmiexec) based on the event IDs you documented. Each rule should reference the specific event ID, the key field, and the condition. You'll tune these in module 09 — for now, validate that the logic is correct against your event notes.

## Connects forward

The lateral movement techniques documented here are the basis for the detection Sigma rules in module 09. The network segmentation recommendations (which hosts should not have SMB admin access between them) feed into the hardening design in module 10 and the tiered admin model in module 11.

## Marketable proof

> "I enumerate Windows networks for lateral movement opportunities — SMB signing gaps, exposed admin shares — execute code via three different techniques with distinct event artefact profiles, and produce the detection guidance that maps each to its Windows event log signature."

## Stretch

- Research **WinRM** as a lateral movement protocol (impacket `wmiexec.py` with the `-silentcommand` flag, or just use `evil-winrm`). What event IDs does it generate? What makes it stealthier or noisier than SMB-based techniques?
- Test what happens when you attempt NTLM relay (using `responder` + `ntlmrelayx.py`) between two hosts where signing is disabled. Understand why this is a separate risk from PTH.
