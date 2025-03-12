# -*- coding: utf-8 -*-
# modules/ui/components.py
# UI组件模块，包含各种UI组件类

import tkinter as tk
from tkinter import ttk
import datetime
import logging
import sv_ttk
from config import CONFIG
from styles import UIStyles

class TimeDisplay:
    """时间显示组件"""
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1)
        self.label = ttk.Label(self.frame, font=("Helvetica", 14, "bold"), anchor="center")
        self.label.pack(fill=tk.X, expand=True, pady=10)
        self.update()
    
    def update(self):
        """更新时间显示"""
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.label.config(text=current_time)
        except Exception as e:
            logging.error(f"更新时间显示失败: {str(e)}")
    
    def pack(self, **kwargs):
        """打包组件"""
        self.frame.pack(**kwargs)

class ThemeSelector:
    """主题选择器组件"""
    def __init__(self, parent, callback=None):
        self.current_theme = "light"
        self.theme_var = tk.StringVar(value="light")
        self.frame = ttk.LabelFrame(parent, text="主题设置", padding=5)
        
        ttk.Radiobutton(self.frame, text="浅色", value="light", 
                        variable=self.theme_var, command=self._on_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.frame, text="深色", value="dark", 
                        variable=self.theme_var, command=self._on_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.frame, text="自动", value="auto", 
                        variable=self.theme_var, command=self._on_change).pack(side=tk.LEFT, padx=5)
        
        self.callback = callback
        self.auto_mode = False
        self.auto_check_id = None
    
    def _on_change(self):
        """主题变更处理"""
        new_theme = self.theme_var.get()
        
        # 处理自动模式
        if new_theme == "auto":
            self.auto_mode = True
            # 立即应用基于时间的主题
            self._apply_auto_theme()
            # 设置定时检查
            if not self.auto_check_id:
                self._schedule_auto_check()
            logging.info("已启用自动主题模式")
        else:
            # 关闭自动模式
            self.auto_mode = False
            if self.auto_check_id:
                if hasattr(self, 'frame') and self.frame.winfo_exists():
                    self.frame.after_cancel(self.auto_check_id)
                    self.auto_check_id = None
            
            # 应用选定的主题
            if new_theme != self.current_theme:
                sv_ttk.set_theme(new_theme)
                self.current_theme = new_theme
                logging.info(f"已切换到{new_theme}主题")
                if self.callback:
                    self.callback(new_theme)
    
    def _apply_auto_theme(self):
        """根据当前时间应用相应主题"""
        current_hour = datetime.datetime.now().hour
        # 6:00-18:00使用浅色主题，其他时间使用深色主题
        new_theme = "light" if 6 <= current_hour < 18 else "dark"
        
        if new_theme != self.current_theme:
            sv_ttk.set_theme(new_theme)
            self.current_theme = new_theme
            logging.info(f"自动模式：已切换到{new_theme}主题")
            if self.callback:
                self.callback(new_theme)
    
    def _schedule_auto_check(self):
        """设置定时检查当前时间并更新主题"""
        if self.auto_mode and hasattr(self, 'frame') and self.frame.winfo_exists():
            self._apply_auto_theme()
            # 每10分钟检查一次
            self.auto_check_id = self.frame.after(600000, self._schedule_auto_check)
    
    def pack(self, **kwargs):
        """打包组件"""
        self.frame.pack(**kwargs)

class CameraSelector:
    """摄像头选择器组件"""
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="摄像头选择", padding=10)
        self.cam_vars = []
        
        cam_grid = ttk.Frame(self.frame)
        cam_grid.pack(fill=tk.X)
        
        # 使用网格布局，每行放置2个摄像头选项
        for i in range(len(CONFIG.cameras)):
            var = tk.BooleanVar(value=True)
            self.cam_vars.append(var)
            row, col = divmod(i, 2)
            ttk.Checkbutton(cam_grid, text=f"摄像头 {i}", variable=var).grid(
                row=row, column=col, sticky=tk.W, padx=10, pady=2)
    
    def get_selected(self):
        """获取选中的摄像头ID列表"""
        return [i for i, var in enumerate(self.cam_vars) if var.get()]
    
    def pack(self, **kwargs):
        """打包组件"""
        self.frame.pack(**kwargs)

