######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : 강화학습 연동 인터페이스 클래스              ##
######################################################
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QMessageBox

from constant import *
from simulator import *

class WidgetReinforcementLearning(QtWidgets.QWidget):
    # Init
    def __init__(self, parent = None):
        super(WidgetReinforcementLearning, self).__init__(parent)
        
        # TODO : GUI 아이템 설계 필요
        self.ui = ()
        self.ui.setupUi(self)

        # TODO : Event Action

 