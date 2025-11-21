######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : R-Viz Dialog                             ##
######################################################
import os
import copy
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QCoreApplication, QSize
from PySide6.QtWidgets import QFrame, QLayout, QSizePolicy, QVBoxLayout, QHBoxLayout, QPushButton
from ui_dlgROSTeleop import Ui_DlgROSTeleop

from constant import *
from simulator import *

PATH_SYSTEM_ROOT = ""
PATH_LAUNCH_FOLDER_NAME = "launch"

class DialogRViz(QtWidgets.QDialog):
    # member
    m_simulator = Simulator()                       # Simulator

    # Init
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSTeleop()
        self.ui.setupUi(self)
        self.m_simulator = rosInfo

        # UI 생성
        self.CreateSelectRobotPanel(self.ui)

    # 로봇 정보를 이용해 로봇에 해당하는 패널을 생성한다.
    def CreateSelectRobotPanel(self, ui):
        # 1. 로봇 대수 별로 패널 생성
        robotCount = len(self.m_simulator.robots)
        for i in range(0, robotCount):
            # 버튼 생성
            btnPush = QPushButton(ui.fmain)
            btnName = self.m_simulator.robots[i].name
            btnPush.setObjectName(btnName)
            btnPush.setMinimumSize(QSize(0, 40))
            btnPush.setSizeIncrement(QSize(0, 20))
            btnPush.setText(QCoreApplication.translate("DlgROSRViz", btnName, None))
            self.ui.verticalLayout.addWidget(btnPush)
            # 이벤트 연결
            btnPush.clicked.connect(self.StartRViz)

    # RViz 생성
    def StartRViz(self):
        # 우선 선택한 버튼의 라벨텍스트에서 모델 타입과 ID를 추출한다
        btn = self.sender()
        label = btn.text()
        # 현재는 로봇 모델의 대수가 각각 10대를 넘어가지 않는다는 가정 하에 아래 조건을 실행 한다.
        robotName = label[:len(label) - 1]
        robotIdx = label[-1:]

        # 로봇별 RViz 생성
        if robotName == CMD_LOCOBOT_MODEL:
             # 로코봇 RViz 생성
             pass
        elif robotName == CMD_TURTLEBOT3_BURGER_MODEL:
             # 터틀봇 버거 RViz 생성
             pass
        elif robotName == CMD_TURTLEBOT3_WAFFLE_MODEL:
             # 터틀봇 와플 RViz 생성
             pass
        elif robotName == CMD_JETBOT_DEFAULT_NAME:
             pass
        
    def showModal(self):
        return super().exec_()