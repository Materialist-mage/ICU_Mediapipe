# -*- coding: utf-8 -*-
# config.py: 系统配置管理模块
#
# 本模块负责管理系统的所有配置参数，包括：
# - 摄像头配置（分辨率、ROI区域、检测阈值等）
# - 系统参数（性能指标、显示选项等）
# - 报警设置（触发阈值、音频文件等）
# - 日志配置（文件路径、大小限制等）

import logging
import os
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
import sys
from typing import Dict, List, Tuple, Optional

@dataclass
class CameraConfig:
    """摄像头配置类
    
    Attributes:
        source: 视频源（摄像头ID或视频文件路径）
        roi: 感兴趣区域，格式为 {"x": int, "y": int, "w": int, "h": int}
        min_confidence: 手势检测的最小置信度阈值
        resolution: 视频分辨率，格式为 (width, height)
        enabled: 是否启用该摄像头
        buffer_size: 视频缓冲区大小（帧数）
        auto_reconnect: 断开连接后是否自动重连
        reconnect_delay: 重连等待时间（秒）
    """
    source: int
    roi: dict
    min_confidence: float
    resolution: tuple
    enabled: bool = True
    buffer_size: int = 3
    auto_reconnect: bool = True
    reconnect_delay: float = 1.0

class SystemConfig:
    """系统配置类
    
    负责管理所有系统级配置参数，包括摄像头设置、界面选项、报警参数等。
    提供配置验证和日志设置功能。
    """
    
    def __init__(self):
        # 摄像头配置列表
        self.cameras: List[CameraConfig] = [
            CameraConfig(
                source=0,
                roi={"x": 200, "y": 100, "w": 800, "h": 600},
                min_confidence=0.8,
                resolution=(1280, 720)
            ),
            CameraConfig(
                source=1,
                roi={"x": 200, "y": 100, "w": 800, "h": 600},
                min_confidence=0.5,
                resolution=(1280, 720)
            )
        ]
        
        # 界面设置
        self.font_path: str = "simhei.ttf"
        self.font_size: int = 24
        self.show_fps: bool = True
        self.show_roi: bool = True
        self.window_title: str = "ICU手部行为监测系统 v2.8"
        self.status_update_interval: float = 1.0  # 状态更新间隔（秒）
        
        # 手势检测参数
        self.gesture_threshold: float = 0.8
        self.detection_interval: float = 0.1  # 检测间隔（秒）
        self.smooth_factor: float = 0.3  # 平滑因子（0-1）
        
        # 报警设置
        self.alarm_triggers: List[int] = [5, 10, 15, 30]
        self.alarm_sounds: Dict[int, str] = {
            t: f"sounds/{t}S报警音.wav" if t < 30 else "sounds/alarm.wav"
            for t in self.alarm_triggers
        }
        self.fallback_sound: str = "sounds/fallback_beep.wav"
        self.alarm_volume: float = 1.0  # 音量（0-1）
        
        # 日志设置
        self.log_file: str = os.path.join("logs", "system.log")
        self.log_max_size: int = 10 * 1024 * 1024  # 10MB
        self.log_backup_count: int = 5
        self.log_level: int = logging.INFO
        
        # 性能优化参数
        self.thread_pool_size: int = 4
        self.frame_buffer_size: int = 3
        self.max_fps: Optional[int] = None  # None表示不限制

    def validate(self) -> None:
        """验证所有配置参数的有效性
        
        检查项包括：
        - ROI区域是否在有效范围内
        - 音频文件是否存在
        - 字体文件是否可用
        - 其他参数的合理性
        
        Raises:
            ValueError: 当配置参数无效时抛出
        """
        # 验证摄像头配置
        for i, cam in enumerate(self.cameras):
            if not (0 <= cam.roi["x"] < cam.resolution[0] and 
                    0 <= cam.roi["y"] < cam.resolution[1]):
                raise ValueError(f"摄像头{cam.source} ROI 超出分辨率范围")
            
            if not (0 < cam.min_confidence <= 1):
                raise ValueError(f"摄像头{cam.source} 置信度阈值必须在0-1之间")
        
        # 验证音频文件
        for path in self.alarm_sounds.values():
            if not os.path.exists(path):
                logging.warning(f"音频文件 {path} 不存在")
        
        # 验证字体文件
        if not os.path.exists(self.font_path):
            logging.warning(f"字体文件 {self.font_path} 不存在，将使用默认字体")
        
        # 验证其他参数
        if not (0 < self.gesture_threshold <= 1):
            raise ValueError("手势检测阈值必须在0-1之间")
        
        if not (0 < self.alarm_volume <= 1):
            raise ValueError("音量必须在0-1之间")

# 全局配置实例
CONFIG = SystemConfig()

def setup_logging() -> None:
    """配置日志系统
    
    设置日志格式、输出位置和级别，包括：
    - 文件日志（带大小限制和备份）
    - 控制台输出
    - 第三方库日志级别调整
    """
    # 创建日志目录
    os.makedirs(os.path.dirname(CONFIG.log_file), exist_ok=True)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置文件处理器
    file_handler = RotatingFileHandler(
        CONFIG.log_file,
        maxBytes=CONFIG.log_max_size,
        backupCount=CONFIG.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(CONFIG.log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('mediapipe').setLevel(logging.WARNING)
    logging.getLogger('pygame').setLevel(logging.WARNING)

# 系统初始化
os.makedirs("sounds", exist_ok=True)
os.makedirs("logs", exist_ok=True)
setup_logging()
CONFIG.validate()

logging.info("系统配置初始化完成")