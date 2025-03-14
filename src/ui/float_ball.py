"""
悬浮球窗口模块
用于在工作模式下显示一个可拖动的小图标
"""

import traceback
import time
import ctypes
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu, QAction
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QCursor
from src.utils.logger import logger

# 定义Windows API常量
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

class FloatBall(QWidget):
    """
    悬浮球窗口类
    在工作模式下显示一个可拖动的小图标，点击可触发截图
    """
    
    def __init__(self, parent=None):
        """
        初始化悬浮球窗口
        
        参数:
            parent: 父窗口，通常是主窗口
        """
        super().__init__(None)  # 使用None作为父窗口，使其成为顶级窗口
        logger.debug("初始化悬浮球窗口")
        
        self.parent_window = parent
        self.dragging = False
        self.offset = QPoint()
        
        # 双击检测
        self.last_click_time = 0
        self.double_click_interval = 300  # 毫秒
        
        self.initUI()
        
        # 设置定时器，定期确保窗口在最顶层
        self.topmost_timer = QTimer(self)
        self.topmost_timer.timeout.connect(self.ensure_topmost)
        self.topmost_timer.start(200)  # 每200毫秒检查一次
    
    def initUI(self):
        """
        初始化用户界面
        """
        try:
            # 设置窗口属性
            self.setWindowFlags(
                Qt.FramelessWindowHint |  # 无边框
                Qt.WindowStaysOnTopHint |  # 置顶
                Qt.Tool  # 工具窗口，不在任务栏显示
            )
            self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
            
            # 设置窗口大小
            self.setFixedSize(50, 50)
            
            # 创建布局
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            
            # 创建图标标签
            self.icon_label = QLabel()
            self.icon_label.setAlignment(Qt.AlignCenter)
            
            # 设置图标 - 使用系统图标
            pixmap = self.parent_window.style().standardIcon(
                self.parent_window.style().SP_ComputerIcon
            ).pixmap(32, 32)
            
            # 将图标设置为圆形
            rounded_pixmap = QPixmap(pixmap.size())
            rounded_pixmap.fill(Qt.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(76, 175, 80, 200))  # 半透明绿色背景
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rounded_pixmap.rect())
            painter.drawPixmap(
                (rounded_pixmap.width() - pixmap.width()) // 2,
                (rounded_pixmap.height() - pixmap.height()) // 2,
                pixmap
            )
            painter.end()
            
            self.icon_label.setPixmap(rounded_pixmap)
            layout.addWidget(self.icon_label)
            
            self.setLayout(layout)
            
            # 设置工具提示
            self.setToolTip("点击截图，双击显示主窗口，右键显示菜单，拖动移动位置\nF12=全屏截图，Ctrl+F12=区域截图")
            
            # 初始位置 - 屏幕右侧中间
            desktop = self.parent_window.screen().availableGeometry()
            self.move(desktop.width() - self.width() - 20, desktop.height() // 2)
            
            logger.debug("悬浮球窗口UI初始化完成")
        except Exception as e:
            logger.error(f"初始化悬浮球窗口UI时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def showEvent(self, event):
        """
        窗口显示事件处理
        
        参数:
            event: 事件对象
        """
        super().showEvent(event)
        # 确保窗口在最顶层
        self.ensure_topmost()
        # 立即再次确保置顶，防止其他应用抢占
        QTimer.singleShot(100, self.ensure_topmost)
        QTimer.singleShot(500, self.ensure_topmost)
    
    def ensure_topmost(self):
        """
        确保窗口始终在最顶层
        使用ctypes设置窗口为TOPMOST
        """
        try:
            if self.isVisible():
                # 获取窗口句柄
                hwnd = int(self.winId())
                
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
                
                # logger.debug("已将悬浮球设置为最顶层窗口")
        except Exception as e:
            logger.error(f"设置悬浮球为最顶层窗口时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def activateWindow(self):
        """
        重写激活窗口方法，确保在激活时置顶
        """
        super().activateWindow()
        self.ensure_topmost()
    
    def moveEvent(self, event):
        """
        窗口移动事件处理
        
        参数:
            event: 事件对象
        """
        super().moveEvent(event)
        # 移动后确保窗口在最顶层
        self.ensure_topmost()
    
    def mousePressEvent(self, event):
        """
        鼠标按下事件处理
        
        参数:
            event: 鼠标事件对象
        """
        try:
            if event.button() == Qt.LeftButton:
                # 左键点击 - 开始拖动或触发截图
                self.dragging = True
                self.offset = event.pos()
                
                # 如果是单击而非拖动开始，将在mouseReleaseEvent中处理
                
            elif event.button() == Qt.RightButton:
                # 右键点击 - 显示菜单
                self.showContextMenu(event.globalPos())
                
            event.accept()
        except Exception as e:
            logger.error(f"处理鼠标按下事件时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def mouseMoveEvent(self, event):
        """
        鼠标移动事件处理
        
        参数:
            event: 鼠标事件对象
        """
        try:
            if self.dragging and (event.buttons() & Qt.LeftButton):
                # 计算新位置
                new_pos = event.globalPos() - self.offset
                self.move(new_pos)
                event.accept()
        except Exception as e:
            logger.error(f"处理鼠标移动事件时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件处理
        
        参数:
            event: 鼠标事件对象
        """
        try:
            if event.button() == Qt.LeftButton:
                # 检查是否是拖动还是点击
                if self.dragging and (self.pos() == event.globalPos() - self.offset):
                    # 位置没有变化，视为点击
                    current_time = time.time() * 1000  # 转换为毫秒
                    
                    # 检查是否是双击
                    if current_time - self.last_click_time < self.double_click_interval:
                        logger.debug("悬浮球被双击，显示主窗口")
                        if self.parent_window:
                            self.parent_window.show_main_window()
                        self.last_click_time = 0  # 重置点击时间
                    else:
                        # 单击，触发截图
                        logger.debug("悬浮球被单击，触发全屏截图")
                        if self.parent_window:
                            self.parent_window.take_fullscreen_screenshot()
                        self.last_click_time = current_time
                
                self.dragging = False
                event.accept()
        except Exception as e:
            logger.error(f"处理鼠标释放事件时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def showContextMenu(self, pos):
        """
        显示右键菜单
        
        参数:
            pos: 菜单显示位置
        """
        try:
            menu = QMenu()
            
            # 添加菜单项
            full_screenshot_action = QAction("全屏截图 (F12)", self)
            full_screenshot_action.triggered.connect(
                lambda: self.parent_window.take_fullscreen_screenshot()
            )
            
            area_screenshot_action = QAction("区域截图 (Ctrl+F12)", self)
            area_screenshot_action.triggered.connect(
                lambda: self.parent_window.start_capture()
            )
            
            exit_action = QAction("退出工作模式", self)
            exit_action.triggered.connect(
                lambda: self.parent_window.exit_working_mode()
            )
            
            # 添加到菜单
            menu.addAction(full_screenshot_action)
            menu.addAction(area_screenshot_action)
            menu.addSeparator()
            menu.addAction(exit_action)
            
            # 显示菜单
            menu.exec_(pos)
        except Exception as e:
            logger.error(f"显示右键菜单时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def enterEvent(self, event):
        """
        鼠标进入事件处理
        
        参数:
            event: 事件对象
        """
        try:
            # 鼠标进入时改变光标形状
            self.setCursor(Qt.PointingHandCursor)
            event.accept()
        except Exception as e:
            logger.error(f"处理鼠标进入事件时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def leaveEvent(self, event):
        """
        鼠标离开事件处理
        
        参数:
            event: 事件对象
        """
        try:
            # 鼠标离开时恢复光标形状
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        except Exception as e:
            logger.error(f"处理鼠标离开事件时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        
        参数:
            event: 关闭事件对象
        """
        try:
            logger.debug("悬浮球窗口关闭")
            event.accept()
        except Exception as e:
            logger.error(f"处理窗口关闭事件时出错: {str(e)}")
            logger.error(traceback.format_exc()) 