#!/bin/bash
# ============================================
# Swap 配置脚本 - 8GB
# ============================================
set -e

echo "=== 配置 8GB Swap ==="

# 检查是否已有 swap
if swapon --show | grep -q '/swapfile'; then
    echo "Swap 已存在，跳过"
    swapon --show
    exit 0
fi

# 创建 swap 文件
fallocate -l 8G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# 持久化
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 调整 swappiness
sysctl vm.swappiness=10
if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi

echo "=== Swap 配置完成 ==="
swapon --show
free -h
