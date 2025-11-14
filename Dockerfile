FROM python:3.11.9-slim-bookworm AS builder
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip==24.0 wheel==0.43.0

COPY requirements.txt .

RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt


FROM python:3.11.9-slim-bookworm AS final
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

RUN apt-get update && \
    apt-cache policy curl && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels

RUN pip install --no-cache-dir /wheels/*

COPY --chown=appuser:appgroup ./app ./app

RUN mkdir uploads && chown -R appuser:appgroup /app/uploads

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
