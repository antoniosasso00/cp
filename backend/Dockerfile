FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Imposta il permesso di esecuzione per lo script di avvio
RUN chmod +x start.sh

# Usa lo script di avvio come comando di default
CMD ["./start.sh"] 