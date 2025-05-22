# -------------------------------
# Stage 1: builder
# -------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Installa dipendenze di sistema (solo se necessarie)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Copia e installa le dipendenze Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia il codice sorgente
COPY . .

# -------------------------------
# Stage 2: runtime
# -------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installa dipendenze di sistema necessarie
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Copia TUTTO /usr/local dal builder (librerie + binari)
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Rendi eseguibile lo script di avvio
RUN chmod +x /app/start.sh

# Expose porta backend
EXPOSE 8000

# Comando di avvio
CMD ["/app/start.sh"]
    