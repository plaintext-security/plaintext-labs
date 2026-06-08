# Reference lab image: an intentionally vulnerable Flask app for SQL injection.
FROM python:3.12-slim

RUN pip install --no-cache-dir flask==3.0.3

WORKDIR /app
COPY app.py demo_attack.py /app/

EXPOSE 5000
CMD ["python", "/app/app.py"]
