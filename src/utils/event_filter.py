"""
全局事件过滤器模块
用于捕获全局按键事件并转发到主应用程序
"""

from PyQt5.QtCore import Qt, QObject, QEvent
from src.utils.logger import logger

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
            
            # 不再直接处理快捷键，避免与HotkeyManager冲突
            # 只处理ESC键，因为它用于退出特殊模式
            if event.key() == Qt.Key_Escape:
                logger.info("全局事件过滤器捕获到 ESC 快捷键")
                if self.parent:
                    self.parent.exit_special_modes()
                return True
                
        # 对于未处理的事件，调用基类方法
        return super().eventFilter(obj, event) 