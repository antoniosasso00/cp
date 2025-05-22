FROM node:18-alpine AS builder

WORKDIR /app

# Copia solo i file necessari per npm ci
COPY package*.json ./

# Usa solo le dipendenze locali, non installa next globalmente
RUN npm ci

# Copia il resto dei file
COPY . .

# Crea la cartella public se non esiste
RUN mkdir -p public

# Esegui la build specificando il percorso completo nel node_modules
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV=production
RUN node node_modules/next/dist/bin/next build

# Crea l'immagine di produzione
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Configura l'utente non-root per motivi di sicurezza
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Crea la directory public nella destinazione
RUN mkdir -p .next/static
RUN mkdir -p public

# Copia solo i file necessari per l'esecuzione
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Imposta i permessi corretti
RUN chown -R nextjs:nodejs /app

# Passa all'utente non-root
USER nextjs

# Espone la porta e avvia l'applicazione
EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"] 