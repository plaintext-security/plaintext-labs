# Module 05 — SASE & Cloud-Delivered Zero Trust lab.
# Standard targets: up / down / reset / demo.
# The Cloudflare account is external; this Makefile manages the local nginx container only.
.PHONY: up down reset demo

up:    ## Start the local nginx application on port 8090
	docker compose up -d
	@echo ""
	@echo "Nginx is running at http://localhost:8090"
	@echo "Verify: curl http://localhost:8090/"
	@echo ""
	@echo "This container is the private application you will publish via cloudflared."
	@echo "Run 'make demo' for Cloudflare setup instructions."

down:  ## Stop nginx
	docker compose down

reset: ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

demo:  ## Print step-by-step Cloudflare tunnel and Access policy setup instructions
	@echo "============================================================"
	@echo "  Lab 05 — SASE & Cloud-Delivered Zero Trust: Cloudflare Access"
	@echo "============================================================"
	@echo ""
	@echo "Prerequisites:"
	@echo "  1. Sign up for Cloudflare Zero Trust (free, 50 users, no expiry):"
	@echo "     https://dash.cloudflare.com/sign-up/teams"
	@echo ""
	@echo "  2. Install cloudflared:"
	@echo "     macOS:  brew install cloudflared"
	@echo "     Linux:  https://github.com/cloudflare/cloudflared/releases"
	@echo ""
	@echo "  3. Confirm nginx is running: curl http://localhost:8090/"
	@echo ""
	@echo "------------------------------------------------------------"
	@echo "Step A: Quick tunnel (no account required for first test)"
	@echo "------------------------------------------------------------"
	@echo "  cloudflared tunnel --url http://localhost:8090"
	@echo "  → Cloudflare prints a *.trycloudflare.com URL."
	@echo "  → Browse to it. You should see the Meridian app (no Access policy yet)."
	@echo "  → Ctrl-C to stop."
	@echo ""
	@echo "------------------------------------------------------------"
	@echo "Step B: Named tunnel + Access policy (requires account)"
	@echo "------------------------------------------------------------"
	@echo "  cloudflared tunnel login"
	@echo "  cloudflared tunnel create meridian-lab"
	@echo "  cloudflared tunnel route dns meridian-lab <your-hostname>"
	@echo "  cloudflared tunnel run meridian-lab --url http://localhost:8090"
	@echo ""
	@echo "  In the Zero Trust dashboard:"
	@echo "  → Access → Applications → Add application → Self-hosted"
	@echo "  → Domain: <your-hostname>"
	@echo "  → Policy: Allow, Include: Emails → your-email@domain.com"
	@echo "  → Save and test: browse to <your-hostname>"
	@echo "  → You should be prompted for email OTP before seeing the app"
	@echo ""
	@echo "------------------------------------------------------------"
	@echo "Step C: Verify denial"
	@echo "------------------------------------------------------------"
	@echo "  - Open a private/incognito window and browse to <your-hostname>"
	@echo "  - You should see the Cloudflare Access login page, not the app"
	@echo "  - Verify port 8090 is not externally reachable:"
	@echo "    https://check.host → TCP check → your IP → port 8090"
	@echo ""
	@echo "Reference: data/access-policy-example.json"
	@echo "  Shows the four policy tiers from email-only to CrowdStrike posture."
	@echo "============================================================"
