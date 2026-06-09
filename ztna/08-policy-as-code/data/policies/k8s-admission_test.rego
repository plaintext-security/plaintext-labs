# k8s-admission_test.rego
# OPA unit tests for k8s-admission.rego.
package k8s.admission_test

import data.k8s.admission
import rego.v1

test_root_user_denied if {
    admission.deny with input as {
        "spec": {
            "securityContext": {"runAsUser": 0},
            "containers": [{"name": "app", "image": "nginx:1.27"}]
        }
    }
}

test_missing_run_as_user_denied if {
    admission.deny with input as {
        "spec": {
            "securityContext": {},
            "containers": [{"name": "app", "image": "nginx:1.27"}]
        }
    }
}

test_container_root_user_denied if {
    admission.deny with input as {
        "spec": {
            "securityContext": {"runAsUser": 1000},
            "containers": [{
                "name": "app",
                "image": "nginx:1.27",
                "securityContext": {"runAsUser": 0}
            }]
        }
    }
}

test_nonroot_user_allowed if {
    not admission.deny with input as {
        "spec": {
            "securityContext": {"runAsUser": 1000},
            "containers": [{
                "name": "app",
                "image": "nginx:1.27",
                "securityContext": {"runAsUser": 1000}
            }]
        }
    }
}
