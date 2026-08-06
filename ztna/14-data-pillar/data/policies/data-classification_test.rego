# data-classification_test.rego
# OPA unit tests for data-classification.rego.
# Run with: opa test ./data/policies/
package corp.data_test

import data.corp.data
import rego.v1

# ── Allow cases — by classification ──────────────────────────────────────────

test_analyst_read_public_allowed if {
    data.allow with input as {
        "user": {"role": "analyst", "email": "alice@corp.com"},
        "action": "read",
        "record": {"record_id": "rec-001", "classification": "public"}
    }
}

test_analyst_read_internal_allowed if {
    data.allow with input as {
        "user": {"role": "analyst", "email": "alice@corp.com"},
        "action": "read",
        "record": {"record_id": "rec-002", "classification": "internal"}
    }
}

test_data_officer_read_restricted_allowed if {
    data.allow with input as {
        "user": {"role": "data-officer", "email": "dpatel@corp.com"},
        "action": "read",
        "record": {"record_id": "rec-003", "classification": "restricted"}
    }
}

test_admin_read_restricted_allowed if {
    data.allow with input as {
        "user": {"role": "admin", "email": "csingh@corp.com"},
        "action": "read",
        "record": {"record_id": "rec-003", "classification": "restricted"}
    }
}

# ── Deny cases — the must-deny proof ─────────────────────────────────────────
# A merely-authenticated, non-privileged role reading restricted data must be denied.
# This is the finish-line assertion the lab (and check-data.sh) both key on.

test_analyst_read_restricted_denied if {
    data.deny with input as {
        "user": {"role": "analyst", "email": "alice@corp.com"},
        "action": "read",
        "record": {"record_id": "rec-003", "classification": "restricted"}
    }
}

test_auditor_read_restricted_denied if {
    data.deny with input as {
        "user": {"role": "auditor", "email": "bwong@corp.com"},
        "action": "read",
        "record": {"record_id": "rec-003", "classification": "restricted"}
    }
}

# ── Fail-closed cases — the missing/unknown label proof ─────────────────────
# A record with no classification field, or one with a typo'd/unrecognized value, must
# resolve to "restricted" — never "public". Prove it two ways: the resolved value itself,
# and the access decision it drives for a non-privileged role.

test_missing_label_resolves_to_restricted_not_public if {
    data.effective_classification == "restricted" with input as {
        "record": {"record_id": "rec-004"}
    }
}

test_typo_label_resolves_to_restricted_not_public if {
    data.effective_classification == "restricted" with input as {
        "record": {"record_id": "rec-004", "classification": "Restricted"}
    }
}

test_analyst_read_unlabeled_record_denied if {
    data.deny with input as {
        "user": {"role": "analyst", "email": "alice@corp.com"},
        "action": "read",
        "record": {"record_id": "rec-004"}
    }
}

# Fail-closed does not mean "lock everyone out" — a role cleared for restricted data can
# still read an unlabeled record, because unlabeled resolves to restricted, and restricted
# is exactly what that role may read. The default protects against under-classification,
# not against the role that was always allowed to see the most sensitive tier.
test_data_officer_read_unlabeled_record_allowed if {
    data.allow with input as {
        "user": {"role": "data-officer", "email": "dpatel@corp.com"},
        "action": "read",
        "record": {"record_id": "rec-004"}
    }
}
