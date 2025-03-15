"""
悬浮球窗口模块
用于在工作模式下显示一个可拖动的小图标
"""

import traceback
import time
import ctypes
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu, QAction, QApplication
from PyQt5.QtCore import Qt, QPoint, QTimer, QSize, QMetaObject, Q_ARG
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
            
            # 保存原始图标作为实例变量，以便在恢复样式时使用
            self.default_icon = QPixmap(rounded_pixmap)
            
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
            
            auto_save_action = QAction("自动保存截图 (F11)", self)
            auto_save_action.triggered.connect(
                lambda: self.parent_window.take_auto_save_screenshot()
            )
            
            exit_action = QAction("显示界面", self)
            exit_action.triggered.connect(
                lambda: self.parent_window.exit_working_mode()
            )
            
            # 添加到菜单
            menu.addAction(full_screenshot_action)
            menu.addAction(area_screenshot_action)
            menu.addAction(auto_save_action)
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
    
    def show_success_tip(self, message="截图已保存"):
        """
        显示成功提示，几秒后自动消失
        
        参数:
            message: 要显示的提示信息
        """
        try:
            # 简化消息格式 - 如果是"第 x 张截图已保存"格式的消息，转换为"savex"格式
            if "截图已保存" in message:
                try:
                    # 提取截图序号
                    import re
                    match = re.search(r'第\s*(\d+)\s*张', message)
                    if match:
                        num = match.group(1)
                        message = f"save{num}"
                    else:
                        message = "saved"
                except Exception as e:
                    logger.error(f"简化消息格式时出错: {str(e)}")
                    message = "saved"  # 默认简化消息
            
            logger.debug(f"开始显示悬浮球成功提示: '{message}'")
            logger.debug(f"当前悬浮球状态: 可见={self.isVisible()}, 大小={self.size().width()}x{self.size().height()}")
            
            # 检查组件是否存在
            if not hasattr(self, 'icon_label'):
                logger.error("悬浮球图标标签属性不存在，无法显示提示")
                return
                
            if self.icon_label is None:
                logger.error("悬浮球图标标签为None，无法显示提示")
                return
                
            logger.debug(f"icon_label状态: 可见={self.icon_label.isVisible()}, 大小={self.icon_label.size().width()}x{self.icon_label.size().height()}")
            
            # 先保存原始状态，确保在恢复时有正确的值
            try:
                logger.debug("开始保存原始样式和图标")
                
                # 保存原始样式表
                self.original_style = self.icon_label.styleSheet()
                logger.debug(f"已保存原始样式表: {self.original_style[:50]}...")  # 只记录前50个字符
                
                # 保存原始图像
                original_pixmap = self.icon_label.pixmap()
                if original_pixmap is None:
                    logger.warning("原始图像为None")
                    self.original_pixmap = None
                elif original_pixmap.isNull():
                    logger.warning("原始图像为空")
                    self.original_pixmap = None
                else:
                    # 创建深拷贝
                    self.original_pixmap = QPixmap(original_pixmap)
                    logger.debug(f"已保存原始图像，尺寸: {self.original_pixmap.width()}x{self.original_pixmap.height()}")
                
                # 保存原始大小
                self.original_size = QSize(self.size())
                logger.debug(f"已保存原始大小: {self.original_size.width()}x{self.original_size.height()}")
            except Exception as e:
                logger.error(f"保存原始样式时出错: {str(e)}")
                logger.error(traceback.format_exc())
                return
            
            # 设置成功提示样式
            try:
                logger.debug("开始设置成功提示样式")
                self.icon_label.setStyleSheet("""
                    background-color: rgba(46, 125, 50, 200);
                    color: white;
                    border-radius: 15px;
                    padding: 5px;
                    font-weight: bold;
                    font-size: 12px;
                """)
                logger.debug("成功提示样式设置完成")
            except Exception as e:
                logger.error(f"设置提示样式时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为样式问题而中断
            
            # 创建一个带有文字的新图像 - 使用更小的尺寸
            try:
                logger.debug("开始创建提示图像")
                # 减小图像尺寸，以适应更短的文本
                success_pixmap = QPixmap(100, 40)  # 将200x70减小到100x40
                if success_pixmap.isNull():
                    logger.error("创建提示图像失败，QPixmap为空")
                    return
                    
                logger.debug("填充透明背景")
                success_pixmap.fill(Qt.transparent)
                
                logger.debug("开始绘制提示图像")
                painter = QPainter(success_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QColor(46, 125, 50, 220))  # 半透明绿色背景，稍微不那么透明
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(success_pixmap.rect(), 15, 15)  # 减小圆角半径
                
                # 绘制文字 - 使用更小的字体
                logger.debug(f"绘制文字: '{message}'")
                painter.setPen(Qt.white)
                font = self.font()
                font.setPointSize(12)  # 减小字体大小
                font.setBold(True)     # 保持粗体
                painter.setFont(font)
                painter.drawText(success_pixmap.rect(), Qt.AlignCenter, message)  # 移除✓符号，直接显示简化的消息
                painter.end()
                logger.debug("提示图像创建完成")
            except Exception as e:
                logger.error(f"创建提示图像时出错: {str(e)}")
                logger.error(traceback.format_exc())
                return
            
            # 临时调整窗口大小以适应提示
            try:
                logger.debug(f"调整窗口大小为: {success_pixmap.width()}x{success_pixmap.height()}")
                
                # 先调整icon_label大小
                if hasattr(self, 'icon_label') and self.icon_label:
                    self.icon_label.setMinimumSize(success_pixmap.width(), success_pixmap.height())
                    self.icon_label.setMaximumSize(success_pixmap.width(), success_pixmap.height())
                    logger.debug(f"已调整icon_label大小为: {success_pixmap.width()}x{success_pixmap.height()}")
                
                # 然后调整窗口大小
                self.safe_resize(success_pixmap.width(), success_pixmap.height())
                logger.debug("窗口大小调整完成")
            except Exception as e:
                logger.error(f"调整窗口大小时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为大小调整问题而中断
            
            # 设置新图像
            try:
                logger.debug("设置新图像到icon_label")
                self.icon_label.setPixmap(success_pixmap)
                self.icon_label.setScaledContents(True)  # 确保图像缩放以填充标签
                logger.debug("新图像设置完成")
            except Exception as e:
                logger.error(f"设置提示图像时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 尝试恢复原始状态
                self.restore_default_style()
                return
            
            # 创建一个定时器，几秒后恢复原样
            try:
                logger.debug("创建恢复定时器，2000毫秒后执行")
                
                # 创建一个新的定时器对象，并保存为实例变量，避免被垃圾回收
                if hasattr(self, 'restore_timer') and self.restore_timer:
                    # 如果已经有定时器，先停止它
                    self.restore_timer.stop()
                
                self.restore_timer = QTimer(self)  # 使用self作为父对象，确保不会被垃圾回收
                self.restore_timer.setSingleShot(True)
                self.restore_timer.timeout.connect(self.restore_default_style)
                self.restore_timer.start(2000)
                
                logger.debug("恢复定时器创建完成")
            except Exception as e:
                logger.error(f"创建恢复定时器时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 立即尝试恢复原始状态
                self.restore_default_style()
            
            logger.debug("成功提示显示完成")
            
        except Exception as e:
            logger.error(f"显示成功提示时出错: {str(e)}")
            logger.error(traceback.format_exc())
            # 尝试恢复正常状态
            self.restore_default_style()
    
    def restore_default_style(self):
        """
        恢复默认样式，由定时器调用
        """
        try:
            logger.debug("定时器触发，恢复默认样式")
            
            # 检查窗口是否仍然有效
            if not self or not self.isVisible() or self.isHidden():
                logger.warning("窗口已不可见或已销毁，跳过恢复样式")
                return
                
            # 使用最简单的方式恢复 - 先恢复大小，再清除样式
            try:
                logger.debug("使用简单方式恢复样式")
                
                # 先恢复大小
                self.safe_resize(50, 50)
                logger.debug("恢复大小为50x50")
                
                # 调整icon_label大小
                if hasattr(self, 'icon_label') and self.icon_label:
                    self.icon_label.setScaledContents(False)  # 关闭缩放模式
                    self.icon_label.setMinimumSize(1, 1)  # 重置最小大小
                    self.icon_label.setMaximumSize(16777215, 16777215)  # 重置最大大小
                    logger.debug("已重置icon_label大小限制")
                
                # 清除样式表
                if hasattr(self, 'icon_label') and self.icon_label:
                    self.icon_label.setStyleSheet("")
                    logger.debug("清除样式表成功")
                
                # 使用初始化时保存的默认图标
                if hasattr(self, 'default_icon') and self.default_icon and not self.default_icon.isNull():
                    if hasattr(self, 'icon_label') and self.icon_label:
                        self.icon_label.setPixmap(self.default_icon)
                        logger.debug("使用默认图标恢复成功")
                else:
                    # 如果没有默认图标，尝试创建一个简单的圆形图标
                    try:
                        # 获取系统图标
                        if self.parent_window:
                            pixmap = self.parent_window.style().standardIcon(
                                self.parent_window.style().SP_ComputerIcon
                            ).pixmap(32, 32)
                            
                            if pixmap and not pixmap.isNull():
                                # 创建一个简单的圆形背景
                                rounded_pixmap = QPixmap(32, 32)
                                rounded_pixmap.fill(Qt.transparent)
                                
                                painter = QPainter(rounded_pixmap)
                                if painter.isActive():
                                    painter.setRenderHint(QPainter.Antialiasing)
                                    painter.setBrush(QColor(76, 175, 80, 200))  # 半透明绿色背景
                                    painter.setPen(Qt.NoPen)
                                    painter.drawEllipse(rounded_pixmap.rect())
                                    
                                    # 在中心绘制图标
                                    painter.drawPixmap(0, 0, pixmap)
                                    painter.end()
                                    
                                    # 设置图标
                                    if hasattr(self, 'icon_label') and self.icon_label:
                                        self.icon_label.setPixmap(rounded_pixmap)
                                        logger.debug("设置简单圆形图标成功")
                    except Exception as e:
                        logger.error(f"创建简单圆形图标时出错: {str(e)}")
                        logger.error(traceback.format_exc())
                        
                        # 如果创建图标失败，尝试使用保存的原始图像
                        if hasattr(self, 'original_pixmap') and self.original_pixmap and not self.original_pixmap.isNull():
                            if hasattr(self, 'icon_label') and self.icon_label:
                                self.icon_label.setPixmap(self.original_pixmap)
                                logger.debug("使用保存的原始图像恢复")
            
            except Exception as e:
                logger.error(f"使用简单方式恢复样式时出错: {str(e)}")
                logger.error(traceback.format_exc())
                
                # 如果简单恢复失败，尝试使用保存的原始状态
                try:
                    logger.debug("尝试使用保存的原始状态恢复")
                    
                    # 恢复样式
                    if hasattr(self, 'original_style') and hasattr(self, 'icon_label') and self.icon_label:
                        self.icon_label.setStyleSheet(self.original_style)
                        logger.debug("恢复原始样式表成功")
                    
                    # 恢复图像
                    if hasattr(self, 'original_pixmap') and self.original_pixmap and not self.original_pixmap.isNull():
                        if hasattr(self, 'icon_label') and self.icon_label:
                            self.icon_label.setPixmap(self.original_pixmap)
                            logger.debug("恢复原始图像成功")
                    
                    # 恢复大小
                    if hasattr(self, 'original_size'):
                        self.safe_resize(self.original_size.width(), self.original_size.height())
                        logger.debug(f"恢复原始大小成功: {self.original_size.width()}x{self.original_size.height()}")
                except Exception as ex:
                    logger.error(f"使用保存的原始状态恢复时出错: {str(ex)}")
                    logger.error(traceback.format_exc())
            
            # 清理引用
            if hasattr(self, 'restore_timer'):
                self.restore_timer = None
            if hasattr(self, 'original_style'):
                self.original_style = None
            if hasattr(self, 'original_pixmap'):
                self.original_pixmap = None
            if hasattr(self, 'original_size'):
                self.original_size = None
                
            logger.debug("恢复默认样式完成")
            
        except Exception as e:
            logger.error(f"恢复默认样式时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def safe_resize(self, width, height):
        """
        安全地调整窗口大小
        
        参数:
            width: 宽度
            height: 高度
        """
        try:
            # 检查窗口是否仍然有效
            if not self or not self.isVisible() or self.isHidden():
                logger.warning("窗口已不可见或已销毁，跳过调整大小")
                return
                
            logger.debug(f"尝试调整窗口大小为: {width}x{height}")
            
            # 先取消固定大小约束
            self.setMinimumSize(1, 1)
            self.setMaximumSize(16777215, 16777215)  # Qt的最大值
            
            # 再使用resize
            self.resize(width, height)
            
            # 等待处理事件，让resize生效
            QApplication.processEvents()
            
            # 然后使用setFixedSize
            self.setFixedSize(width, height)
            
            # 再次处理事件
            QApplication.processEvents()
            
            # 记录实际调整后的大小
            logger.debug(f"调整后的实际大小: {self.width()}x{self.height()}")
            
            # 如果调整失败，记录警告
            if self.width() != width or self.height() != height:
                logger.warning(f"大小调整不匹配: 当前={self.width()}x{self.height()}, 目标={width}x{height}")
                
        except Exception as e:
            logger.error(f"安全调整大小时出错: {str(e)}")
            logger.error(traceback.format_exc()) 