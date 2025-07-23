#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
应用启动器主模块

支持通过 python -m 运行整个包
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from main import main
    sys.exit(main())