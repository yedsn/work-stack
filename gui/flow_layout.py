#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QRect, QSize, QPoint
from PyQt5.QtWidgets import QLayout, QSizePolicy

class FlowLayout(QLayout):
    """流式布局，自动换行"""
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        
        self.items = []
    
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    
    def addItem(self, item):
        self.items.append(item)
    
    def count(self):
        return len(self.items)
    
    def itemAt(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
            
        margin = self.contentsMargins().left()
        size += QSize(2 * margin, 2 * margin)
        return size
    
    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        maxWidth = rect.width()  # 获取可用最大宽度
        
        for item in self.items:
            wid = item.widget()
            # 确保每个部件宽度不超过可用宽度
            itemWidth = min(item.sizeHint().width(), maxWidth)
            
            spaceX = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            
            nextX = x + itemWidth + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + itemWidth + spaceX
                lineHeight = 0
                
            if not testOnly:
                itemRect = QRect(QPoint(x, y), QSize(itemWidth, item.sizeHint().height()))
                item.setGeometry(itemRect)
                
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
            
        return y + lineHeight - rect.y() 