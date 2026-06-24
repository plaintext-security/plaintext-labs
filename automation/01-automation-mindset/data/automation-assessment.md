# SOC Automation Assessment — Task Inventory

## Framework

| Axis | Description | Scale |
|------|-------------|-------|
| **Repeatability** | How often does this exact task sequence occur? | daily / weekly / ad-hoc |
| **Determinism** | Given the same inputs, does the correct action always look the same? | high / medium / low |
| **Maintenance burden** | What could change and break this automation? | low / medium / high |

**ROI = (time_saved_minutes × frequency_per_week) − (maintenance_burden_hours_per_month × 4)**

### Three zones

| Zone | Criteria | Approach |
|------|----------|----------|
| **Full automation** | High repeatability + High determinism | Automate; add kill-switch + logging |
| **Human-in-the-loop** | High repeatability + Medium determinism | Automate data gathering; human decides |
| **Keep manual** | Low repeatability OR Low determinism | Don't automate; improve runbook instead |

---

## Task List

Complete the table for each task. Replace the `?` placeholders with your assessment.

| # | Task | Repeatability | Determinism | Maint. burden | Zone | Notes |
|---|------|--------------|-------------|---------------|------|-------|
| 1 | Enrich an IOC (IP/hash) against VirusTotal + AbuseIPDB | ? | ? | ? | ? | |
| 2 | Route a HIGH SIEM alert to the on-call analyst | ? | ? | ? | ? | |
| 3 | Determine if an alert is a false positive | ? | ? | ? | ? | |
| 4 | Create a Jira ticket for a confirmed incident | ? | ? | ? | ? | |
| 5 | Block a source IP at the perimeter firewall | ? | ? | ? | ? | |
| 6 | Generate the weekly vulnerability report from scanner output | ? | ? | ? | ? | |
| 7 | Decide whether a CVE is applicable to our infrastructure | ? | ? | ? | ? | |
| 8 | Reset a locked-out employee account after verifying identity | ? | ? | ? | ? | |
| 9 | Scan new cloud resources for IaC misconfigurations | ? | ? | ? | ? | |
| 10 | Respond to a phishing report: analyze headers, extract IOCs | ? | ? | ? | ? | |

---

## Top 3 Full Automation Candidates

### Candidate 1: [task name]
- **Tool/language:**
- **Trigger:**
- **Log format:**
- **Kill-switch:**
- **What changes could break it:**

### Candidate 2: [task name]
- **Tool/language:**
- **Trigger:**
- **Log format:**
- **Kill-switch:**
- **What changes could break it:**

### Candidate 3: [task name]
- **Tool/language:**
- **Trigger:**
- **Log format:**
- **Kill-switch:**
- **What changes could break it:**

---

## Top 2 Human-in-the-Loop Candidates

### Candidate 1: [task name]
- **What the automation does:**
- **What information the human sees:**
- **Human choices:**
- **What happens after the human responds:**

### Candidate 2: [task name]
- **What the automation does:**
- **What information the human sees:**
- **Human choices:**
- **What happens after the human responds:**
