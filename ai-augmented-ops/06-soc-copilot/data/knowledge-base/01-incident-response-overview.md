# LastPass 2022 Breach — Incident Overview and Timeline
**Document type:** Public post-mortem summary | **Source:** LastPass disclosures | **Compiled:** 2025

## Purpose
This knowledge base is built from LastPass's *public* disclosures about the 2022 breach. It is a
factual study corpus for a retrieval system — every claim here traces to LastPass's own statements
or its incident write-ups. Primary source: https://blog.lastpass.com/posts/notice-of-recent-security-incident

## What happened, in one paragraph
The 2022 LastPass breach was a **two-stage** intrusion. In the first stage (August 2022) an attacker
compromised a single software developer's account and accessed the LastPass **development**
environment, stealing source code and proprietary technical information — no customer data or vaults
were reached, because the dev environment was separated from production. In the second stage
(roughly August–December 2022) the attacker used information stolen in stage one to target a
**different** employee, ultimately reaching cloud-based **backup** storage and exfiltrating customer
account information and **encrypted customer vault backups**.

## High-level timeline
| Date | Event |
|------|-------|
| August 2022 | Stage 1: developer account compromised; attacker accesses the LastPass development environment; source code and technical information stolen. |
| August 25, 2022 | LastPass publicly discloses the first incident. |
| Aug–Dec 2022 | Stage 2: attacker uses stolen information to target a second employee (a DevOps engineer) and reach cloud backup storage. |
| November 30, 2022 | LastPass discloses that an unauthorized party accessed elements of customer information using data taken in the first incident. |
| December 22, 2022 | LastPass discloses the full scope: customer account data and encrypted vault backups were copied. |

## Why this is a useful corpus
The two stages are easy to confuse, and several facts are subtle (what was encrypted vs. in
cleartext; which environment each stage touched). Those distinctions are exactly what a retrieval +
generation pipeline must get right — a confident answer that conflates the two stages is the silent
failure this lab is about.

## Source
- LastPass, "Notice of Recent Security Incident": https://blog.lastpass.com/posts/notice-of-recent-security-incident
