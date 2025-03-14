"""
关于对话框模块
用于显示应用程序的版本、作者等信息
"""

import traceback
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame)
from PyQt5.QtCore import Qt
from src.utils.logger import logger

class AboutDialog(QDialog):
    """
    关于对话框类
    显示应用程序的版本、作者等信息
    """
    
    def __init__(self, parent=None):
        """
        初始化关于对话框
        
        参数:
            parent: 父窗口
        """
        try:
            super().__init__(parent)
            logger.debug("初始化关于对话框")
            self.initUI()
        except Exception as e:
            logger.error(f"初始化关于对话框时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
    def initUI(self):
        """
        初始化用户界面
        """
        try:
            logger.debug("设置关于对话框UI")
            self.setWindowTitle('关于')
            self.setFixedSize(400, 300)
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            
            layout = QVBoxLayout()
            
            # 标题
            title_label = QLabel('屏幕截图工具')
            title_label.setStyleSheet("""
                font-size: 24px;
                font-weight: bold;
                color: #2E7D32;
                margin-bottom: 10px;
            """)
            title_label.setAlignment(Qt.AlignCenter)
            
            # 版本
            version_label = QLabel('版本 1.0')
            version_label.setStyleSheet("font-size: 14px; color: #555;")
            version_label.setAlignment(Qt.AlignCenter)
            
            # 分隔线
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #CCCCCC;")
            
            # 描述
            desc_label = QLabel('这是一个简单易用的屏幕截图工具，可以快速截取屏幕并保存到Word文档中。')
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignCenter)
            
            # 设计者信息
            designer_label = QLabel('Designed by 王伟')
            designer_label.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #4CAF50;
                margin-top: 20px;
            """)
            designer_label.setAlignment(Qt.AlignCenter)
            
            # 版权信息
            copyright_label = QLabel('© 2023 版权所有')
            copyright_label.setStyleSheet("font-size: 12px; color: #777;")
            copyright_label.setAlignment(Qt.AlignCenter)
            
            # 确定按钮
            ok_button = QPushButton('确定')
            ok_button.clicked.connect(self.accept)
            ok_button.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            """)
            
            # 添加所有组件到布局
            layout.addWidget(title_label)
            layout.addWidget(version_label)
            layout.addWidget(line)
            layout.addSpacing(10)
            layout.addWidget(desc_label)
            layout.addSpacing(10)
            layout.addWidget(designer_label)
            layout.addWidget(copyright_label)
            layout.addSpacing(20)
            
            # 创建一个水平布局来居中放置按钮
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(ok_button)
            button_layout.addStretch()
            
            layout.addLayout(button_layout)
            self.setLayout(layout)
            
            logger.debug("关于对话框UI设置完成")
        except Exception as e:
            logger.error(f"设置关于对话框UI时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise 