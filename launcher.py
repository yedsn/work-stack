#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
应用启动器统一入口点

提供GUI和CLI两种模式的统一入口
"""

import sys
import argparse
import os

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='应用启动器')
    parser.add_argument('--cli', action='store_true', help='启动CLI模式')
    parser.add_argument('--gui', action='store_true', help='启动GUI模式（默认）')
    parser.add_argument('--build', action='store_true', help='构建可执行文件')
    
    args, unknown = parser.parse_known_args()
    
    # 如果没有指定模式，检查是否有未知参数来决定使用CLI还是GUI
    if not args.cli and not args.gui and not args.build:
        if unknown:
            args.cli = True
        else:
            args.gui = True
    
    if args.build:
        from build_exe import main as build_main
        return build_main()
    elif args.cli:
        from cli import main as cli_main
        # 将未知参数传递给CLI
        sys.argv = ['cli.py'] + unknown
        return cli_main()
    else:
        from main import main as gui_main
        return gui_main()

if __name__ == "__main__":
    sys.exit(main())