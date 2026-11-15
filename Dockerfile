FROM node:22-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ARG CODE_COMMIT=unknown
LABEL org.opencontainers.image.title="OrbitLens SPHEREx" \
      org.opencontainers.image.description="Secuencias temporales SPHEREx desde IRSA" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.revision="${CODE_COMMIT}"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ORBITLENS_DATA_DIR=/app/data ORBITLENS_CODE_COMMIT=${CODE_COMMIT} \
    XDG_CACHE_HOME=/app/data/external-cache PORT=8000 HOME=/home/orbitlens
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt \
    && useradd --uid 10001 --create-home --shell /bin/false orbitlens \
    && mkdir -p /app/data && chown orbitlens:orbitlens /app/data
COPY api.py ./
COPY orbitlens/ ./orbitlens/
COPY scripts/serve.py ./scripts/serve.py
COPY --from=frontend /build/frontend/dist/ ./frontend/dist/
USER orbitlens
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/health', timeout=3)"
CMD ["python", "scripts/serve.py"]
