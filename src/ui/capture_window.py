"""
截图窗口模块
用于实现区域截图功能
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint, QRect, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath
from src.utils.logger import logger
from PyQt5.QtWidgets import QApplication

class CaptureWindow(QWidget):
    """
    截图窗口类
    用于实现区域截图功能，允许用户通过鼠标选择截图区域
    """
    
    def __init__(self, parent=None):
        """
        初始化截图窗口
        
        参数:
            parent: 父窗口，通常是主窗口
        """
        super().__init__()
        logger.debug("初始化截图窗口")
        self.parent_window = parent
        
        # 获取全屏截图
        self.screenshot = QApplication.primaryScreen().grabWindow(0)
        logger.debug(f"获取全屏截图，尺寸: {self.screenshot.width()}x{self.screenshot.height()}")
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color:transparent;")
        self.setCursor(Qt.CrossCursor)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_drawing = False
        self.auto_save_mode = False  # 是否自动保存模式
        self.float_ball_visible = False  # 记录悬浮球是否应该可见
    
    def paintEvent(self, event):
        """
        绘制事件处理
        绘制截图背景和选择框
        
        参数:
            event: 绘制事件对象
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制原始截图
        painter.drawPixmap(self.rect(), self.screenshot)
        
        # 创建半透明遮罩
        mask_color = QColor(0, 0, 0, 128)  # 使用更深的半透明黑色
        painter.fillRect(self.rect(), mask_color)
        
        if self.is_drawing and not self.begin.isNull() and not self.end.isNull():
            # 计算选择区域
            rect = QRect(self.begin, self.end).normalized()
            
            # 创建选择区域的路径
            path = QPainterPath()
            path.addRect(QRectF(rect))  # 将QRect转换为QRectF
            
            # 创建遮罩路径（整个窗口减去选择区域）
            mask_path = QPainterPath()
            mask_path.addRect(QRectF(self.rect()))  # 将QRect转换为QRectF
            mask_path = mask_path.subtracted(path)
            
            # 绘制遮罩
            painter.fillPath(mask_path, mask_color)
            
            # 绘制选择框边框
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(rect)
            
            # 在选择框周围显示尺寸信息
            painter.setPen(QPen(Qt.white, 1))
            size_text = f"{abs(rect.width())} x {abs(rect.height())}"
            painter.drawText(rect.bottomRight() + QPoint(5, 15), size_text)
    
    def keyPressEvent(self, event):
        """
        按键事件处理
        处理ESC键退出截图
        
        参数:
            event: 按键事件对象
        """
        if event.key() == Qt.Key_Escape:
            logger.debug("用户按下ESC键取消截图")
            self.close()
            self.restore_parent_window()
    
    def mousePressEvent(self, event):
        """
        鼠标按下事件处理
        开始绘制选择框
        
        参数:
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            logger.debug("用户开始绘制选择框")
            self.begin = event.pos()
            self.end = event.pos()
            self.is_drawing = True
            self.update()
    
    def mouseMoveEvent(self, event):
        """
        鼠标移动事件处理
        更新选择框大小
        
        参数:
            event: 鼠标事件对象
        """
        if self.is_drawing:
            self.end = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """
        鼠标释放事件处理
        完成选择框绘制并捕获截图
        
        参数:
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton and self.is_drawing:
            logger.debug("用户完成绘制选择框")
            self.end = event.pos()
            self.is_drawing = False
            self.capture_screenshot()
    
    def restore_parent_window(self):
        """
        恢复父窗口状态
        根据工作模式决定显示主窗口或悬浮球
        """
        # 根据工作模式决定显示主窗口或悬浮球
        if self.parent_window.is_working_mode:
            if hasattr(self.parent_window, 'float_ball') and self.parent_window.float_ball and self.float_ball_visible:
                logger.debug("恢复显示悬浮球")
                self.parent_window.float_ball.show()
                # 使用Win32 API确保悬浮球在最顶层
                self.parent_window.set_window_topmost(self.parent_window.float_ball)
                # 隐藏主窗口
                self.parent_window.hide()
        else:
            logger.debug("恢复显示主窗口")
            self.parent_window.show()
            # 如果主窗口是置顶的，确保它在最顶层
            if self.parent_window.is_topmost:
                self.parent_window.set_window_topmost(self.parent_window)
    
    def capture_screenshot(self):
        """
        捕获选定区域的截图
        """
        logger.debug("开始捕获选定区域的截图")
        if self.begin == self.end:
            logger.debug("选择区域无效（点击而非拖动）")
            self.close()
            self.restore_parent_window()
            return
        
        # 计算选择区域
        rect = QRect(self.begin, self.end).normalized()
        
        if rect.width() <= 0 or rect.height() <= 0:
            logger.debug("选择区域无效（宽度或高度为0）")
            self.close()
            self.restore_parent_window()
            return
        
        # 从全屏截图中裁剪选择区域
        logger.debug(f"裁剪选择区域: {rect.x()}, {rect.y()}, {rect.width()} x {rect.height()}")
        cropped_pixmap = self.screenshot.copy(rect)
        
        # 关闭截图窗口
        self.close()
        
        # 处理截图
        logger.debug("将截图传递给主窗口处理")
        if self.auto_save_mode:
            # 自动保存模式
            logger.debug("使用自动保存模式处理截图")
            # 先恢复窗口显示状态，确保悬浮球可见（如果在工作模式下）
            self.restore_parent_window()
            # 然后处理截图
            self.parent_window.screenshot_manager.process_screenshot_auto_save(cropped_pixmap)
        else:
            # 普通模式，显示对话框
            logger.debug("使用普通模式处理截图（显示对话框）")
            self.parent_window.process_screenshot_with_dialog(cropped_pixmap) 