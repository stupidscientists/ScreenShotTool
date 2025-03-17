"""
全屏图片查看器模块
用于全屏显示图片
"""

import traceback
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QKeySequence, QFont
from src.utils.logger import logger

class FullscreenImageViewer(QDialog):
    """
    全屏图片查看器类
    用于全屏显示图片
    """
    
    def __init__(self, pixmap, parent=None, index=None, total=None):
        """
        初始化全屏图片查看器
        
        参数:
            pixmap: QPixmap对象，要显示的图片
            parent: 父窗口
            index: 当前图片的索引（从0开始）
            total: 图片总数
        """
        super().__init__(parent)
        logger.debug("初始化全屏图片查看器")
        
        self.pixmap = pixmap
        self.index = index
        self.total = total
        self.init_ui()
        
    def init_ui(self):
        """
        初始化用户界面
        """
        try:
            # 设置窗口属性
            self.setWindowTitle("图片查看器")
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setModal(True)
            
            # 创建主布局
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # 创建标题标签
            self.title_label = QLabel()
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setStyleSheet("""
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 8px;
                font-weight: bold;
            """)
            
            # 设置标题文本
            title_text = "Image"
            if self.index is not None:
                title_text = f"Image {self.index + 1}"
                if self.total is not None:
                    title_text += f" / {self.total}"
            
            self.title_label.setText(title_text)
            
            # 设置标题字体
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            self.title_label.setFont(font)
            
            # 创建图片标签
            self.image_label = QLabel()
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setStyleSheet("background-color: black;")
            
            # 添加到主布局
            main_layout.addWidget(self.title_label)
            main_layout.addWidget(self.image_label, 1)  # 图片标签占据剩余空间
            
            # 显示图片
            self.update_image()
            
            # 设置窗口大小为全屏
            self.showFullScreen()
            
            # 确保窗口获得焦点
            self.activateWindow()
            self.raise_()
            
            logger.debug("全屏图片查看器UI初始化完成")
        except Exception as e:
            logger.error(f"初始化全屏图片查看器UI时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def update_image(self):
        """
        更新图片显示
        """
        try:
            # 获取屏幕尺寸
            screen_size = QApplication.primaryScreen().size()
            
            # 缩放图片以适应屏幕，保持宽高比
            scaled_pixmap = self.pixmap.scaled(
                screen_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # 设置图片
            self.image_label.setPixmap(scaled_pixmap)
            
            logger.debug(f"图片已缩放显示，原始尺寸: {self.pixmap.width()}x{self.pixmap.height()}, 缩放后尺寸: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
        except Exception as e:
            logger.error(f"更新图片显示时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def closeEvent(self, event):
        """
        处理窗口关闭事件
        
        参数:
            event: 关闭事件对象
        """
        logger.debug("全屏图片查看器关闭事件")
        # 释放资源
        self.pixmap = None
        self.image_label.clear()
        event.accept()
    
    def keyPressEvent(self, event):
        """
        处理按键事件
        
        参数:
            event: 按键事件对象
        """
        # ESC键关闭窗口
        if event.key() == Qt.Key_Escape:
            logger.debug("按下ESC键，关闭全屏图片查看器")
            self.close()
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """
        处理鼠标按下事件
        
        参数:
            event: 鼠标事件对象
        """
        # 点击任意位置关闭窗口
        logger.debug("鼠标点击，关闭全屏图片查看器")
        self.close() 