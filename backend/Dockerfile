# GameScope backend image.
# Slim Python base; deps cached in their own layer for fast rebuilds.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: libpq not required (asyncpg is pure-python wheels); keep minimal.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Safety net: strip stray carriage returns (e.g. from Windows CRLF checkouts) so the
# shebang resolves to /bin/bash inside the Linux container, not "/bin/bash\r".
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8000

# Entrypoint runs migrations (and optional seed) before starting the API.
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
