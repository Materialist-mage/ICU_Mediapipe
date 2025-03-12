#!/bin/bash

# 确保Docker服务正在运行
service docker status > /dev/null 2>&1 || sudo service docker start

# 构建Docker镜像
echo "构建Docker镜像..."
docker build -t icu-mediapipe .

# 获取当前用户的UID和GID
USER_UID=$(id -u)
USER_GID=$(id -g)

# 获取音频组ID
AUDIO_GID=$(getent group audio | cut -d: -f3)

# 启动Docker容器
echo "启动容器..."
docker run -it --rm \
  --device=/dev/video0:/dev/video0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /dev/snd:/dev/snd \
  -v "$(pwd)/logs:/app/logs" \
  -e DISPLAY=$DISPLAY \
  -e PULSE_SERVER=unix:/run/user/$USER_UID/pulse/native \
  --group-add $AUDIO_GID \
  icu-mediapipe

echo "容器已启动！"