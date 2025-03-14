# 屏幕截图工具

一个基于PyQt5的屏幕截图工具，可以捕获全屏或选定区域的截图，并将其添加到Word文档中。

## 功能特点

- 全屏截图和区域截图功能
- 截图预览和编辑
- 自动保存截图到Word文档
- 工作模式（透明窗口+全局热键）
- 系统托盘支持
- 全局热键支持（即使应用不在前台也能使用）

## 系统要求

- Windows 10或更高版本
- Python 3.6+
- Microsoft Word（用于文档操作）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行应用程序：

```bash
python run.py
```

2. 创建或打开Word文档
3. 使用界面按钮或快捷键进行截图：
   - F12：全屏截图
   - Ctrl+F12：区域截图
   - ESC：退出特殊模式（工作模式/置顶模式）

4. 点击"开始工作"按钮进入工作模式，窗口将变为透明，但快捷键仍然有效

## 项目结构

```
ScreenShotTool/
├── run.py                  # 启动脚本
├── requirements.txt        # 依赖列表
├── README.md               # 项目说明
└── src/                    # 源代码目录
    ├── __init__.py
    ├── main.py             # 主程序入口
    ├── ui/                 # 用户界面模块
    │   ├── __init__.py
    │   ├── main_window.py  # 主窗口
    │   ├── about_dialog.py # 关于对话框
    │   ├── screenshot_dialog.py # 截图对话框
    │   └── capture_window.py    # 截图区域选择窗口
    ├── core/               # 核心功能模块
    │   ├── __init__.py
    │   ├── document_manager.py  # 文档管理
    │   └── screenshot_manager.py # 截图管理
    └── utils/              # 工具模块
        ├── __init__.py
        ├── logger.py       # 日志工具
        ├── event_filter.py # 事件过滤器
        └── hotkey_manager.py # 热键管理
```

## 打包为可执行文件

使用PyInstaller打包为可执行文件：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name=ScreenShotTool run.py
```

## 注意事项

- 确保已安装Microsoft Word并且可以正常使用
- 全局热键可能与其他应用程序的快捷键冲突
- 工作模式下窗口透明但仍然接收键盘事件

## 许可证

MIT License 