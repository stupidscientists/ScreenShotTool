"""
截图管理模块
用于处理截图的捕获和处理
"""

import time
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QSystemTrayIcon
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from src.utils.logger import logger
from src.ui.screenshot_dialog import ScreenshotDialog
from src.ui.capture_window import CaptureWindow

class ScreenshotManager:
    """
    截图管理器类
    负责截图的捕获、处理和管理
    """
    
    def __init__(self, parent=None):
        """
        初始化截图管理器
        
        参数:
            parent: 父对象，通常是主窗口
        """
        self.parent = parent
        self.screenshots = []  # 存储截图
        self.full_screen_mode = True  # 默认使用全屏截图模式
        logger.debug("初始化截图管理器")
    
    def take_fullscreen_screenshot(self):
        """
        捕获全屏截图
        
        返回:
            bool: 截图成功返回True，否则返回False
        """
        logger.info("触发全屏截图快捷键")
        try:
            if not self.parent.document_manager.word_doc:
                if not self.parent.is_working_mode:  # 只在非工作模式下显示警告
                    logger.warning("尝试截图但未创建文档")
                    QMessageBox.warning(self.parent, '警告', '请先创建或打开Word文档')
                return False
            
            # 如果悬浮球存在且可见，则暂时隐藏
            float_ball_visible = False
            if self.parent.float_ball and self.parent.float_ball.isVisible():
                logger.debug("暂时隐藏悬浮球以进行截图")
                float_ball_visible = True
                self.parent.float_ball.hide()
                QApplication.processEvents()
                time.sleep(0.2)  # 给悬浮球隐藏的时间
            
            # 获取全屏截图
            logger.debug("开始获取全屏截图")
            try:
                screen = QApplication.primaryScreen()
                if screen is None:
                    logger.error("无法获取主屏幕")
                    raise Exception("无法获取主屏幕")
                    
                pixmap = screen.grabWindow(0)
                if pixmap.isNull():
                    logger.error("截图为空")
                    raise Exception("截图为空")
                    
                logger.info(f"完成全屏截图，尺寸: {pixmap.width()}x{pixmap.height()}")
            except Exception as e:
                logger.error(f"获取屏幕截图时出错: {str(e)}")
                # 恢复显示悬浮球（如果之前是可见的）
                if float_ball_visible and self.parent.float_ball:
                    logger.debug("截图出错，恢复显示悬浮球")
                    self.parent.float_ball.show()
                    # 确保悬浮球在最顶层
                    self.parent.set_window_topmost(self.parent.float_ball)
                raise
            
            # 处理截图
            logger.debug("开始处理截图")
            result = self.process_screenshot_with_dialog(pixmap)
            
            # 恢复显示悬浮球（如果之前是可见的）
            if float_ball_visible and self.parent.float_ball and self.parent.is_working_mode:
                logger.debug("截图完成，恢复显示悬浮球")
                self.parent.float_ball.show()
                # 确保悬浮球在最顶层
                self.parent.set_window_topmost(self.parent.float_ball)
            
            return result
            
        except Exception as e:
            logger.error(f"全屏截图过程中出错: {str(e)}")
            logger.error(traceback.format_exc())
            if not self.parent.is_working_mode:
                QMessageBox.critical(self.parent, '错误', f'截图过程中出错: {str(e)}')
            # 确保悬浮球可见（如果在工作模式下）
            if self.parent.is_working_mode and self.parent.float_ball:
                self.parent.float_ball.show()
                # 确保悬浮球在最顶层
                self.parent.set_window_topmost(self.parent.float_ball)
            return False
    
    def start_area_capture(self, force_area=False):
        """
        开始区域截图
        
        参数:
            force_area: 是否强制使用区域截图，无论full_screen_mode的值是什么
            
        返回:
            bool: 开始截图成功返回True，否则返回False
        """
        logger.info("触发区域截图快捷键")
        if not self.parent.document_manager.word_doc:
            if not self.parent.is_working_mode:  # 只在非工作模式下显示警告
                logger.warning("尝试截图但未创建文档")
                QMessageBox.warning(self.parent, '警告', '请先创建或打开Word文档')
            return False
            
        if self.full_screen_mode and not force_area:
            return self.take_fullscreen_screenshot()
        else:
            # 如果悬浮球存在且可见，则暂时隐藏
            float_ball_visible = False
            if self.parent.float_ball and self.parent.float_ball.isVisible():
                logger.debug("暂时隐藏悬浮球以进行区域截图")
                float_ball_visible = True
                self.parent.float_ball.hide()
                QApplication.processEvents()
                time.sleep(0.2)  # 给悬浮球隐藏的时间
            
            # 延迟一小段时间，确保窗口完全隐藏
            QApplication.processEvents()
            time.sleep(0.3)
            
            # 创建全屏截图
            self.full_screen = QApplication.primaryScreen().grabWindow(0)
            
            # 创建截图窗口
            self.capture_window = CaptureWindow(self.full_screen, self.parent)
            # 保存悬浮球可见状态，以便在截图完成后恢复
            self.capture_window.float_ball_visible = float_ball_visible
            self.capture_window.showFullScreen()
            logger.info("显示区域截图选择窗口")
            
            # 注意：不在这里恢复悬浮球，而是在CaptureWindow关闭时处理
            # 这样可以确保在取消截图时也能正确恢复悬浮球
            
            return True
    
    def process_screenshot_with_dialog(self, pixmap):
        """
        处理截图并显示对话框
        
        参数:
            pixmap: QPixmap对象，要处理的截图
            
        返回:
            bool: 处理成功返回True，否则返回False
        """
        logger.debug("进入process_screenshot_with_dialog方法")
        try:
            if pixmap and not pixmap.isNull():
                logger.debug("截图有效，准备显示对话框")
                
                # 如果悬浮球存在且可见，则暂时隐藏
                float_ball_visible = False
                if self.parent.float_ball and self.parent.float_ball.isVisible():
                    logger.debug("暂时隐藏悬浮球以显示截图对话框")
                    float_ball_visible = True
                    self.parent.float_ball.hide()
                    QApplication.processEvents()
                
                # 显示截图对话框
                dialog = ScreenshotDialog(pixmap, self.parent)  # 使用主窗口作为父窗口
                logger.debug("截图对话框已创建，准备显示")
                
                # 确保对话框置顶显示
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
                
                # 激活对话框
                dialog.activateWindow()
                dialog.raise_()
                
                # 显示对话框
                try:
                    result = dialog.exec_()
                    logger.debug(f"对话框结果: {result}, 保存状态: {dialog.save_screenshot}")
                except Exception as e:
                    logger.error(f"显示对话框时出错: {str(e)}")
                    logger.error(traceback.format_exc())
                    # 恢复显示悬浮球（如果之前是可见的）
                    if float_ball_visible and self.parent.float_ball and self.parent.is_working_mode:
                        logger.debug("对话框出错，恢复显示悬浮球")
                        self.parent.float_ball.show()
                        # 确保悬浮球在最顶层
                        self.parent.set_window_topmost(self.parent.float_ball)
                    return False
                
                # 恢复显示悬浮球（如果之前是可见的）
                if float_ball_visible and self.parent.float_ball and self.parent.is_working_mode:
                    logger.debug("对话框关闭，恢复显示悬浮球")
                    self.parent.float_ball.show()
                    # 确保悬浮球在最顶层
                    self.parent.set_window_topmost(self.parent.float_ball)
                
                if result == QDialog.Accepted and dialog.save_screenshot:
                    logger.debug("用户选择保存截图")
                    # 保存截图
                    self.screenshots.append(pixmap)
                    
                    # 显示最新截图的预览
                    self.parent.show_preview(pixmap)
                    
                    # 更新状态和计数
                    self.parent.screenshot_count.setText(str(len(self.screenshots)))
                    self.parent.status_label.setText(f'已截取 {len(self.screenshots)} 张图片')
                    
                    # 自动添加到Word文档，包括文本说明
                    logger.debug(f"添加截图到Word文档，文本说明长度: {len(dialog.text)}")
                    success = self.parent.document_manager.add_screenshot(pixmap, dialog.text)
                    
                    # 启用按钮
                    self.parent.save_doc_btn.setEnabled(True)
                    self.parent.clear_btn.setEnabled(True)
                    
                    # 如果在工作模式下，显示一个简短的通知
                    if self.parent.is_working_mode:
                        try:
                            self.parent.tray_icon.showMessage("截图已保存", "截图已成功添加到Word文档", QSystemTrayIcon.Information, 2000)
                            logger.debug("工作模式下显示托盘通知")
                        except Exception as e:
                            logger.error(f"显示托盘通知时出错: {str(e)}")
                    
                    # 处理窗口显示状态
                    if self.parent.is_working_mode:
                        # 在工作模式下，始终显示悬浮球
                        logger.debug("截图保存完成，在工作模式下显示悬浮球")
                        if self.parent.float_ball:
                            self.parent.float_ball.show()
                            # 确保悬浮球置顶
                            self.parent.set_window_topmost(self.parent.float_ball)
                        # 隐藏主窗口
                        self.parent.hide()
                    else:
                        # 非工作模式下，显示主窗口
                        logger.debug("截图保存完成，在非工作模式下显示主窗口")
                        self.parent.show()
                        self.parent.activateWindow()
                    
                    return True
                else:
                    logger.debug("用户取消保存截图")
                    # 处理窗口显示状态
                    if self.parent.is_working_mode:
                        # 在工作模式下，始终显示悬浮球
                        logger.debug("截图取消保存，在工作模式下显示悬浮球")
                        if self.parent.float_ball:
                            self.parent.float_ball.show()
                            # 确保悬浮球置顶
                            self.parent.set_window_topmost(self.parent.float_ball)
                        # 隐藏主窗口
                        self.parent.hide()
                    else:
                        # 非工作模式下，显示主窗口
                        logger.debug("截图取消保存，在非工作模式下显示主窗口")
                        self.parent.show()
                        self.parent.activateWindow()
                    
                    return False
            else:
                logger.warning("截图无效，无法处理")
                return False
        except Exception as e:
            logger.error(f"处理截图时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def clear_screenshots(self):
        """
        清除所有截图
        """
        self.screenshots.clear()
        self.parent.preview_label.clear()
        self.parent.preview_label.setText('截图预览区域')
        self.parent.screenshot_count.setText('0')
        self.parent.status_label.setText('已清除所有截图')
        logger.info("已清除所有截图") 