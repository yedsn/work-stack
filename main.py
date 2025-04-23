#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.main_window import LaunchGUI

def main():
    app = QApplication(sys.argv)
    # 设置应用程序图标
    app.setWindowIcon(QIcon("resources/icon.png"))
    window = LaunchGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 