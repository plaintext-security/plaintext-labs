# data-classification.rego
# Evaluates whether a user may READ a record, based on (identity role x data classification).
# This is the Data pillar's access-control input: the label on the record decides the answer,
# not the network the request arrived from.
#
# Input shape:
#   input.user.role          — string: "analyst" | "auditor" | "data-officer" | "admin"
#   input.user.email         — string: e.g. "dpatel@corp.com"
#   input.action              — string: "read" (this policy is read-only; bulk-volume abuse of an
#                                ALLOWED read is a Module 09-style Sigma job, not an OPA job — see
#                                examples/zt-bulk-restricted-read.yml)
#   input.record.record_id   — string: e.g. "rec-003"
#   input.record.classification — string, OPTIONAL: "public" | "internal" | "restricted" | missing/
#                                anything else (typo'd label, null, absent key)
#
# Evaluation queries: data.corp.data.allow / data.corp.data.deny / data.corp.data.effective_classification
package corp.data

import rego.v1

# ── Fail closed on classification itself ─────────────────────────────────────
# A record whose label is missing, null, or not one of the three known values is
# NEVER treated as public. It is treated as the most restrictive tier. This is the
# single load-bearing line in the whole policy: an unlabeled record must resolve to
# "restricted", not silently fall through to "public" because a role check never ran.
known_classifications := {"public", "internal", "restricted"}

default effective_classification := "restricted"

effective_classification := input.record.classification if {
    input.record.classification in known_classifications
}

# ── Default: deny unless a rule below explicitly allows ─────────────────────
default allow := false

# Anyone with standing to make an authenticated request may read public data.
allow if {
    effective_classification == "public"
}

# Analysts, auditors, data-officers, and admins may read internal data.
allow if {
    effective_classification == "internal"
    input.user.role in {"analyst", "auditor", "data-officer", "admin"}
}

# Only data-officers and admins may read restricted data.
allow if {
    effective_classification == "restricted"
    input.user.role in {"data-officer", "admin"}
}

# ── Deny rules make the reason visible and testable ──────────────────────────
# OPA evaluates every rule; a query against `deny` is how the lab (and check-data.sh)
# proves a rejection actually fired, rather than merely proving `allow` was false.

# Any role NOT in the restricted-clearance set is denied on restricted data — this is
# the rule that fires whether the record's real label is "restricted" OR the label was
# missing/unknown and fell back to "restricted" by the fail-closed default above. This
# is the one rule that covers analyst, auditor, and any role never listed at all — the
# same "deny overrides allow, and absence of allow is not the proof" shape as Module 08's
# auditor/"/export" deny.
deny if {
    effective_classification == "restricted"
    not input.user.role in {"data-officer", "admin"}
}
