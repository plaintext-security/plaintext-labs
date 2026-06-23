# promptfoo Evaluation Results
## SOC Copilot — Adversarial Evaluation

**Date:** <!-- fill in -->
**Model:** tinyllama (via ollama:0.3.14)

---

## Test results summary

| Test | Description | Pass/Fail | Notes |
|------|-------------|-----------|-------|
| 1 | System prompt extraction — direct | | |
| 2 | System prompt extraction — indirect | | |
| 3 | Role override — DAN jailbreak | | |
| 4 | Severity override via embedded instruction | | |
| 5 | Malicious command generation | | |
| 6 | Data exfiltration instruction | | |
| 7 | [Your test case] | | |

---

## Failing assertion analysis

For each FAIL above, explain:
- What was the model's actual output?
- Which assertion did it violate?
- What does this mean for the copilot's safety in a SOC context?

### Test N — [Name]

**Prompt sent:** <!-- excerpt -->

**Model output:**
```
<!-- paste the actual output -->
```

**Failed assertion:** <!-- e.g. "not-contains: 'net stop'" -->

**SOC impact:** <!-- what could an attacker do with this behaviour? -->

**Mitigation:** <!-- what prompt change or output validation would fix this? -->
