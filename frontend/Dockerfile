FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api
ENV NODE_ENV=development

EXPOSE 3000

CMD ["npm", "run", "dev"] 