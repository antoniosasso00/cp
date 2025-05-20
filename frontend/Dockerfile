FROM node:18-alpine AS base

# Installa le dipendenze solo quando necessario
FROM base AS deps
WORKDIR /app

# Copia i file necessari per l'installazione
COPY package.json package-lock.json* ./
# Installa tutte le dipendenze, incluse quelle di sviluppo
RUN npm ci

# Rebuilda il codice sorgente solo quando necessario
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Copia anche i file di configurazione di PostCSS e Tailwind
COPY postcss.config.js ./
COPY tailwind.config.ts ./

# Esegue la build dell'applicazione
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Immagine di produzione
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Configura l'utente non-root per motivi di sicurezza
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copia il codice compilato
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Imposta i permessi corretti per la directory .next
RUN chown -R nextjs:nodejs /app/.next

# Passa all'utente non-root
USER nextjs

# Espone la porta e avvia l'applicazione
EXPOSE 3000
ENV PORT 3000

# Comando corretto per avviare l'app in produzione
CMD ["node", "server.js"] 