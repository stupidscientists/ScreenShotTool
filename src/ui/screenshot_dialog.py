"""
截图对话框模块
用于显示截图预览和获取用户输入的说明文字
"""

import traceback
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QPushButton)
from PyQt5.QtCore import Qt
from src.utils.logger import logger

class ScreenshotDialog(QDialog):
    """
    截图对话框类
    显示截图预览并允许用户添加说明文字
    """
    
    def __init__(self, screenshot, parent=None):
        """
        初始化截图对话框
        
        参数:
            screenshot: QPixmap对象，要显示的截图
            parent: 父窗口
        """
        try:
            super().__init__(parent)
            logger.debug("初始化截图对话框")
            
            # 检查截图是否有效
            if screenshot.isNull():
                logger.error("截图对话框收到无效的截图")
                raise ValueError("截图无效")
                
            self.screenshot = screenshot
            self.text = ""
            self.save_screenshot = True
            self.initUI()
            
            # 设置模态对话框，阻止与其他窗口的交互
            self.setModal(True)
        except Exception as e:
            logger.error(f"初始化截图对话框时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
    def initUI(self):
        """
        初始化用户界面
        """
        try:
            logger.debug("设置截图对话框UI")
            self.setWindowTitle('截图预览')
            self.setGeometry(300, 300, 600, 500)
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            
            layout = QVBoxLayout()
            
            # 预览区域
            preview_label = QLabel()
            preview_pixmap = self.screenshot.scaled(
                500, 300,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            preview_label.setPixmap(preview_pixmap)
            preview_label.setAlignment(Qt.AlignCenter)
            
            # 文本输入区域
            text_label = QLabel("请输入说明文字:")
            self.text_edit = QTextEdit()
            self.text_edit.setPlaceholderText("在此输入对截图的说明...")
            
            # 按钮区域
            button_layout = QHBoxLayout()
            save_btn = QPushButton("保存")
            cancel_btn = QPushButton("取消")
            
            button_layout.addWidget(save_btn)
            button_layout.addWidget(cancel_btn)
            
            # 添加到主布局
            layout.addWidget(preview_label)
            layout.addWidget(text_label)
            layout.addWidget(self.text_edit)
            layout.addLayout(button_layout)
            
            self.setLayout(layout)
            
            # 连接信号和槽
            save_btn.clicked.connect(self.accept)
            cancel_btn.clicked.connect(self.reject)
            logger.debug("截图对话框UI设置完成")
        except Exception as e:
            logger.error(f"设置截图对话框UI时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def accept(self):
        """
        处理用户点击保存按钮的事件
        """
        try:
            logger.debug("用户点击保存按钮")
            self.text = self.text_edit.toPlainText()
            self.save_screenshot = True
            super().accept()
        except Exception as e:
            logger.error(f"处理保存按钮点击时出错: {str(e)}")
            logger.error(traceback.format_exc())
            # 确保对话框关闭但不导致应用程序退出
            self.done(QDialog.Accepted)
    
    def reject(self):
        """
        处理用户点击取消按钮的事件
        """
        try:
            logger.debug("用户点击取消按钮")
            self.save_screenshot = False
            logger.debug("设置save_screenshot为False")
            super().reject()
        except Exception as e:
            logger.error(f"处理取消按钮点击时出错: {str(e)}")
            logger.error(traceback.format_exc())
            # 确保对话框关闭但不导致应用程序退出
            self.done(QDialog.Rejected)
    
    def showEvent(self, event):
        """
        处理对话框显示事件
        
        参数:
            event: 显示事件对象
        """
        try:
            logger.debug("截图对话框显示")
            super().showEvent(event)
        except Exception as e:
            logger.error(f"截图对话框显示事件处理出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def closeEvent(self, event):
        """
        处理对话框关闭事件
        
        参数:
            event: 关闭事件对象
        """
        try:
            logger.debug("截图对话框关闭")
            # 确保关闭对话框不会导致应用程序退出
            self.save_screenshot = False
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"截图对话框关闭事件处理出错: {str(e)}")
            logger.error(traceback.format_exc())
            # 确保事件被接受
            event.accept() 