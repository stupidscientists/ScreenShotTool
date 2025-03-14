import os
import sys

def get_temp_screenshots_path():
    """获取temp_screenshots文件夹的路径"""
    # 方法1: 从document_manager.py中的逻辑获取
    try:
        # 获取应用程序目录
        current_dir = os.path.abspath(os.path.dirname(__file__))
        app_dir = current_dir  # 当前目录就是应用程序目录
        temp_dir1 = os.path.join(app_dir, 'temp_screenshots')
        print(f"方法1 - 应用程序目录下的temp_screenshots: {temp_dir1}")
    except Exception as e:
        print(f"方法1出错: {str(e)}")
    
    # 方法2: 从main.py中的逻辑获取
    try:
        app_dir = os.path.abspath(os.path.dirname(__file__))
        app_root_dir = app_dir  # 当前目录就是应用程序根目录
        temp_dir2 = os.path.join(app_root_dir, 'temp_screenshots')
        print(f"方法2 - 应用程序根目录下的temp_screenshots: {temp_dir2}")
    except Exception as e:
        print(f"方法2出错: {str(e)}")
    
    # 检查文件夹是否存在
    if os.path.exists(temp_dir1):
        print(f"方法1的文件夹存在，包含 {len(os.listdir(temp_dir1))} 个文件")
    else:
        print("方法1的文件夹不存在")
    
    if os.path.exists(temp_dir2):
        print(f"方法2的文件夹存在，包含 {len(os.listdir(temp_dir2))} 个文件")
    else:
        print("方法2的文件夹不存在")

if __name__ == "__main__":
    get_temp_screenshots_path() 