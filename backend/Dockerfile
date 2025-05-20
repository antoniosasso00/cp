FROM python:3.11-slim

WORKDIR /app

# Installa netcat per il controllo della porta
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 