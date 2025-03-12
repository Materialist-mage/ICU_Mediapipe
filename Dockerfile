# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpulse0 \
    pulseaudio \
    x11-apps \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# 创建必要的目录
RUN mkdir -p /tmp/.X11-unix && \
    mkdir -p /dev/video0 && \
    mkdir -p /dev/snd

# 创建非root用户
RUN useradd -m -s /bin/bash appuser \
    && chown -R appuser:appuser /app

# 复制项目文件
COPY --chown=appuser:appuser . /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0
ENV PULSE_SERVER=unix:/run/user/1000/pulse/native

# 创建日志目录并设置权限
RUN mkdir -p /app/logs \
    && chown -R appuser:appuser /app/logs

# 切换到非root用户
USER appuser

# 容器运行说明
# 使用以下命令运行容器：
# docker run -it --rm \
#   --device=/dev/video0:/dev/video0 \
#   -v /tmp/.X11-unix:/tmp/.X11-unix \
#   -v /dev/snd:/dev/snd \
#   -v ${PWD}/logs:/app/logs \
#   -e DISPLAY=${DISPLAY} \
#   -e PULSE_SERVER=unix:/run/user/1000/pulse/native \
#   --group-add $(getent group audio | cut -d: -f3) \
#   icu-mediapipe

# 启动命令
CMD ["python", "main.py"]