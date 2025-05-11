# Base image with latest Node version (not LTS)
FROM node:latest as dev

# Set working directory
WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies using pnpm
RUN pnpm install

# Copy app files
COPY . .

# Start the development server (adjust the script if needed)
CMD ["pnpm", "dev", "--host", "0.0.0.0"]

# --- Production build commented out below ---
# FROM docker.io/library/nginx:alpine
# COPY --from=build /app/dist /usr/share/nginx/html
# RUN echo 'server { \
#     listen 80; \
#     location / { \
#         root /usr/share/nginx/html; \
#         index index.html; \
#         try_files $uri $uri/ /index.html; \
#     } \
#     location /api { \
#         proxy_pass http://api-gateway:8000; \
#         proxy_set_header Host $host; \
#         proxy_set_header X-Real-IP $remote_addr; \
#     } \
# }' > /etc/nginx/conf.d/default.conf
# EXPOSE 80
# CMD ["nginx", "-g", "daemon off;"]
