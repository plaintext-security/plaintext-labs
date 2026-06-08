# --- ROOT version (the default, insecure) ---
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
# No USER instruction → runs as root
EXPOSE 8000
CMD ["python3", "app.py"]
