"""
启动脚本
用于从项目根目录启动屏幕截图工具应用程序
"""

import sys
import os

# 确保当前目录在Python路径中
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入主程序入口
from src.main import main

if __name__ == "__main__":
    main() 