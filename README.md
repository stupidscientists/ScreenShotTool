# 屏幕截图工具

一个基于PyQt5的屏幕截图工具，可以捕获全屏或选定区域的截图，并将其添加到Word文档中。适合需要频繁截图并整理到文档中的用户，如软件测试人员、技术文档编写者等。

## 功能特点

- **多种截图模式**：支持全屏截图和区域截图功能
- **悬浮球模式**：可切换到悬浮球模式，使主界面隐藏，只显示一个小悬浮球，减少干扰
- **截图预览**：实时预览截图，固定大小的预览区域确保界面稳定
- **自动保存**：一键自动保存截图到Word文档，无需额外确认
- **文档管理**：创建、打开和保存Word文档
- **系统集成**：
  - 系统托盘支持，最小化后仍可快速访问
  - 全局热键支持（即使应用不在前台也能使用）
  - 窗口置顶功能
- **用户友好界面**：
  - 清晰的功能分区
  - 直观的操作按钮
  - 详细的快捷键提示

## 系统要求

- Windows 10或更高版本
- Python 3.6+（如使用源码运行）
- Microsoft Word（用于文档操作）

## 安装方法

### 方法一：使用预编译的可执行文件

1. 从[发布页面](https://github.com/yourusername/ScreenShotTool/releases)下载最新版本的`ScreenShotTool.exe`
2. 双击运行即可，无需安装

### 方法二：从源码运行

1. 克隆或下载本仓库
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行应用程序：
   ```bash
   python run.py
   ```

## 使用指南

### 基本操作

1. **启动程序**：双击可执行文件或运行`python run.py`
2. **创建/打开文档**：点击"创建新文档"或"打开现有文档"按钮
3. **截图操作**：
   - 点击"截取屏幕"按钮进行截图
   - 使用全屏/区域模式切换复选框选择截图模式
   - 截图后会自动显示在预览区域
4. **保存文档**：点击"保存文档"按钮将所有截图保存到Word文档中

### 快捷键

- **F12**：全屏截图
- **Ctrl+F12**：区域截图
- **F11**：自动保存截图（不显示确认对话框）
- **ESC**：退出悬浮球模式或取消置顶
- **←/→**：在预览区域切换查看不同截图
- **双击预览图片**：全屏查看截图

### 悬浮球模式

1. 创建或打开文档后，点击"悬浮球模式"按钮
2. 主界面将隐藏，屏幕上会显示一个小悬浮球
3. 在悬浮球模式下，可以使用全局快捷键进行截图
4. 点击悬浮球可显示快捷菜单
5. 按ESC键退出悬浮球模式，返回主界面

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
    │   ├── float_ball.py   # 悬浮球窗口
    │   ├── fullscreen_image_viewer.py # 全屏图片查看器
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

### 使用PyInstaller打包

1. 安装PyInstaller：
   ```bash
   pip install pyinstaller
   ```

2. 基本打包命令：
   ```bash
   pyinstaller --onefile --windowed --icon=resources/icon.ico --name=ScreenShotTool run.py
   ```

3. 高级打包选项（推荐）：
   ```bash
   pyinstaller --onefile --windowed --icon=resources/icon.ico --name=ScreenShotTool --clean --noconfirm --add-data "resources;resources" run.py
   ```

### 使用build.py自动化打包（推荐）

项目提供了一个自动化打包脚本`build.py`，它提供了更完整的打包流程：

1. 运行打包脚本：
   ```bash
   python build.py
   ```

2. 脚本功能：
   - 自动清理旧的构建文件和缓存
   - 安装必要的依赖
   - 设置正确的版本信息
   - 添加所有必要的隐藏导入
   - 构建可执行文件
   - 创建发布包

3. 打包后的文件将位于：
   - `dist/ScreenshotTool.exe`：可执行文件
   - `release/`：发布包目录，包含可执行文件和说明文档

### 打包后的文件

打包完成后，可执行文件将位于`dist`目录中：
- `dist/ScreenShotTool.exe`：可直接运行的可执行文件

## 最近更新

- 优化了界面布局，将文档操作和截图操作放在同一行
- 修改了快捷键提示文本，使其更加清晰
- 修复了程序退出时keyboard模块的清理错误
- 改进了预览区域的显示逻辑，确保固定大小
- 优化了悬浮球模式的交互体验

## 常见问题

1. **Q: 为什么我的截图没有显示在Word文档中？**  
   A: 请确保已正确创建或打开Word文档，并且Word应用程序已安装并能正常运行。

2. **Q: 全局热键不起作用怎么办？**  
   A: 可能与其他应用程序的快捷键冲突，尝试关闭其他可能使用相同快捷键的应用程序;另要用管理员模式启动

3. **Q: 程序崩溃了怎么办？**  
   A: 查看日志文件（位于程序目录下的`screenshot_tool.log`）以获取错误信息，并报告给开发者。

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue