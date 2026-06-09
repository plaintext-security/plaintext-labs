# Module 07 — Microsegmentation lab.
# Requires: docker, kind, kubectl, helm (for Cilium install).
# Standard targets: up / down / reset / demo / shell / verify
.PHONY: up down reset demo shell verify check-prereqs

CLUSTER_NAME := ztna-microseg
CILIUM_VERSION := 1.15.6

check-prereqs:
	@command -v kind   >/dev/null 2>&1 || { echo "kind not found — install from https://kind.sigs.k8s.io/docs/user/quick-start/#installation"; exit 1; }
	@command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found — install from https://kubernetes.io/docs/tasks/tools/"; exit 1; }
	@command -v helm   >/dev/null 2>&1 || { echo "helm not found — install from https://helm.sh/docs/intro/install/"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "docker not found"; exit 1; }
	@echo "Prerequisites: OK"

up: check-prereqs    ## Create kind cluster, install Cilium, deploy three-tier app
	@echo "== Creating kind cluster '$(CLUSTER_NAME)' =="
	kind create cluster --name $(CLUSTER_NAME) --config data/kind-config.yaml
	@echo ""
	@echo "== Installing Cilium $(CILIUM_VERSION) =="
	helm repo add cilium https://helm.cilium.io/ --force-update
	helm install cilium cilium/cilium --version $(CILIUM_VERSION) \
	  --namespace kube-system \
	  --set kubeProxyReplacement=true \
	  --set k8sServiceHost=auto \
	  --set ipam.mode=kubernetes
	@echo "Waiting for Cilium to be ready..."
	kubectl rollout status daemonset/cilium -n kube-system --timeout=120s
	@echo ""
	@echo "== Deploying three-tier application =="
	kubectl apply -f data/manifests.yaml
	kubectl rollout status deployment/frontend -n frontend --timeout=60s
	kubectl rollout status deployment/backend  -n backend  --timeout=60s
	kubectl rollout status deployment/database -n database --timeout=60s
	@echo ""
	@echo "== Done. Run: make demo =="
	@echo "Cluster is running with default allow-all (no policy yet)."

down:    ## Delete the kind cluster
	kind delete cluster --name $(CLUSTER_NAME)

reset: down  ## Delete cluster (alias for down)

# ── Demo ─────────────────────────────────────────────────────────────────────
demo:    ## Show allow/deny contrast before and after policy
	@echo "== 1. BEFORE POLICY: frontend → database (should SUCCEED — default allow-all) =="
	kubectl exec -n frontend deploy/frontend -- \
	  curl -s http://database.database.svc.cluster.local:80 -m 5 \
	  -w "\nHTTP status: %{http_code}" || echo "(timed out or refused)"
	@echo ""
	@echo "== Applying Cilium network policy =="
	kubectl apply -f data/database-policy.yaml
	@echo "Waiting 5s for policy to propagate..."
	sleep 5
	@echo ""
	@echo "== 2. AFTER POLICY: backend → database (should SUCCEED — allowed by policy) =="
	kubectl exec -n backend deploy/backend -- \
	  curl -s http://database.database.svc.cluster.local:80 -m 5 \
	  -w "\nHTTP status: %{http_code}" || echo "(timed out or refused)"
	@echo ""
	@echo "== 3. AFTER POLICY: frontend → database (should FAIL — denied by policy) =="
	@echo "   (Cilium drops silently — expect connection timeout, not TCP RST)"
	kubectl exec -n frontend deploy/frontend -- \
	  curl -s http://database.database.svc.cluster.local:80 -m 5 \
	  -w "\nHTTP status: %{http_code}" || echo "(timed out — EXPECTED: policy drop)"
	@echo ""
	@echo "== 4. frontend → backend (should SUCCEED — no policy restricts this path) =="
	kubectl exec -n frontend deploy/frontend -- \
	  curl -s http://backend.backend.svc.cluster.local:80 -m 5 \
	  -w "\nHTTP status: %{http_code}" || echo "(timed out or refused)"
	@echo ""
	@echo "Run in a second terminal to watch live drop events:"
	@echo "  kubectl exec -n kube-system ds/cilium -c cilium-agent -- cilium monitor --type drop"

shell:   ## Open a shell in the frontend pod
	kubectl exec -n frontend -it deploy/frontend -- sh

# ── Policy regression test ────────────────────────────────────────────────────
verify:  ## Assert allow (backend→db) and deny (frontend→db) cases
	@echo "== Policy verification =="
	@echo "Test 1: backend → database (expect: success)"
	@kubectl exec -n backend deploy/backend -- \
	  curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null -w "%{http_code}" && \
	  echo " PASS: backend reached database" || \
	  { echo " FAIL: backend could not reach database — policy is too restrictive"; exit 1; }
	@echo ""
	@echo "Test 2: frontend → database (expect: denied/timeout)"
	@kubectl exec -n frontend deploy/frontend -- \
	  curl -s http://database.database.svc.cluster.local:80 -m 5 -o /dev/null && \
	  { echo " FAIL: frontend reached database — policy did not deny!"; exit 1; } || \
	  echo " PASS: frontend denied (timed out or refused)"
	@echo ""
	@echo "All policy checks passed."
