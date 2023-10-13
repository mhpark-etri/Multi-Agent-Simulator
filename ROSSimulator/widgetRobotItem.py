######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : Robot Listview                            ##
######################################################
import os
import copy
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt, QCoreApplication, QSize
from PySide6.QtWidgets import QFrame, QLayout, QSizePolicy, QVBoxLayout, QHBoxLayout, QPushButton
from ui_widgetRobotItem import Ui_WidgetRobotItem

from constant import *
from simulator import *

class WidgetRobotItem(QtWidgets.QWidget):
    # Thmubnail List
    lstThumbs = []
    m_nCurrentThumbIdx = 0

    # Init
    def __init__(self, parent = None):
        super(WidgetRobotItem, self).__init__(parent)
        self.ui = Ui_WidgetRobotItem()
        self.ui.setupUi(self)

        self.ui.btnSelectRobotLeft.clicked.connect(self.ChangeRobotToLeft)
        self.ui.btnSelectRobotRight.clicked.connect(self.ChangeRobotToRight)

        # Set robots thumbnail
        thumb = Thumb()
        thumb.thumbPath = CONST_LOCOBOT_PATH
        thumb.thumbName = CONST_LOCOBOT_NAME
         # TEST : 1차 릴리즈 버전에서는 Locobot 제외
        # self.lstThumbs.append(thumb)
        thumb = Thumb()
        thumb.thumbPath = CONST_TURTLEBOT3_BURGER_PATH
        thumb.thumbName = CONST_TURTLEBOT3_BUTGER_NAME
        self.lstThumbs.append(thumb)
        thumb = Thumb()
        thumb.thumbPath = CONST_TURTLEBOT3_WAFFLE_PATH
        thumb.thumbName = CONST_TURTLEBOT3_WAFFLE_NAME
        self.lstThumbs.append(thumb)
        # thumb.thumbPath = ":/thumbnail/Resources/thumbnail/icon_thumb_robot_jetbot.png"
        # thumb.thumbName = "Jetbot"
        # self.lstThumbs.append(thumb)        

        # Set thumb image and robot name
        pixmap = QtGui.QPixmap(str(self.lstThumbs[self.m_nCurrentThumbIdx].thumbPath))
        self.ui.lbRobotThumb.setPixmap(pixmap)
        self.ui.lbRobotName.setText(str(self.lstThumbs[self.m_nCurrentThumbIdx].thumbName))

    # 썸네일 이미지 변경 (왼쪽)
    def ChangeRobotToLeft(self):
        if self.m_nCurrentThumbIdx == 0:
            self.m_nCurrentThumbIdx = len(self.lstThumbs) - 1
        else:
            self.m_nCurrentThumbIdx = self.m_nCurrentThumbIdx - 1

        self.SetThumbAndName()

    # 썸네일 이미지 변경 (오른쪽)
    def ChangeRobotToRight(self):
        if self.m_nCurrentThumbIdx == (len(self.lstThumbs) - 1):
            self.m_nCurrentThumbIdx = 0
        else:
            self.m_nCurrentThumbIdx = self.m_nCurrentThumbIdx + 1

        self.SetThumbAndName()

    # 썸네일 이미지 변경
    def SetThumbAndName(self):
        pixmap = QtGui.QPixmap(str(self.lstThumbs[self.m_nCurrentThumbIdx].thumbPath))
        self.ui.lbRobotThumb.setPixmap(pixmap)
        self.ui.lbRobotName.setText(str(self.lstThumbs[self.m_nCurrentThumbIdx].thumbName))

    # 초기 위치 설정
    def SetStartPosition(self, x, y):
        self.ui.dsbRobotStartPosX.setValue(x)
        self.ui.dsbRobotStartPosY.setValue(y)

    # # UI 정보를 로봇 정보로 추출하여 반환(기술적 문제로 현재 사용되지 않음)
    # def GetRobotInfo(self):
    #     robot = Robot()
    #     # Check robot type
    #     if self.ui.lbRobotName.getText() == CONST_LOCOBOT_NAME:
    #         robot.type = ENUM_ROBOT_TYPE.LOCOBOT
    #     elif self.ui.lbRobotName.getText() == CONST_TURTLEBOT3_BUTGER_NAME:
    #         robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER
    #     elif self.ui.lbRobotName.getText() == CONST_TURTLEBOT3_WAFFLE_NAME:
    #         robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE
    #     else:
    #         robot.type = ENUM_ROBOT_TYPE.JETBOT
    #     # Check starting position
    #     robot.startX = self.ui.dsbRobotStartPosX.value()
    #     robot.startY = self.ui.dsbRobotStartPosY.value()
    #     robot.startZ = self.ui.dsbRobotStartPosZ.value()
    #     # Check robot option
    #     robot.option.camera = self.ui.ckbRobotOptionCamera.isChecked()
    #     robot.option.arm = self.ui.ckbRobotOptionUseArm.isChecked()
    #     robot.option.base = self.ui.ckbRobotOptionBase.isChecked()
    #     return robot