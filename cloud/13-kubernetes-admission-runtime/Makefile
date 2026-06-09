# Module 13 — Kubernetes Admission & Runtime
# Prerequisites: Docker (running), kind >= v0.23.0, kubectl, helm
.PHONY: up down reset demo shell logs-falco check-prereqs

CLUSTER_NAME = plaintext-lab-13
KYVERNO_VER  = 3.2.6
FALCO_VER    = 4.3.2

check-prereqs:
	@command -v kind    >/dev/null 2>&1 || { echo "ERROR: kind not found. Install: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"; exit 1; }
	@command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl not found. Install: https://kubernetes.io/docs/tasks/tools/"; exit 1; }
	@command -v helm    >/dev/null 2>&1 || { echo "ERROR: helm not found. Install: https://helm.sh/docs/intro/install/"; exit 1; }
	@docker info        >/dev/null 2>&1 || { echo "ERROR: Docker is not running."; exit 1; }
	@echo "Prerequisites OK"

up: check-prereqs    ## Create kind cluster, install Kyverno + Falco, apply seed policies
	@echo "--- Creating kind cluster: $(CLUSTER_NAME) ---"
	kind create cluster --name $(CLUSTER_NAME) --wait 60s
	@echo ""
	@echo "--- Installing Kyverno via Helm ---"
	helm repo add kyverno https://kyverno.github.io/kyverno/
	helm repo update
	helm install kyverno kyverno/kyverno \
		--namespace kyverno --create-namespace \
		--version $(KYVERNO_VER) \
		--set admissionController.replicas=1 \
		--wait --timeout 120s
	@echo ""
	@echo "--- Installing Falco via Helm ---"
	helm repo add falcosecurity https://falcosecurity.github.io/charts
	helm repo update falcosecurity
	helm install falco falcosecurity/falco \
		--namespace falco --create-namespace \
		--version $(FALCO_VER) \
		--set driver.kind=modern_ebpf \
		--set falco.json_output=true \
		--set-file falco.rules_file[0]=manifests/falco-runtime-rules.yaml \
		--wait --timeout 180s
	@echo ""
	@echo "--- Applying seed Kyverno policies ---"
	kubectl apply -f manifests/policies/
	@echo ""
	@echo "--- Waiting for policies to be active ---"
	sleep 10
	@echo ""
	@echo "Cluster ready. Run: make demo"

down:    ## Delete the kind cluster
	kind delete cluster --name $(CLUSTER_NAME)

reset:   ## Delete and recreate from scratch
	kind delete cluster --name $(CLUSTER_NAME) 2>/dev/null || true
	$(MAKE) up

shell:   ## kubectl shell for cluster exploration
	kubectl run -it --rm debug --image=busybox:1.36 --restart=Never -- sh

logs-falco: ## Tail Falco output (run in a second terminal)
	kubectl logs -n falco -l app.kubernetes.io/name=falco -f

# ── Demo ─────────────────────────────────────────────────────────────────
demo:    ## Deploy non-compliant pod (denied) and compliant pod (allowed); show Falco alert
	@echo "=== Module 13 Demo: Kyverno + Falco ==="
	@echo ""
	@echo "--- 1. List installed Kyverno policies ---"
	kubectl get clusterpolicies
	@echo ""
	@echo "--- 2. Try to deploy NON-COMPLIANT pod (should be DENIED) ---"
	kubectl apply -f manifests/pod-bad.yaml 2>&1 || true
	@echo ""
	@echo "--- 3. Deploy COMPLIANT pod (should be ADMITTED) ---"
	kubectl apply -f manifests/pod-good.yaml
	kubectl wait --for=condition=Ready pod/lab-compliant --timeout=60s
	@echo "Compliant pod is Running: $$(kubectl get pod lab-compliant --no-headers)"
	@echo ""
	@echo "--- 4. Trigger a Falco runtime alert (read /etc/passwd) ---"
	kubectl exec lab-compliant -- sh -c 'cat /etc/passwd' 2>/dev/null || true
	@echo "(Check 'make logs-falco' in a second terminal for the Falco alert)"
	@echo ""
	@echo "--- 5. Policy report ---"
	kubectl get policyreport -A --no-headers 2>/dev/null | head -10 || echo "(policy reports may take a moment)"
	@echo ""
	@echo "--- 6. Clean up demo pod ---"
	kubectl delete pod lab-compliant --ignore-not-found=true
	@echo ""
	@echo "=== Demo complete. See policy-report.md for your findings. ==="
