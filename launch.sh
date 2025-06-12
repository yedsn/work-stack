#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "未找到Python命令，请确保已安装Python"
    exit 1
fi

# 检查平台
PLATFORM="$(uname -s)"
if [ "$PLATFORM" = "Darwin" ]; then
    # macOS 特定设置
    # 检查必要的 Python 模块
    if ! $PYTHON_CMD -c "import PyQt5" &>/dev/null; then
        echo "请安装 PyQt5: pip install PyQt5"
        exit 1
    fi
    
    if ! $PYTHON_CMD -c "import AppKit" &>/dev/null; then
        echo "请安装 PyObjC (用于 Mac 平台): pip install pyobjc"
        exit 1
    fi
    
    # 确保 QT_MAC_WANTS_LAYER 环境变量设置 (可以防止一些 macOS 上的渲染问题)
    export QT_MAC_WANTS_LAYER=1
fi

# 设置PYTHONPATH环境变量，使Python能够找到launcher模块
export PYTHONPATH="$DIR:$PYTHONPATH"

# 定义启动函数
launch_app() {
    # 直接将所有参数传递给Python脚本
    if [ "$PLATFORM" = "Darwin" ]; then
        # 在 macOS 上，使用 open 命令运行 GUI 应用，以获得更好的集成
        if [ -z "$*" ]; then
            # 如果没有参数，启动 GUI
            $PYTHON_CMD "$DIR/main.py" &
        else
            # 如果有参数，启动 CLI
            $PYTHON_CMD "$DIR/cli.py" "$@"
        fi
    else
        # 在其他平台上，直接运行 Python 脚本
        if [ -z "$*" ]; then
            # 如果没有参数，启动 GUI
            $PYTHON_CMD "$DIR/main.py"
        else
            # 如果有参数，启动 CLI
            $PYTHON_CMD "$DIR/cli.py" "$@"
        fi
    fi
}

# 如果脚本直接运行（不是被source），则使用所有命令行参数启动
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 将所有命令行参数传递给launch_app函数
    launch_app "$@"
fi