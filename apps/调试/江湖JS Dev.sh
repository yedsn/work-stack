#!/bin/bash

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# 加载launch.sh
source "$PROJECT_ROOT/launch.sh"

# 启动应用 - 直接传递所有参数给launch_app
name="江湖JSDev"
app="edge"

# 分别传递每个URL作为单独的参数
launch_app "$name" "$app" "https://192.168.7.33:10744/files" "https://192.168.7.33:10744/files/index.html"