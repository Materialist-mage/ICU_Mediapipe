# -*- coding: utf-8 -*-
# modules/ui/control_panel.py
# 控制面板模块，负责系统的图形用户界面和用户交互

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import datetime
import sv_ttk

from config import CONFIG
from processor import CameraManager
from .components import (
    TimeDisplay,
    ThemeSelector,
    CameraSelector,
    SettingsPanel,
    ControlButtons,
    StatusDisplay
)

class ControlPanel:
    """控制面板类，负责系统的图形用户界面和用户交互。
    
    主要功能：
    - 提供摄像头选择和控制界面
    - 显示摄像头状态和报警信息
    - 处理用户交互事件
    
    此类使用组件化设计，将UI元素拆分为多个独立组件，提高代码可维护性。
    """
    def __init__(self):
        """初始化控制面板"""
        try:
            self.root = tk.Tk()
            self.root.title(CONFIG.window_title)
            self.root.geometry("800x1200")  # 增加窗口高度以适应新增的控件
            self.manager = CameraManager()
            self._setup_ui()
            self._center_window()
            self._start_status_update()
            logging.info("控制面板初始化完成")
        except Exception as e:
            logging.critical(f"控制面板初始化失败: {str(e)}")
            messagebox.showerror("初始化错误", f"系统初始化失败: {str(e)}")
            raise
            
    def _center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"+{x}+{y}")
        
    def _setup_ui(self):
        """设置用户界面组件"""
        try:
            # 应用Sun Valley主题
            sv_ttk.set_theme("light")
            self.current_theme = "light"
            
            # 创建主框架
            main_frame = ttk.Frame(self.root, padding=20)
            main_frame.pack(expand=True, fill=tk.BOTH)
            
            # 顶部工具栏
            toolbar = ttk.Frame(main_frame)
            toolbar.pack(fill=tk.X, pady=(0, 10))
            
            # 添加时间显示
            self.time_display = TimeDisplay(main_frame)
            self.time_display.pack(fill=tk.X, pady=(0, 10))
            
            # 添加主题切换按钮
            self.theme_selector = ThemeSelector(toolbar, callback=self._on_theme_change)
            self.theme_selector.pack(side=tk.RIGHT, padx=5)
            
            # 摄像头选择区域
            self.camera_selector = CameraSelector(main_frame)
            self.camera_selector.pack(fill=tk.X, pady=5)
            
            # 参数设置区域
            self.settings_panel = SettingsPanel(main_frame, apply_callback=self._apply_settings)
            self.settings_panel.pack(fill=tk.X, pady=5)
            
            # 控制按钮区域
            self.control_buttons = ControlButtons(
                main_frame,
                callbacks={
                    'start': self.start_selected,
                    'stop': self.stop_all,
                    'pause': self.pause_alarm,
                    'reset': self.reset_status
                }
            )
            self.control_buttons.pack(fill=tk.X, pady=5)
            
            # 状态显示区域
            self.status_display = StatusDisplay(main_frame)
            self.status_display.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # 绑定关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            
            logging.info("界面组件初始化完成")
        except Exception as e:
            logging.error(f"界面组件初始化失败: {str(e)}")
            raise
            
    def _on_theme_change(self, theme):
        """主题变更回调"""
        self.current_theme = theme
        
    def _apply_settings(self):
        """应用参数设置更新"""
        try:
            # 记录当前运行的摄像头
            running_cameras = []
            for cam_id in range(len(CONFIG.cameras)):
                if self.manager.get_processor(cam_id):
                    running_cameras.append(cam_id)
            
            # 获取设置面板的设置值
            settings = self.settings_panel.get_settings()
            
            # 更新手势检测灵敏度
            CONFIG.gesture_threshold = settings['gesture_threshold']
            
            # 更新报警间隔设置
            new_triggers = settings['alarm_triggers']
            if new_triggers:
                new_triggers.sort()
                CONFIG.alarm_triggers = new_triggers
                # 更新报警音频映射
                CONFIG.alarm_sounds = {
                    t: f"sounds/{t}S报警音.wav" if t < 30 else "sounds/alarm.wav"
                    for t in CONFIG.alarm_triggers
                }
            
            # 更新ROI设置 - 为每个摄像头单独更新
            roi_updated = False
            for cam_id, roi in settings['roi_settings'].items():
                CONFIG.cameras[cam_id].roi = roi
                roi_updated = True
            
            # 如果ROI设置已更新且有摄像头正在运行，询问用户是否重启摄像头
            if roi_updated and running_cameras:
                restart = messagebox.askyesno(
                    "应用ROI设置", 
                    "ROI设置已更新，是否重启摄像头以应用新设置？\n\n选择'是'将重启摄像头\n选择'否'将动态更新ROI设置（不中断监测）"
                )
                if restart:
                    # 停止所有运行的摄像头
                    self.manager.stop_all()
                    # 重新启动之前运行的摄像头
                    for cam_id in running_cameras:
                        try:
                            self.manager.start_camera(cam_id)
                            logging.info(f"摄像头 {cam_id} 已重启以应用新的ROI设置")
                        except Exception as e:
                            logging.error(f"重启摄像头 {cam_id} 失败: {str(e)}")
                            messagebox.showerror("重启错误", f"摄像头 {cam_id} 重启失败: {str(e)}")
                else:
                    # 动态更新ROI设置，不重启摄像头
                    update_success = True
                    failed_cameras = []
                    for cam_id in running_cameras:
                        processor = self.manager.get_processor(cam_id)
                        if processor:
                            if not processor.update_roi():
                                update_success = False
                                failed_cameras.append(cam_id)
                                logging.warning(f"摄像头 {cam_id} ROI设置动态更新失败")
                    
                    if update_success:
                        self.status_display.set_status_text("ROI设置已动态更新")
                        logging.info("ROI设置已动态更新，无需重启摄像头")
                    else:
                        if len(failed_cameras) == len(running_cameras):
                            # 所有摄像头更新失败
                            messagebox.showwarning("更新失败", "所有摄像头ROI设置更新失败，建议重启摄像头以应用新设置。")
                            self.status_display.set_status_text("ROI设置更新失败，请重启摄像头")
                            logging.warning("所有摄像头ROI设置更新失败")
                        else:
                            # 部分摄像头更新失败
                            failed_str = ", ".join([str(cam) for cam in failed_cameras])
                            messagebox.showwarning("部分更新", f"摄像头 {failed_str} 的ROI设置未能动态更新，建议重启这些摄像头以确保设置生效。")
                            self.status_display.set_status_text("ROI设置部分更新，建议重启部分摄像头")
                            logging.warning(f"摄像头 {failed_str} ROI设置更新失败")
            
            self.status_display.set_status_text("设置已更新")
            logging.info("参数设置已更新")
        except ValueError as e:
            messagebox.showerror("输入错误", "请确保所有输入都是有效的数字")
            logging.error(f"参数设置更新失败: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"更新设置失败: {str(e)}")
            logging.error(f"参数设置更新失败: {str(e)}")
            
    def start_selected(self):
        """启动选中的摄像头"""
        selected_cameras = self.camera_selector.get_selected()
        started_cameras = []
        
        for i in selected_cameras:
            try:
                self.manager.start_camera(i)
                started_cameras.append(i)
                self.status_display.set_status_text(f"摄像头 {i} 运行中")
                logging.info(f"摄像头 {i} 已启动")
            except ValueError as e:
                messagebox.showerror("配置错误", str(e))
                logging.error(f"摄像头{i}配置错误: {str(e)}")
            except RuntimeError as e:
                messagebox.showerror("运行错误", str(e))
                logging.error(f"摄像头{i}运行错误: {str(e)}")
            except Exception as e:
                messagebox.showerror("未知错误", f"摄像头{i}启动失败: {str(e)}")
                logging.error(f"摄像头{i}启动失败: {str(e)}")
        
        if not started_cameras:
            self.status_display.set_status_text("请选择要启动的摄像头")
        elif len(started_cameras) > 1:
            self.status_display.set_status_text(f"已启动 {len(started_cameras)} 个摄像头")
            
    def stop_all(self):
        """停止所有摄像头"""
        try:
            self.manager.stop_all()
            self.status_display.set_status_text("系统已停止")
            self._update_status()
            logging.info("所有摄像头已停止")
        except Exception as e:
            logging.error(f"停止摄像头失败: {str(e)}")
            messagebox.showerror("错误", f"停止摄像头失败: {str(e)}")
            
    def pause_alarm(self):
        """暂停所有报警声音"""
        try:
            for i in range(len(CONFIG.cameras)):
                processor = self.manager.get_processor(i)
                if processor:
                    processor.alarm_channel.stop()
            self.status_display.set_status_text("报警已暂停")
            logging.info("报警已暂停")
        except Exception as e:
            logging.error(f"暂停报警失败: {str(e)}")
            messagebox.showerror("错误", f"暂停报警失败: {str(e)}")
            
    def reset_status(self):
        """重置所有摄像头的检测状态"""
        try:
            for i in range(len(CONFIG.cameras)):
                processor = self.manager.get_processor(i)
                if processor:
                    processor._reset_alarm()
                    processor.alarm_channel.stop()
            self.status_display.set_status_text("状态已重置")
            self._update_status()
            logging.info("所有摄像头状态已重置")
        except Exception as e:
            logging.error(f"重置状态失败: {str(e)}")
            messagebox.showerror("错误", f"重置状态失败: {str(e)}")
            
    def on_close(self):
        """窗口关闭事件处理"""
        try:
            logging.info("系统正在关闭...")
            self.stop_all()
            self.root.destroy()
        except Exception as e:
            logging.error(f"系统关闭异常: {str(e)}")
            
    def run(self):
        """运行主循环"""
        self.root.mainloop()
        
    def _start_status_update(self):
        """启动状态更新定时器"""
        self._update_status()
        self.time_display.update()  # 更新时间显示
        self.root.after(int(CONFIG.status_update_interval * 1000), self._start_status_update)
    
    def _update_status(self):
        """更新摄像头状态显示"""
        try:
            # 获取所有摄像头处理器
            processors = []
            for i in range(len(CONFIG.cameras)):
                processors.append(self.manager.get_processor(i))
            
            # 更新状态显示
            self.status_display.update_status(processors)
        except Exception as e:
            logging.error(f"更新状态失败: {str(e)}")