class SettingsPanel:
    """设置面板组件"""
    def __init__(self, parent, apply_callback=None):
        self.frame = ttk.LabelFrame(parent, text="参数设置", padding=10)
        self.apply_callback = apply_callback
        
        # 手势灵敏度设置
        ttk.Label(self.frame, text="手势检测灵敏度:").pack(anchor=tk.W)
        self.gesture_scale = ttk.Scale(self.frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL)
        self.gesture_scale.set(CONFIG.gesture_threshold)
        self.gesture_scale.pack(fill=tk.X)
        
        # 报警间隔设置
        alarm_interval_frame = ttk.Frame(self.frame)
        alarm_interval_frame.pack(fill=tk.X, pady=5)
        ttk.Label(alarm_interval_frame, text="报警间隔设置(秒):").pack(anchor=tk.W)
        
        # 报警间隔输入框
        alarm_inputs = ttk.Frame(alarm_interval_frame)
        alarm_inputs.pack(fill=tk.X)
        
        self.alarm_vars = []
        for i, trigger in enumerate(CONFIG.alarm_triggers):
            var = tk.StringVar(value=str(trigger))
            self.alarm_vars.append(var)
            ttk.Label(alarm_inputs, text=f"级别{i+1}:").grid(row=0, column=i*2, padx=5)
            ttk.Entry(alarm_inputs, textvariable=var, width=5).grid(row=0, column=i*2+1, padx=5)
        
        # ROI设置 - 为每个摄像头创建单独的ROI设置
        roi_notebook = ttk.Notebook(self.frame)
        roi_notebook.pack(fill=tk.X, pady=5)
        
        self.roi_vars = {}
        for cam_id in range(len(CONFIG.cameras)):
            roi_frame = ttk.Frame(roi_notebook)
            roi_notebook.add(roi_frame, text=f"摄像头 {cam_id} ROI")
            
            roi_inputs = ttk.Frame(roi_frame)
            roi_inputs.pack(fill=tk.X, pady=5)
            
            # 为每个摄像头创建ROI输入框
            self.roi_vars[cam_id] = {}
            for i, label in enumerate(['X', 'Y', '宽度', '高度']):
                ttk.Label(roi_inputs, text=label).grid(row=0, column=i*2)
                var = tk.StringVar(value=str(CONFIG.cameras[cam_id].roi[['x','y','w','h'][i]]))
                self.roi_vars[cam_id][label] = var
                ttk.Entry(roi_inputs, textvariable=var, width=8).grid(row=0, column=i*2+1, padx=5)
        
        # 应用按钮
        ttk.Button(self.frame, text="应用设置", command=self._on_apply).pack(fill=tk.X, pady=5)
    
    def _on_apply(self):
        """应用设置按钮点击处理"""
        if self.apply_callback:
            self.apply_callback()
    
    def get_settings(self):
        """获取当前设置值"""
        settings = {
            'gesture_threshold': self.gesture_scale.get(),
            'alarm_triggers': [],
            'roi_settings': {}
        }
        
        # 获取报警间隔设置
        for var in self.alarm_vars:
            try:
                value = int(var.get())
                if value > 0:
                    settings['alarm_triggers'].append(value)
            except ValueError:
                pass
        
        # 获取ROI设置
        for cam_id in self.roi_vars:
            settings['roi_settings'][cam_id] = {
                'x': int(self.roi_vars[cam_id]['X'].get()),
                'y': int(self.roi_vars[cam_id]['Y'].get()),
                'w': int(self.roi_vars[cam_id]['宽度'].get()),
                'h': int(self.roi_vars[cam_id]['高度'].get())
            }
        
        return settings
    
    def pack(self, **kwargs):
        """打包组件"""
        self.frame.pack(**kwargs)

class ControlButtons:
    """控制按钮组件"""
    def __init__(self, parent, callbacks=None):
        self.frame = ttk.LabelFrame(parent, text="控制按钮", padding=10)
        self.callbacks = callbacks or {}
        
        # 使用网格布局，每行放置2个按钮
        button_grid = ttk.Frame(self.frame)
        button_grid.pack(fill=tk.X, pady=5)
        
        # 第一行按钮
        start_btn = ttk.Button(button_grid, text="启动选中", 
                              command=self._on_start, style="Accent.TButton")
        start_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        stop_btn = ttk.Button(button_grid, text="停止所有", 
                             command=self._on_stop)
        stop_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 第二行按钮
        pause_btn = ttk.Button(button_grid, text="暂停报警", 
                              command=self._on_pause)
        pause_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        reset_btn = ttk.Button(button_grid, text="重置状态", 
                              command=self._on_reset)
        reset_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # 配置网格列权重，使按钮均匀分布
        button_grid.columnconfigure(0, weight=1)
        button_grid.columnconfigure(1, weight=1)
    
    def _on_start(self):
        if 'start' in self.callbacks:
            self.callbacks['start']()
    
    def _on_stop(self):
        if 'stop' in self.callbacks:
            self.callbacks['stop']()
    
    def _on_pause(self):
        if 'pause' in self.callbacks:
            self.callbacks['pause']()
    
    def _on_reset(self):
        if 'reset' in self.callbacks:
            self.callbacks['reset']()
    
    def pack(self, **kwargs):
        """打包组件"""
        self.frame.pack(**kwargs)

