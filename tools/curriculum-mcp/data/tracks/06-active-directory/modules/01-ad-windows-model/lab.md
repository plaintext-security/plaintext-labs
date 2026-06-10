# Lab 01 — Map the Meridian Domain

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This lab uses no containers — it is a structured analysis exercise against a pre-built domain description.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/01-ad-windows-model
make demo   # prints the Meridian domain structure
```

The `data/` directory contains `meridian-domain.md` — a detailed description of the fictional Meridian Financial AD structure: domains, OUs, groups, service accounts, trusts, and the key security design decisions (good and bad).

> Everything in this lab is against data you own. No external targets, no authorization needed.

## Scenario

You've just joined Meridian Financial's security team. Before you can find attack paths or write detections, you need an accurate mental map of the domain. Your job: read the Meridian domain spec and answer the questions below — in writing — as if you're briefing a new red teamer who has never seen the environment.

## Do

1. [ ] Run `make demo` to print the Meridian domain structure. Read `data/meridian-domain.md` in full.

2. [ ] **Map the trust boundary.** Draw (by hand or in a Markdown table) the Meridian forest/domain topology. Identify: what is the single forest? What domains exist? Are there any external trusts? Which is the forest root?

3. [ ] **Trace a Kerberos authentication.** Pick the scenario: *jsmith* (Finance OU) opens a file share on `\\fs01.meridian.local`. Write down, step by step: what ticket does jsmith's workstation request first? From whom? What does the KDC verify before issuing it? What ticket is requested next? What does `fs01` check to decide whether jsmith can read the share? Map each step to the field in the Kerberos exchange.

4. [ ] **Identify the high-value groups.** From the domain spec: list every group whose membership gives domain-wide elevated access. For each, note what access it grants and whether it has any service accounts in it (a common misconfiguration).

5. [ ] **Spot the GPO gaps.** The domain spec lists which GPOs apply to which OUs. Identify at least two OUs where a security-relevant GPO is missing or has a weaker setting than best practice. Explain what an attacker gains from each gap.

6. [ ] **Identify the NTLM fallback surfaces.** List the services in the spec that accept NTLM authentication. Why is each one a risk even if Kerberos is the default?

## Success criteria — you're done when

- [ ] You can explain the Meridian Kerberos flow end-to-end without consulting your notes.
- [ ] You have a written topology map (text or table) of the Meridian forest/domain structure.
- [ ] You have identified the three highest-risk groups and at least two GPO gaps with explanations.
- [ ] You have listed the NTLM fallback surfaces and can articulate the attack scenario for each.

## Deliverables

`meridian-map.md` — your annotated domain map, Kerberos walkthrough, high-value group list, GPO gaps, and NTLM risk notes. Commit it to your fork. This becomes the reference document for every later module.

## Automate & own it

**Required.** Write a short Python script (`parse_domain.py`) that reads `data/meridian-domain.md` and prints a summary: number of users per OU, list of groups with more than 5 members, list of service accounts with SPNs. Have a model draft it; you read every line and verify the output matches the spec. Commit it next to your `meridian-map.md`. The point is that even conceptual analysis should produce a reproducible artifact.

## AI acceleration

Use a model to quiz you: paste the Kerberos flow you wrote in step 3 and ask the model to find any gaps or inaccuracies. The model is good at this — but treat its corrections as hypotheses, not verdicts. Verify each one against the Microsoft Kerberos Docs before you accept it.

## Connects forward

The Meridian domain structure is the target for every subsequent lab. Your `meridian-map.md` is a living document — you'll add findings to it in modules 02 (enumeration), 05 (ACL abuse), and 08 (path to DA). The service accounts with SPNs you identified here are the Kerberoasting targets in module 03.

## Marketable proof

> "I can read an Active Directory environment's design, trace authentication flows through Kerberos, and identify structural risk — OUs without hardening GPOs, over-privileged service accounts, NTLM fallback surfaces — before running a single scan."

## Stretch

- Look up what a **SID history** attack is and whether any accounts in the Meridian spec could be exploited for it.
- Research what the **Protected Users** security group does (hint: Kerberos-only, no delegation, short ticket lifetime) and identify which Meridian accounts *should* be in it but aren't.
