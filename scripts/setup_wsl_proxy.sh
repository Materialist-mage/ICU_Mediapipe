#!/bin/bash

# 获取Windows主机IP地址
WIN_IP=$(ip route | grep default | awk '{print $3}')

# 设置代理环境变量
export http_proxy="http://${WIN_IP}:7890"
export https_proxy="http://${WIN_IP}:7890"

# 将代理设置添加到.bashrc以持久化
echo "\n# Proxy Settings" >> ~/.bashrc
echo "export http_proxy=\"http://${WIN_IP}:7890\"" >> ~/.bashrc
echo "export https_proxy=\"http://${WIN_IP}:7890\"" >> ~/.bashrc

# 配置Git代理
git config --global http.proxy "http://${WIN_IP}:7890"
git config --global https.proxy "http://${WIN_IP}:7890"

echo "WSL2代理配置完成！"
echo "当前代理设置："
echo "http_proxy=${http_proxy}"
echo "https_proxy=${https_proxy}"