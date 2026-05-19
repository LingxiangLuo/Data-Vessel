#!/usr/bin/env bash
set -euo pipefail

TEST_HOST="192.168.1.3"
TEST_USER="root"
TEST_DIR="/opt/data-platform-mvp"
SSH_KEY="$HOME/.ssh/test_server_key"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 参数解析
BACKEND_ONLY=false
FRONTEND_ONLY=false
SKIP_CHECK=false
FORCE_REBUILD=false

for arg in "$@"; do
    case "$arg" in
        --backend-only)  BACKEND_ONLY=true ;;
        --frontend-only) FRONTEND_ONLY=true ;;
        --skip-check)    SKIP_CHECK=true ;;
        --force)         FORCE_REBUILD=true ;;
    esac
done

# 互斥检查
if [ "$BACKEND_ONLY" = true ] && [ "$FRONTEND_ONLY" = true ]; then
    echo "❌ --backend-only 和 --frontend-only 不能同时使用"
    exit 1
fi

echo "=========================================="
echo "  部署到测试服务器 $TEST_HOST"
echo "  分支: $(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD)"
echo "  Commit: $(git -C "$PROJECT_DIR" rev-parse --short HEAD)"
echo "=========================================="

# 步骤 1：后端语法检查（可跳过）
if [ "$SKIP_CHECK" = false ] && [ "$FRONTEND_ONLY" = false ]; then
    echo "[1/4] 后端语法检查..."
    cd "$PROJECT_DIR/portal/backend"
    python3 -m compileall -q -d . -x '/\.venv/' .
    echo "  ✅ 语法检查通过"
else
    echo "[1/4] 跳过语法检查"
fi

# 步骤 2：同步代码
echo "[2/4] 同步代码到 $TEST_HOST..."
cd "$PROJECT_DIR"
rsync -az --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='dist' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    --exclude='portal/frontend/dist' \
    --exclude='portal/backend/.venv' \
    --exclude='drivers' \
    --exclude='datax' \
    --exclude='.env' \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    "$PROJECT_DIR/" \
    "$TEST_USER@$TEST_HOST:$TEST_DIR/"
echo "  ✅ 同步完成"

# 步骤 3：构建并重启（根据参数选择构建目标）
echo "[3/4] 构建并启动服务..."

BUILD_ARGS=""
if [ "$FORCE_REBUILD" = true ]; then
    echo "  强制全量重建（--force 模式）"
    BUILD_ARGS="--no-cache"
fi

# 确定构建目标
BUILD_TARGETS="portal-frontend portal-backend"
STOP_SERVICES="portal-frontend portal-backend nginx"
if [ "$BACKEND_ONLY" = true ]; then
    BUILD_TARGETS="portal-backend"
    STOP_SERVICES="portal-backend"
    echo "  仅部署后端"
elif [ "$FRONTEND_ONLY" = true ]; then
    BUILD_TARGETS="portal-frontend"
    STOP_SERVICES="portal-frontend nginx"
    echo "  仅部署前端"
fi

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$TEST_USER@$TEST_HOST" "
    set -e
    cd $TEST_DIR

    docker compose build $BUILD_ARGS $BUILD_TARGETS

    docker compose stop $STOP_SERVICES 2>/dev/null || true
    docker compose up -d
"
echo "  ✅ 服务已启动"

# 步骤 4：健康检查
echo "[4/4] 健康检查..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$TEST_USER@$TEST_HOST" "
    set -e
    cd $TEST_DIR
    for i in \$(seq 1 20); do
        if curl -sf http://localhost:8888/ > /dev/null 2>&1; then
            echo '  ✅ 服务已就绪'
            exit 0
        fi
        sleep 3
    done
    echo '  ❌ 服务未在 60 秒内就绪'
    docker compose ps --format 'table {{.Name}}\t{{.Status}}'
    exit 1
"

echo ""
echo "=========================================="
echo "  ✅ 部署完成: http://$TEST_HOST:8888"
echo "=========================================="
