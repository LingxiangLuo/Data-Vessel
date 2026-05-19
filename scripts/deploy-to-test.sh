#!/usr/bin/env bash
set -e

TEST_HOST="192.168.1.3"
TEST_USER="root"
TEST_DIR="/opt/data-platform-mvp"
SSH_KEY="$HOME/.ssh/test_server_key"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FORCE_REBUILD="${1:-}"

echo "=========================================="
echo "  部署到测试服务器 $TEST_HOST"
echo "  分支: $(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD)"
echo "  Commit: $(git -C "$PROJECT_DIR" rev-parse --short HEAD)"
echo "=========================================="

# 1. 后端语法检查
echo "[1/4] 后端语法检查..."
cd "$PROJECT_DIR/portal/backend"
find . -name "*.py" -not -path "./.venv/*" | xargs python3 -m py_compile
echo "  ✅ 语法检查通过"

# 2. 同步代码
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

# 3. 构建并重启
echo "[3/4] 构建并启动服务..."
BUILD_ARGS=""
if [ "$FORCE_REBUILD" = "--force" ]; then
    echo "  强制全量重建（--force 模式）"
    BUILD_ARGS="--no-cache"
fi

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$TEST_USER@$TEST_HOST" "
    set -e
    cd $TEST_DIR

    docker compose build $BUILD_ARGS portal-frontend portal-backend

    docker compose stop portal-frontend portal-backend nginx 2>/dev/null || true
    docker compose up -d

    echo '等待服务就绪...'
    for i in \$(seq 1 20); do
        if curl -sf http://localhost:8888/ > /dev/null 2>&1; then
            echo '  ✅ 服务已就绪'
            break
        fi
        sleep 3
    done

    docker compose ps --format 'table {{.Name}}\t{{.Status}}'
"

echo ""
echo "=========================================="
echo "  ✅ 部署完成: http://$TEST_HOST:8888"
echo "=========================================="