class StatusDisplay:
    """状态显示组件"""
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="系统状态", padding=10)
        
        # 摄像头状态指示区域
        self.cam_status_frame = ttk.Frame(self.frame)
        self.cam_status_frame.pack(fill=tk.X, pady=5)
        
        # 添加状态标题行
        header_frame = ttk.Frame(self.cam_status_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(header_frame, text="状态", width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="摄像头", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="报警级别", width=30).pack(side=tk.LEFT, padx=5)
        
        # 分隔线
        separator = ttk.Separator(self.cam_status_frame, orient="horizontal")
        separator.pack(fill=tk.X, pady=5)
        
        self.cam_status_labels = []
        self.alarm_count_labels = []
        for i in range(len(CONFIG.cameras)):
            cam_label_frame = ttk.Frame(self.cam_status_frame)
            cam_label_frame.pack(fill=tk.X, pady=4)
            
            # 状态指示器
            status_indicator = tk.Label(cam_label_frame, width=4, height=2, 
                                       bg=UIStyles.STATUS_COLORS['disabled'])
            status_indicator.pack(side=tk.LEFT, padx=5)
            
            cam_label = ttk.Label(cam_label_frame, text=f"摄像头 {i}", font=UIStyles.FONTS['body'])
            cam_label.pack(side=tk.LEFT, padx=5)
            
            # 报警计数显示
            alarm_count_frame = ttk.Frame(cam_label_frame)
            alarm_count_frame.pack(side=tk.LEFT, padx=10)
            
            alarm_counts = {}
            for j, trigger in enumerate(CONFIG.alarm_triggers):
                # 使用更美观的标签样式
                count_frame = ttk.Frame(alarm_count_frame)
                count_frame.pack(side=tk.LEFT, padx=5)
                
                level_label = ttk.Label(count_frame, text=f"L{j+1}", font=UIStyles.FONTS['small'])
                level_label.pack(anchor=tk.CENTER)
                
                count_label = ttk.Label(count_frame, text="0", width=2, font=UIStyles.FONTS['body'])
                count_label.pack(anchor=tk.CENTER)
                
                alarm_counts[trigger] = count_label
            
            self.alarm_count_labels.append(alarm_counts)
            self.cam_status_labels.append(status_indicator)
        
        # 状态信息显示区域
        info_frame = ttk.LabelFrame(self.frame, text="系统信息", padding=5)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.status_label = ttk.Label(info_frame, text="系统就绪", font=UIStyles.FONTS['subtitle'])
        self.status_label.pack(anchor=tk.W, pady=5)
        
        self.status_text = tk.Text(info_frame, height=8, wrap=tk.WORD, font=UIStyles.FONTS['body'])
        self.status_text.pack(fill=tk.BOTH, expand=True)
        self.status_text.config(state='disabled')
    
    def update_status(self, camera_processors):
        """更新摄像头状态显示"""
        try:
            status_str = ""
            self.status_text.config(state='normal')
            self.status_text.delete(1.0, tk.END)
            
            for i, processor in enumerate(camera_processors):
                if processor:
                    status = processor.get_status()
                    
                    # 更新状态指示器颜色
                    if status['alarm_level'] > 0:
                        status_color = UIStyles.get_alarm_level_color(status['alarm_level'])
                        self.cam_status_labels[i].config(bg=status_color)
                    elif status['detection_time'] > 0:
                        self.cam_status_labels[i].config(bg=UIStyles.STATUS_COLORS['detecting'])
                    else:
                        self.cam_status_labels[i].config(bg=UIStyles.STATUS_COLORS['normal'])
                    
                    # 更新报警计数显示
                    if i < len(self.alarm_count_labels):
                        alarm_counts = {}
                        for trigger in CONFIG.alarm_triggers:
                            alarm_counts[trigger] = 0
                        
                        # 从processor获取已触发的报警
                        for trigger in processor.played_sounds:
                            if trigger in alarm_counts:
                                alarm_counts[trigger] = 1
                        
                        # 更新显示
                        for j, trigger in enumerate(CONFIG.alarm_triggers):
                            if trigger in self.alarm_count_labels[i]:
                                count = alarm_counts[trigger]
                                level_color = UIStyles.get_alarm_level_color(j+1) if count > 0 else 'black'
                                self.alarm_count_labels[i][trigger].config(
                                    text=str(count),
                                    foreground=level_color
                                )
                    
                    # 格式化状态信息
                    status_str += f"摄像头 {i}: "
                    status_str += f"状态: {status['status']} "
                    if status['fps'] > 0:
                        status_str += f"FPS: {status['fps']:.1f} "
                    if status['detection_time'] > 0:
                        status_str += f"检测时间: {status['detection_time']:.1f}秒 "
                    if status['alarm_level'] > 0:
                        status_str += f"报警级别: {status['alarm_level']} "
                    status_str += "\n"
                else:
                    # 摄像头未运行，显示为禁用状态
                    self.cam_status_labels[i].config(bg=UIStyles.STATUS_COLORS['disabled'])
            
            if not status_str:
                status_str = "无活动摄像头"
                
            self.status_text.insert(tk.END, status_str)
            self.status_text.config(state='disabled')
        except Exception as e:
            logging.error(f"更新状态失败: {str(e)}")
    
    def set_status_text(self, text):
        """设置状态文本"""
        self.status_label.config(text=text)
    
    def pack(self, **kwargs):
        """打包组件"""
        self.frame.pack(**kwargs)