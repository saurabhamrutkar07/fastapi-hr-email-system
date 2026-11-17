# Website image, built in two stages.

# ---- Stage 1: build the React app into plain HTML/JS/CSS files
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# The site calls the API at /api on its own address (Nginx forwards it)
ENV VITE_API_URL=/api
RUN npm run build

# ---- Stage 2: serve those files with Nginx (Node is not needed any more)
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html