FROM python:3.12-slim
RUN pip install --no-cache-dir flask==3.0.3
WORKDIR /app
COPY app.py .
CMD ["python3", "app.py"]
