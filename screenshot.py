import logging
import os
from datetime import datetime

# ... existing code ...

# 在类的开始处设置日志配置
def __init__(self):
    # 设置日志配置
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"screenshot_{datetime.now().strftime('%Y%m%d')}.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    self.logger = logging.getLogger(__name__)
    self.logger.info("Screenshot tool initialized")
    
    # ... existing code ...

def merge_images(self):
    self.logger.info("Starting merge_images process")
    try:
        if not self.screenshot_list:
            self.logger.warning("No screenshots to merge")
            return
        
        self.logger.info(f"Number of screenshots to merge: {len(self.screenshot_list)}")
        
        # ... existing code ...
        
        self.logger.info("Creating merged image")
        merged_image = Image.new('RGB', (total_width, max_height), (255, 255, 255))
        
        current_x = 0
        for idx, img in enumerate(images):
            self.logger.debug(f"Processing image {idx+1}/{len(images)}, size: {img.size}")
            merged_image.paste(img, (current_x, 0))
            current_x += img.size[0]
        
        self.logger.info("Saving merged image")
        # ... existing code ...
        
        self.logger.info("Merge completed successfully")
    except Exception as e:
        self.logger.error(f"Error during merge process: {str(e)}", exc_info=True)
        raise

def floating_ball_mode(self):
    self.logger.info("Entering floating ball mode")
    try:
        # ... existing code ...
        
        while True:
            self.logger.debug("Floating ball mode loop iteration")
            event, values = self.window.read()
            
            if event == sg.WIN_CLOSED:
                self.logger.info("Floating ball mode window closed")
                break
                
            if event == '截图':
                self.logger.info("Screenshot button clicked in floating ball mode")
                self.take_screenshot()
                
            if event == '合并':
                self.logger.info("Merge button clicked in floating ball mode")
                self.merge_images()
                
        self.logger.info("Exiting floating ball mode")
    except Exception as e:
        self.logger.error(f"Error in floating ball mode: {str(e)}", exc_info=True)
        raise

def take_screenshot(self):
    self.logger.info("Starting screenshot capture")
    try:
        # ... existing code ...
        self.logger.info("Screenshot captured successfully")
    except Exception as e:
        self.logger.error(f"Error during screenshot capture: {str(e)}", exc_info=True)
        raise 