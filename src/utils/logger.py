"""
日志工具模块
提供应用程序的日志记录功能
"""

import sys
import logging

def setup_logger():
    """
    配置并初始化日志系统
    
    返回:
        logging.Logger: 配置好的日志记录器对象
    """
    # 创建logger对象
    logger = logging.getLogger('screenshot_tool')
    logger.setLevel(logging.DEBUG)
    
    # 清除已有的处理器，防止重复日志
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建文件处理器，设置编码为utf-8
    file_handler = logging.FileHandler('screenshot_tool.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志
logger = setup_logger() 