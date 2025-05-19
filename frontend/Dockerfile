FROM node:18-alpine AS base

# Installa le dipendenze solo quando necessario
FROM base AS deps
WORKDIR /app

# Copia i file necessari per l'installazione
COPY package.json ./
RUN npm install

# Rebuilda il codice sorgente solo quando necessario
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Esegue la build dell'applicazione
RUN npm run build

# Immagine di produzione
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

# Configura l'utente non-root per motivi di sicurezza
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

# Copia il codice compilato
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Espone la porta e avvia l'applicazione
EXPOSE 3000
ENV PORT 3000

CMD ["npm", "start"] 