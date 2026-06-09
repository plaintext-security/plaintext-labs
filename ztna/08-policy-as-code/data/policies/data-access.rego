# data-access.rego
# Evaluates whether a user may perform an action on a data resource.
# Input shape:
#   input.user.role    — string: "analyst" | "admin" | "service_account" | "auditor"
#   input.user.email   — string: e.g. "jdoe@meridian.com"
#   input.action       — string: "read" | "write"
#   input.resource     — string: resource path, e.g. "/api/v1/records"
#
# Evaluation query: data.meridian.access.allow
package meridian.access

import rego.v1

# Default: deny unless a rule below explicitly allows.
default allow := false

# Analysts may read any resource.
allow if {
    input.user.role == "analyst"
    input.action == "read"
}

# Admins may read or write any resource.
allow if {
    input.user.role == "admin"
}

# Service accounts (automated report jobs) may only read.
allow if {
    input.user.role == "service_account"
    input.action == "read"
}

# ── Deny rules override allow rules ──────────────────────────────────────────
# OPA evaluates all rules; if any deny fires, enforcement should treat the
# request as denied. The convention is: deny overrides allow in your
# enforcement code (or use OPA's `not allow` pattern).

# Analysts may not write.
deny if {
    input.user.role == "analyst"
    input.action == "write"
}

# Service accounts may not write.
deny if {
    input.user.role == "service_account"
    input.action == "write"
}

# ── Lab exercise: add auditor role ────────────────────────────────────────────
# Step 3 asks you to add an auditor role that:
#   - Can read (allow rule)
#   - Cannot write (deny rule)
#   - Cannot access /export at all (deny rule, regardless of action)
#
# Uncomment and complete:
#
# allow if {
#     input.user.role == "auditor"
#     input.action == "read"
# }
#
# deny if {
#     input.user.role == "auditor"
#     input.action == "write"
# }
#
# deny if {
#     input.user.role == "auditor"
#     input.resource == "/export"
# }
