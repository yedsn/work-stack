# 应用启动器

一个便捷的应用程序和网站启动工具，支持 Windows 和 macOS 系统优化。

## 特性

- 分类管理应用程序
- 快速搜索和启动
- 支持命令行参数
- 跨平台支持（Windows、macOS）
- 系统托盘支持
- 键盘导航
- 配置Webdav、Github gist、Open gist同步服务

## GitHub Gist 配置同步

应用启动器支持通过 GitHub Gist 在多台设备之间同步您的配置：

1. 在 GitHub 上获取个人访问令牌（需要 Gist 权限）
2. 在应用菜单中选择"GitHub Gist同步" > "GitHub设置"
3. 输入您的 Token 并创建新的 Gist 或使用现有 Gist
4. 通过"上传配置到同步服务"和"从同步服务下载配置"按钮同步您的设置
5. 启用"自动同步"选项，应用将在启动时自动检查并下载最新配置

## 安装

### 依赖项

```
pip install -r requirements.txt
```

### Windows EXE 打包
1. 安装 PyInstaller：`pip install pyinstaller`
2. 运行 `python build_exe.py`（脚本会校验 `main.py`、`resources/`、`config.template.json` 等必需资源并写入版本信息）
3. 完成后在 `dist/应用启动器/应用启动器.exe` 找到生成的可执行文件，分享前请将 `config.template.json` 复制到用户配置目录（Windows `%APPDATA%\Work Stack\config.json`、macOS `~/Library/Application Support/Work Stack/config.json`、Linux `${XDG_CONFIG_HOME:-~/.config}/work-stack/config.json`）并按需定制内容以避免泄露个人配置

> 故障排查：如果提示缺少 PyInstaller 或资源文件，按提示安装依赖或补齐文件后重新运行；打包日志会打印在终端，可附加到评审记录。

## 使用方法

### 启动应用

#### 统一启动方式（推荐）：
```bash
# GUI模式
./launch.sh
# 或者
python launcher.py --gui

# CLI模式
./launch.sh [参数]
# 或者
python launcher.py --cli [参数]

# 通过Python模块运行
python -m work-stack
```

#### 传统启动方式：
```bash
# GUI模式
python main.py

# CLI模式
python cli.py [参数]
```

### 全局热键设置（macOS）

1. 启动应用后，点击右上角的"☰"菜单按钮
2. 选择"设置">"设置全局热键"
3. 在弹出的对话框中，按下您想要设置的快捷键组合（例如：Command+Option+L）
4. 点击"确定"保存设置

> **注意**：首次使用全局热键功能时，macOS 可能会要求授予"辅助功能"权限。请按照系统提示，在"系统偏好设置">"安全性与隐私">"隐私">"辅助功能"中授权本应用。

## 许可证

MIT

## 配置存储路径

应用会把配置、凭证以及配置历史存放到每个用户的独立目录，确保即使安装在不可写的系统目录或通过 PyInstaller 打包后仍能保存设置：

- Windows：`%APPDATA%\Work Stack\config.json`
- macOS：`~/Library/Application Support/Work Stack/config.json`
- Linux：`${XDG_CONFIG_HOME:-~/.config}/work-stack/config.json`

`credentials.enc` 和 `config_history/` 也位于上述目录。升级到该版本后，如果项目根目录存在旧版配置或历史，应用会在首次启动时自动迁移到新的用户目录并留下带时间戳的备份。

## 平台设置功能

应用启动器支持多平台运行（Windows、macOS、Linux），并根据不同平台自动应用适合的UI样式和行为设置。

### 平台设置文件

平台特定的设置存储在 `utils/platform_settings.py` 文件中，该文件包含：

1. 不同平台的UI样式表
2. 窗口行为设置（如关闭窗口的表现）
3. 默认窗口大小设置
4. 窗口激活方法设置

### 使用方法

#### 获取当前平台样式
```python
from utils.platform_settings import get_platform_style

# 获取当前平台的主窗口样式
style = get_platform_style('main_window')
widget.setStyleSheet(style)
```

#### 获取平台特定设置
```python
from utils.platform_settings import get_platform_setting

# 获取当前平台的窗口关闭行为
close_behavior = get_platform_setting('window_close_behavior')

# 获取嵌套设置
width_ratio = get_platform_setting('default_window_size.width_ratio')
```

#### 检查当前平台
```python
from utils.platform_settings import is_windows, is_mac, is_linux

if is_windows():
    # Windows特定代码
elif is_mac():
    # macOS特定代码
else:
    # Linux特定代码
```

### 扩展平台设置

可以通过修改 `utils/platform_settings.py` 文件中的 `PLATFORM_STYLES` 和 `PLATFORM_SETTINGS` 字典来添加新的平台特定设置。

## 其他功能

- 支持应用程序和文件快速启动
- 分类管理功能
- 搜索和过滤功能
- 键盘导航支持
- 系统托盘集成
- 多平台支持（Windows、macOS、Linux）

## 故障排除

### macOS 热键问题

如果全局热键无法正常工作：

1. 确保已安装 PyObjC 库：
   ```bash
   pip3 install pyobjc
   ```

2. 检查"系统偏好设置">"安全性与隐私">"隐私">"辅助功能"中是否已授权本应用

3. 尝试重新设置热键，避免使用系统已占用的快捷键组合

### 应用无法启动

1. 检查Python版本（需要3.6+）
2. 安装依赖项：`pip install -r requirements.txt`
3. 在终端中运行以查看详细错误信息：
   ```bash
   python main.py
   ```

### 权限问题（macOS/Linux）

确保启动脚本有执行权限：
```bash
chmod +x launch.sh
``` 
