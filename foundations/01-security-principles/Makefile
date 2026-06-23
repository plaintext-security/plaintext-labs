.PHONY: demo cert-demo solution-demo

# Print the principle-autopsy guide, then try YOUR cert-expiry checker.
demo:
	python3 guide.py
	@echo
	@$(MAKE) --no-print-directory cert-demo

# Run YOUR cert_check.py against the bundled expired sample (offline,
# deterministic). It's a skeleton until you build it — until then this prints
# how to start. Once implemented, it exits non-zero on the expired cert, which
# is the correct "blind spot" outcome.
cert-demo:
	@echo "── cert_check.py — the Equifax blind spot (Hop 3) ──"
	@echo "Running YOUR cert_check.py on sample-expired-cert.pem (offline):"
	@echo
	@if python3 cert_check.py --pem sample-expired-cert.pem 2>/tmp/cert_check_err; then \
	  echo; echo "(exit 0 — but an EXPIRED cert should FAIL. Re-check your exit codes.)"; \
	else \
	  if grep -q NotImplementedError /tmp/cert_check_err; then \
	    echo "cert_check.py isn't built yet — it's your exercise."; \
	    echo "Implement main() per the spec in the file, then re-run 'make cert-demo'."; \
	    echo "See lab.md → 'Automate & own it'. Reference: solution/cert_check.py."; \
	  else \
	    cat /tmp/cert_check_err; echo; \
	    echo "(non-zero exit — correct: an expired cert is a FAIL, just as"; \
	    echo " Equifax's lapsed inspection cert should have been.)"; \
	  fi; \
	fi; \
	rm -f /tmp/cert_check_err

# Sanity-check the reference build (for verifying your own against, or for CI).
solution-demo:
	@echo "── reference solution on sample-expired-cert.pem ──"
	@python3 solution/cert_check.py --pem sample-expired-cert.pem; \
	  echo "(exit $$? — non-zero is correct on an expired cert.)"
