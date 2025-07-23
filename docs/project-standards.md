# 应用启动器项目规范文档

## 项目概述

应用启动器（Application Launcher）是一个跨平台的Python桌面应用程序，基于PyQt5构建，用于组织和快速启动应用程序、文件和网站。支持Windows、macOS和Linux系统。

## 目录结构规范

### 标准目录结构

```
work-stack/
├── main.py                     # 主入口文件
├── cli.py                      # 命令行接口
├── launcher.py                 # 启动器模块
├── __main__.py                 # Python模块入口
├── config.json                 # 主配置文件
├── requirements.txt            # Python依赖文件
├── build_exe.py               # 可执行文件构建脚本
├── launch.sh                   # 跨平台启动脚本
├── 应用启动器.spec             # PyInstaller配置文件
├── README.md                   # 项目说明文档
├── CLAUDE.md                   # AI助手项目上下文
├── .gitignore                  # Git忽略文件配置
├── gui/                        # GUI组件包
│   ├── __init__.py            # 包初始化文件
│   ├── main_window.py         # 主窗口
│   ├── category_tab.py        # 分类标签页
│   ├── launch_item.py         # 启动项组件
│   ├── flow_layout.py         # 流式布局管理器
│   ├── base_dialog.py         # 基础对话框
│   ├── *_dialog.py           # 各种功能对话框
│   ├── tag_*.py              # 标签系统相关组件
│   └── hotkey_manager_*.py   # 平台特定热键管理器
├── utils/                      # 工具函数包
│   ├── __init__.py            # 包初始化文件
│   ├── config_manager.py      # 配置管理
│   ├── app_launcher.py        # 应用启动逻辑
│   ├── platform_settings.py  # 平台特定设置
│   ├── logger.py              # 日志系统
│   ├── os_utils.py            # 操作系统工具
│   ├── ui_utils.py            # UI工具函数
│   ├── *_manager.py          # 各种管理器（Gist、WebDAV等）
│   └── config_history.py     # 配置历史管理
├── tests/                      # 测试文件目录
│   ├── __init__.py            # 测试包初始化
│   └── *.py                   # 测试文件
├── docs/                       # 文档目录
│   ├── project-standards.md   # 项目规范文档
│   └── *.md                   # 其他文档
├── resources/                  # 资源文件目录
│   ├── icon.ico               # Windows图标
│   ├── icon.png               # 通用图标
│   └── *                      # 其他资源文件
├── logs/                       # 日志文件目录（运行时生成）
│   └── app.log                # 应用日志
└── config_history/             # 配置历史目录（运行时生成）
    └── *.json                 # 配置备份文件
```

### 目录结构约定

1. **顶级文件**：主要入口文件和配置文件放在根目录
2. **gui包**：所有GUI相关组件，按功能模块划分
3. **utils包**：工具函数和管理器，按功能职责划分
4. **tests包**：测试文件，与源码结构对应
5. **docs目录**：项目文档，包括规范、API文档等
6. **resources目录**：静态资源文件
7. **运行时目录**：logs和config_history在运行时自动创建

## 代码规范

### Python代码规范

#### 1. 基本代码风格
- 遵循PEP 8代码风格规范
- 使用4个空格缩进，不使用制表符
- 行长度限制为88字符（Black格式化工具标准）
- 文件编码统一使用UTF-8

#### 2. 文件头部规范
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模块功能简要描述

详细描述模块的作用和用途
"""
```

#### 3. 导入规范
```python
# 标准库导入
import os
import sys
from typing import Optional, List, Dict

# 第三方库导入
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

# 本地导入
from utils.logger import get_logger
from utils.config_manager import load_config
```

#### 4. 命名规范
- **类名**：使用PascalCase（大驼峰），如`MainWindow`、`ConfigManager`
- **函数名**：使用snake_case（下划线），如`load_config`、`save_settings`
- **变量名**：使用snake_case，如`app_launcher`、`config_data`
- **常量**：使用UPPER_SNAKE_CASE，如`DEFAULT_CONFIG_PATH`、`MAX_RETRY_COUNT`
- **私有方法**：以单下划线开头，如`_init_ui`、`_load_settings`

#### 5. 文档字符串规范
```python
def load_config(config_path: str) -> Dict:
    """
    加载配置文件
    
    Args:
        config_path (str): 配置文件路径
        
    Returns:
        Dict: 配置字典
        
    Raises:
        FileNotFoundError: 配置文件不存在
        JSONDecodeError: 配置文件格式错误
    """
    pass
```

#### 6. 类结构规范
```python
class MainWindow(QWidget):
    """主窗口类"""
    
    # 信号定义
    window_closed = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化方法"""
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """初始化用户界面"""
        pass
    
    def _connect_signals(self):
        """连接信号和槽"""
        pass
    
    # 公共方法
    def show_window(self):
        """显示窗口"""
        pass
    
    # 私有方法
    def _handle_close_event(self):
        """处理关闭事件"""
        pass
