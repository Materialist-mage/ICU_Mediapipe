# -*- coding: utf-8 -*-
# modules/camera_manager.py
# 摄像头管理器模块

import logging
from threading import Thread, Event
from config import CONFIG

# 导入VideoProcessor类，这里使用相对导入
from .video_processor import VideoProcessor

class CameraManager:
    """摄像头管理器类，负责管理多个摄像头的生命周期
    
    主要功能：
    - 创建和管理VideoProcessor实例
    - 控制摄像头的启动和停止
    - 提供摄像头状态查询接口
    """
    
    def __init__(self):
        """初始化摄像头管理器"""
        self.processors = {}
        self.stop_events = {}
        self.threads = {}
        
    def start_camera(self, camera_id):
        """启动指定摄像头
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            bool: 启动是否成功
            
        Raises:
            ValueError: 当摄像头ID无效时
            RuntimeError: 当摄像头已在运行或初始化失败时
        """
        if not isinstance(camera_id, int) or camera_id < 0:
            logging.error(f"无效的摄像头ID: {camera_id}")
            raise ValueError(f"无效的摄像头ID: {camera_id}")
            
        if camera_id in self.processors:
            logging.warning(f"摄像头{camera_id}已在运行")
            raise RuntimeError(f"摄像头{camera_id}已在运行")
            
        try:
            if camera_id >= len(CONFIG.cameras):
                raise ValueError(f"摄像头{camera_id}未配置")
                
            stop_event = Event()
            processor = VideoProcessor(camera_id, stop_event)
            thread = Thread(target=processor.process_stream)
            
            self.processors[camera_id] = processor
            self.stop_events[camera_id] = stop_event
            self.threads[camera_id] = thread
            
            thread.start()
            return True
        except Exception as e:
            logging.error(f"启动摄像头{camera_id}失败: {str(e)}")
            return False
            
    def stop_camera(self, camera_id):
        """停止指定摄像头
        
        Args:
            camera_id: 摄像头ID
        """
        if camera_id in self.stop_events:
            self.stop_events[camera_id].set()
            if camera_id in self.threads:
                self.threads[camera_id].join()
                del self.threads[camera_id]
            if camera_id in self.processors:
                del self.processors[camera_id]
            del self.stop_events[camera_id]
            
    def stop_all(self):
        """停止所有摄像头"""
        for camera_id in list(self.stop_events.keys()):
            self.stop_camera(camera_id)
            
    def get_processor(self, camera_id):
        """获取指定摄像头的处理器
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            VideoProcessor: 摄像头处理器实例
        """
        return self.processors.get(camera_id)