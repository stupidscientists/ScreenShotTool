"""
构建脚本
用于将截图工具打包成可执行文件
"""

import os
import sys
import shutil
import subprocess
import PyInstaller.__main__
from datetime import datetime

# 应用程序配置
APP_NAME = "ScreenshotTool"
APP_VERSION = "1.0.4"  # 更新版本号到1.0.4
MAIN_SCRIPT = "run.py"  # 使用正确的入口点脚本
OUTPUT_DIR = "dist"

# 最近的更新:
# 1.0.4 - 修复悬浮球模式自动退出问题，支持管理员权限运行使全局快捷键更可靠
# 1.0.3 - 改进了文件合并逻辑，解决了合并内容重复问题，优化了对话框按钮文本
# 1.0.2 - 修复了合并文档时的图片处理错误
# 1.0.1 - 修复了程序退出时keyboard模块的清理错误
# 1.0.0 - 初始版本

def clean_build_directories():
    """
    清理构建目录
    """
    print("清理构建目录...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # 清理所有 .spec 文件
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)
            print(f"已删除: {file}")
    
    # 清理 Python 缓存文件
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_dir = os.path.join(root, dir_name)
                shutil.rmtree(cache_dir)
                print(f"已删除: {cache_dir}")

def install_requirements():
    """
    安装必要的依赖
    """
    print("检查并安装必要的依赖...")
    try:
        # 检查是否安装了 PyInstaller
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        
        # 安装项目依赖
        if os.path.exists('requirements.txt'):
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
            print("已安装 requirements.txt 中的所有依赖")
        else:
            print("警告: 未找到 requirements.txt 文件，安装基本依赖")
            # 安装基本依赖
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'PyQt5', 'python-docx', 'keyboard', 'Pillow'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"安装依赖时出错: {e}")
        sys.exit(1)

def create_icon():
    """
    创建应用程序图标
    """
    print("检查应用程序图标...")
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
    
    # 如果图标已存在，直接返回路径
    if os.path.exists(icon_path):
        print(f"使用现有图标: {icon_path}")
        return icon_path
    
    # 尝试使用create_icon.py脚本创建图标
    create_icon_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_icon.py')
    if os.path.exists(create_icon_script):
        print("使用create_icon.py脚本创建图标...")
        try:
            # 导入并执行create_icon函数
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from create_icon import create_icon as generate_icon
            icon_path = generate_icon()
            return icon_path
        except Exception as e:
            print(f"创建图标时出错: {e}")
    
    print("警告: 无法创建图标，将使用默认图标")
    return None

def create_version_file():
    """
    创建版本信息文件
    """
    version_info = f"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(1, 0, 4, 0),
    prodvers=(1, 0, 4, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404b0',
        [StringStruct(u'CompanyName', u''),
        StringStruct(u'FileDescription', u'屏幕截图工具'),
        StringStruct(u'FileVersion', u'1.0.4'),
        StringStruct(u'InternalName', u'ScreenshotTool'),
        StringStruct(u'LegalCopyright', u'Copyright (C) {datetime.now().year}'),
        StringStruct(u'OriginalFilename', u'ScreenshotTool.exe'),
        StringStruct(u'ProductName', u'屏幕截图工具'),
        StringStruct(u'ProductVersion', u'1.0.4')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
"""
    version_file = "version_info.txt"
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(version_info)
    return version_file

def build_executable():
    """
    构建可执行文件
    """
    print("开始构建可执行文件...")
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建临时目录用于存放额外文件
    temp_dir = os.path.join(current_dir, 'temp_build')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建版本信息文件
    version_file = create_version_file()
    
    # 创建或获取图标文件
    icon_path = create_icon()
    
    # 收集额外的数据文件
    datas = []
    if os.path.exists('README.md'):
        datas.append(('README.md', '.'))
    
    # 定义 PyInstaller 参数
    params = [
        MAIN_SCRIPT,  # 主程序入口文件
        f'--name={APP_NAME}',  # 生成的 EXE 文件名
        '--onefile',  # 生成单个 EXE 文件
        '--windowed',  # 使用窗口模式，不显示控制台
        '--clean',  # 清理临时文件
        '--noconfirm',  # 不询问确认
        f'--version-file={version_file}',  # 版本信息文件
    ]
    
    # 添加数据文件
    for src, dst in datas:
        params.append(f'--add-data={src};{dst}')
    
    # 如果有图标文件，添加图标参数
    if icon_path:
        params.append(f'--icon={icon_path}')
    
    # 添加隐藏导入
    hidden_imports = [
        '--hidden-import=docx',
        '--hidden-import=keyboard',
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=ctypes',
        '--hidden-import=datetime',
        '--hidden-import=shutil',
        '--hidden-import=atexit',
        '--hidden-import=signal',
    ]
    params.extend(hidden_imports)
    
    # 运行 PyInstaller
    try:
        PyInstaller.__main__.run(params)
        print("构建完成！")
        print(f"可执行文件位于: {os.path.join(current_dir, OUTPUT_DIR, APP_NAME + '.exe')}")
        
        # 创建发布包
        create_release_package()
    except Exception as e:
        print(f"构建过程中出错: {e}")
        sys.exit(1)
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        if os.path.exists(version_file):
            os.remove(version_file)

def create_release_package():
    """
    创建发布包
    """
    try:
        print("创建发布包...")
        
        # 获取当前目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 创建发布目录
        release_dir = os.path.join(current_dir, 'release')
        os.makedirs(release_dir, exist_ok=True)
        
        # 复制可执行文件
        exe_file = os.path.join(current_dir, OUTPUT_DIR, APP_NAME + '.exe')
        if os.path.exists(exe_file):
            release_file = os.path.join(release_dir, APP_NAME + '.exe')
            shutil.copy2(exe_file, release_file)
            
            # 复制 README 文件
            if os.path.exists('README.md'):
                shutil.copy2('README.md', os.path.join(release_dir, 'README.md'))
            
            print(f"发布包已创建: {release_dir}")
        else:
            print(f"警告: 可执行文件不存在: {exe_file}")
    except Exception as e:
        print(f"创建发布包时出错: {e}")

def main():
    """
    主函数
    """
    print(f"=== 开始构建 {APP_NAME} v{APP_VERSION} ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 清理旧的构建文件
    clean_build_directories()
    
    # 安装必要的依赖
    install_requirements()
    
    # 构建可执行文件
    build_executable()
    
    print(f"=== {APP_NAME} v{APP_VERSION} 构建完成 ===")

if __name__ == "__main__":
    main()