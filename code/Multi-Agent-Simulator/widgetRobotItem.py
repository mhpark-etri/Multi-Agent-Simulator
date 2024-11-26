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
    # Init
    def __init__(self, parent = None):
        super(WidgetRobotItem, self).__init__(parent)
        self.ui = Ui_WidgetRobotItem()
        self.ui.setupUi(self)

        # Thumb 네일 이미지 리스트
        self.lstThumbs = []
        self.m_nCurrentThumbIdx = 0

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
        thumb = Thumb()
        thumb.thumbPath = CONST_INTERBOTIX_PATH
        thumb.thumbName = CONST_INTERBOTIX_NAME
        self.lstThumbs.append(thumb)  
        thumb = Thumb()
        thumb.thumbPath = CONST_UNI_PATH
        thumb.thumbName = CONST_UNI_NAME
        self.lstThumbs.append(thumb)  

        # Set thumb image and robot name
        pixmap = QtGui.QPixmap(str(self.lstThumbs[self.m_nCurrentThumbIdx].thumbPath))
        self.ui.lbRobotThumb.setPixmap(pixmap)
        self.ui.lbRobotName.setText(str(self.lstThumbs[self.m_nCurrentThumbIdx].thumbName))

    # 썸네일 이미지 변경 (협업 태스크 고정용)
    def ChageCurrentThumbIdxByName(self, robotName):
        if robotName== CONST_LOCOBOT_NAME:
            pass
        elif robotName == CONST_TURTLEBOT3_BUTGER_NAME:
            self.m_nCurrentThumbIdx = 0
        elif robotName == CONST_TURTLEBOT3_WAFFLE_NAME:
            self.m_nCurrentThumbIdx = 1
        elif robotName == CONST_INTERBOTIX_NAME:
            self.m_nCurrentThumbIdx = 2
        elif robotName == CONST_UNI_NAME:
            self.m_nCurrentThumbIdx = 3

        self.SetThumbAndName()

    # 선택 인덱스 변경 (idx)
    def ChangeCurrentThumbIdx(self, idx):
        self.m_nCurrentThumbIdx = idx
        self.SetThumbAndName()

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
    def SetStartPosition(self, x, y, z):
        self.ui.dsbRobotStartPosX.setValue(float(x))
        self.ui.dsbRobotStartPosY.setValue(float(y))
        self.ui.dsbRobotStartPosZ.setValue(float(z))

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