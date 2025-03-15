"""
主程序入口文件
用于启动屏幕截图工具应用程序
"""

import sys
import os
import traceback
import atexit
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger, logger

def cleanup():
    """
    程序退出时的清理函数
    """
    try:
        logger.info("执行退出清理操作")
        
        # 清理临时截图文件夹
        try:
            import shutil
            app_dir = os.path.abspath(os.path.dirname(__file__))
            app_root_dir = os.path.dirname(app_dir)
            temp_dir = os.path.join(app_root_dir, 'temp_screenshots')
            
            if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                logger.info(f"清理临时截图文件夹: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"清理临时截图文件夹时出错: {str(e)}")
        
        # 尝试清理keyboard模块
        try:
            import keyboard
            # 先解除所有热键
            keyboard.unhook_all()
            
            # 安全地停止监听器
            if hasattr(keyboard, '_listener') and keyboard._listener:
                try:
                    # 直接调用stop方法，避免使用可能不存在的start_if_necessary
                    if hasattr(keyboard._listener, 'stop'):
                        keyboard._listener.stop()
                except Exception as inner_e:
                    logger.debug(f"停止keyboard监听器时出错: {str(inner_e)}")
            
            # 清理其他可能的资源
            if hasattr(keyboard, '_hotkeys'):
                keyboard._hotkeys.clear()
                
            logger.info("已清理keyboard模块")
        except Exception as e:
            logger.error(f"清理keyboard模块时出错: {str(e)}")
        
        logger.info("程序退出，退出代码: 0")
    except Exception as e:
        logger.error(f"执行退出清理操作时出错: {str(e)}")
        logger.error(traceback.format_exc())

def log_temp_screenshots_path():
    """
    记录temp_screenshots文件夹的路径到日志
    """
    try:
        # 获取应用程序目录
        app_dir = os.path.abspath(os.path.dirname(__file__))
        app_root_dir = os.path.dirname(app_dir)
        temp_dir = os.path.join(app_root_dir, 'temp_screenshots')
        
        # 记录路径到日志
        logger.info("=" * 50)
        logger.info(f"临时截图文件夹路径: {temp_dir}")
        logger.info("=" * 50)
        
        # 检查文件夹是否存在
        if os.path.exists(temp_dir):
            file_count = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
            logger.info(f"临时截图文件夹已存在，包含 {file_count} 个文件")
        else:
            logger.info("临时截图文件夹尚未创建")
    except Exception as e:
        logger.error(f"记录临时截图文件夹路径时出错: {str(e)}")
        logger.error(traceback.format_exc())

def main():
    """
    主函数，程序入口点
    """
    try:
        # 设置退出处理
        atexit.register(cleanup)
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
        
        # 记录临时截图文件夹路径
        log_temp_screenshots_path()
        
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)
        
        # 创建主窗口
        main_window = MainWindow()
        main_window.show()
        
        # 启动应用程序
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"程序启动时出错: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 