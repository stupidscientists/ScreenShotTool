"""
全局事件过滤器模块
用于捕获全局按键事件并转发到主应用程序
"""

from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import QApplication
from src.utils.logger import logger
import traceback

class GlobalEventFilter(QObject):
    """
    全局事件过滤器类
    用于捕获全局按键事件，如快捷键
    """
    def __init__(self, parent=None):
        """
        初始化全局事件过滤器
        
        参数:
            parent: 父对象，通常是主窗口
        """
        super().__init__(parent)
        self.parent = parent
        logger.debug("初始化全局事件过滤器")
    
    def eventFilter(self, obj, event):
        """
        事件过滤器方法，处理所有被监听的事件
        
        参数:
            obj: 产生事件的对象
            event: 事件对象
            
        返回:
            bool: 如果事件被处理则返回True，否则返回False
        """
        if event.type() == QEvent.KeyPress:
            logger.debug(f"捕获按键事件: {event.key()}, modifiers: {event.modifiers()}")
            
            # 处理ESC键，用于退出特殊模式
            if event.key() == Qt.Key_Escape:
                logger.info("全局事件过滤器捕获到 ESC 快捷键")
                
                # 检查当前焦点窗口是否是全屏图片查看器
                focused_widget = QApplication.focusWidget()
                if focused_widget and "FullscreenImageViewer" in str(type(focused_widget)):
                    logger.debug("ESC键被全屏图片查看器处理")
                    # 让事件继续传递给全屏图片查看器
                    return False
                
                if self.parent:
                    self.parent.exit_special_modes()
                return True
            
            # 处理左右方向键，用于切换截图
            elif event.key() == Qt.Key_Left or event.key() == Qt.Key_Right:
                logger.debug(f"全局事件过滤器捕获到方向键: {event.key()}")
                if self.parent and not self.parent.is_working_mode and self.parent.isVisible():
                    # 将事件传递给主窗口的keyPressEvent方法
                    self.parent.keyPressEvent(event)
                    return True
            
            # 处理F11键，用于自动保存截图
            # 注意：F11键已经由热键管理器处理，这里不再重复处理
            # 为了避免重复触发，我们在这里直接返回True，表示事件已处理
            elif event.key() == Qt.Key_F11:
                logger.debug(f"全局事件过滤器捕获到F11键，但由热键管理器处理，不再重复处理")
                return True
                
        # 对于未处理的事件，调用基类方法
        return super().eventFilter(obj, event) 