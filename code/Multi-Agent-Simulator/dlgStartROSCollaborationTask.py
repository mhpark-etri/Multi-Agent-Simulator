######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : 협업태스크 작업자 다이얼로그                ##
######################################################
import os
from PySide6 import QtWidgets
from PySide6.QtGui import QTextCursor
from widgetStartROSCollaborationTasktItem import WidgetStartROSCollaborationTaskItem
from dlgStartROSCollaborationTask_ui import Ui_DlgROSCollaborationTask
from taskRelay import TaskRelay
import subprocess
import copy
import time
from PySide6.QtCore import QThread, Signal

from constant import *
from simulator import *

class DialogStartROSCollaborationTask(
    QtWidgets.QDialog):
    # Init
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSCollaborationTask()
        self.ui.setupUi(self)

        self.m_simulator = copy.deepcopy(rosInfo)
        self.PATH_LOCO_INIT_SH = "/root/tesla/ros/navi/sh/loco_init_all.sh"

        # UI 생성
        self.SetRobotsInfoToList(self.m_simulator.robots)

        # 이벤트 연결
        self.ui.btnROSCollaborationTaskStart.clicked.connect(self.StartColloaborationTask)

    # 로봇 정보를 이용해 리스트뷰에 로봇 정보 입력
    def SetRobotsInfoToList(self, robots):
        for i in range(len(robots)):
            lstRobot = self.ui.lstwROSCollaborationTaskRobots
            item = QtWidgets.QListWidgetItem(lstRobot)
            # 로봇 위젯 생성
            custom_widget = WidgetStartROSCollaborationTaskItem()
            item.setSizeHint(custom_widget.sizeHint())

            custom_widget.SetupListItem(robots[i].type, robots[i].name)
            custom_widget.SetRobotPosXYZ(str(robots[i].startX), str(robots[i].startY), str(robots[i].startZ))

            # TODO : 현재는 테스트를 위해 초기값 강제 입력
            if i == 0:
                custom_widget.SetRobotMoveToXYZ("1.0", "1.0", "0.0")
            elif i == 1:
                custom_widget.SetRobotMoveToXYZ("1.0", "-1.0", "0.0")
            elif i == 2:
                custom_widget.SetRobotMoveToXYZ("0.0", "0.0", "0.0")
            elif i == 3:
                custom_widget.SetRobotMoveToXYZ("0.0", "-2.0", "0.0")

            # 리스트뷰에 로봇 위젯 셋
            lstRobot.addItem(item)
            lstRobot.setItemWidget(item, custom_widget)

    # 협업 태스크 시작
    def StartColloaborationTask(self):
        self.disableUI()
        # 먼저 locobot init shell을 실행
        print("loco_init_all.sh 스크립트를 실행합니다...")

        try:
            # 새로운 터미널 창을 열고 스크립트를 실행하며 완료될 때까지 기다립니다.
            terminal_command = f"gnome-terminal -- bash -c 'bash {self.PATH_LOCO_INIT_SH}; exec bash'"
            process = subprocess.Popen(terminal_command, shell=True)
            process.wait()  # 스크립트가 완료될 때까지 대기

            print("loco_init_all.sh 스크립트 실행이 완료되었습니다.\n")
            
        except Exception as e:
            print(f"터미널을 여는 중 오류가 발생했습니다: {e}")
            self.enableUI()
            return

        # init이 끝나면 다음으로 설정한 정보를 토대로 relay agent 작업을 실행합니다.
        print("릴레이 작업을 시작합니다.")
        robots = []
        for i in range(len(self.m_simulator.robots)):
            rb = Robot()
            rb.id = self.m_simulator.robots[i].id
            rb.name = self.m_simulator.robots[i].name
            rb.option = self.m_simulator.robots[i].option
            rb.startX = self.m_simulator.robots[i].startX
            rb.startY = self.m_simulator.robots[i].startY
            rb.startZ = self.m_simulator.robots[i].startZ

            # i번째 위젯 가져오기
            if i < self.ui.lstwROSCollaborationTaskRobots.count():
                list_item = self.ui.lstwROSCollaborationTaskRobots.item(i)
                custom_widget = self.ui.lstwROSCollaborationTaskRobots.itemWidget(list_item)
                rb.moveToX = custom_widget.GetRobotMoveToX()
                rb.moveToY = custom_widget.GetRobotMoveToY()
                rb.moveToZ = custom_widget.GetRobotMoveToZ()
            
            robots.append(rb)

        taskRelay = TaskRelay()
        taskRelay.StartTask(robots)

        print("릴레이 작업이 완료되었습니다.\n")
        self.enableUI()

    # System Message
    def SystemMessage(self, msg):
        current_text = self.ui.pteditROSCollaborationTaskMsg.toPlainText()
        new_text = current_text + msg + "\n"
        self.ui.pteditROSCollaborationTaskMsg.setPlainText(new_text)

        # Move cursor to the end
        cursor = self.ui.pteditROSCollaborationTaskMsg.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ui.pteditROSCollaborationTaskMsg.setTextCursor(cursor)
        self.ui.pteditROSCollaborationTaskMsg.ensureCursorVisible()

    # 시스템 UI 프리즈
    def disableUI(self):
        self.ui.btnROSCollaborationTaskStart.setEnabled(False)

    # 시스템 UI 릴리즈
    def enableUI(self):
        self.ui.btnROSCollaborationTaskStart.setEnabled(True)

    def showModal(self):
        return super().exec_()
    