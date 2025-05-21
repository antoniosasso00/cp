FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
# TODO: Considerare l'uso di pnpm per build più veloci
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"] 