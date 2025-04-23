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

# 设置PYTHONPATH环境变量，使Python能够找到launcher模块
export PYTHONPATH="$DIR:$PYTHONPATH"

# 定义启动函数
launch_app() {
    # 直接将所有参数传递给Python脚本
    $PYTHON_CMD "$DIR/cli.py" "$@"
}

# 如果脚本直接运行（不是被source），则使用所有命令行参数启动
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 将所有命令行参数传递给launch_app函数
    launch_app "$@"
fi