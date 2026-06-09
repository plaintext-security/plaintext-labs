# Module 12 — Kubernetes RBAC & Network Policy
# Prerequisites: Docker (running), kind >= v0.23.0, kubectl
.PHONY: up down reset demo shell check-prereqs

CLUSTER_NAME = plaintext-lab
KUBECONFIG   = $(HOME)/.kube/config

check-prereqs:
	@command -v kind    >/dev/null 2>&1 || { echo "ERROR: kind not found. Install: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"; exit 1; }
	@command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl not found. Install: https://kubernetes.io/docs/tasks/tools/"; exit 1; }
	@docker info        >/dev/null 2>&1 || { echo "ERROR: Docker is not running."; exit 1; }
	@echo "Prerequisites OK: kind $$(kind version), kubectl $$(kubectl version --client --short 2>/dev/null)"

up: check-prereqs     ## Create the kind cluster and apply seeded RBAC manifests
	@echo "--- Creating kind cluster: $(CLUSTER_NAME) ---"
	kind create cluster --name $(CLUSTER_NAME) --config kind-config.yaml --wait 60s
	@echo "--- Applying seeded RBAC and namespace manifests ---"
	kubectl apply -f manifests/namespaces.yaml
	kubectl apply -f manifests/rbac-bad.yaml
	kubectl apply -f manifests/demo-pod.yaml
	kubectl apply -f manifests/payments-app.yaml
	@echo "--- Waiting for demo-pod to be ready ---"
	kubectl wait --for=condition=Ready pod/demo-pod --timeout=60s
	@echo ""
	@echo "Cluster ready. Run: make demo"

down:    ## Delete the kind cluster
	kind delete cluster --name $(CLUSTER_NAME)

reset:   ## Delete and recreate the cluster from scratch
	kind delete cluster --name $(CLUSTER_NAME) 2>/dev/null || true
	$(MAKE) up

shell:   ## kubectl shell inside demo-pod (runs as the over-privileged ci-deployer SA)
	kubectl exec -it demo-pod -- sh

# ── Demo ────────────────────────────────────────────────────────────────
demo:    ## Run kube-bench and show the misconfigured SA findings
	@echo "=== Module 12 Demo: kube-bench + RBAC misconfiguration ==="
	@echo ""
	@echo "--- 1. Running kube-bench (CIS Kubernetes Benchmark) ---"
	kubectl apply -f manifests/kube-bench-job.yaml
	@echo "Waiting for kube-bench to complete..."
	kubectl wait --for=condition=Complete job/kube-bench --timeout=120s
	@echo ""
	@echo "--- kube-bench findings (section 5 — Policies / RBAC) ---"
	kubectl logs job/kube-bench | grep -A 4 "5\.1\|FAIL\|WARN" | head -60
	@echo ""
	@echo "--- 2. Showing the misconfigured ClusterRoleBinding ---"
	kubectl get clusterrolebinding ci-deployer-admin -o yaml
	@echo ""
	@echo "--- 3. Effective permissions of ci-deployer ServiceAccount ---"
	kubectl auth can-i --list --as=system:serviceaccount:default:ci-deployer | head -20
	@echo ""
	@echo "--- 4. NetworkPolicy status in payments namespace ---"
	kubectl get networkpolicy -n payments
	@echo ""
	@echo "=== Demo complete. See rbac-audit.md for your findings. ==="
	kubectl delete job kube-bench --ignore-not-found=true
