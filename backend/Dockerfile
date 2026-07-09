FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY ingest ./ingest
RUN pip install --no-cache-dir .
EXPOSE 8000
# Single worker on purpose: the submission rate limiter is in-process (SPEC 6).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
