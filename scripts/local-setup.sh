#!/bin/bash
# ============================================
# 数据中台 MVP - 本地完整复刻脚本
# 适用于 macOS (Docker Desktop) / Windows WSL
# ============================================
set -e

echo "=== 数据中台 MVP 本地复刻 ==="
echo ""

# 0. 检测平台
OS="$(uname -s)"
case "$OS" in
    Darwin) PLATFORM="macOS" ;;
    Linux)  PLATFORM="Linux/WSL" ;;
    *)      PLATFORM="$OS" ;;
esac
echo "平台: $PLATFORM"
echo ""

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker 未安装。"
    if [ "$PLATFORM" = "macOS" ]; then
        echo "  brew install --cask docker  或下载 https://www.docker.com/products/docker-desktop/"
    else
        echo "  请安装 Docker Desktop 或 docker-ce"
    fi
    exit 1
fi

if ! docker info &> /dev/null 2>&1; then
    echo "ERROR: Docker 未运行。请启动 Docker Desktop。"
    exit 1
fi

echo "[1/5] Docker 环境正常"

# 2. 确保 .env 存在
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
MYSQL_ROOT_PASSWORD=DpMvp2026Secure
REDIS_PASSWORD=DpMvp2026Secure
PORTAL_SECRET_KEY=data-platform-mvp-secret-key-2026
DS_ADMIN_PASSWORD=dolphinscheduler123
OM_ADMIN_PASSWORD=admin
ENVEOF
    echo "[2/5] .env 文件已创建"
else
    echo "[2/5] .env 文件已存在"
fi

# 3. 启动基础服务（MySQL + Redis）
echo "[3/5] 启动 MySQL + Redis..."
docker compose up -d mysql redis
echo "    等待 MySQL 健康检查..."
for i in $(seq 1 30); do
    if docker exec dmp-mysql mysqladmin ping -uroot -pDpMvp2026Secure 2>/dev/null | grep -q alive; then
        break
    fi
    sleep 2
done

# 4. 导入完整数据
echo "[4/5] 导入数据库..."
if [ -f docker/mysql/full-backup.sql ]; then
    docker exec -i dmp-mysql mysql -uroot -pDpMvp2026Secure < docker/mysql/full-backup.sql 2>/dev/null
    echo "    数据导入完成（含 portal_db + dolphinscheduler）"
else
    echo "    WARNING: full-backup.sql 不存在，将使用 init.sql 初始化空库"
fi

# 5. 启动所有服务
echo "[5/5] 启动全部服务..."
docker compose up -d --build

echo ""
echo "=== 部署完成 ==="
echo ""
echo "等待服务启动（约 60-90 秒）..."
sleep 10

# 检查服务状态
echo ""
echo "服务状态："
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "访问地址: http://localhost"
echo "账号: admin / admin123"
echo ""
echo "提示："
echo "  - DolphinScheduler 首次启动需要 2 分钟"
echo "  - macOS 建议 Docker Desktop 分配 4GB+ 内存"
echo "  - 停止: docker compose down"
echo "  - 停止并清数据: docker compose down -v"
