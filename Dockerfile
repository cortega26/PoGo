# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder
WORKDIR /app

# Install dependencies and build wheels
COPY requirements.lock pyproject.toml ./
RUN pip install --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements.lock
COPY . .
RUN pip wheel --wheel-dir /wheels .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Create non-root user
RUN useradd --create-home appuser
USER appuser

ENTRYPOINT ["pokemon-rarity"]
