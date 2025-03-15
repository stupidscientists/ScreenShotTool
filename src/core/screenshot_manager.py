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
import datetime

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
    
    def start_area_capture(self, force_area=False, auto_save=False):
        """
        开始区域截图
        
        参数:
            force_area: 布尔值，是否强制使用区域截图模式
            auto_save: 布尔值，是否自动保存截图（不显示对话框）
            
        返回:
            bool: 成功返回True，否则返回False
        """
        logger.debug(f"开始区域截图，强制区域模式: {force_area}, 自动保存模式: {auto_save}")
        try:
            if not self.parent.document_manager.word_doc:
                if not self.parent.is_working_mode:  # 只在非工作模式下显示警告
                    logger.warning("尝试区域截图但未创建文档")
                    QMessageBox.warning(self.parent, '警告', '请先创建或打开Word文档')
                return False
            
            # 确保窗口状态正确
            self.parent.ensure_window_state_for_screenshot()
            
            # 如果是全屏模式且不强制使用区域截图，则直接调用全屏截图
            if self.full_screen_mode and not force_area:
                logger.debug("全屏模式下调用全屏截图")
                return self.take_fullscreen_screenshot()
            
            # 隐藏主窗口和悬浮球，以免影响截图
            if self.parent.isVisible():
                logger.debug("暂时隐藏主窗口以进行区域截图")
                self.parent.hide()
            
            if self.parent.float_ball and self.parent.float_ball.isVisible():
                logger.debug("暂时隐藏悬浮球以进行区域截图")
                self.parent.float_ball.hide()
            
            # 处理事件，确保窗口状态更新
            QApplication.processEvents()
            time.sleep(0.2)  # 给窗口隐藏的时间
            
            # 创建区域截图窗口
            logger.debug("创建区域截图窗口")
            self.capture_window = CaptureWindow(self.parent)
            
            # 设置自动保存模式
            if auto_save:
                self.capture_window.auto_save_mode = True
                logger.debug("设置区域截图窗口为自动保存模式")
            
            # 显示区域截图窗口
            self.capture_window.showFullScreen()
            
            return True
        except Exception as e:
            logger.error(f"开始区域截图时出错: {str(e)}")
            logger.error(traceback.format_exc())
            
            # 恢复窗口显示
            if self.parent.is_working_mode and self.parent.float_ball:
                logger.debug("截图出错，恢复显示悬浮球")
                self.parent.float_ball.show()
                # 确保悬浮球在最顶层
                self.parent.set_window_topmost(self.parent.float_ball)
            else:
                logger.debug("截图出错，恢复显示主窗口")
                self.parent.show()
            
            return False
    
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
                    old_count = len(self.screenshots)
                    self.screenshots.append(pixmap)
                    logger.debug(f"截图已添加到列表，数量: {old_count} -> {len(self.screenshots)}")
                    
                    # 显示最新截图的预览，并更新当前索引
                    logger.debug(f"调用show_preview更新预览，当前索引: {self.parent.current_screenshot_index}")
                    self.parent.show_preview(pixmap, update_index=True)
                    logger.debug(f"预览更新完成，更新后索引: {self.parent.current_screenshot_index}")
                    
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
    
    def process_screenshot_auto_save(self, pixmap):
        """
        处理截图并自动保存，不显示对话框
        
        参数:
            pixmap: QPixmap对象，要处理的截图
            
        返回:
            bool: 处理成功返回True，否则返回False
        """
        logger.debug("进入process_screenshot_auto_save方法")
        try:
            # 检查参数
            if pixmap is None:
                logger.error("截图对象为None，无法自动保存")
                return False
                
            if not isinstance(pixmap, QPixmap):
                logger.error(f"截图对象类型错误: {type(pixmap)}，无法自动保存")
                return False
                
            if pixmap.isNull():
                logger.error("截图为空，无法自动保存")
                return False
                
            logger.debug("截图有效，准备自动保存")
            
            # 检查父窗口
            if not self.parent:
                logger.error("父窗口对象为None，无法自动保存")
                return False
                
            # 生成当前时间作为默认说明文字
            try:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                default_text = f"自动保存的截图 - {current_time}"
                logger.debug(f"生成默认说明文字: {default_text}")
            except Exception as e:
                logger.error(f"生成默认说明文字时出错: {str(e)}")
                default_text = "自动保存的截图"
            
            # 保存截图
            try:
                old_count = len(self.screenshots)
                self.screenshots.append(pixmap)
                logger.debug(f"截图已添加到列表，数量: {old_count} -> {len(self.screenshots)}")
            except Exception as e:
                logger.error(f"添加截图到列表时出错: {str(e)}")
                logger.error(traceback.format_exc())
                return False
            
            # 显示最新截图的预览，并更新当前索引
            try:
                logger.debug(f"调用show_preview更新预览，当前索引: {self.parent.current_screenshot_index}")
                self.parent.show_preview(pixmap, update_index=True)
                logger.debug(f"预览更新完成，更新后索引: {self.parent.current_screenshot_index}")
            except Exception as e:
                logger.error(f"更新预览时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为预览问题而中断
            
            # 更新状态和计数
            try:
                self.parent.screenshot_count.setText(str(len(self.screenshots)))
                self.parent.status_label.setText(f'已自动保存 {len(self.screenshots)} 张图片')
            except Exception as e:
                logger.error(f"更新状态和计数时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为UI更新问题而中断
            
            # 自动添加到Word文档，包括默认文本说明
            try:
                logger.debug(f"添加截图到Word文档，使用默认文本说明")
                success = self.parent.document_manager.add_screenshot(pixmap, default_text)
                if not success:
                    logger.warning("添加截图到Word文档失败")
            except Exception as e:
                logger.error(f"添加截图到Word文档时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为文档问题而中断
            
            # 启用按钮
            try:
                self.parent.save_doc_btn.setEnabled(True)
                self.parent.clear_btn.setEnabled(True)
            except Exception as e:
                logger.error(f"启用按钮时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为UI更新问题而中断
            
            # 显示一个简短的通知
            try:
                if hasattr(self.parent, 'tray_icon') and self.parent.tray_icon:
                    self.parent.tray_icon.showMessage("截图已自动保存", "截图已成功添加到Word文档", QSystemTrayIcon.Information, 2000)
                    logger.debug("显示托盘通知：截图已自动保存")
            except Exception as e:
                logger.error(f"显示托盘通知时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为通知问题而中断
            
            # 处理窗口显示状态
            try:
                if hasattr(self.parent, 'is_working_mode') and self.parent.is_working_mode:
                    # 在工作模式下，始终显示悬浮球
                    logger.debug("截图自动保存完成，在工作模式下显示悬浮球")
                    if hasattr(self.parent, 'float_ball') and self.parent.float_ball:
                        try:
                            self.parent.float_ball.show()
                            # 确保悬浮球置顶
                            if hasattr(self.parent, 'set_window_topmost'):
                                self.parent.set_window_topmost(self.parent.float_ball)
                            # 在悬浮球上显示成功提示
                            if hasattr(self.parent.float_ball, 'show_success_tip'):
                                try:
                                    self.parent.float_ball.show_success_tip(f"第 {len(self.screenshots)} 张截图已保存")
                                except Exception as e:
                                    logger.error(f"显示悬浮球成功提示时出错: {str(e)}")
                                    logger.error(traceback.format_exc())
                        except Exception as e:
                            logger.error(f"显示悬浮球时出错: {str(e)}")
                            logger.error(traceback.format_exc())
                    # 隐藏主窗口
                    if hasattr(self.parent, 'hide'):
                        self.parent.hide()
                else:
                    # 非工作模式下，显示主窗口
                    logger.debug("截图自动保存完成，在非工作模式下显示主窗口")
                    if hasattr(self.parent, 'show'):
                        self.parent.show()
                    if hasattr(self.parent, 'activateWindow'):
                        self.parent.activateWindow()
            except Exception as e:
                logger.error(f"处理窗口显示状态时出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续执行，不要因为窗口状态问题而中断
            
            logger.debug("自动保存截图完成")
            return True
        except Exception as e:
            logger.error(f"自动保存截图时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def clear_screenshots(self):
        """
        清除所有截图
        """
        logger.debug(f"开始清除截图，当前数量: {len(self.screenshots)}, 当前索引: {self.parent.current_screenshot_index}")
        self.screenshots.clear()
        self.parent.preview_label.clear()
        self.parent.preview_label.setText('截图预览区域')
        self.parent.screenshot_count.setText('0')
        self.parent.status_label.setText('已清除所有截图')
        self.parent.current_screenshot_index = -1  # 重置当前截图索引
        logger.debug("截图已清除，索引已重置为-1")
        logger.info("已清除所有截图") 