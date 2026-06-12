FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn python-multipart websockets httpx

COPY --from=frontend-build /app/dist /var/www/html
COPY nginx.conf /etc/nginx/sites-available/default
COPY backend/ /app/backend/
COPY public/samples/ /var/www/html/samples/
RUN chmod -R 755 /var/www/html/
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

WORKDIR /app/backend

EXPOSE 80

CMD ["/app/start.sh"]
