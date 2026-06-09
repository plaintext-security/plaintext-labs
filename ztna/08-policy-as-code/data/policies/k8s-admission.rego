# k8s-admission.rego
# Kubernetes admission policy: deny pods that run as root.
# Covers two cases:
#   1. runAsUser is explicitly set to 0 (root)
#   2. runAsUser is omitted entirely (many images default to root)
#
# Input shape: a Kubernetes AdmissionReview request.object (Pod spec).
# For the lab we use a simplified shape matching data/inputs/pod-*.json.
# In production this runs as a Validating Admission Webhook via OPA Gatekeeper.
#
# Evaluation query: data.k8s.admission.deny
package k8s.admission

import rego.v1

default deny := false

# Deny if the pod-level security context explicitly sets runAsUser: 0.
deny if {
    input.spec.securityContext.runAsUser == 0
}

# Deny if the pod-level security context omits runAsUser (nil/missing means
# the container may run as whatever user the image specifies, which is often
# root for base images).
deny if {
    not input.spec.securityContext.runAsUser
}

# Deny if any container explicitly sets runAsUser: 0 in its own securityContext.
deny if {
    some container in input.spec.containers
    container.securityContext.runAsUser == 0
}

# Reason string for admission response (used in Gatekeeper's constraint message).
reason := "Pod must not run as root. Set spec.securityContext.runAsUser to a non-zero UID."
