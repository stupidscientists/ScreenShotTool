"""
热键管理模块
用于注册和管理全局热键
"""

import datetime
import traceback
import keyboard
from PyQt5.QtCore import QTimer
from src.utils.logger import logger

class HotkeyManager:
    """
    热键管理器类
    负责注册和管理全局热键
    """
    
    def __init__(self, parent=None):
        """
        初始化热键管理器
        
        参数:
            parent: 父对象，通常是主窗口
        """
        self.parent = parent
        self.last_hotkey_time = {}  # 记录上次热键触发时间，防止重复触发
        
        # 初始化待处理信号标志
        self._pending_fullscreen = False
        self._pending_area = False
        self._pending_esc = False
        
        logger.debug("初始化热键管理器")
    
    def register_hotkeys(self):
        """
        注册系统级全局热键
        """
        try:
            # 创建一个函数，它只设置标志而不直接执行 GUI 操作
            def emit_fullscreen_signal():
                logger.info("键盘库捕获到 F12 快捷键，设置待处理标志")
                # 检查是否在短时间内重复触发
                current_time = datetime.datetime.now()
                last_time = self.last_hotkey_time.get('fullscreen')
                if last_time and (current_time - last_time).total_seconds() < 1.0:
                    logger.debug("忽略重复触发的全屏截图快捷键")
                    return
                
                self.last_hotkey_time['fullscreen'] = current_time
                self._pending_fullscreen = True
                # 不再直接发射信号，只设置标志
            
            # 注册热键，但回调只设置标志
            keyboard.add_hotkey('f12', emit_fullscreen_signal)
            
            # 类似地处理其他热键
            def emit_area_signal():
                logger.info("键盘库捕获到 Ctrl+F12 快捷键，设置待处理标志")
                # 检查是否在短时间内重复触发
                current_time = datetime.datetime.now()
                last_time = self.last_hotkey_time.get('area')
                if last_time and (current_time - last_time).total_seconds() < 1.0:
                    logger.debug("忽略重复触发的区域截图快捷键")
                    return
                
                self.last_hotkey_time['area'] = current_time
                self._pending_area = True
                # 不再直接发射信号，只设置标志
            
            def emit_esc_signal():
                logger.info("键盘库捕获到 ESC 快捷键，设置待处理标志")
                # 检查是否在短时间内重复触发
                current_time = datetime.datetime.now()
                last_time = self.last_hotkey_time.get('esc')
                if last_time and (current_time - last_time).total_seconds() < 1.0:
                    logger.debug("忽略重复触发的ESC快捷键")
                    return
                
                self.last_hotkey_time['esc'] = current_time
                self._pending_esc = True
                # 不再直接发射信号，只设置标志
            
            keyboard.add_hotkey('ctrl+f12', emit_area_signal)
            keyboard.add_hotkey('esc', emit_esc_signal)
            
            logger.info("成功注册系统级全局热键")
        except Exception as e:
            logger.error(f"注册系统级全局热键时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def unregister_hotkeys(self):
        """
        注销所有已注册的热键
        """
        try:
            # 尝试多种方式确保键盘监听器完全关闭
            keyboard.unhook_all()
            
            # 尝试清除所有热键回调
            if hasattr(keyboard, '_hotkeys'):
                keyboard._hotkeys.clear()
            
            # 尝试停止监听器（如果存在）
            try:
                if hasattr(keyboard, '_listener') and keyboard._listener:
                    # 尝试不同的方法来停止监听器
                    if hasattr(keyboard._listener, 'stop'):
                        keyboard._listener.stop()
                    elif hasattr(keyboard._listener, 'terminate'):
                        keyboard._listener.terminate()
                    elif hasattr(keyboard._listener, 'join'):
                        keyboard._listener.join(timeout=0.1)
            except:
                pass  # 忽略任何错误
            
            # 重置键盘模块状态
            if hasattr(keyboard, '_listener'):
                keyboard._listener = None
            
            logger.info("成功注销所有热键")
        except Exception as e:
            logger.error(f"注销热键时出错: {str(e)}")
            logger.error(traceback.format_exc())
    
    def check_hotkey_status(self):
        """
        检查热键状态，处理待处理的热键信号
        """
        try:
            # 检查是否有热键被触发但未处理
            current_time = datetime.datetime.now()
            
            # 检查是否有待处理的热键信号
            if self._pending_fullscreen:
                logger.debug("检测到待处理的全屏截图信号")
                self._pending_fullscreen = False
                # 使用信号而不是直接调用
                self.parent.fullscreen_signal.emit()
                
            if self._pending_area:
                logger.debug("检测到待处理的区域截图信号")
                self._pending_area = False
                # 使用信号而不是直接调用
                self.parent.area_signal.emit()
                
            if self._pending_esc:
                logger.debug("检测到待处理的ESC信号")
                self._pending_esc = False
                # 使用信号而不是直接调用
                self.parent.esc_signal.emit()
        except Exception as e:
            logger.error(f"检查热键状态时出错: {str(e)}")
            logger.error(traceback.format_exc()) 