# -*- coding: utf-8 -*-
# styles.py: UI样式定义模块

class UIStyles:
    """UI样式类，定义系统界面的颜色、字体和样式
    
    主要功能：
    - 提供统一的颜色方案
    - 定义不同主题（浅色/深色）
    - 提供字体和按钮样式
    """
    
    # 主题定义
    THEMES = {
        "light": {
            "bg": "#f0f0f0",
            "fg": "#333333",
            "accent": "#1e88e5",
            "success": "#43a047",
            "warning": "#ff9800",
            "error": "#e53935",
            "button_bg": "#e0e0e0",
            "button_fg": "#333333",
            "button_active": "#1e88e5",
            "frame_bg": "#ffffff",
            "border": "#cccccc"
        },
        "dark": {
            "bg": "#2c2c2c",
            "fg": "#e0e0e0",
            "accent": "#64b5f6",
            "success": "#66bb6a",
            "warning": "#ffa726",
            "error": "#ef5350",
            "button_bg": "#424242",
            "button_fg": "#e0e0e0",
            "button_active": "#64b5f6",
            "frame_bg": "#383838",
            "border": "#555555"
        }
    }
    
    # 默认主题
    DEFAULT_THEME = "light"
    
    # 字体设置
    FONTS = {
        "title": ("SimHei", 16, "bold"),
        "subtitle": ("SimHei", 14, "bold"),
        "body": ("SimHei", 12, "normal"),
        "small": ("SimHei", 10, "normal"),
        "button": ("SimHei", 12, "normal")
    }
    
    # 按钮样式
    BUTTON_STYLES = {
        "normal": {
            "padding": (10, 5),
            "border_width": 1,
            "border_radius": 4
        },
        "small": {
            "padding": (5, 2),
            "border_width": 1,
            "border_radius": 3
        },
        "large": {
            "padding": (15, 8),
            "border_width": 1,
            "border_radius": 5
        }
    }
    
    # 状态颜色
    STATUS_COLORS = {
        "normal": "#43a047",  # 绿色
        "detecting": "#ff9800",  # 橙色
        "alarm": "#e53935",  # 红色
        "disabled": "#9e9e9e"  # 灰色
    }
    
    # 报警级别颜色
    ALARM_LEVEL_COLORS = {
        0: "#43a047",  # 绿色 - 无报警
        1: "#ffeb3b",  # 黄色 - 5秒报警
        2: "#ff9800",  # 橙色 - 10秒报警
        3: "#f44336",  # 红色 - 15秒报警
        4: "#d32f2f"   # 深红色 - 30秒报警
    }
    
    @classmethod
    def get_theme(cls, theme_name=None):
        """获取指定主题的颜色方案
        
        Args:
            theme_name: 主题名称，默认为None，使用默认主题
            
        Returns:
            dict: 主题颜色方案
        """
        if not theme_name:
            theme_name = cls.DEFAULT_THEME
        return cls.THEMES.get(theme_name, cls.THEMES[cls.DEFAULT_THEME])
    
    @classmethod
    def get_status_color(cls, status, theme_name=None):
        """获取状态对应的颜色
        
        Args:
            status: 状态名称
            theme_name: 主题名称
            
        Returns:
            str: 颜色代码
        """
        theme = cls.get_theme(theme_name)
        if status == "normal":
            return cls.STATUS_COLORS["normal"]
        elif status == "detecting":
            return cls.STATUS_COLORS["detecting"]
        elif status == "alarm":
            return cls.STATUS_COLORS["alarm"]
        else:
            return cls.STATUS_COLORS["disabled"]
    
    @classmethod
    def get_alarm_level_color(cls, level):
        """获取报警级别对应的颜色
        
        Args:
            level: 报警级别
            
        Returns:
            str: 颜色代码
        """
        return cls.ALARM_LEVEL_COLORS.get(level, cls.ALARM_LEVEL_COLORS[0])