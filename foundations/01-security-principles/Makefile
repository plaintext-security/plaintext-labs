.PHONY: demo cert-demo

# Print the principle-autopsy guide, then run the cert-expiry checker against
# the bundled expired sample cert — fully offline, no network required.
demo:
	python3 guide.py
	@echo
	@$(MAKE) --no-print-directory cert-demo

# Demonstrate cert_check.py on the bundled expired sample (deterministic,
# network-free). It exits non-zero on the expired cert by design, so we report
# that as the expected "blind spot" outcome rather than failing the target.
cert-demo:
	@echo "── cert_check.py — the Equifax blind spot (Hop 3) ──"
	@echo "Checking bundled sample-expired-cert.pem (offline, deterministic):"
	@echo
	@python3 cert_check.py --pem sample-expired-cert.pem; \
	  status=$$?; echo; \
	  echo "(exit $$status — non-zero is correct: an expired cert is a FAIL,"; \
	  echo " just as Equifax's lapsed inspection cert should have been.)"
