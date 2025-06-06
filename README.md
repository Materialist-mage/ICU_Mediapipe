# ICU 手部行为监测系统 v2.8（企业增强版）

## 系统概述
本系统是一个基于计算机视觉的智能监控解决方案，专门针对重症监护室（ICU）患者的安全监护需求设计。通过先进的手势识别算法和多级报警机制，系统能够实时监测并预警患者的危险行为，有效降低医疗事故风险。

### 核心特性
- **实时手势识别**：基于MediaPipe的高精度手部关键点检测
- **多级报警机制**：自适应的时间阈值和声音提示系统
- **分布式架构**：支持多摄像头并行处理和统一管理
- **高可用设计**：自动故障恢复和资源管理机制
- **自动主题切换**：根据系统时间智能切换界面主题

## 版本信息
- **当前版本**：v2.8（企业增强版）
- **上一版本**：v2.5（企业级版）
- **发布日期**：2025年3月11日
- **更新目标**：全面提升系统性能和用户体验，优化手势识别精度和多摄像头协同能力

## 技术架构

### 系统组件
- **视频处理模块**：基于OpenCV的实时视频流处理
- **手势识别引擎**：MediaPipe Hands模型
- **报警控制系统**：Pygame音频处理引擎
- **用户界面**：Tkinter图形界面框架

### 项目结构
项目采用模块化设计，主要结构如下：

```
.
├── main.py                 # 系统入口文件
├── config.py               # 配置文件
├── processor.py            # 摄像头处理器核心逻辑
├── styles.py               # UI样式定义
├── modules/                # 功能模块目录
│   ├── __init__.py         # 模块包初始化
│   ├── camera_manager.py   # 摄像头管理模块
│   ├── fps_counter.py      # 帧率计数器
│   ├── video_processor.py  # 视频处理模块
│   └── ui/                 # 用户界面模块
│       ├── __init__.py     # UI模块初始化
│       ├── components.py   # UI组件定义
│       └── control_panel.py # 控制面板实现
├── sounds/                 # 报警音频文件
└── logs/                   # 日志文件目录
```

### 模块功能说明

#### 核心模块
- **main.py**: 系统启动入口，初始化音频系统和UI界面
- **config.py**: 系统配置，包含摄像头设置、报警阈值等参数
- **processor.py**: 摄像头处理器的核心逻辑，包含CameraManager类
- **styles.py**: 定义UI样式，包括颜色、字体等

#### 功能模块 (modules/)
- **camera_manager.py**: 负责摄像头的管理，包括启动、停止摄像头等功能
- **fps_counter.py**: 帧率计数器，用于监控系统性能
- **video_processor.py**: 视频处理模块，包含手势识别和行为分析算法

#### UI模块 (modules/ui/)
- **components.py**: 定义各种UI组件，如时间显示、主题选择器、摄像头选择器等
- **control_panel.py**: 实现主控制面板，整合各UI组件并处理用户交互

## 核心更新亮点

### 1. 企业级架构优化
- **代码架构**：
  - 严格遵循企业级软件开发规范
  - 完善的异常处理机制
  - 统一的日志记录系统
  - 模块化设计，便于维护和扩展

### 2. 配置系统升级
- **集中化配置**：
  - 所有系统参数统一在 `config.py` 中管理
  - 支持多摄像头配置
  - 灵活的报警阈值设置
  - 可自定义ROI（感兴趣区域）

### 3. 性能优化
- **资源管理**：
  - 优化内存使用
  - 改进CPU占用（降低至30%以下）
  - 支持多摄像头并行处理
- **稳定性提升**：
  - 自动重连机制
  - 故障恢复能力
  - 资源自动释放

### 4. 用户界面改进
- **交互优化**：
  - 直观的状态显示
  - 实时性能监控
  - 便捷的参数调整界面
  - 新增自动主题切换功能
- **可视化增强**：
  - 清晰的摄像头状态指示
  - 实时FPS显示
  - ROI可视化

### 5. 报警系统增强
- **多级报警机制**：
  - 5秒、10秒、15秒、30秒多级报警
  - 不同级别对应不同报警音
  - 可自定义报警阈值
- **报警控制**：
  - 一键暂停所有报警
  - 状态快速重置
  - 报警音量控制

## 性能指标
- 视频处理延迟：<50ms
- CPU占用率：<30%（单摄像头）
- 内存占用：<500MB
- 手势识别准确率：>95%

## 环境要求

### 硬件配置
- **处理器**：Intel Core i5 或同等性能
- **内存**：8GB RAM（推荐）
- **摄像头**：720p或更高分辨率USB摄像头
- **存储**：500MB可用空间

### 软件环境
- **操作系统**：
  - Windows 10/11
  - Ubuntu 20.04+
  - macOS 10.15+
- **Python环境**：
  - Python 3.9+
  - pip 20.0+

### 依赖库
```
opencv-python>=4.5.0
mediapipe>=0.8.9
pygame>=2.0.0
numpy>=1.19.0
```

## 安装指南

### 快速安装
1. **克隆代码仓库** 【暂未开放】
<!-- ```bash
git clone [repository_url]
cd ICU_Mediapipe
``` -->

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行系统**
```bash
python main.py
```

## 后续规划

### 1. 功能扩展
- 远程监控支持
- 数据统计分析
- 自动化测试套件
- 配置文件导入导出

### 2. 性能提升
- GPU加速支持
- 多线程优化
- 内存管理改进
- 启动速度优化

---

> 本文档最后更新：2025年3月11日