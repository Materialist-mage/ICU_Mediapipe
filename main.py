# -*- coding: utf-8 -*-
# main.py: 系统启动入口

import os
import logging
import numpy as np
import wave
import pygame
from config import CONFIG
from modules.ui import ControlPanel


if __name__ == '__main__':
    try:
        # 确保备用音频文件存在
        if not os.path.exists(CONFIG.fallback_sound):
            logging.info("创建备用音频文件")
            sample_rate = 44100
            duration = 0.5
            t = np.linspace(0, duration, int(sample_rate * duration))
            data = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
            with wave.open(CONFIG.fallback_sound, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(data.tobytes())
        
        # 初始化音频系统
        pygame.init()
        logging.info("系统启动中...")
        
        # 启动应用
        app = ControlPanel()
        app.run()
    except Exception as e:
        logging.critical(f"系统崩溃: {str(e)}")
        from tkinter import messagebox
        messagebox.showerror("致命错误", f"系统发生不可恢复错误: {str(e)}")