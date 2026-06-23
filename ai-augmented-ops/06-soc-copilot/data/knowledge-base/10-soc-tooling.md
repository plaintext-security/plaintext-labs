# LastPass Breach — Disclosure Timeline and Public Sources
**Document type:** Reference | **Source:** LastPass public disclosures

## Disclosure milestones
| Date | Disclosure |
|------|-----------|
| August 25, 2022 | First incident disclosed: unauthorized access to the development environment via a compromised developer account; source code and technical information taken; no customer data accessed. |
| November 30, 2022 | LastPass discloses that an unauthorized party used information from the August incident to access elements of customers' information held in a third-party cloud storage service. |
| December 22, 2022 | Full scope disclosed: customer account information/metadata and a backup of customer vault data (unencrypted URLs + AES-256-encrypted secrets) were copied. |

## What each disclosure added
- **Aug 25:** scoped the first incident to development; reassured that production/vaults were not
  touched.
- **Nov 30:** revealed the two incidents were **linked** — the attacker reused stage-1 information.
- **Dec 22:** quantified what customer data was taken and clarified the **encrypted-vs-cleartext**
  split, plus master-password-based customer guidance.

## Primary sources for this corpus
- LastPass, "Notice of Recent Security Incident" (the consolidated notice with the timeline and
  updates): https://blog.lastpass.com/posts/notice-of-recent-security-incident
- CISA tracked the incident and references LastPass's advisories:
  https://www.cisa.gov/news-events/alerts/2022/12/28/lastpass-data-breach

## How to use this corpus in the lab
Sample questions whose answers live in these documents:
- "What was the initial access vector of the first incident?" → document 02.
- "How did the attacker access the cloud backup storage?" → documents 03 and 05.
- "Was customer vault data encrypted?" → document 04 (URLs cleartext; secrets AES-256).
- "What vulnerability was exploited on the engineer's home computer?" → document 05.
