# Lab 09 — Serverless Security

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/09-serverless-security
make up
make demo
make shell
make down
```

The environment provides a LocalStack container (AWS emulator) and a lab container with the AWS
SAM CLI and `cloudfox`. `make up` starts both containers and deploys a deliberately vulnerable
Lambda function using SAM: `data/lambda/` contains the function code and `template.yaml`.

The deployed Lambda has three deliberate misconfigurations:
1. An over-privileged execution role (`sts:AssumeRole *`, `s3:*`, `iam:*`)
2. An event handler that passes the input `command` field to a subprocess without sanitisation
3. A sensitive value (a fake API key) loaded into an environment variable

No real AWS account or SAM account is needed — LocalStack handles the Lambda runtime simulation.

> Only test systems you own or have explicit written permission to test.

## Scenario

Meridian Financial acquired a startup that ran its payment notification system as a set of Lambda
functions. Before connecting the acquired account to the corporate AWS org, you have been asked to
audit the Lambda environment. You will enumerate the execution roles with `cloudfox`, identify the
attack paths, demonstrate the injection vulnerability, and deliver a remediated version of the
function and its IAM role.

## Do

### Part 1: Enumeration with cloudfox

1. [ ] **List all Lambda functions in the LocalStack environment.**
   From the lab shell, enumerate the deployed functions. How many are there? What are their
   names and runtimes?

2. [ ] **Enumerate permissions with cloudfox.**
   Point `cloudfox`'s `permissions` command at the LocalStack endpoint and the `localstack`
   profile. Note which functions have attached policies. What role does `meridian-notifier` use?

3. [ ] **Inspect the execution role in detail.**
   Retrieve the role and its attached policies. What does `sts:AssumeRole *` on the role trust
   policy enable? What can an attacker do with `iam:*` and `s3:*` if they achieve code execution
   inside the function?

4. [ ] **Check environment variables.**
   Read the function's configuration. What sensitive values are stored in environment variables?
   In a real account, how would you retrieve these if you had code execution in the function —
   what is the smallest snippet that dumps the runtime's environment?

5. [ ] **Map the finding to MITRE ATT&CK.**
   The over-privileged role + accessible environment variables maps to T1078 (Valid Accounts) and
   T1552.005 (Cloud Instance Metadata API / Lambda environment). Write a two-sentence threat brief:
   what an attacker who compromises this function can do, and in what order.

### Part 2: Injection demonstration

6. [ ] **Invoke the Lambda with a normal input.**
   Send a well-formed event payload (e.g. an `account_id` and an `event_type` for a payment
   notification) and read the response. What did the function do?

7. [ ] **Invoke the Lambda with a malicious input.**
   The function passes one field of the event straight to a subprocess. Craft a payload whose
   injected field reads the function's own source from its task directory. What does the response
   show? Can you read the handler's source code back through the event?

8. [ ] **Understand the root cause in the function code.**
   Read `data/lambda/handler.py`. Find the line that causes the injection. What is the one-line
   fix that closes it without breaking the function's legitimate behaviour?

### Part 3: Remediation

9. [ ] **Write a least-privilege IAM policy for the function.**
   The function's legitimate purpose is: write a notification record to one specific DynamoDB
   table and send a message to one specific SNS topic. Write an IAM policy JSON that allows
   exactly that and nothing more. No wildcard actions, no wildcard resources.

10. [ ] **Fix the injection in the handler.**
    Edit a copy of `data/lambda/handler.py` and apply the fix: validate that the `command` field
    is in an explicit allowlist before using it; if it's not, return an error response. Add an
    explicit environment variable sanitisation: do not log or return environment variables in
    error responses.

11. [ ] **Redeploy and verify.**
    Update `data/lambda/handler.py` with your fix and redeploy the SAM stack against the
    LocalStack endpoint. Re-run the injection payload from step 7 and confirm the function now
    returns an error instead of executing the injected command.

## Success criteria — you're done when

- [ ] cloudfox enumeration identifies the over-privileged role and its permissions
- [ ] Environment variable finding is documented with the threat brief
- [ ] Injection payload (step 7) successfully retrieves data from the function's source code
- [ ] Least-privilege IAM policy JSON is written with correct resource ARNs
- [ ] Fixed handler.py rejects the injection payload and the re-run confirms it

## Deliverables

Commit to your portfolio repo:
- `threat-brief.md` — MITRE-mapped threat brief from step 5
- `least-privilege-policy.json` — the corrected IAM policy from step 9
- `handler-fixed.py` — the remediated function handler
- `lambda-auditor.sh` — the automation script from **Automate & own it** below

Do **not** commit: LocalStack state, SAM `.aws-sam/` build directory, or any real AWS credentials.

## Automate & own it

**Required.** Write `lambda-auditor.sh` — a script that audits Lambda functions in an AWS account:
1. Lists all functions and their execution role ARNs (`awslocal` / `aws` depending on `$ENDPOINT_URL`)
2. For each function, checks: (a) whether the role has any wildcard action policies, (b) whether
   environment variables exist (flag for manual review), (c) whether the function has a resource-
   based policy that allows public invocation
3. Outputs a Markdown report: Function | Role | Wildcard Actions | Env Vars | Public Invocation

AI drafts the `aws cli` commands and the jq filters. You verify:
- that the wildcard check correctly handles both inline and attached policies
- that the script handles pagination for accounts with many functions
- that "no environment variables" and "empty environment variables" are correctly distinguished

```bash
#!/usr/bin/env bash
# Starter scaffold
ENDPOINT="${ENDPOINT_URL:-}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
# YOU: list functions; for each, get role, check policies, check env vars, check resource policy
# YOU: output Markdown table
```

## AI acceleration

Run `cloudfox aws permissions` and paste the output JSON to a model. Prompt: "You are a red team
operator. Given these Lambda execution role permissions, describe the highest-impact attack path
from initial code execution in the function to account compromise. List each step, the IAM action
used, and the ATT&CK technique ID." The model is excellent at this chain-of-custody reasoning
across IAM permissions. What you verify: that the described path is actually executable given the
effective permissions (permission boundaries and SCPs can truncate what the policy text suggests),
and that the remediation you write closes every hop in the path, not just the loudest permission.

## Connects forward

The IAM enumeration skills from Module 03 (IAM Attack Paths) are the foundation of this module's
execution role analysis — you are applying the same graph-traversal mindset to a Lambda's role.
In Module 14 (Cloud Attack Techniques), you will use `pacu` to automate the exploitation of an
over-privileged Lambda role end-to-end. In Module 16 (Cloud Incident Response), you will learn to
detect this pattern in CloudTrail logs.

## Marketable proof

> "I deployed a deliberately vulnerable serverless function, enumerated its over-privileged
> execution role with cloudfox, demonstrated an event injection attack that exposed the function's
> source and environment variables, and delivered a remediated handler and a least-privilege IAM
> policy."

## Stretch

- Use `pacu`'s Lambda modules to automate the privilege escalation from the over-privileged role:
  create a new IAM user with AdministratorAccess using the function's `iam:*` permission. Confirm
  the new user can list all S3 buckets. Then write the detection: which CloudTrail event sequence
  would a SIEM fire on to catch this?
- Enable Lambda function URL authentication (none vs. IAM) and show how an unauthenticated function
  URL is another confused-deputy exposure for over-privileged functions.
