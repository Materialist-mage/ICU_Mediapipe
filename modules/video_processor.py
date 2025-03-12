# -*- coding: utf-8 -*-
# modules/video_processor.py
# 视频处理器模块

import cv2
import mediapipe as mp
import pygame
import time
import numpy as np
import logging
import traceback
import os
import wave
from threading import Event
from config import CONFIG

# 导入FPSCounter类，使用相对导入
from .fps_counter import FPSCounter

class VideoProcessor:
    """视频处理器类，负责摄像头视频流的处理、手势检测和报警控制。

    主要功能：
    - 实时视频流处理和手势识别
    - 多级报警机制
    - 自动重连和错误恢复
    - 资源管理和释放
    """

    def __init__(self, camera_id: int, stop_event: Event):
        """初始化视频处理器

        Args:
            camera_id: 摄像头ID
            stop_event: 停止事件，用于控制处理器的运行状态
        """
        try:
            self.camera_id = camera_id
            self.config = CONFIG.cameras[camera_id]
            self.stop_event = stop_event
            self.detection_start_time = 0
            self.last_detection = 0
            self.alarm_active = False
            self.played_sounds = set()
            self.fps_counter = FPSCounter()
            self._verify_resources()
            self._init_components()
            logging.info(f"摄像头{camera_id}初始化完成")
        except Exception as e:
            logging.error(f"摄像头{camera_id}初始化失败: {str(e)}\n{traceback.format_exc()}")
            raise

    def _verify_resources(self):
        """验证所需资源文件是否存在，如不存在则生成备用资源"""
        try:
            for path in CONFIG.alarm_sounds.values():
                if not os.path.exists(path):
                    logging.warning(f"缺少音频文件: {path}")
            if not os.path.exists(CONFIG.fallback_sound):
                self._generate_fallback_beep(CONFIG.fallback_sound)
        except Exception as e:
            logging.error(f"资源验证失败: {str(e)}")
            raise

    def _generate_fallback_beep(self, filename):
        """生成备用警报音频文件
        
        Args:
            filename: 音频文件保存路径
        """
        sample_rate = 44100
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        data = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(data.tobytes())

    def _init_components(self):
        """初始化各个组件，包括MediaPipe、摄像头和音频系统"""
        try:
            # 初始化MediaPipe，使用更高效的配置
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,  # 视频模式
                max_num_hands=1,  # 减少为1只手，提高性能
                min_detection_confidence=self.config.min_confidence,
                min_tracking_confidence=0.5,
                model_complexity=0  # 使用最轻量级模型
            )
            
            # 初始化摄像头
            self.cap = self._init_capture()
            # 设置摄像头缓冲区大小，减少延迟
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.config.buffer_size)
            
            # 初始化音频系统
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.alarm_sounds = {}
            self.alarm_channel = pygame.mixer.Channel(self.camera_id)
            self._load_alarm_sounds()
            
            # 初始化性能监控变量
            self._last_fps_update = 0
            self._cached_fps = 0
            
        except Exception as e:
            logging.error(f"组件初始化失败: {str(e)}")
            # 添加自定义异常类以便更好地处理错误
            class ResourceError(Exception):
                def __init__(self, message, code=1000):
                    self.message = message
                    self.code = code
                    super().__init__(self.message)
            
            error_msg = f"组件初始化失败: {str(e)}"
            raise ResourceError(error_msg, 1003) from e
            
    def _init_capture(self):
        """初始化摄像头捕获对象
        
        Returns:
            cv2.VideoCapture: 初始化后的摄像头对象
            
        Raises:
            RuntimeError: 当无法打开视频源时抛出
        """
        source = self.config.source
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logging.error(f"无法打开视频源: {source}")
            raise RuntimeError(f"无法打开视频源: {source}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if actual_width != self.config.resolution[0] or actual_height != self.config.resolution[1]:
            logging.warning(f"摄像头{source} 分辨率设置失败，实际: ({actual_width}, {actual_height})")
        return cap
            
    def _load_alarm_sounds(self):
        """加载报警音频文件"""
        for duration, path in CONFIG.alarm_sounds.items():
            try:
                self.alarm_sounds[duration] = pygame.mixer.Sound(path)
            except FileNotFoundError:
                logging.warning(f"加载 {path} 失败，使用备用音")
                self.alarm_sounds[duration] = pygame.mixer.Sound(CONFIG.fallback_sound)
            except Exception as e:
                logging.error(f"加载音频失败: {str(e)}")
                raise

    def process_stream(self):
        """处理视频流的主循环"""
        try:
            prev_time = time.time()
            frame_count = 0
            skip_count = 0
            target_interval = 1.0 / 30 if CONFIG.max_fps is None else 1.0 / CONFIG.max_fps  # 目标帧间隔时间
            
            with self.hands:
                while not self.stop_event.is_set():
                    try:
                        # 帧率控制 - 如果距离上一帧时间太短，则等待
                        current_time = time.time()
                        elapsed = current_time - prev_time
                        if elapsed < target_interval:
                            # 使用短暂睡眠而不是忙等待，减少CPU占用
                            sleep_time = target_interval - elapsed
                            if sleep_time > 0.001:  # 避免过短的睡眠
                                time.sleep(sleep_time)
                            continue
                            
                        # 读取帧
                        ret, frame = self.cap.read()
                        if not ret:
                            self._handle_stream_error()
                            continue
                            
                        # 跳帧处理 - 在高负载时跳过部分帧的处理
                        frame_count += 1
                        if frame_count % (skip_count + 1) != 0:
                            # 即使跳过处理，也要显示原始帧以保持流畅
                            self._display_frame(frame)
                            continue
                            
                        # 动态调整跳帧数量 - 根据处理时间自适应
                        if elapsed > 2 * target_interval and skip_count < 2:
                            skip_count += 1
                            logging.debug(f"性能优化: 增加跳帧数量至 {skip_count}")
                        elif elapsed < target_interval * 0.8 and skip_count > 0:
                            skip_count -= 1
                            logging.debug(f"性能优化: 减少跳帧数量至 {skip_count}")
                            
                        # 处理帧
                        processed_frame = self._process_frame(frame)
                        self._display_frame(processed_frame)
                        
                        # 更新FPS计数
                        current_time = time.time()
                        self.fps_counter.update(1 / (current_time - prev_time))
                        prev_time = current_time
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    except Exception as e:
                        logging.error(f"帧处理错误: {str(e)}")
                        continue
        except Exception as e:
            logging.error(f"视频流处理错误: {str(e)}\n{traceback.format_exc()}")
        finally:
            self._release_resources()

    def _process_frame(self, frame):
        """处理单帧图像

        Args:
            frame: 原始图像帧

        Returns:
            处理后的图像帧
        """
        # 避免不必要的复制，直接在原始帧上操作
        roi_frame = self._safe_crop(frame)
        
        # 检查是否需要进行手势检测（基于时间间隔）
        current_time = time.time()
        should_detect = (current_time - self.last_detection) >= CONFIG.detection_interval
        
        if should_detect:
            # 转换颜色空间并进行手势检测
            rgb_frame = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            gesture_detected = self._detect_gesture(results)

            if gesture_detected:
                self.last_detection = current_time
                self._update_alarm_state()
                self._draw_landmarks(frame, results)
            else:
                self._reset_alarm()
        
        # 添加叠加信息（ROI框、FPS等）
        self._add_overlay(frame)
        return frame

    def _safe_crop(self, frame):
        """安全裁剪图像，确保ROI在图像范围内
        
        Args:
            frame: 原始图像
            
        Returns:
            裁剪后的ROI区域图像
        """
        # 使用缓存的ROI坐标，避免每帧重新计算
        if not hasattr(self, '_cached_roi_coords'):
            h, w = frame.shape[:2]
            roi = self.config.roi
            x1 = max(0, min(roi["x"], w - 1))
            y1 = max(0, min(roi["y"], h - 1))
            x2 = min(x1 + roi["w"], w)
            y2 = min(y1 + roi["h"], h)
            self._cached_roi_coords = (y1, y2, x1, x2)
        
        y1, y2, x1, x2 = self._cached_roi_coords
        return frame[y1:y2, x1:x2]

    def _detect_gesture(self, results):
        """检测特定手势（拇指和小指靠近）
        
        Args:
            results: MediaPipe手部检测结果
            
        Returns:
            bool: 是否检测到目标手势
        """
        # 快速路径：如果没有检测到手，直接返回False
        if not results.multi_hand_landmarks:
            return False
            
        # 只检查第一只检测到的手（因为我们设置了max_num_hands=1）
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # 只获取需要的关键点，避免不必要的计算
        thumb = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        pinky = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        
        # 使用曼哈顿距离计算，比欧氏距离计算更快
        distance = abs(thumb.x - pinky.x) + abs(thumb.y - pinky.y)
        
        # 应用平滑因子，减少抖动
        if not hasattr(self, '_last_distance'):
            self._last_distance = distance
        else:
            # 平滑处理，减少误触发
            distance = CONFIG.smooth_factor * distance + (1 - CONFIG.smooth_factor) * self._last_distance
            self._last_distance = distance
            
        return distance < CONFIG.gesture_threshold

    def _update_alarm_state(self):
        """更新报警状态，根据检测持续时间触发不同级别的报警"""
        current_time = time.time()
        if self.detection_start_time == 0:
            self.detection_start_time = current_time
            self.played_sounds.clear()
            logging.debug(f"Camera {self.camera_id} 开始计时")
        detection_duration = current_time - self.detection_start_time
        logging.debug(f"Camera {self.camera_id} 检测时长: {detection_duration:.1f}秒")

        for duration in sorted(CONFIG.alarm_triggers):
            if detection_duration >= duration and duration not in self.played_sounds:
                logging.info(f"Camera {self.camera_id} 触发 {duration}秒 报警")
                self.alarm_active = True
                self._trigger_alarm(duration, continuous=(duration == CONFIG.alarm_triggers[-1]))
                self.played_sounds.add(duration)

    def _trigger_alarm(self, duration, continuous=False):
        """触发报警声音
        
        Args:
            duration: 报警触发的时长级别
            continuous: 是否持续播放
        """
        if not self.alarm_channel.get_busy():
            loops = -1 if continuous else 0
            self.alarm_channel.play(self.alarm_sounds[duration], loops=loops)

    def _reset_alarm(self):
        """重置报警状态"""
        if self.detection_start_time > 0:
            logging.debug(f"Camera {self.camera_id} 检测到手部消失，立即重置状态")
        self.detection_start_time = 0
        self.alarm_active = False
        self.played_sounds.clear()
        self.alarm_channel.stop()

    def _draw_landmarks(self, frame, results):
        """在图像上绘制手部关键点
        
        Args:
            frame: 图像帧
            results: MediaPipe手部检测结果
        """
        # 如果没有检测到手，直接返回
        if not results.multi_hand_landmarks:
            return
            
        # 使用简化的绘制样式，减少计算量
        landmark_spec = mp.solutions.drawing_styles.get_default_hand_landmarks_style()
        connection_spec = mp.solutions.drawing_styles.get_default_hand_connections_style()
        
        # 只绘制第一只检测到的手（因为我们设置了max_num_hands=1）
        mp.solutions.drawing_utils.draw_landmarks(
            frame,
            results.multi_hand_landmarks[0],
            self.mp_hands.HAND_CONNECTIONS,
            landmark_drawing_spec=landmark_spec,
            connection_drawing_spec=connection_spec
        )

    def _add_overlay(self, frame):
        """添加图像叠加信息（ROI框、FPS等）
        
        Args:
            frame: 图像帧
        """
        # 仅在需要时绘制ROI框
        if CONFIG.show_roi:
            # 使用缓存的ROI坐标
            if hasattr(self, '_cached_roi_coords'):
                y1, y2, x1, x2 = self._cached_roi_coords
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            else:
                roi = self.config.roi
                cv2.rectangle(frame, (roi["x"], roi["y"]), (roi["x"] + roi["w"], roi["y"] + roi["h"]), (0, 255, 0), 2)
        
        # 仅在需要时显示FPS，并减少更新频率
        if CONFIG.show_fps and hasattr(self, '_last_fps_update'):
            current_time = time.time()
            if current_time - self._last_fps_update >= 0.5:  # 每0.5秒更新一次FPS显示
                self._cached_fps = int(self.fps_counter.get_average())
                self._last_fps_update = current_time
        else:
            self._cached_fps = int(self.fps_counter.get_average())
            self._last_fps_update = time.time()
            
        if CONFIG.show_fps:
            cv2.putText(frame, f"FPS: {self._cached_fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    def _display_frame(self, frame):
        """显示处理后的图像帧
        
        Args:
            frame: 处理后的图像帧
        """
        # 检查是否需要调整大小
        h, w = frame.shape[:2]
        if w != 1280 or h != 720:
            # 使用INTER_NEAREST插值方法，速度更快
            display_frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_NEAREST)
        else:
            display_frame = frame
            
        # 使用imshow显示图像
        cv2.imshow(f'Camera {self.camera_id}', display_frame)

    def _handle_stream_error(self):
        """处理视频流错误，尝试重新连接摄像头"""
        logging.warning(f"摄像头{self.camera_id} 断流，尝试重连...")
        self.cap.release()
        time.sleep(1)
        try:
            self.cap = cv2.VideoCapture(self.config.source)
            if not self.cap.isOpened():
                raise RuntimeError("摄像头打开失败")
            logging.info(f"摄像头{self.camera_id} 重连成功")
        except Exception as e:
            logging.error(f"摄像头{self.camera_id} 重连失败: {str(e)}")

    def _release_resources(self):
        """释放所有资源"""
        try:
            self.cap.release()
            self.hands.close()
            pygame.mixer.quit()
            cv2.destroyAllWindows()
            logging.info(f"摄像头{self.camera_id} 资源已释放")
        except Exception as e:
            logging.error(f"资源释放失败: {str(e)}")
            
    def get_detection_duration(self):
        """Get current detection duration
        
        Returns:
            float: Detection duration in seconds
        """
        if self.detection_start_time > 0:
            return time.time() - self.detection_start_time
        return 0

    def get_status(self):
        """Get current camera status
        
        Returns:
            dict: Status information including fps, detection time, and alarm level
        """
        status = {
            'status': self.get_alarm_status(),
            'fps': self.fps_counter.get_average(),
            'detection_time': self.get_detection_duration(),
            'alarm_level': len(self.played_sounds)
        }
        return status

    def get_alarm_status(self):
        if self.alarm_active and self.played_sounds:
            last_played = max(self.played_sounds)
            if last_played == CONFIG.alarm_triggers[-1]:
                return f"持续报警 ({last_played}秒)"
            return f"报警触发 ({last_played}秒)"
        elif self.detection_start_time > 0:
            return "检测中"
        return "无报警"
        
    def update_roi(self):
        """更新ROI设置，从CONFIG重新加载当前摄像头的ROI配置"""
        # 更新配置对象引用
        self.config = CONFIG.cameras[self.camera_id]
        # 确保更新后的ROI设置被正确应用
        if hasattr(self, 'hands') and self.hands:
            # 如果需要，可以根据新的ROI设置更新手部检测参数
            self.hands.min_detection_confidence = self.config.min_confidence
            
        # 验证ROI设置的有效性
        roi = self.config.roi
        if roi['x'] < 0 or roi['y'] < 0 or roi['w'] <= 0 or roi['h'] <= 0:
            logging.warning(f"摄像头{self.camera_id} ROI设置无效: {roi}")
            return False
            
        # 检查ROI是否超出摄像头分辨率范围
        if self.cap and self.cap.isOpened():
            frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if roi['x'] + roi['w'] > frame_width or roi['y'] + roi['h'] > frame_height:
                logging.warning(f"摄像头{self.camera_id} ROI设置超出范围: {roi}, 摄像头分辨率: {frame_width}x{frame_height}")
                # 自动调整ROI以适应摄像头分辨率
                self.config.roi['x'] = min(roi['x'], frame_width - 1)
                self.config.roi['y'] = min(roi['y'], frame_height - 1)
                self.config.roi['w'] = min(roi['w'], frame_width - self.config.roi['x'])
                self.config.roi['h'] = min(roi['h'], frame_height - self.config.roi['y'])
                logging.info(f"摄像头{self.camera_id} ROI已自动调整为: {self.config.roi}")
        
        # 记录日志
        logging.info(f"摄像头{self.camera_id} ROI设置已更新: {self.config.roi}")
        return True