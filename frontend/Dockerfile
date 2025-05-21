# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Installa le dipendenze
COPY package*.json ./
RUN npm ci

# Copia il codice sorgente
COPY . .

# Build dell'applicazione
RUN npm run build

# Runtime stage
FROM node:18-alpine AS runner

WORKDIR /app

# Imposta le variabili d'ambiente
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copia i file necessari dal builder
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Esponi la porta
EXPOSE 3000

# Comando di avvio
CMD ["node", "server.js"] 