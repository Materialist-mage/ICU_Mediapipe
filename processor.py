# -*- coding: utf-8 -*-
# processor.py: 处理视频流、手势检测、报警逻辑和摄像头管理
# 此文件作为兼容层，从modules包中导入所需的类

# 从模块化结构中导入所有类
from modules import VideoProcessor, FPSCounter, CameraManager

# 重新导出这些类，保持与原始processor.py相同的接口
__all__ = ['VideoProcessor', 'FPSCounter', 'CameraManager']