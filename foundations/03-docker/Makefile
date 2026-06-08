.PHONY: demo clean

# Run the full Docker lifecycle demo (no compose needed — uses docker directly)
demo:
	python3 demo.py

# Remove demo image
clean:
	docker rmi plaintext/docker-demo-server 2>/dev/null || true
