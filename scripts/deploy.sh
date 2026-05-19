#!/bin/bash
# ============================================
# 一键部署脚本
# ============================================
set -e

PROJECT_DIR="/opt/data-platform-mvp"
echo "=========================================="
echo "  数据中台 MVP - 一键部署"
echo "=========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

# 进入项目目录
cd "$PROJECT_DIR"

# 初始化服务器 (仅首次)
if [ ! -f /opt/.dmp-initialized ]; then
    echo "[1/5] 初始化服务器..."
    bash scripts/init-server.sh
    touch /opt/.dmp-initialized
else
    echo "[1/5] 服务器已初始化，跳过"
fi

# 拉取镜像
echo "[2/5] 拉取 Docker 镜像..."
docker compose pull

# 启动基础服务
echo "[3/5] 启动基础服务 (MySQL, Redis)..."
docker compose up -d mysql redis
echo "等待 MySQL 就绪..."
sleep 15
# 等待 MySQL 健康检查通过
for i in $(seq 1 30); do
    if docker inspect --format='{{.State.Health.Status}}' dmp-mysql 2>/dev/null | grep -q healthy; then
        echo "MySQL 就绪"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 5
done

# 启动所有服务
echo "[4/5] 启动所有服务..."
docker compose up -d

# 等待服务就绪
echo "[5/5] 等待服务就绪..."
sleep 30

echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "服务状态:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=========================================="
