"""
主窗口模块
实现应用程序的主界面和核心功能
"""

import os
import traceback
import datetime
import ctypes
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QLabel, QMessageBox,
                            QShortcut, QCheckBox, QSystemTrayIcon, QMenu, QAction,
                            QStyle, QFrame, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QKeySequence, QPixmap
from src.utils.logger import logger
from src.utils.event_filter import GlobalEventFilter
from src.utils.hotkey_manager import HotkeyManager
from src.core.document_manager import DocumentManager
from src.core.screenshot_manager import ScreenshotManager
from src.ui.about_dialog import AboutDialog
from src.ui.float_ball import FloatBall
from src.ui.fullscreen_image_viewer import FullscreenImageViewer

# 定义Windows API常量
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

class MainWindow(QMainWindow):
    """
    主窗口类
    实现应用程序的主界面和核心功能
    """
    
    # 定义信号
    fullscreen_signal = pyqtSignal()
    area_signal = pyqtSignal()
    esc_signal = pyqtSignal()
    auto_save_signal = pyqtSignal()  # 添加自动保存信号
    
    def __init__(self):
        """
        初始化主窗口
        """
        super().__init__()
        logger.info("初始化主窗口")
        
        # 初始化属性
        self.is_capturing = False
        self.is_topmost = False  # 窗口是否置顶
        self.is_working_mode = False  # 是否处于工作模式
        self.float_ball = None  # 悬浮球窗口
        self.current_screenshot_index = -1  # 当前显示的截图索引，-1表示没有显示任何截图
        
        # 初始化管理器
        self.document_manager = DocumentManager(self)
        self.screenshot_manager = ScreenshotManager(self)
        self.hotkey_manager = HotkeyManager(self)
        
        # 记录初始状态
        self.log_screenshots_state("初始化")
        
        # 初始化UI
        self.initUI()
        
        # 创建系统托盘图标
        self.setup_tray_icon()
        
        # 设置全局事件过滤器
        self.event_filter = GlobalEventFilter(self)
        QApplication.instance().installEventFilter(self.event_filter)
        logger.info("已安装全局事件过滤器")
        
        # 设置快捷键（作为备用）
        self.setup_shortcuts()
        
        # 连接信号到槽
        self.connect_signals()
        
        # 注册系统级全局热键
        self.hotkey_manager.register_hotkeys()
        
        # 创建一个定时器，定期检查热键状态
        self.hotkey_check_timer = QTimer(self)
        self.hotkey_check_timer.timeout.connect(self.hotkey_manager.check_hotkey_status)
        self.hotkey_check_timer.start(500)  # 每500毫秒检查一次
        
        # 创建一个定时器，定期检查并确保窗口置顶
        self.topmost_check_timer = QTimer(self)
        self.topmost_check_timer.timeout.connect(self.check_topmost)
        self.topmost_check_timer.start(300)  # 每300毫秒检查一次
    
    def connect_signals(self):
        """
        连接所有信号到槽函数
        """
        try:
            # 使用Qt.QueuedConnection确保信号在主线程中处理
            self.fullscreen_signal.connect(self.take_fullscreen_screenshot, Qt.QueuedConnection)
            self.area_signal.connect(self.start_capture, Qt.QueuedConnection)
            self.esc_signal.connect(self.exit_special_modes, Qt.QueuedConnection)
            self.auto_save_signal.connect(self.take_auto_save_screenshot, Qt.QueuedConnection)
            logger.info("成功连接所有信号到槽函数")
        except Exception as e:
            logger.error(f"连接信号到槽函数时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _safe_emit_signal(self, signal_type):
        """
        安全地发射信号，并添加额外的日志记录
        
        参数:
            signal_type: 字符串，信号类型
        """
        try:
            logger.debug(f"准备发射 {signal_type} 信号")
            if signal_type == "fullscreen":
                logger.debug("发射全屏截图信号")
                self.fullscreen_signal.emit()
                # 不再使用备份机制，避免双重触发
            elif signal_type == "area":
                logger.debug("发射区域截图信号")
                self.area_signal.emit()
                # 不再使用备份机制，避免双重触发
            elif signal_type == "esc":
                logger.debug("发射ESC信号")
                self.esc_signal.emit()
                # 不再使用备份机制，避免双重触发
            elif signal_type == "auto_save":
                logger.debug("发射自动保存截图信号")
                self.auto_save_signal.emit()
                # 不再使用备份机制，避免双重触发
            logger.debug(f"{signal_type} 信号已发射")
        except Exception as e:
            logger.error(f"发射 {signal_type} 信号时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def ensure_window_state_for_screenshot(self):
        """
        确保窗口处于正确的状态以进行截图
        """
        try:
            logger.debug("确保窗口处于正确状态以进行截图")
            
            # 如果在工作模式下，确保悬浮球是可见的
            if self.is_working_mode and self.float_ball:
                # 确保悬浮球是可见的
                if not self.float_ball.isVisible():
                    logger.debug("显示悬浮球")
                    self.float_ball.show()
                
                # 使用ctypes确保悬浮球在最顶层
                self.set_window_topmost(self.float_ball)
            
            # 处理事件，确保窗口状态更新
            QApplication.processEvents()
            
            logger.debug("窗口状态已准备好进行截图")
        except Exception as e:
            logger.error(f"确保窗口状态时出错: {str(e)}")
    
    def setup_shortcuts(self):
        """
        设置应用程序快捷键
        """
        logger.info("设置应用程序快捷键")
        try:
            # 不再注册F12全屏截图快捷键，因为已经通过HotkeyManager注册了全局热键
            # 这样可以避免F12热键被重复触发
            # self.fullscreen_shortcut = QShortcut(QKeySequence("F12"), self)
            # self.fullscreen_shortcut.activated.connect(self.take_fullscreen_screenshot)
            # logger.debug("已设置F12全屏截图快捷键")
            
            # 同样，不再注册Ctrl+F12区域截图快捷键
            # self.area_shortcut = QShortcut(QKeySequence("Ctrl+F12"), self)
            # self.area_shortcut.activated.connect(self.start_capture)
            # logger.debug("已设置Ctrl+F12区域截图快捷键")
            
            # 不再注册F11快捷键
            # self.auto_save_shortcut = QShortcut(QKeySequence("F11"), self)
            # self.auto_save_shortcut.activated.connect(self.take_auto_save_screenshot)
            # logger.debug("已设置F11自动保存截图快捷键")
            
            # 保留ESC键退出置顶/工作模式
            self.esc_shortcut = QShortcut(QKeySequence("Escape"), self)
            self.esc_shortcut.activated.connect(self.exit_special_modes)
            logger.debug("已设置ESC退出快捷键")
            
            logger.info("已移除重复的热键注册，只保留ESC快捷键")
        except Exception as e:
            logger.error(f"设置快捷键时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def setup_tray_icon(self):
        """
        设置系统托盘图标
        """
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        
        screenshot_action = QAction("全屏截图 (F12)", self)
        screenshot_action.triggered.connect(self.take_fullscreen_screenshot)
        
        area_screenshot_action = QAction("区域截图 (Ctrl+F12)", self)
        area_screenshot_action.triggered.connect(self.start_capture)
        
        auto_save_action = QAction("自动保存截图 (F11)", self)
        auto_save_action.triggered.connect(self.take_auto_save_screenshot)
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(screenshot_action)
        tray_menu.addAction(area_screenshot_action)
        tray_menu.addAction(auto_save_action)
        tray_menu.addSeparator()
        tray_menu.addAction(about_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        logger.debug("系统托盘图标设置完成")
    
    def tray_icon_activated(self, reason):
        """
        处理托盘图标激活事件
        
        参数:
            reason: 激活原因
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def initUI(self):
        """
        初始化用户界面
        """
        self.setWindowTitle('屏幕截图工具')
        self.setGeometry(300, 300, 550, 650)  # 稍微增加窗口大小
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
            QCheckBox {
                color: #333333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)  # 增加布局间距
        main_layout.setContentsMargins(15, 15, 15, 15)  # 增加边距
        
        # ===== 悬浮球模式区域 =====
        work_frame = QFrame()
        work_frame.setFrameShape(QFrame.StyledPanel)
        work_frame.setStyleSheet("""
            background-color: #E3F2FD;
            border: 1px solid #90CAF9;
            border-radius: 8px;
            margin: 0px;
        """)
        work_layout = QVBoxLayout(work_frame)
        work_layout.setContentsMargins(15, 15, 15, 15)
        
        # 添加标题标签
        title_label = QLabel("快速操作")
        title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #1565C0;
            margin-bottom: 5px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        work_layout.addWidget(title_label)
        
        # 创建开始工作按钮
        self.start_work_btn = QPushButton('▶ 悬浮球模式 ▶')
        self.start_work_btn.setStyleSheet("""
            background-color: #4CAF50; 
            color: white; 
            font-weight: bold;
            font-size: 18px;
            padding: 12px;
            border-radius: 8px;
            border: none;
            margin: 5px;
        """)
        self.start_work_btn.setMinimumHeight(60)
        self.start_work_btn.setCursor(Qt.PointingHandCursor)
        work_layout.addWidget(self.start_work_btn)
        
        # 添加提示标签
        hint_label = QLabel("点击进入悬浮球截图模式")
        hint_label.setStyleSheet("color: #555; font-style: italic;")
        hint_label.setAlignment(Qt.AlignCenter)
        work_layout.addWidget(hint_label)
        
        # ===== 文档操作区域 =====
        doc_frame = QFrame()
        doc_frame.setFrameShape(QFrame.StyledPanel)
        doc_frame.setStyleSheet("""
            background-color: #FFF8E1;
            border: 1px solid #FFECB3;
            border-radius: 8px;
        """)
        doc_frame.setMinimumWidth(250)  # 设置最小宽度
        doc_frame_layout = QVBoxLayout(doc_frame)
        doc_frame_layout.setContentsMargins(10, 10, 10, 10)  # 减小内边距
        
        doc_title = QLabel("文档操作")
        doc_title.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #FF8F00;
            margin-bottom: 5px;
        """)
        doc_title.setAlignment(Qt.AlignCenter)
        doc_frame_layout.addWidget(doc_title)
        
        # 修改为两行布局
        doc_layout_top = QHBoxLayout()
        doc_layout_top.setSpacing(8)
        
        self.create_doc_btn = QPushButton('创建新文档')
        self.create_doc_btn.setStyleSheet("""
            background-color: #FFA000;
            color: white;
        """)
        self.open_doc_btn = QPushButton('打开现有文档')
        self.open_doc_btn.setStyleSheet("""
            background-color: #FFA000;
            color: white;
        """)
        
        doc_layout_top.addWidget(self.create_doc_btn)
        doc_layout_top.addWidget(self.open_doc_btn)
        doc_frame_layout.addLayout(doc_layout_top)
        
        doc_layout_bottom = QHBoxLayout()
        self.save_doc_btn = QPushButton('保存文档')
        self.save_doc_btn.setStyleSheet("""
            background-color: #FFA000;
            color: white;
        """)
        doc_layout_bottom.addWidget(self.save_doc_btn)
        doc_frame_layout.addLayout(doc_layout_bottom)
        
        # 文档状态
        doc_status_layout = QHBoxLayout()
        doc_status_layout.addWidget(QLabel('当前文档:'))
        self.doc_status_label = QLabel('未选择文档')
        self.doc_status_label.setStyleSheet("font-weight: bold; color: #FF6F00;")
        doc_status_layout.addWidget(self.doc_status_label)
        doc_frame_layout.addLayout(doc_status_layout)
        
        # ===== 截图操作区域 =====
        screenshot_frame = QFrame()
        screenshot_frame.setFrameShape(QFrame.StyledPanel)
        screenshot_frame.setStyleSheet("""
            background-color: #E8F5E9;
            border: 1px solid #C8E6C9;
            border-radius: 8px;
        """)
        screenshot_frame.setMinimumWidth(250)  # 设置最小宽度
        screenshot_frame_layout = QVBoxLayout(screenshot_frame)
        screenshot_frame_layout.setContentsMargins(10, 10, 10, 10)  # 减小内边距
        
        screenshot_title = QLabel("截图操作")
        screenshot_title.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #2E7D32;
            margin-bottom: 5px;
        """)
        screenshot_title.setAlignment(Qt.AlignCenter)
        screenshot_frame_layout.addWidget(screenshot_title)
        
        # 截图操作区域 - 调整为更紧凑的布局
        screenshot_layout = QHBoxLayout()
        screenshot_layout.setSpacing(8)
        
        self.capture_btn = QPushButton('截取屏幕')
        self.capture_btn.setStyleSheet("""
            background-color: #43A047;
            color: white;
        """)
        self.clear_btn = QPushButton('清除所有截图')
        self.clear_btn.setStyleSheet("""
            background-color: #E53935;
            color: white;
        """)
        screenshot_layout.addWidget(self.capture_btn)
        screenshot_layout.addWidget(self.clear_btn)
        screenshot_frame_layout.addLayout(screenshot_layout)
        
        # 截图模式选择
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)
        
        self.full_screen_checkbox = QCheckBox('全屏截图模式')
        self.full_screen_checkbox.setChecked(True)
        self.full_screen_checkbox.setStyleSheet("""
            font-weight: bold;
            color: #2E7D32;
        """)
        
        self.topmost_btn = QPushButton('窗口置顶')
        self.topmost_btn.setStyleSheet("""
            background-color: #43A047;
            color: white;
        """)
        
        mode_layout.addWidget(self.full_screen_checkbox)
        mode_layout.addWidget(self.topmost_btn)
        screenshot_frame_layout.addLayout(mode_layout)
        
        # 截图计数
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel('已截图数量:'))
        self.screenshot_count = QLabel('0')
        self.screenshot_count.setStyleSheet("font-weight: bold; color: #2E7D32;")
        count_layout.addWidget(self.screenshot_count)
        count_layout.addStretch()
        screenshot_frame_layout.addLayout(count_layout)
        
        # ===== 预览区域 =====
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setStyleSheet("""
            background-color: #FFFFFF;
            border: 1px solid #BDBDBD;
            border-radius: 8px;
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(15, 15, 15, 15)
        
        preview_title = QLabel("预览区域")
        preview_title.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #424242;
            margin-bottom: 5px;
        """)
        preview_title.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_title)
        
        # 创建预览区域
        self.preview_label = QLabel('截图预览区域')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            border: 1px solid #BDBDBD;
            background-color: #EEEEEE;
            border-radius: 4px;
        """)
        # 设置固定大小
        self.preview_label.setFixedHeight(300)
        self.preview_label.setFixedWidth(400)
        # 设置鼠标追踪和光标形状
        self.preview_label.setMouseTracking(True)
        self.preview_label.setCursor(Qt.PointingHandCursor)
        self.preview_label.setToolTip("双击查看全屏图片")
        # 安装事件过滤器，用于处理双击事件
        self.preview_label.installEventFilter(self)
        
        preview_layout.addWidget(self.preview_label, 0, Qt.AlignCenter)
        
        # ===== 快捷键提示 =====
        shortcut_frame = QFrame()
        shortcut_frame.setFrameShape(QFrame.StyledPanel)
        shortcut_frame.setStyleSheet("""
            background-color: #E8EAF6;
            border: 1px solid #C5CAE9;
            border-radius: 8px;
        """)
        shortcut_layout = QVBoxLayout(shortcut_frame)
        shortcut_layout.setContentsMargins(15, 10, 15, 10)
        
        shortcut_title = QLabel("快捷键")
        shortcut_title.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #3949AB;
            margin-bottom: 5px;
        """)
        shortcut_title.setAlignment(Qt.AlignCenter)
        shortcut_layout.addWidget(shortcut_title)
        
        # 快捷键提示
        shortcut_label = QLabel('F12 = 全屏截图, Ctrl+F12 = 区域截图, F11 = 自动保存截图\nESC = 退出悬浮球模式, ←/→ = 切换截图, 双击预览图片可全屏显示')
        shortcut_label.setAlignment(Qt.AlignCenter)
        shortcut_label.setWordWrap(True)
        shortcut_label.setStyleSheet("""
            color: #3949AB;
            padding: 5px;
        """)
        shortcut_layout.addWidget(shortcut_label)
        
        # ===== 底部状态栏 =====
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_frame.setStyleSheet("""
            background-color: #ECEFF1;
            border: 1px solid #CFD8DC;
            border-radius: 8px;
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(15, 10, 15, 10)
        
        # 状态标签
        self.status_label = QLabel('请先创建或打开Word文档')
        self.status_label.setStyleSheet("font-weight: bold; color: #455A64;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # 添加关于按钮
        self.about_btn = QPushButton('关于')
        self.about_btn.setStyleSheet("""
            background-color: #673AB7;
            color: white;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 4px;
            border: none;
        """)
        self.about_btn.setCursor(Qt.PointingHandCursor)
        status_layout.addWidget(self.about_btn)
        
        # ===== 添加所有组件到主布局 =====
        main_layout.addWidget(work_frame)
        
        # 创建一个水平布局来容纳文档操作和截图操作
        operations_layout = QHBoxLayout()
        operations_layout.setSpacing(10)
        operations_layout.addWidget(doc_frame)
        operations_layout.addWidget(screenshot_frame)
        
        # 将水平布局添加到主布局
        main_layout.addLayout(operations_layout)
        
        main_layout.addWidget(preview_frame, 1)  # 预览区域可以拉伸
        main_layout.addWidget(shortcut_frame)
        main_layout.addWidget(status_frame)
        
        central_widget.setLayout(main_layout)
        
        # 连接信号和槽
        self.create_doc_btn.clicked.connect(self.create_word_doc)
        self.open_doc_btn.clicked.connect(self.open_word_doc)
        self.save_doc_btn.clicked.connect(self.save_word_doc)
        self.capture_btn.clicked.connect(self.start_capture)
        self.clear_btn.clicked.connect(self.clear_screenshots)
        self.full_screen_checkbox.stateChanged.connect(self.toggle_screenshot_mode)
        self.topmost_btn.clicked.connect(self.toggle_topmost)
        self.start_work_btn.clicked.connect(self.toggle_working_mode)
        self.about_btn.clicked.connect(self.show_about_dialog)
        
        # 初始状态设置
        self.save_doc_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.start_work_btn.setEnabled(False)
        
        logger.debug("主窗口UI初始化完成")
    
    def toggle_screenshot_mode(self, state):
        """
        切换截图模式
        
        参数:
            state: 复选框状态
        """
        self.screenshot_manager.full_screen_mode = (state == Qt.Checked)
        mode_text = "全屏截图模式" if self.screenshot_manager.full_screen_mode else "区域截图模式"
        self.status_label.setText(f'当前模式: {mode_text}')
        logger.debug(f"切换截图模式为: {mode_text}")
    
    def toggle_topmost(self):
        """
        切换窗口置顶状态
        """
        if not self.is_topmost:
            # 设置窗口置顶
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.is_topmost = True
            self.topmost_btn.setText("取消置顶")
            self.status_label.setText("窗口已置顶，按ESC键退出置顶模式")
            logger.debug("窗口已置顶")
            
            # 使用ctypes确保窗口在最顶层
            self.set_window_topmost(self)
        else:
            # 取消窗口置顶
            self.exit_topmost()
        
        # 重新显示窗口以应用新的窗口标志
        self.show()
    
    def toggle_working_mode(self):
        """
        切换工作模式
        """
        if not self.document_manager.word_doc:
            logger.warning("尝试进入工作模式但未创建文档")
            QMessageBox.warning(self, '警告', '请先创建或打开Word文档')
            return
            
        if not self.is_working_mode:
            # 进入工作模式
            logger.info("进入悬浮球模式")
            self.is_working_mode = True
            self.start_work_btn.setText("▶ 悬浮球模式 ▶")
            self.start_work_btn.setStyleSheet("""
                background-color: #f44336; 
                color: white; 
                font-weight: bold;
                font-size: 18px;
                padding: 12px;
                border-radius: 8px;
                border: 2px solid #B71C1C;
                margin: 5px;
            """)
            self.status_label.setText("已进入悬浮球模式，使用F12/Ctrl+F12快捷键截图，按ESC恢复界面")
            
            # 设置窗口置顶
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.is_topmost = True
            self.topmost_btn.setText("取消置顶")
            
            # 显示系统托盘图标
            self.tray_icon.show()
            
            # 确保快捷键在工作模式下仍然有效
            logger.debug("确保快捷键在工作模式下有效")
            
            # 创建并显示悬浮球
            logger.info("创建并显示悬浮球")
            if not self.float_ball:
                self.float_ball = FloatBall(self)
            self.float_ball.show()
            
            # 使用ctypes确保悬浮球在最顶层
            self.set_window_topmost(self.float_ball)
            
            # 隐藏主窗口
            logger.info("隐藏主窗口，进入悬浮球模式")
            self.hide()
            
            # 处理事件，确保窗口状态更新
            QApplication.processEvents()
        else:
            # 退出工作模式
            self.exit_working_mode()
    
    def exit_working_mode(self):
        """
        退出工作模式
        """
        if self.is_working_mode:
            self.is_working_mode = False
            self.start_work_btn.setText("▶ 悬浮球模式 ▶")
            self.start_work_btn.setStyleSheet("""
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold;
                font-size: 18px;
                padding: 12px;
                border-radius: 8px;
                border: 2px solid #2E7D32;
                margin: 5px;
            """)
            self.status_label.setText("已退出悬浮球模式")
            
            # 隐藏悬浮球
            if self.float_ball:
                logger.debug("隐藏悬浮球")
                self.float_ball.hide()
            
            # 显示主窗口
            logger.info("显示主窗口，退出悬浮球模式")
            self.show()
            
            logger.info("已退出悬浮球模式")
    
    def exit_topmost(self):
        """
        退出置顶模式
        """
        if self.is_topmost:
            # 取消窗口置顶
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.is_topmost = False
            self.topmost_btn.setText("窗口置顶")
            self.status_label.setText("已退出置顶模式")
            # 重新显示窗口以应用新的窗口标志
            self.show()
            
            logger.debug("已退出置顶模式")
    
    def exit_special_modes(self):
        """
        退出特殊模式（置顶模式和工作模式）
        """
        # 退出置顶模式和工作模式
        if self.is_working_mode:
            self.exit_working_mode()
        elif self.is_topmost:
            self.exit_topmost()
        else:
            # 如果窗口是透明的但不在工作模式，恢复透明度
            if self.windowOpacity() < 1.0:
                self.setWindowOpacity(1.0)
                self.show()
                
        logger.debug("已退出特殊模式")
    
    def take_fullscreen_screenshot(self):
        """
        捕获全屏截图
        """
        self.screenshot_manager.take_fullscreen_screenshot()
    
    def start_capture(self):
        """
        开始截图
        """
        logger.debug("开始截图 - 从信号触发")
        # 直接调用区域截图方法，不考虑full_screen_mode的值
        logger.debug("区域模式 - 直接调用start_area_capture")
        # 确保不会再次触发全屏截图
        self.screenshot_manager.start_area_capture(force_area=True)
    
    def process_screenshot_with_dialog(self, pixmap):
        """
        处理截图并显示对话框
        
        参数:
            pixmap: QPixmap对象，要处理的截图
        """
        self.screenshot_manager.process_screenshot_with_dialog(pixmap)
    
    def show_preview(self, pixmap, update_index=False):
        """
        在预览区域显示截图
        
        参数:
            pixmap: QPixmap对象，要显示的截图
            update_index: 布尔值，是否更新当前截图索引
        """
        logger.debug(f"开始更新预览，原始图像尺寸: {pixmap.width()}x{pixmap.height()}, 预览区域尺寸: {self.preview_label.width()}x{self.preview_label.height()}")
        
        # 保存当前预览区域的大小
        current_width = self.preview_label.width()
        current_height = self.preview_label.height()
        
        # 确保预览标签有固定的最小尺寸
        if self.preview_label.minimumHeight() < 300:
            self.preview_label.setMinimumHeight(300)
            self.preview_label.setMinimumWidth(400)  # 设置一个合理的最小宽度
        
        # 调整图像大小以适应预览区域
        preview_pixmap = pixmap.scaled(
            current_width, 
            current_height,
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        logger.debug(f"缩放后的预览图像尺寸: {preview_pixmap.width()}x{preview_pixmap.height()}")
        
        # 检查预览标签是否有效
        if self.preview_label is None:
            logger.error("预览标签对象为None")
            return
            
        # 设置预览图像
        self.preview_label.setPixmap(preview_pixmap)
        
        # 如果需要更新索引，则设置为最新截图的索引
        if update_index and self.screenshot_manager.screenshots:
            old_index = self.current_screenshot_index
            self.current_screenshot_index = len(self.screenshot_manager.screenshots) - 1
            logger.debug(f"更新当前索引: {old_index} -> {self.current_screenshot_index}")
            
        # 确保预览标签更新
        self.preview_label.update()
        
        # 确保预览标签大小不变
        self.preview_label.setFixedSize(current_width, current_height)
        
        logger.debug(f"已更新预览区域，保持固定大小: {current_width}x{current_height}")
    
    def create_word_doc(self):
        """
        创建新的Word文档
        """
        if self.document_manager.create_document():
            self.status_label.setText(f'Word文档已创建: {self.document_manager.word_path}')
            self.doc_status_label.setText(os.path.basename(self.document_manager.word_path))
            
            # 启用按钮
            self.capture_btn.setEnabled(True)
            self.save_doc_btn.setEnabled(True)
            self.start_work_btn.setEnabled(True)
            
            logger.info("成功创建Word文档")
        else:
            self.status_label.setText('创建Word文档失败')
            logger.warning("创建Word文档失败")
    
    def open_word_doc(self):
        """
        打开现有Word文档
        """
        if self.document_manager.open_document():
            self.status_label.setText(f'已打开Word文档: {self.document_manager.word_path}')
            self.doc_status_label.setText(os.path.basename(self.document_manager.word_path))
            
            # 启用按钮
            self.capture_btn.setEnabled(True)
            self.save_doc_btn.setEnabled(True)
            self.start_work_btn.setEnabled(True)
            
            logger.info("成功打开Word文档")
        else:
            self.status_label.setText('打开Word文档失败')
            logger.warning("打开Word文档失败")
    
    def save_word_doc(self):
        """
        保存当前Word文档
        """
        if self.document_manager.save_document():
            self.status_label.setText(f'Word文档已保存: {self.document_manager.word_path}')
            QMessageBox.information(self, '成功', f'已成功保存Word文档，包含 {len(self.screenshot_manager.screenshots)} 张截图')
            logger.info("成功保存Word文档")
        else:
            self.status_label.setText('保存Word文档失败')
            logger.warning("保存Word文档失败")
    
    def clear_screenshots(self):
        """
        清除所有截图
        """
        self.screenshot_manager.clear_screenshots()
    
    def keyPressEvent(self, event):
        """
        处理按键事件
        
        参数:
            event: 按键事件对象
        """
        # 记录截图状态
        self.log_screenshots_state("按键事件前")
        
        # 处理ESC键事件
        if event.key() == Qt.Key_Escape:
            self.exit_special_modes()
        # 在非工作模式下处理左右方向键
        elif not self.is_working_mode and self.isVisible():
            if event.key() == Qt.Key_Left:
                logger.debug(f"按下左方向键，显示上一张截图，当前工作模式: {self.is_working_mode}, 窗口可见: {self.isVisible()}")
                logger.debug(f"当前截图数量: {len(self.screenshot_manager.screenshots)}, 当前索引: {self.current_screenshot_index}")
                self.show_previous_screenshot()
            elif event.key() == Qt.Key_Right:
                logger.debug(f"按下右方向键，显示下一张截图，当前工作模式: {self.is_working_mode}, 窗口可见: {self.isVisible()}")
                logger.debug(f"当前截图数量: {len(self.screenshot_manager.screenshots)}, 当前索引: {self.current_screenshot_index}")
                self.show_next_screenshot()
            else:
                super().keyPressEvent(event)
        else:
            logger.debug(f"按键事件未处理，键值: {event.key()}, 当前工作模式: {self.is_working_mode}, 窗口可见: {self.isVisible()}")
            super().keyPressEvent(event)
            
        # 记录截图状态
        self.log_screenshots_state("按键事件后")
    
    def closeEvent(self, event):
        """
        处理窗口关闭事件
        
        参数:
            event: 关闭事件对象
        """
        try:
            # 注销全局热键
            self.hotkey_manager.unregister_hotkeys()
            
            # 停止热键检查定时器
            if hasattr(self, 'hotkey_check_timer') and self.hotkey_check_timer.isActive():
                self.hotkey_check_timer.stop()
            
            # 停止置顶检查定时器
            if hasattr(self, 'topmost_check_timer') and self.topmost_check_timer.isActive():
                self.topmost_check_timer.stop()
            
            # 关闭前保存文档
            if self.document_manager.word_doc and self.document_manager.word_path:
                if not self.document_manager.close_document(ask_save=True):
                    event.ignore()  # 取消关闭
                    return
            
            # 隐藏悬浮球
            if self.float_ball:
                self.float_ball.close()
            
            # 隐藏系统托盘图标
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
                
            logger.info("程序正常关闭")
            
            # 确保应用程序完全退出
            QTimer.singleShot(200, lambda: QApplication.instance().quit())
            
            event.accept()
        except Exception as e:
            logger.error(f"关闭窗口时出错: {str(e)}")
            logger.error(traceback.format_exc())
            # 强制退出应用程序
            QTimer.singleShot(500, lambda: QApplication.instance().exit(1))
    
    def show_about_dialog(self):
        """
        显示关于对话框
        """
        try:
            logger.debug("显示关于对话框")
            about_dialog = AboutDialog(self)
            about_dialog.exec_()
        except Exception as e:
            logger.error(f"显示关于对话框时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def show_main_window(self):
        """
        显示主窗口
        """
        logger.debug("显示主窗口")
        self.show()
        self.activateWindow()
        
        # 如果是置顶模式，确保窗口在最顶层
        if self.is_topmost:
            self.set_window_topmost(self)
    
    def show_previous_screenshot(self):
        """
        显示上一张截图
        """
        if not self.screenshot_manager.screenshots:
            logger.debug("没有可显示的截图")
            return
            
        # 计算上一张截图的索引
        old_index = self.current_screenshot_index
        if self.current_screenshot_index <= 0:
            # 如果当前是第一张或未设置，则循环到最后一张
            self.current_screenshot_index = len(self.screenshot_manager.screenshots) - 1
        else:
            self.current_screenshot_index -= 1
            
        logger.debug(f"切换截图索引: {old_index} -> {self.current_screenshot_index}")
            
        # 显示当前索引的截图
        pixmap = self.screenshot_manager.screenshots[self.current_screenshot_index]
        logger.debug(f"获取到截图，尺寸: {pixmap.width()}x{pixmap.height()}")
        
        # 记录预览前的状态
        logger.debug(f"显示预览前，预览标签状态: 有像素图={self.preview_label.pixmap() is not None}")
        if self.preview_label.pixmap():
            logger.debug(f"当前预览图像尺寸: {self.preview_label.pixmap().width()}x{self.preview_label.pixmap().height()}")
        
        # 显示预览
        self.show_preview(pixmap)
        
        # 记录预览后的状态
        logger.debug(f"显示预览后，预览标签状态: 有像素图={self.preview_label.pixmap() is not None}")
        if self.preview_label.pixmap():
            logger.debug(f"更新后预览图像尺寸: {self.preview_label.pixmap().width()}x{self.preview_label.pixmap().height()}")
        
        # 更新状态栏
        self.status_label.setText(f'显示第 {self.current_screenshot_index + 1}/{len(self.screenshot_manager.screenshots)} 张截图')
        logger.debug(f"显示上一张截图完成，当前索引: {self.current_screenshot_index}")
    
    def show_next_screenshot(self):
        """
        显示下一张截图
        """
        if not self.screenshot_manager.screenshots:
            logger.debug("没有可显示的截图")
            return
            
        # 计算下一张截图的索引
        old_index = self.current_screenshot_index
        if self.current_screenshot_index >= len(self.screenshot_manager.screenshots) - 1:
            # 如果当前是最后一张，则循环到第一张
            self.current_screenshot_index = 0
        else:
            self.current_screenshot_index += 1
            
        logger.debug(f"切换截图索引: {old_index} -> {self.current_screenshot_index}")
            
        # 显示当前索引的截图
        pixmap = self.screenshot_manager.screenshots[self.current_screenshot_index]
        logger.debug(f"获取到截图，尺寸: {pixmap.width()}x{pixmap.height()}")
        
        # 记录预览前的状态
        logger.debug(f"显示预览前，预览标签状态: 有像素图={self.preview_label.pixmap() is not None}")
        if self.preview_label.pixmap():
            logger.debug(f"当前预览图像尺寸: {self.preview_label.pixmap().width()}x{self.preview_label.pixmap().height()}")
        
        # 显示预览
        self.show_preview(pixmap)
        
        # 记录预览后的状态
        logger.debug(f"显示预览后，预览标签状态: 有像素图={self.preview_label.pixmap() is not None}")
        if self.preview_label.pixmap():
            logger.debug(f"更新后预览图像尺寸: {self.preview_label.pixmap().width()}x{self.preview_label.pixmap().height()}")
        
        # 更新状态栏
        self.status_label.setText(f'显示第 {self.current_screenshot_index + 1}/{len(self.screenshot_manager.screenshots)} 张截图')
        logger.debug(f"显示下一张截图完成，当前索引: {self.current_screenshot_index}")
    
    def set_window_topmost(self, window):
        """
        使用ctypes设置窗口为最顶层
        
        参数:
            window: 要设置为最顶层的窗口
        """
        try:
            if window and window.isVisible():
                # 获取窗口句柄
                hwnd = int(window.winId())
                
                # 先尝试激活窗口
                ctypes.windll.user32.BringWindowToTop(hwnd)
                
                # 设置为最顶层窗口
                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    HWND_TOPMOST,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                )
                
                # 再次确认置顶
                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    HWND_TOPMOST,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                )
                
                # logger.debug(f"已将窗口设置为最顶层: {window.__class__.__name__}")
                
                # 延迟再次确认置顶
                QTimer.singleShot(100, lambda: self._delayed_topmost(window))
        except Exception as e:
            logger.error(f"设置窗口为最顶层时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _delayed_topmost(self, window):
        """
        延迟再次确认窗口置顶
        
        参数:
            window: 要设置为最顶层的窗口
        """
        try:
            if window and window.isVisible():
                hwnd = int(window.winId())
                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    HWND_TOPMOST,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                )
        except Exception as e:
            logger.error(f"延迟设置窗口为最顶层时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def check_topmost(self):
        """
        检查并确保窗口置顶
        """
        try:
            # 如果主窗口是置顶的，确保它保持置顶
            if self.is_topmost and self.isVisible():
                self.set_window_topmost(self)
            
            # 如果在工作模式下，确保悬浮球保持置顶
            if self.is_working_mode and self.float_ball and self.float_ball.isVisible():
                self.set_window_topmost(self.float_ball)
        except Exception as e:
            logger.error(f"检查并确保窗口置顶时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def log_screenshots_state(self, context=""):
        """
        记录截图列表的当前状态
        
        参数:
            context: 上下文信息，用于标识日志来源
        """
        logger.debug(f"{context} - 截图列表状态: 数量={len(self.screenshot_manager.screenshots)}, 当前索引={self.current_screenshot_index}")
        if self.screenshot_manager.screenshots:
            for i, pixmap in enumerate(self.screenshot_manager.screenshots):
                logger.debug(f"  截图[{i}]: 尺寸={pixmap.width()}x{pixmap.height()}, {'当前' if i == self.current_screenshot_index else ''}") 
    
    def eventFilter(self, obj, event):
        """
        事件过滤器方法，处理所有被监听的事件
        
        参数:
            obj: 产生事件的对象
            event: 事件对象
            
        返回:
            bool: 如果事件被处理则返回True，否则返回False
        """
        # 处理预览标签的双击事件
        if obj == self.preview_label and event.type() == QEvent.MouseButtonDblClick:
            logger.debug("检测到预览标签的双击事件")
            self.show_fullscreen_preview()
            return True
            
        # 对于未处理的事件，调用基类方法
        return super().eventFilter(obj, event)
    
    def show_fullscreen_preview(self):
        """
        显示全屏预览
        """
        try:
            # 检查是否有截图可供显示
            if not self.screenshot_manager.screenshots or self.current_screenshot_index < 0:
                logger.debug("没有截图可供全屏显示")
                return
                
            # 获取当前显示的截图
            pixmap = self.screenshot_manager.screenshots[self.current_screenshot_index]
            logger.debug(f"准备全屏显示截图，索引: {self.current_screenshot_index}, 尺寸: {pixmap.width()}x{pixmap.height()}")
            
            # 创建并显示全屏图片查看器，传递当前索引和总数
            total_screenshots = len(self.screenshot_manager.screenshots)
            viewer = FullscreenImageViewer(
                pixmap, 
                self, 
                index=self.current_screenshot_index,
                total=total_screenshots
            )
            
            # 确保窗口置顶
            if hasattr(self, 'set_window_topmost'):
                self.set_window_topmost(viewer)
                
            # 使用exec_()模态显示对话框
            viewer.exec_()
            
            logger.debug("全屏图片查看器已关闭")
        except Exception as e:
            logger.error(f"显示全屏预览时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def take_auto_save_screenshot(self):
        """
        捕获截图并自动保存，不显示对话框
        """
        logger.info("触发自动保存截图快捷键 F11")
        try:
            # 检查文档是否已创建
            if not self.document_manager or not hasattr(self.document_manager, 'word_doc') or not self.document_manager.word_doc:
                if not self.is_working_mode:  # 只在非工作模式下显示警告
                    logger.warning("尝试自动保存截图但未创建文档")
                    QMessageBox.warning(self, '警告', '请先创建或打开Word文档')
                return
            
            # 确保窗口状态正确
            try:
                self.ensure_window_state_for_screenshot()
            except Exception as e:
                logger.error(f"确保窗口状态时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为窗口状态问题而中断
            
            # 根据当前模式决定截图方式
            try:
                if hasattr(self.screenshot_manager, 'full_screen_mode') and self.screenshot_manager.full_screen_mode:
                    # 全屏截图模式
                    logger.debug("自动保存模式 - 全屏截图")
                    # 获取全屏截图
                    screen = QApplication.primaryScreen()
                    if not screen:
                        logger.error("无法获取主屏幕")
                        return
                        
                    pixmap = screen.grabWindow(0)
                    if pixmap and not pixmap.isNull():
                        # 自动保存截图
                        logger.debug("获取到全屏截图，准备自动保存")
                        self.screenshot_manager.process_screenshot_auto_save(pixmap)
                    else:
                        logger.error("自动保存模式 - 全屏截图失败，截图为空")
                else:
                    # 区域截图模式
                    logger.debug("自动保存模式 - 区域截图")
                    # 创建区域截图窗口，但设置为自动保存模式
                    self.screenshot_manager.start_area_capture(auto_save=True)
            except Exception as e:
                logger.error(f"执行截图操作时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 显示错误通知
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.showMessage("截图失败", f"自动保存截图时出错: {str(e)}", QSystemTrayIcon.Critical, 3000)
        except Exception as e:
            logger.error(f"自动保存截图时出错: {str(e)}")
            logger.error(traceback.format_exc())
            # 显示错误通知
            if hasattr(self, 'tray_icon'):
                self.tray_icon.showMessage("截图失败", f"自动保存截图时出错: {str(e)}", QSystemTrayIcon.Critical, 3000) 