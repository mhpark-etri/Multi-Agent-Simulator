######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                      ## 
## 설명 : Collaboration ListWidget Item              ##
######################################################
import os
import copy
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt, QCoreApplication, QSize
from PySide6.QtWidgets import QFrame, QLayout, QSizePolicy, QVBoxLayout, QHBoxLayout, QPushButton
from ui_widgetROSCollaborationTaskItem import Ui_WidgetCollaborationTask

from constant import *
from simulator import *

class widgetROSCollaborationTaskItem(QtWidgets.QWidget):
    # Init
    def __init__(self, parent = None):
        super(widgetROSCollaborationTaskItem, self).__init__(parent)
        self.ui = Ui_WidgetCollaborationTask()
        self.ui.setupUi(self)

    # Collaboration Task 내용 입력
    def AddCollaborationTask(self, name, path):
        pixmap = QtGui.QPixmap(str(path))
        self.ui.lbROSCollaborationTaskImage.setPixmap(pixmap)
        self.ui.lbROSCollaborationTaskName.setText(name)