# ── Frontend Dockerfile ─────────────────────
# Multi-stage: Build with Node, serve with nginx
# Build:  docker build -t jenanbiz-web -f Dockerfile .
# Run:    docker run -p 80:80 jenanbiz-web

# ── Stage 1: Build ──
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: Serve ──
FROM nginx:1.27-alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
