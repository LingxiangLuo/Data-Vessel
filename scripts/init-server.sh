#!/bin/bash
# ============================================
# 服务器初始化脚本
# 目标: Ubuntu 22.04, 8C/14GB/49GB
# ============================================
set -e

echo "=========================================="
echo "  数据中台 MVP - 服务器初始化"
echo "=========================================="

# 1. 系统更新 & 基础工具
echo "[1/6] 安装基础工具..."
apt-get update -qq
apt-get install -y -qq curl wget vim htop net-tools unzip > /dev/null 2>&1

# 2. 配置 Swap
echo "[2/6] 配置 Swap..."
if [ -f /opt/data-platform-mvp/scripts/setup-swap.sh ]; then
    bash /opt/data-platform-mvp/scripts/setup-swap.sh
else
    if ! swapon --show | grep -q '/swapfile'; then
        fallocate -l 8G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        sysctl vm.swappiness=10
        echo 'vm.swappiness=10' >> /etc/sysctl.conf
        echo "Swap 8GB 已创建"
    else
        echo "Swap 已存在，跳过"
    fi
fi

# 3. Docker 日志限制
echo "[3/6] 配置 Docker 日志限制..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "default-ulimits": {
        "nofile": {
            "Name": "nofile",
            "Hard": 65535,
            "Soft": 65535
        }
    }
}
EOF
systemctl restart docker

# 4. 系统参数优化
echo "[4/6] 优化系统参数..."
cat >> /etc/sysctl.conf << 'EOF'
# 数据中台优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
vm.overcommit_memory = 1
fs.file-max = 655350
fs.inotify.max_user_watches = 524288
EOF
sysctl -p > /dev/null 2>&1

# 5. 文件描述符限制
echo "[5/6] 配置文件描述符限制..."
cat >> /etc/security/limits.conf << 'EOF'
* soft nofile 655350
* hard nofile 655350
* soft nproc 655350
* hard nproc 655350
EOF

# 6. 防火墙 (ufw)
echo "[6/6] 配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp > /dev/null 2>&1 || true
    ufw allow 80/tcp > /dev/null 2>&1 || true
    ufw allow 443/tcp > /dev/null 2>&1 || true
    # 开发调试端口 (可选关闭)
    ufw allow 12345/tcp > /dev/null 2>&1 || true  # DS
    ufw allow 8585/tcp > /dev/null 2>&1 || true   # OM
    echo "防火墙规则已添加"
else
    echo "ufw 未安装，跳过防火墙配置"
fi

echo ""
echo "=========================================="
echo "  服务器初始化完成！"
echo "=========================================="
echo "Swap: $(swapon --show | grep swapfile | awk '{print $3}')"
echo "Docker: $(docker --version)"
echo "内存: $(free -h | awk '/Mem:/{print $2}')"
echo "CPU: $(nproc) 核"
echo "磁盘: $(df -h / | awk 'NR==2{print $4}') 可用"
echo "=========================================="
