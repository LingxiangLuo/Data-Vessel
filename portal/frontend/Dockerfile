FROM node:20-alpine AS builder

WORKDIR /app

# 单独复制 lock 文件，利用 Docker layer 缓存——只有依赖变化才重装
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build || npx vite build

# 使用 busybox 将构建产物复制到共享 volume
FROM busybox
COPY --from=builder /app/dist /build
CMD ["sh", "-c", "rm -rf /output/* && cp -r /build/. /output/ && echo 'Frontend build copied to volume'"]
