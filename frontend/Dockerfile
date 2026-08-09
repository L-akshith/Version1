# ── Build Stage ───────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

# Build the react application
RUN npm run build

# ── Runtime Stage ─────────────────────────────────────────────────
FROM nginx:stable-alpine AS runner

# Copy built static files to Nginx public folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration for single page application routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