```

### GUI组件规范

#### 1. 对话框继承规范
- 所有对话框继承自`base_dialog.py`中的基类
- 实现统一的样式和行为

#### 2. 信号和槽使用规范
- 信号命名使用过去式，如`item_clicked`、`config_changed`
- 槽函数命名使用`handle_`或`on_`前缀

#### 3. 平台特定代码规范
- 平台特定代码放在对应的模块中
- 使用`platform_settings.py`统一管理平台差异

### 配置管理规范

#### 1. 配置文件格式
- 主配置文件使用JSON格式
- 配置结构保持向后兼容
- 添加版本字段用于迁移

#### 2. 配置访问规范
- 统一通过`config_manager.py`访问配置
- 不直接读写配置文件
- 配置修改后立即保存

### 错误处理规范

#### 1. 异常处理
```python
try:
    result = risky_operation()
except SpecificError as e:
    self.logger.error(f"操作失败: {e}")
    # 具体错误处理
except Exception as e:
    self.logger.exception("未预期的错误")
    # 通用错误处理
```

#### 2. 日志记录
- 使用统一的日志系统
- 日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL
- 错误信息包含足够的上下文

### 测试规范

#### 1. 测试文件组织
- 测试文件放在`tests/`目录
- 测试文件名以`test_`开头
- 测试类以`Test`开头

#### 2. 测试方法命名
- 测试方法以`test_`开头
- 使用描述性名称，如`test_load_config_with_valid_file`

## 开发流程规范

### 1. 代码提交规范

#### 提交信息格式
```
<type>: <description>

<body>

<footer>
```

#### 提交类型
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 2. 分支管理规范
- `master`: 主分支，保持稳定
- `develop`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 热修复分支

### 3. 代码审查规范
- 所有代码变更需要经过审查
- 确保代码符合规范
- 测试覆盖新增功能

## 依赖管理规范

### 1. 依赖文件管理
- `requirements.txt`：记录所有直接依赖
- 使用版本固定或兼容性约束
- 定期更新依赖版本

### 2. 平台特定依赖
```
pywin32>=300; platform_system == "Windows"
pyobjc==10.1; sys_platform == 'darwin'
python-xlib==0.33; sys_platform == 'linux'
```

## 构建和发布规范

### 1. 可执行文件构建
- 使用PyInstaller构建
- 配置文件：`应用启动器.spec`
- 支持多平台构建

### 2. 版本管理
- 遵循语义化版本规范（SemVer）
- 格式：MAJOR.MINOR.PATCH
- 版本信息记录在配置中

## 性能规范

### 1. 启动性能
- 应用启动时间控制在3秒内
- 延迟加载非关键模块

### 2. 内存使用
- 监控内存使用情况
- 及时释放不需要的资源

### 3. 响应性能
- UI操作响应时间控制在100ms内
- 长时间操作使用进度指示

## 安全规范

### 1. 敏感信息处理
- API密钥等敏感信息加密存储
- 不在日志中记录敏感信息

### 2. 文件权限
- 配置文件设置适当权限
- 临时文件及时清理

## 文档规范

### 1. 代码文档
- 关键函数和类添加文档字符串
- 复杂逻辑添加内联注释

### 2. 项目文档
- README.md：项目介绍和快速开始
- CLAUDE.md：AI助手上下文
- docs/：详细文档和规范

## 国际化规范

### 1. 文本处理
- 所有用户可见文本支持国际化
- 使用统一的文本资源管理

### 2. 编码规范
- 统一使用UTF-8编码
- 正确处理多字节字符

---

**维护信息**
- 文档版本：1.0
- 最后更新：2025-01-23
- 维护者：项目团队

此规范文档应定期审查和更新，确保与项目发展保持同步。