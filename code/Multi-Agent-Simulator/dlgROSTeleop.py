######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : Teleop Dialog                             ##
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

class DialogTeleop(QtWidgets.QDialog):
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
        # # Test
        # lstRobots = []
        # robot = Robot()
        # robot.id = 0
        # robot.rosNamespace = "turtlebot3_waffle_0"
        # robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER
        # # Option Check
        # option = Option()
        # robot.option = option
        # # 로봇 정보 입력
        # lstRobots.append(robot)
        # robot = Robot()
        # robot.id = 1
        # robot.rosNamespace = "locobot_0"
        # robot.type = ENUM_ROBOT_TYPE.LOCOBOT
        # # Option Check
        # option = Option()
        # robot.option = option
        # lstRobots.append(robot)
        # # Test end

        # 1. 로봇 대수 별로 패널 생성
        robotCount = len(self.m_simulator.robots)
        for i in range(0, robotCount):
            # 버튼 생성
            btnPush = QPushButton(ui.fmain)
            # btnName = CONST_LOCOBOT_NAME
            # if lstRobots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER:
            #         btnName = CONST_TURTLEBOT3_BUTGER_NAME
            # elif lstRobots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE:
            #         btnName = CONST_TURTLEBOT3_WAFFLE_NAME
            # elif lstRobots[i].type == ENUM_ROBOT_TYPE.JETBOT:
            #         btnName = CONST_JETBOT_NAME
            # btnName = btnName + "_" + str(lstRobots[i].id)
            btnName = self.m_simulator.robots[i].name
            btnPush.setObjectName(btnName)
            btnPush.setMinimumSize(QSize(0, 40))
            btnPush.setSizeIncrement(QSize(0, 20))
            btnPush.setText(QCoreApplication.translate("DlgROSTeleop", btnName, None))
            self.ui.verticalLayout.addWidget(btnPush)
            # 이벤트 연결
            btnPush.clicked.connect(self.StartTeleop)

    # Teleop 생성
    def StartTeleop(self):
        # 우선 선택한 버튼의 라벨텍스트에서 모델 타입과 ID를 추출한다
        btn = self.sender()
        label = btn.text()
        # 현재는 로봇 모델의 대수가 각각 10대를 넘어가지 않는다는 가정 하에 아래 조건을 실행 한다.
        robotName = label[:len(label) - 1]
        robotIdx = label[-1:]

        # 로봇별 텔레오프 실행
        if robotName == CMD_LOCOBOT_MODEL:
             # 로코봇 텔레오프 실행
             command = CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_LOCOBOT_TELEOP_TWIST_KEYBOARD_PKG + CMD_COMMON_SPACE + CMD_ROS_LOCOBOT_TELEOP_TWIST_KEYBOARD_PY + CMD_COMMON_SPACE
             command = command + CMD_ROS_COMMON_CMD_VEL + CMD_COMMON_PARAM_INSERT + label + CMD_COMMON_SLASH + CMD_ROS_COMMON_CMD_VEL + CMD_COMMON_SPACE
             command = command + CMD_ROS_COMMON_NODE_NAME + CMD_COMMON_PARAM_INSERT + label
             os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)
             pass
        elif robotName == CMD_TURTLEBOT3_DEFAULT_NAME:
                # Buger
                if self.m_simulator.robots[int(robotIdx)].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER:
                    # 터틀봇 버거 텔레오프 실행
                    command = CMD_ROS_COMMON_EXPORT + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_MODEL + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE
                    command = command + CMD_ROS_COMMON_ROS_NAMESPACE + label + CMD_COMMON_SPACE + CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP_KEY
                    os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)
                # Waffle
                elif self.m_simulator.robots[int(robotIdx)].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE:
                    # 터틀봇 와플 텔레오프 실행
                    command = CMD_ROS_COMMON_EXPORT + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_MODEL + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE
                    command = command + CMD_ROS_COMMON_ROS_NAMESPACE + label + CMD_COMMON_SPACE + CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP_KEY
                    os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)
        elif robotName == CMD_INTERBOTIX_ROBOT_NAME_DEFAULT:
            pass
        elif robotName == CMD_UNI_DEFAULT_NAME_UNDERBAR:
            pass
        elif robotName == CMD_HELLO_STRETCH2_MODEL_NAME_UNDERBAR:
            pass
        elif robotName == CMD_JETBOT_DEFAULT_NAME:
             # TODO : jetbot...
             pass
        
    def showModal(self):
        return super().exec_()