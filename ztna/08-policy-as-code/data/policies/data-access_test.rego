# data-access_test.rego
# OPA unit tests for data-access.rego.
# Run with: opa test ./data/policies/
package meridian.access_test

import data.meridian.access
import rego.v1

# ── Allow cases ───────────────────────────────────────────────────────────────

test_analyst_read_allowed if {
    access.allow with input as {
        "user": {"role": "analyst", "email": "jdoe@meridian.com"},
        "action": "read",
        "resource": "/api/v1/records"
    }
}

test_admin_write_allowed if {
    access.allow with input as {
        "user": {"role": "admin", "email": "admin@meridian.com"},
        "action": "write",
        "resource": "/api/v1/records"
    }
}

test_service_account_read_allowed if {
    access.allow with input as {
        "user": {"role": "service_account", "email": "svc-reports@meridian.com"},
        "action": "read",
        "resource": "/api/v1/reports"
    }
}

# ── Deny cases ────────────────────────────────────────────────────────────────

test_analyst_write_denied if {
    access.deny with input as {
        "user": {"role": "analyst", "email": "jdoe@meridian.com"},
        "action": "write",
        "resource": "/api/v1/records"
    }
}

test_service_account_write_denied if {
    access.deny with input as {
        "user": {"role": "service_account", "email": "svc-reports@meridian.com"},
        "action": "write",
        "resource": "/api/v1/reports"
    }
}

# ── Lab exercise: auditor tests (add after completing step 3) ─────────────────
# Uncomment after adding the auditor rules to data-access.rego.
#
# test_auditor_read_allowed if {
#     access.allow with input as {
#         "user": {"role": "auditor", "email": "auditor@meridian.com"},
#         "action": "read",
#         "resource": "/api/v1/records"
#     }
# }
#
# test_auditor_export_denied if {
#     access.deny with input as {
#         "user": {"role": "auditor", "email": "auditor@meridian.com"},
#         "action": "read",
#         "resource": "/export"
#     }
# }
