# -*- coding: utf-8 -*-
# modules/fps_counter.py
# FPS计数器模块

import numpy as np

class FPSCounter:
    """FPS计数器类，用于计算和平滑帧率显示
    
    主要功能：
    - 记录最近的帧率历史
    - 计算平均帧率用于显示
    """

    def __init__(self):
        """初始化FPS计数器"""
        self.fps_history = []

    def update(self, fps):
        """更新帧率历史
        
        Args:
            fps: 当前帧率
        """
        self.fps_history.append(fps)
        if len(self.fps_history) > 10:
            self.fps_history.pop(0)

    def get_average(self):
        """获取平均帧率
        
        Returns:
            float: 平均帧率
        """
        return np.mean(self.fps_history) if self.fps_history else 0