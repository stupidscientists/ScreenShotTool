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
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeySequence, QPixmap
from src.utils.logger import logger
from src.utils.event_filter import GlobalEventFilter
from src.utils.hotkey_manager import HotkeyManager
from src.core.document_manager import DocumentManager
from src.core.screenshot_manager import ScreenshotManager
from src.ui.about_dialog import AboutDialog
from src.ui.float_ball import FloatBall

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
        
        # 初始化管理器
        self.document_manager = DocumentManager(self)
        self.screenshot_manager = ScreenshotManager(self)
        self.hotkey_manager = HotkeyManager(self)
        
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
            logger.error(traceback.format_exc())
    
    def setup_shortcuts(self):
        """
        设置应用程序快捷键
        """
        logger.info("设置应用程序快捷键")
        try:
            # 设置快捷键 - F12全屏截图，Ctrl+F12区域截图
            self.fullscreen_shortcut = QShortcut(QKeySequence("F12"), self)
            self.fullscreen_shortcut.activated.connect(self.take_fullscreen_screenshot)
            logger.debug("已设置F12全屏截图快捷键")
            
            self.area_shortcut = QShortcut(QKeySequence("Ctrl+F12"), self)
            self.area_shortcut.activated.connect(self.start_capture)
            logger.debug("已设置Ctrl+F12区域截图快捷键")
            
            # ESC键退出置顶/工作模式
            self.esc_shortcut = QShortcut(QKeySequence("Escape"), self)
            self.esc_shortcut.activated.connect(self.exit_special_modes)
            logger.debug("已设置ESC退出快捷键")
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
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(screenshot_action)
        tray_menu.addAction(area_screenshot_action)
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
        self.setGeometry(300, 300, 500, 550)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # 工作模式区域 - 特殊显示
        work_frame = QWidget()
        work_frame.setStyleSheet("""
            background-color: #E8F5E9;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            margin: 5px;
        """)
        work_layout = QVBoxLayout(work_frame)
        
        # 添加标题标签
        title_label = QLabel("快速操作")
        title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #2E7D32;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        work_layout.addWidget(title_label)
        
        # 创建开始工作按钮
        self.start_work_btn = QPushButton('▶ 开始工作 ▶')
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
        self.start_work_btn.setMinimumHeight(60)
        self.start_work_btn.setCursor(Qt.PointingHandCursor)  # 鼠标悬停时显示手型光标
        work_layout.addWidget(self.start_work_btn)
        
        # 添加提示标签
        hint_label = QLabel("点击开始自动截图模式")
        hint_label.setStyleSheet("color: #555; font-style: italic;")
        hint_label.setAlignment(Qt.AlignCenter)
        work_layout.addWidget(hint_label)
        
        # 文档操作区域
        doc_layout = QHBoxLayout()
        self.create_doc_btn = QPushButton('创建新文档')
        self.open_doc_btn = QPushButton('打开现有文档')
        self.save_doc_btn = QPushButton('保存文档')
        doc_layout.addWidget(self.create_doc_btn)
        doc_layout.addWidget(self.open_doc_btn)
        doc_layout.addWidget(self.save_doc_btn)
        
        # 截图操作区域
        screenshot_layout = QHBoxLayout()
        self.capture_btn = QPushButton('截取屏幕')
        self.clear_btn = QPushButton('清除所有截图')
        screenshot_layout.addWidget(self.capture_btn)
        screenshot_layout.addWidget(self.clear_btn)
        
        # 截图模式选择
        mode_layout = QHBoxLayout()
        self.full_screen_checkbox = QCheckBox('全屏截图模式')
        self.full_screen_checkbox.setChecked(True)
        self.topmost_btn = QPushButton('窗口置顶')
        mode_layout.addWidget(self.full_screen_checkbox)
        mode_layout.addWidget(self.topmost_btn)
        
        # 快捷键提示
        shortcut_label = QLabel('快捷键: F12 = 全屏截图, Ctrl+F12 = 区域截图, ESC = 退出置顶/工作模式')
        shortcut_label.setAlignment(Qt.AlignCenter)
        
        # 文档状态
        doc_status_layout = QHBoxLayout()
        doc_status_layout.addWidget(QLabel('当前文档:'))
        self.doc_status_label = QLabel('未选择文档')
        doc_status_layout.addWidget(self.doc_status_label)
        
        # 截图计数
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel('已截图数量:'))
        self.screenshot_count = QLabel('0')
        count_layout.addWidget(self.screenshot_count)
        count_layout.addStretch()
        
        # 添加关于按钮
        self.about_btn = QPushButton('关于')
        self.about_btn.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            font-weight: bold;
            padding: 5px;
            border-radius: 4px;
        """)
        count_layout.addWidget(self.about_btn)
        
        # 创建预览区域
        self.preview_label = QLabel('截图预览区域')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid black;")
        self.preview_label.setMinimumHeight(300)
        
        # 状态标签
        self.status_label = QLabel('请先创建或打开Word文档')
        
        # 添加所有组件到主布局
        main_layout.addWidget(work_frame)  # 添加带有特殊样式的工作模式框架
        main_layout.addSpacing(10)  # 添加一些间距
        main_layout.addLayout(doc_layout)
        main_layout.addLayout(screenshot_layout)
        main_layout.addLayout(mode_layout)
        main_layout.addWidget(shortcut_label)
        main_layout.addLayout(doc_status_layout)
        main_layout.addLayout(count_layout)
        main_layout.addWidget(self.preview_label)
        main_layout.addWidget(self.status_label)
        
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
            logger.info("进入工作模式")
            self.is_working_mode = True
            self.start_work_btn.setText("■ 结束工作 ■")
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
            self.status_label.setText("已进入工作模式，使用F12/Ctrl+F12快捷键截图，按ESC恢复界面")
            
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
            logger.info("隐藏主窗口，进入工作模式")
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
            self.start_work_btn.setText("▶ 开始工作 ▶")
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
            self.status_label.setText("已退出工作模式")
            
            # 隐藏悬浮球
            if self.float_ball:
                logger.debug("隐藏悬浮球")
                self.float_ball.hide()
            
            # 显示主窗口
            logger.info("显示主窗口，退出工作模式")
            self.show()
            
            logger.info("已退出工作模式")
    
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
    
    def show_preview(self, pixmap):
        """
        在预览区域显示截图
        
        参数:
            pixmap: QPixmap对象，要显示的截图
        """
        # 调整图像大小以适应预览区域
        preview_pixmap = pixmap.scaled(
            self.preview_label.width(), 
            self.preview_label.height(),
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(preview_pixmap)
        logger.debug("已更新预览区域")
    
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
        # 处理ESC键事件
        if event.key() == Qt.Key_Escape:
            self.exit_special_modes()
        else:
            super().keyPressEvent(event)
    
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