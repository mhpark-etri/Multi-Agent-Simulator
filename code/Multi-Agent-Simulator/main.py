######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ##
## 설명 : 3D Agent Simulator 프로그램의 main 스크립트 ##
######################################################
import os
import shutil
import copy
import random
import subprocess
from datetime import datetime  
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QSettings, QProcess
from ui_main import Ui_MainWindow
from dlgROSTeleop import DialogTeleop
from dlgROSSlam import DialogSmal
from dlgROSNavigation import DialogNavigation
from dlgWorldOptionFire import DialogWorldOptionFire
from dlgROSRViz import DialogRViz
from dlgROSI2I import DialogROSI2I
from dlgStartROSCollaborationTask import DialogStartROSCollaborationTask
from dlgJnpMonitor import DialogJnpMonitor
from dlgNavSettings import (DialogNavSettings, generate_nav_overrides,
                            nav_check_value, task_nav_key)
# from dlgDBOpen import DialogDBOpen
from widgetRobotItem import WidgetRobotItem
from widgetROSCollaborationTaskItem import widgetROSCollaborationTaskItem
import atexit
from PySide6.QtGui import QPixmap
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog
import time
import atexit
import rospy

from constant import *
from simulator import *

PATH_SYSTEM_ROOT = ""
PATH_LAUNCH_FOLDER_NAME = "launch"
# PATH_SOURCE_WAREHOUSE = "source /home/tesla/Desktop/tesla_work/01_Models/aws-robomaker-small-warehouse-world-ros1/install/setup.sh"
# PATH_SOURCE_HOSPITAL = "source /home/tesla/Desktop/tesla_work/01_Models/aws-robomaker-hospital-world-ros1/install/setup.sh"
# PATH_SOURCE_SMALL_HOUSE = "source /home/tesla/Desktop/tesla_work/01_Models/aws-robomaker-small-house-world-ros1/install/setup.sh"
# PATH_SOURCE_BOOK_STORE = "source /home/tesla/Desktop/tesla_work/01_Models/aws-robomaker-bookstore-world-ros1/install/setup.sh"
PATH_SOURCE_WAREHOUSE = "source /root/tesla/models/aws-robomaker-small-warehouse-world-ros1/install/setup.sh"
PATH_SOURCE_HOSPITAL = "source /root/tesla/models/aws-robomaker-hospital-world-ros1/install/setup.sh"
PATH_SOURCE_SMALL_HOUSE = "source /root/tesla/models/aws-robomaker-small-house-world-ros1/install/setup.sh"
PATH_SOURCE_BOOK_STORE = "source /root/tesla/models/aws-robomaker-bookstore-world-ros1/install/setup.sh"
PATH_SOURCE_UNI = "source /root/catkin_ws_ai_bot/devel/setup.bash"
PATH_SOURCE_STRETCH2 ="source /root/catkin_ws_stretch2/devel/setup.bash" 
MAX_MODEL_COUNT_ROBOT = 10  # Max robot model count
MAX_MODEL_COUNT_PERSON = 3 # Max person model count
PATH_SOURCE_JNP_SETUP = "source /root/catkin_ws_jnp/devel/setup.sh"
# 연쇄 릴레이 일렬 배치 (2026-08-08, warehouse 지도 실측: x=1.0 통로 y+5~-8.5 자유)
# 스폰 위치·체인 goal 계산·GUI 목록이 전부 이 상수 하나를 기준으로 동기화된다
RELAY_LINE_POSITIONS = {'locobot_0': (1.0, 4.0), 'locobot_1': (1.0, 1.5),
                        'tb3_burger_0': (1.0, -1.0), 'tb3_burger_1': (1.0, -3.5)}
# 다목적 이동: 공동 출발지(베이스) 한 곳에 2×2 클러스터로 모여 스폰
# — 로봇들이 베이스에서 goal 로 왕복. 2026-08-08 지시로 0.8m 뒤(−x)로 이동
#   (지도 실측: 네 지점 모두 자유 공간, free>=250 확인)
# 간격 1.5m (0.8m 은 위치공유 lethal+인플레이션과 겹쳐 복귀 리커버리 회전 유발 — 2026-08-08 실측)
MULTIGOAL_BASE_POSITIONS = {'locobot_0': (-1.25, -0.15), 'locobot_1': (-2.75, -0.15),
                            'tb3_burger_0': (-1.25, -1.65), 'tb3_burger_1': (-2.75, -1.65)}
# 충돌회피(Avoidance): bnt_partition_scaled 월드 — R1=locobot_0(A영역), R2=locobot_1(B영역),
# R3=tb3_burger_0(C영역). tb3_burger_1 은 B영역 구석에 주차(태스크 불참, spawn 만).
# 좌표는 world 벽 실측 해독(2026-08-08). 병목 중심 (0.08,0.24) r=1.35
# ★ world 의 벽 모델 자체가 (0.2009,-0.3634) 이동 배치 — 모든 좌표에 반영 (리뷰 결함 #10/#12)
AVOID_POSITIONS = {'locobot_0': (-2.80, 1.04), 'locobot_1': (3.30, -1.96),
                   'tb3_burger_0': (-2.70, -3.66), 'tb3_burger_1': (4.40, -4.26)}
AVOID_WORLD = '/root/tesla/ros/navi/worlds/bnt_partition_scaled.world'
AVOID_MAP = '/root/tesla/ros/navi/maps/bnt_partition/map.yaml'
SEARCH_WORLD = '/root/tesla/ros/navi/worlds/bnt_partition_scaled_aligned_desk_v3.world'  # 물건찾기 (desk 포함)
SEARCH_TARGETS = 'sports_ball,orange'   # 공 2개 — 주황 공은 YOLO 가 'orange' 로 인식(실측)
# 분산 탐색(지도 제작): locobot 2대 — A/C 영역에서 출발해 커버리지 분담
# 중앙 통로 세로 배치 (2026-08-09 그림 지시: 세 점) — waffle 은 원점(gmapping 정렬)
EXPLORE_POSITIONS = {'locobot_0': (0.30, -0.40), 'locobot_1': (0.30, -2.30),
                     'tb3_waffle_0': (0.0, -1.30)}  # 중앙 통로 일렬, 아래로 -1.3m (2026-08-09 지시; 지도 여유 실측 OK)
PATH_ROS_INTERBOTIX_LAUNCH = "/root/interbotix_ws/src/interbotix_ros_rovers/interbotix_ros_xslocobots/interbotix_xslocobot_gazebo/launch"
PATH_ROS_INTERBOTIX_RVIZ = "/root/interbotix_ws/src/interbotix_ros_rovers/interbotix_ros_xslocobots/interbotix_xslocobot_descriptions/rviz"
PATH_ROS_COLLABORATION_TASK_LAUNCH = "/root/tesla/ros/navi/launch/locobot/"
PATH_ROS_COLLABORATION_TASK_RVIZ = "/root/tesla/ros/navi/rviz/locobot/"
PATH_ROS_COLLABORATION_TASK_LAUNCH_RELAY = "/root/tesla/ros/navi/launch/locobot/locobot_turtle_nav_sim2.launch"
PATH_SOURCE_WAREHOUSE_TASK = "export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:/root/tesla/models/aws-robomaker-small-warehouse-world-ros1/install/aws_robomaker_small_warehouse_world/share"

PATH_DEFAULT_MODEL_PERSON = "/usr/local/share/gazebo-11/media/models"
PATH_DEFAULT_MODEL_PERSON_OTHER = "/usr/share/gazebo-11/media/models"
PATH_DEFAULT_MODEL = ".gazebo/models"
NAME_MODEL_PERSON = "walk.dae"
NAME_MODEL_PERSON_CLOTH_TOP = "sweater-green-effect"
NAME_MODEL_PERSON_CLOTH_BOTTOM = "jeans-blue-effect"
PATH_DEFAULT_WORLDS = "/usr/local/share/gazebo-11/worlds"
PATH_DEFAULT_WORLDS_OTHER = "/usr/share/gazebo-11/worlds"
NAME_BACKUP_WORLD = "backup_world"

ICON_THUMBNAIL_NONE = "Resources/thumbnail/icon_noworld.png"
ICON_THUMBNAIL_ROS_COLLABORATION_TASK_NONE = ""
ICON_THUMBNAIL_ROS_COLLABORATION_TASK_RELAY = "Resources/thumbnail/CollaborationTask/icon_task_relay.png"
ICON_THUMBNAIL_ROS_COLLABORATION_TASK_MOVE = "Resources/thumbnail/CollaborationTask/icon_task_move.png"
ICON_THUMBNAIL_ROS_COLLABORATION_TASK_AVOIDANCE = "Resources/thumbnail/CollaborationTask/icon_task_avoidance.png"
ICON_THUMBNAIL_ROS_COLLABORATION_TASK_SEARCH_FIND = "Resources/thumbnail/CollaborationTask/icon_task_search_find.png"
ICON_THUMBNAIL_ROS_COLLABORATION_TASK_SEARCH_MAKE_MAP = "Resources/thumbnail/CollaborationTask/icon_task_search_make_map.png"

FLOAT_COLOR_X_MIN = 0.0000001               # Minimum x value of random color
FLOAT_COLOR_Y_MIN = 0.0000001               # Minimum y value of random color
FLOAT_COLOR_Z_MIN = 0.0000001               # Minimum z value of random color
FLOAT_COLOR_X_MAX = 0.9999999               # Maximum x value of random color
FLOAT_COLOR_Y_MAX = 0.9999999               # Maximum y value of random color
FLOAT_COLOR_Z_MAX = 0.9999999               # Maximum z value of random color
FLOAT_COLOR_DIGIT = 7                       # Decimal places in random colors
FLOAT_COLOR_ALPHA = 1                       # Alpha color value

class MainWindow(QtWidgets.QMainWindow):
   
    # member
    m_simulator = Simulator()               # Simulator
    m_worlds = []                           # Worlds    
    m_orgPersonColorSweater = []            # OrgPersonSwaterColor x,y,z
    m_orgPersonColorJeans = []              # OrgPersonJeansColor x,y,z    
    m_exeSimulator = None                   # 현재 실핼중인 Gazebo Process
    m_arrJnpProcess = []                    # Jnp sub proecess
    m_startedJnp081 = False                 # JnP 0.8.1 모드로 에이전트를 띄웠는지 (협업태스크 분기용)
    m_startedJnp021 = False                 # JnP 0.2.1 모드로 에이전트를 띄웠는지 (협업태스크 미지원 안내용)
    m_arrROSCollaborationTask = []          # ROS Collaboration Task
    m_prevSelectedCollaborationTask = 0     # 이전 선택된 협업태스크 작업 목록
    m_settings = QSettings(SETTING_COMPANY, SETTING_APP)  # 설정 파일 이름 설정

    # Init
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 소멸자
        atexit.register(self.CleanUp)

        ## UI Event
        self.ui.btnStartSimulator.clicked.connect(self.StartSimualtor)
        self.ui.btnStopSimulator.clicked.connect(self.StopSimulator)
        self.ui.btnExitSimulator.clicked.connect(self.ExitApplication)
        self.ui.actionExit.triggered.connect(self.ExitApplication)   # File>Exit (기존 미연결)
        # 팝업 메시지 언어 (한국어/English) — 설정에 저장/복원
        savedLang = self.m_settings.value('ui_lang')
        if savedLang is not None:
            self.ui.cmbUiLang.setCurrentIndex(int(savedLang))
        self.ui.cmbUiLang.currentIndexChanged.connect(
            lambda i: self.m_settings.setValue('ui_lang', i))

        # Wolrd option
        self.ui.btnWorldOptionFire.clicked.connect(self.OpenWorldOptionFireDialog)

        # Add & Delete Model
        self.ui.btnAddRobot.clicked.connect(self.AddRobot)
        self.ui.btnDeleteRobot.clicked.connect(self.DeleteRobot)
        self.ui.lstwWorldMainCategory.itemSelectionChanged.connect(self.on_item_selection_changed_main_category)
        self.ui.lstwWorldSubCategory.itemSelectionChanged.connect(self.on_item_selection_changed_sub_category)
        self.ui.sbWorldOptionPersonCount.setMaximum(MAX_MODEL_COUNT_PERSON)
        self.ui.chkWorldOptionPerson.stateChanged.connect(self.ChangedWolrdOptionPersonCheckbox)
        self.ui.actionSave.triggered.connect(self.saveFile)
        self.ui.actionOpen.triggered.connect(self.loadFile)
        self.ui.actionOpenDB.triggered.connect(self.OpenDBDialog)
        self.ui.btnAddModel.setVisible(False)
        self.ui.btnAddModel.clicked.connect(self.AddModel)

        # ROS
        self.ui.btnROSTeleop.clicked.connect(self.StartTeleopDialog)
        self.ui.btnROSSlamEdit.clicked.connect(self.StartSlamDialog)
        self.ui.btnROSNavigationEdit.clicked.connect(self.OpenCollaborationSettingDialog)
        self.btnGroupROS = QtWidgets.QButtonGroup()
        self.btnGroupROS.setExclusive(True)
        self.btnGroupROS.addButton(self.ui.rbROSNone)
        self.btnGroupROS.addButton(self.ui.rbROSSlam)
        self.btnGroupROS.addButton(self.ui.rbROSNavigation)
        self.btnGroupROS.buttonToggled.connect(self.ROSRadioButtonItemSelected)
        self.ui.btnRobotROSJNPStart.clicked.connect(self.StartJnp)
        self.ui.btnRobotROSJNPMonitor.clicked.connect(self.ShowJnpMonitor)
        # RViz 체크박스는 토글 즉시 반영 (켜면 2D 뷰 기동, 끄면 종료)
        self.ui.chkRelayRviz.stateChanged.connect(lambda _s: self.EnsureRelayRviz())
        # Nav 설정 — 매 시뮬레이션(Start)마다 반영되는 항법 파라미터 프리셋
        self.btnNavSettings = QtWidgets.QPushButton("Nav 설정 (Nav Settings)")
        # 이웃 Setting 버튼과 동일 스타일 — 밋밋한 라벨처럼 보여 못 찾는 문제 방지
        self.btnNavSettings.setStyleSheet(
            self.ui.btnRobotROSCollaborationSetting.styleSheet())
        # ★ 이웃 버튼의 minimumSize 복사 금지 — 명시 최소폭(114)이 이 버튼이
        #   필요로 하는 폭(162)보다 작아 레이아웃이 글자보다 좁게 찌그러뜨려
        #   라벨이 잘렸다(실측 2026-08-10). 스타일시트의 margin 10+padding 5+
        #   border 2 (양쪽 ≈34px)까지 포함한 sizeHint 를 최소폭으로 쓴다
        #   — 폰트/언어가 바뀌어도 따라간다.
        #   ※ ensurePolished() 필수 — polish 전에는 스타일시트가 sizeHint 에
        #     반영되지 않아 작은 값(114)을 그대로 최소폭으로 굳혀 버린다(실측).
        self.btnNavSettings.ensurePolished()
        self.btnNavSettings.setMinimumWidth(max(
            self.btnNavSettings.sizeHint().width(),
            self.ui.btnRobotROSCollaborationSetting.minimumWidth()))
        self.btnNavSettings.setMinimumHeight(
            self.ui.btnRobotROSCollaborationSetting.minimumHeight())
        # 줄 순서 재배치 (2026-08-08 지시): [Start][RViz] 먼저 — 패널이 좁아도
        # 핵심 조작이 안 잘리게 — 그 다음 [Nav 설정][Setting]
        _lay = self.ui.horizontalLayout_20
        # label_10(빈 라벨)이 앞에 남으면 줄 전체가 오른쪽으로 밀린다 — 맨 뒤로
        _order = [self.ui.btnRobotROSCollaborationStartTask, self.ui.chkRelayRviz,
                  self.btnNavSettings, self.ui.btnRobotROSCollaborationSetting,
                  self.ui.label_10]
        for _w in _order:
            _lay.removeWidget(_w)
        for _w in _order:
            _lay.addWidget(_w)
        _lay.addStretch(1)                  # 왼쪽 정렬 고정
        # 이 줄(Start·RViz·Nav 설정·Setting)이 통째로 들어갈 만큼 Behavior 패널을
        # 가로로 넓힌다 — 패널이 좁으면 버튼 라벨이 잘린다 (2026-08-10 지시).
        # 위젯 sizeHint 합으로 계산하므로 폰트/언어가 바뀌어도 따라간다.
        # 오버헤드 128 = 그룹박스/스크롤영역 여백 + 세로 스크롤바 (이분탐색 실측
        # 2026-08-10). 스크롤영역은 내용의 최소폭을 창까지 전파하지 않아 계산이
        # 아니라 실측값이 필요했다.
        _need = (sum(max(_w.sizeHint().width(), _w.minimumWidth())
                     for _w in _order[:-1])
                 + max(0, _lay.spacing()) * (len(_order) - 2) + 128)
        self.ui.gbRobotROS.setMinimumWidth(
            max(self.ui.gbRobotROS.minimumWidth(), _need))
        # 하단 버튼 순서: [Start][Stop][Exit] (2026-08-09 지시 — 기존 Exit-Stop-Start)
        _bl = self.ui.horizontalLayout_5
        _border = [self.ui.btnStartSimulator, self.ui.btnStopSimulator,
                   self.ui.btnExitSimulator]
        for _w in _border:
            _bl.removeWidget(_w)
        for _w in _border:
            _bl.addWidget(_w)
        self.btnNavSettings.clicked.connect(lambda: DialogNavSettings(self).exec())
        self.ui.gbRobotROSNavigation.setVisible(False)
        self.ui.gbRobotROSJnl.setVisible(False)
        self.ui.gbRobotROSI2IEnhancement.setVisible(True)
        self.ui.lstwRobotROSCollaborationTasks.itemSelectionChanged.connect(self.on_item_selection_changed_collaboration_task)
        self.ui.btnRobotROSCollaborationSetting.clicked.connect(self.OpenCollaborationSettingDialog)
        self.ui.btnRobotROSI2IStart.clicked.connect(self.OpenROSI2IDialoglog)
        self.ui.btnRobotROSCollaborationStartTask.clicked.connect(self.StartCollaborationTask)
        self.ui.btnRobotROSDQNSave.clicked.connect(self.SaveDQNWeightFile)
        self.ui.btnRobotROSDQNLoad.clicked.connect(self.LoadDQNWeightFile)

        # Set Default Init
        # ROS Navigation = None
        self.m_simulator.ros = ENUM_ROS_TYPE.NONE
        # ROS Collaboration = None
        self.m_arrROSCollaborationTask.append(ROSCollaborationTask(ENUM_ROS_COLLABORATION_TASK_TYPE.NONE, ICON_THUMBNAIL_ROS_COLLABORATION_TASK_NONE))
        self.m_arrROSCollaborationTask.append(ROSCollaborationTask(ENUM_ROS_COLLABORATION_TASK_TYPE.RELAY, ICON_THUMBNAIL_ROS_COLLABORATION_TASK_RELAY))
        self.m_arrROSCollaborationTask.append(ROSCollaborationTask(ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE, ICON_THUMBNAIL_ROS_COLLABORATION_TASK_MOVE))
        self.m_arrROSCollaborationTask.append(ROSCollaborationTask(ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE, ICON_THUMBNAIL_ROS_COLLABORATION_TASK_AVOIDANCE))
        self.m_arrROSCollaborationTask.append(ROSCollaborationTask(ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND, ICON_THUMBNAIL_ROS_COLLABORATION_TASK_SEARCH_FIND))
        self.m_arrROSCollaborationTask.append(ROSCollaborationTask(ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP, ICON_THUMBNAIL_ROS_COLLABORATION_TASK_SEARCH_MAKE_MAP))
        for task in self.m_arrROSCollaborationTask:
            # 협업 태스크 리스트에 위젯 추가
            item = QtWidgets.QListWidgetItem(self.ui.lstwRobotROSCollaborationTasks)
            self.ui.lstwRobotROSCollaborationTasks.addItem(item)
            # 협업 태스크 리스트 생성
            row = widgetROSCollaborationTaskItem()
            item.setSizeHint(row.sizeHint())
            # 리스트뷰에 협업 태스트 생성
            row.AddCollaborationTask(task.type.value, task.thumbPath)
            self.ui.lstwRobotROSCollaborationTasks.setItemWidget(item, row)

            # Relay / 다목적 이동 / 충돌회피 활성 — 나머지는 아직 Disable
            if task.type not in (ENUM_ROS_COLLABORATION_TASK_TYPE.NONE,
                                 ENUM_ROS_COLLABORATION_TASK_TYPE.RELAY,
                                 ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE,
                                 ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE,
                                 ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                                 ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND):
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

        self.ui.lstwRobotROSCollaborationTasks.setCurrentRow(0)

        # ROS - Teleop - 현재는 Disable - 이유 : 어떤 모델은 되고 어떤 모델은 안되기 때문에 일단 전체 블럭
        self.ui.btnROSTeleop.setDisabled(True)
        self.ui.btnROSTeleop.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;  /* 기본 스타일 */
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #A9A9A9;  /* 비활성화 시 배경색 */
                color: #808080;  /* 비활성화 시 텍스트 색 */
            }
        """)

        # World
        self.SetWorld()

    # DeInit
    def CleanUp(self):
        os.system("pkill -9 -f gz[s]erver")   # killall 은 이 컨테이너에 없음
        os.system("pkill gnome-terminal")

    # Check world file
    def CheckWorldFile(self, worldFileName):
        # Custom 맵일 경우에는 그냥 통과
        if worldFileName in ("collaboration.world", "collaboration_bnt.world",
                             "collaboration_empty.world"):
            return True

        # check..
        path = PATH_DEFAULT_WORLDS_OTHER + "/" + worldFileName
        if os.path.exists(path) :
            return True
        else :
            return False

    # 시뮬레이터 시작
    def StartSimualtor(self):
        ## 맵 체크
        # Custom 맵들은 일반적인 작업으론 사용 할 수 없도록 조치
        selected_items = self.ui.lstwRobotROSCollaborationTasks.selectedItems()
        item = selected_items[0]
        # 선택된 아이템의 행 번호
        row = self.ui.lstwRobotROSCollaborationTasks.row(item)
        if self.m_arrROSCollaborationTask[row].type == ENUM_ROS_COLLABORATION_TASK_TYPE.NONE:
            if self.m_simulator.categoryMain == ENUM_WORLD_CATEGORY_MAIN.CUSTOM:
                msg = QtWidgets.QMessageBox(self)
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setWindowTitle("Warning")
                msg.setText(self._msg("Custom 맵은 전용 목적에만 사용할 수 있습니다.", "Custom maps can only be used for specialized purposes."))
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg.exec_()
                return

        # 시작전 서버 전부 비활성화
        os.system("pkill -9 -f gz[s]erver")   # killall 은 이 컨테이너에 없음
        # Simulator 구조체 초기화
        if len(self.m_simulator.robots) > 0 :
            self.m_simulator.robots.clear()

        # 1. World 선택
        # 하단 World 라디오 버튼 이벤트에 연결
       
        # 2. 로봇 생성(복수)
        lstRobots = []

        self.SaveUIRobotInfoToSimRobotsInfo(lstRobots)

        # 로봇 정보가 없으면 종료
        if len(lstRobots) <= 0 :
            req = QtWidgets.QMessageBox.question(self, 'Start simulator', 'Please create a robot before running the simulator.',QtWidgets.QMessageBox.Ok)
            return

        # 위치 점검
        if self.CheckRobotPosition(lstRobots) == False:
            req = QtWidgets.QMessageBox.question(self, 'Start simulator', 'There are robots with the same Start Position.',QtWidgets.QMessageBox.Ok)
            return

        # 3. Person 추가된 상태라면 원본 world 복사 뒤 변경
        if self.ui.chkWorldOptionPerson.isChecked():
            personCount = self.ui.sbWorldOptionPersonCount.value()
            self.addPersonToWorld(self.m_simulator.categorySub + self.m_simulator.worldFileType, personCount)

        # 4. RandomColor 추가된 상태라면 원본 .dae 파일 복사 후 색 변경, 해당 항목 사용 하도록 지칭
        if self.ui.chkWorldOptionRandomColor.isChecked():
            personCount = self.ui.sbWorldOptionPersonCount.value()
            self.setPersonColorRandom(personCount)

        # 5. Launch 파일 제작
        self.m_simulator.robots = copy.deepcopy(lstRobots)
        launchFile = self.MakeLaunch(self.m_simulator)
       
        # 6. Launch 파일 실행
        PATH_SYSTEM_ROOT = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME
        tmpFile = PATH_SYSTEM_ROOT + "/shelltemp.sh"
        f = open(tmpFile, 'w+')
        f.write("#!/bin/bash" + CMD_COMMON_ENTER)
        cmdLine = ""

        # UNI050_BASE source 지정
        cmdLine = PATH_SOURCE_UNI
        f.write(cmdLine + CMD_COMMON_ENTER)

        # Hello Robot source 지정
        cmdLine = PATH_SOURCE_STRETCH2
        f.write(cmdLine + CMD_COMMON_ENTER)

        f.write("roslaunch " + launchFile)
        f.close()   # ★ 원본 버그: 괄호 없으면 호출 안 됨 → 쓰기-열림 파일 실행 시 Text file busy
        # Executable 권한 설정
        os.system('chmod 777 ' + tmpFile)  
        # roslaunch (shell)
        
        # TODO : 협업 콜라보레이션 실행
        ## 현재는 협업 콜라보레이션이 체크 된 실행시 로봇 정보가 고정 되므로 미리 준비된 launch 파일을 실행 하도록 적용 한다, 그 외에는 기존 생성한 launch 파일로 실행한다.
        if self.m_simulator.ros_collaboration != ENUM_ROS_COLLABORATION_TASK_TYPE.NONE:
            self.StartROSCollaboration(self.m_simulator.ros_collaboration)
        else :
            # # Gazebo 실행
            exeSimulator = subprocess.Popen(tmpFile, shell=True, executable="/bin/bash")
            if exeSimulator.poll() is None:
                print("Gazebo 실행 성공.")
                self.disableRobotList()
                self.m_exeSimulator = exeSimulator
                self.ui.btnStartSimulator.setEnabled(False)
                self.m_simulator.launchFileName = launchFile
                self.disableRobotList()
            else:
                print("Gazebo 실행 실패.")

            # 만약 Person 추가된 상태라면 원본 파일을 변경 한다
            # if self.ui.chkWorldOptionPerson.isChecked():
            #     time.sleep(1)
            #     self.replaceWorldFile(self.m_simulator.categorySub + self.m_simulator.worldFileType)

    # 설정 파일 정보를 토대로 Launch 파일 정보를 생성
    def MakeLaunch(self, sim):
        ## launch 폴더 생성
        PATH_SYSTEM_ROOT = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME
        if os.path.isdir(PATH_SYSTEM_ROOT) == False :
            os.mkdir(PATH_SYSTEM_ROOT)

        ## launch 파일 제작(파일명 : 년도월일_시분초.launch)
        now = datetime.now()
        tmpFile = PATH_SYSTEM_ROOT + "/" + str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2) + "_" + str(now.hour).zfill(2) + str(now.minute).zfill(2) + str(now.second).zfill(2) + ".launch"
        f = open(tmpFile, 'w')
   
        ###################################################
        ### Simulator 정보를 이용해 launch 파일 작성 시작 ##    
        ###################################################
        ## <Launch>
        f.write(CMD_COMMON_OPEN_LAUNCH + CMD_COMMON_ENTER)  
        f.write(CMD_COMMON_ENTER)

        # 먼저 Interbotix Arguments 입력
        # Interbotix Resources 설정 때문에 World 호출보다 먼저 해줘야한다
        interbotixRobotCount = 0
        robotCount = len(sim.robots)
        for i in range(0, robotCount):
            if sim.robots[i].type == ENUM_ROBOT_TYPE.INTERBOTIX :
                interbotixRobotCount = interbotixRobotCount + 1
        
        if interbotixRobotCount > 0 :
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_COMMENT_ARGUMENTS_START + CMD_COMMON_ENTER)
            # robot model
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_ROBOT_MODEL + "\"                       " + CMD_COMMON_DEFAULT + "\"" + CMD_INTERBOTIX_ROBOT_MODEL_LOCOBOT_WX250S + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # robot name
            for j in range(0, interbotixRobotCount) :
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_ROBOT_NAME + "_" + str(j) + "\"                      " + CMD_COMMON_DEFAULT + "\"" + CMD_INTERBOTIX_ROBOT_NAME_DEFAULT + str(j) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # arm_model
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_ARM_MODEL + "\"                         " + CMD_INTERBOTIX_ARM_MODEL_VALUE + CMD_COMMON_ENTER)
            # show_lidar
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_SHOW_LIDAR + "\"                        " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # show_gripper_bar
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_SHOW_GRIPPER_BAR + "\"                  " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # show_gripper_fingers
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_SHOW_GRIPPER_FINGERS + "\"              " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # external_urdf_loc
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_EXTERNAL_URDF_LOC + "\"                 " + CMD_COMMON_DEFAULT + "\"" + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # use_rviz
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_USE_RVIZ + "\"                          " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_FALSE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # rviz_frame
            for j in range(0, interbotixRobotCount) :
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_RVIZ_FRAME + "_" + str(j) + "\"                      " + CMD_INTERBOTIX_RVIZ_FRAME_VALUE_OPEN + CMD_INTERBOTIX_ROBOT_NAME +"_" + str(j) + CMD_INTERBOTIX_RVIZ_FRAME_VALUE_CLOSE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # use_position_controllers
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_USE_POSITION_CONTROLLERS + "\"          " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_FALSE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # use_trajectory_controllers
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_USE_TRAJECTORY_CONTROLLERS + "\"        " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # dof
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_DOF + "\"                               " + CMD_COMMON_DEFAULT + "\"" + CMD_INTERBOTIX_DOF_VALUE_DEFAULT + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_ENTER)
            # gazebo resources path
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_ENV_GAZEBO_RESOURCE_PATH + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_ENTER)
            # locobot_gazebo_controllers.yaml
            for j in range(0, interbotixRobotCount) :
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_ROSPARAM_FILE_LOCOBOT_GAZEBO_CONTROLLERS_OPEN + CMD_INTERBOTIX_ROBOT_NAME + "_" + str(j) + CMD_INTERBOTIX_ROSPARAM_FILE_LOCOBOT_GAZEBO_CONTROLLERS_CLOSE + CMD_COMMON_ENTER)

            # Interbotix Arguments end..
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_COMMENT_ARGUMENTS_END + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_ENTER)

        ## World 정보 입력
    	# gazebo resources path
        f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_ENV_GAZEBO_RESOURCE_PATH + CMD_COMMON_ENTER)
        f.write(CMD_COMMON_ENTER)
        f.write(CMD_COMMON_SPACE_DOUBLE + CMD_WORLD_COMMENT_START + CMD_COMMON_ENTER)
        # <Inlcude
        f.write(CMD_COMMON_SPACE_DOUBLE + CMD_WORLD_INCLUDE_OPEN + CMD_COMMON_ENTER)
        # <arg name="world_name"
        if sim.worldType == ENUM_WORLD.WAREHOUSE :
            f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_WORLDNAME_WAREHOUSE + CMD_COMMON_ENTER)
        elif sim.worldType == ENUM_WORLD.HOSPITAL :
            f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_WORLDNAME_HOSPITAL + CMD_COMMON_ENTER)
        elif sim.worldType == ENUM_WORLD.SMALLHOUSE :
            f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_WORLDNAME_SMALLHOUSE + CMD_COMMON_ENTER)
        elif sim.worldType == ENUM_WORLD.BOOK_STORE :
            f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_WORLDNAME_BOOKSTORE + CMD_COMMON_ENTER)
        elif sim.worldType == ENUM_WORLD.GAZEBO_DEFAULT :
            strWorld = "worlds/" + sim.categorySub
            if self.ui.chkWorldOptionPerson.isChecked() :
                strWorld = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME + "/"
                strWorld += sim.categorySub
            f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_WORLDNAME_ARG_LEFT + strWorld + CMD_WORLD_ARG_WORLDNAME_ARG_RIGHT + CMD_COMMON_ENTER)
        f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_PAUSED + CMD_COMMON_ENTER)                    # <arg name="paused"
        f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_USE_SIM_TIME + CMD_COMMON_ENTER)              # <arg name="use_sim_time"
        f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_GUI + CMD_COMMON_ENTER)                       # <arg name="gui"
        f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_HEADLESS + CMD_COMMON_ENTER)                  # <arg name="headless"
        f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_ARG_DEBUG + CMD_COMMON_ENTER)                     # <arg name="debug"
        # </Inlcude>
        f.write(CMD_COMMON_SPACE_DOUBLE + CMD_WORLD_INCLUDE_CLOSE + CMD_COMMON_ENTER)
        f.write(CMD_COMMON_SPACE_DOUBLE + CMD_WORLD_COMMENT_END + CMD_COMMON_ENTER)
        f.write(CMD_COMMON_ENTER)

        ## ROS 정보 입력
        if sim.ros == ENUM_ROS_TYPE.NONE:
            pass
        elif sim.ros == ENUM_ROS_TYPE.SLAM:
            pass
        elif sim.ros == ENUM_ROS_TYPE.NAVIGATION:
            # Navigation 정보 입력
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_ROS_NAVIGATION_COMMENT_START + CMD_COMMON_ENTER)
            # map_file
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_MAP_FILE + "\"" + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION_MPA_DEFAULT + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # open_rviz
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_OPEN_RVIZ + "\"" + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # move_forward_only
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_MOVE_FORWARD_ONLY + "\"" + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_FALSE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # multi_robot_name
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_MULTI_ROBOT_NAME + "\"" + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + "" + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # end
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_ROS_NAVIGATION_COMMENT_END + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_ENTER)

        ## 로봇 정보 입력 시작
        for i in range(0, robotCount):
            ## 분기 - ROS에 따른 조정
            # ROS 없음
            if sim.ros == ENUM_ROS_TYPE.NONE:
                ## 1. Locobot
                # if sim.robots[i].type == ENUM_ROBOT_TYPE.LOCOBOT :
                #     f.write(CMD_COMMON_SPACE_DOUBLE + CMD_LOCOBOT_COMMENT_START + CMD_COMMON_ENTER)
                #     # Model names
                #     robotName = CMD_LOCOBOT_MODEL + str(sim.robots[i].id)
                #     robotName = "\"" + robotName + "\""
                #     f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                #     # Model Position
                #     posX = sim.robots[i].startX
                #     posY = sim.robots[i].startY
                #     posZ = sim.robots[i].startZ
                #     robotName = CMD_LOCOBOT_MODEL + str(sim.robots[i].id)
                #     # Group
                #     robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                #     f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                #     # Static transform to make camera work in sim
                #     f.write(CMD_COMMON_SPACE_FOUR + CMD_LOCOBOT_NODE_PKG_TF + CMD_COMMON_ENTER)
                #     # nodel info
                #     sim.robots[i].name = robotName
                #     f.write(CMD_COMMON_SPACE_FOUR + CMD_LOCOBOT_PARAM_NAME_ROBOT_DESCRIPTION + CMD_COMMON_ENTER)
                #     f.write(CMD_COMMON_SPACE_FOUR + CMD_LOCOBOT_INCLUDE_FILE + CMD_COMMON_ENTER)
                #     f.write(CMD_COMMON_SPACE_SIX + CMD_LOCOBOT_ARG_LOAD_ROBOT + CMD_COMMON_ENTER)
                #     f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_INCLUDE + CMD_COMMON_ENTER)
                #     # model의 속성 작성 구문(문법 제작 방식이 복잡한 관계로 sim 객체에서 필요 정보들을 가져와 직접 정적인 구문을 만든다)
                #     f.write(CMD_COMMON_SPACE_FOUR + CMD_LOCOBOT_OPEN_GROUP_NODE_NAME_SPAWN_URDF + " -x " + str(posX) + " -y " + str(posY) + " -z " + CMD_LOCOBOT_POSITION_Z_DEFAULT + CMD_COMMON_SPACE + CMD_LOCOBOT_OPEN_GROUP_MODEL + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET+ CMD_LOCOBOT_CLOSE_GROUP_NODE_NAME_SPAWN_URDF + CMD_COMMON_ENTER)
                #     f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)

                #     # locobot end
                #     f.write(CMD_COMMON_SPACE_DOUBLE + CMD_LOCOBOT_COMMENT_END + CMD_COMMON_ENTER)
                #     f.write(CMD_COMMON_ENTER)
                #     continue
                ## 2. Turtlebot3 - burger
                if sim.robots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER :
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_BURGER_COMMENT_START + CMD_COMMON_ENTER)
                    # Model names
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                    robotName = "\"" + robotName + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Model Position
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                    sim.robots[i].name = robotName
                    robotNamePosX = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_X + "\""
                    robotNamePosY = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Y + "\""
                    robotNamePosZ = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Z + "\""
                    robotNameYaw = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_YAW + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNameYaw + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + CMD_COMMON_DEFAULT_POS + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Group
                    robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_OPEN_GROUP_PARAM_NAME_ROBOT_DESCRIPTION + CMD_TURTLEBOT3_MODEL_BURGER + CMD_TURTLEBOT3_CLOSE_GROUP_PARAM_NAME_ROBOT_DESCRIPTION + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_PARAM_NAME_TF_PREFIX + robotNameRef + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_NODE_PKG_ROBOT_STATE_PUBLISHER + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_SIX + CMD_TURTLEBOT3_GROUP_PARAM_NAME_PUBLISH_FREQUENCY + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_NODE + CMD_COMMON_ENTER)
                    # model의 속성 작성 구문(문법 제작 방식이 복잡한 관계로 sim 객체에서 필요 정보들을 가져와 직접 정적인 구문을 만든다)
                    robotNamePosX = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_X
                    robotNamePosY = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Y
                    robotNamePosZ = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Z
                    robotNameYaw = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_YAW
                    modelProf = "args=\"-urdf -model $(arg " + robotName + ") -x $(arg " + robotNamePosX + ") -y $(arg " + robotNamePosY + ") -z $(arg " + robotNamePosZ + ") -Y $(arg " + robotNameYaw + ")"
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_OPEN_GROUP_NODE_NAME_SPAWN_URDF + modelProf + CMD_TURTLEBOT3_CLOSE_GROUP_NODE_NAME_SPAWN_URDF + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    # Turtlebot3 - burger end
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_BURGER_COMMENT_END + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    continue
                ## 3. Turtlebot3 - waffle
                if sim.robots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE :
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_WAFFLE_COMMENT_START + CMD_COMMON_ENTER)
                    # Model names
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                    robotName = "\"" + robotName + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Model Position
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                    sim.robots[i].name = robotName
                    robotNamePosX = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_X + "\""
                    robotNamePosY = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Y + "\""
                    robotNamePosZ = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Z + "\""
                    robotNameYaw = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_YAW + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNameYaw + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + CMD_COMMON_DEFAULT_POS + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Group
                    robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_OPEN_GROUP_PARAM_NAME_ROBOT_DESCRIPTION + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_TURTLEBOT3_CLOSE_GROUP_PARAM_NAME_ROBOT_DESCRIPTION + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_PARAM_NAME_TF_PREFIX + robotNameRef + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_NODE_PKG_ROBOT_STATE_PUBLISHER + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_SIX + CMD_TURTLEBOT3_GROUP_PARAM_NAME_PUBLISH_FREQUENCY + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_NODE + CMD_COMMON_ENTER)
                    # model의 속성 작성 구문(문법 제작 방식이 복잡한 관계로 sim 객체에서 필요 정보들을 가져와 직접 정적인 구문을 만든다)
                    robotNamePosX = robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_X
                    robotNamePosY = robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Y
                    robotNamePosZ = robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Z
                    robotNameYaw = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_YAW
                    modelProf = "args=\"-urdf -model $(arg " + robotName + ") -x $(arg " + robotNamePosX + ") -y $(arg " + robotNamePosY + ") -z $(arg " + robotNamePosZ + ") -Y $(arg " + robotNameYaw + ")"
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_OPEN_GROUP_NODE_NAME_SPAWN_URDF + modelProf + CMD_TURTLEBOT3_CLOSE_GROUP_NODE_NAME_SPAWN_URDF + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    # Turtlebot3 - burger end
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_WAFFLE_COMMENT_END + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    continue

                ## 4. Jetbot
                if sim.robots[i].type == ENUM_ROBOT_TYPE.JETBOT :                                       # TODO : Jetbot
                    continue

                ## 5. Interbotix
                if sim.robots[i].type == ENUM_ROBOT_TYPE.INTERBOTIX :
                    # default value
                    robotName = CMD_INTERBOTIX_ROBOT_NAME + "_" + str(sim.robots[i].id)
                    sim.robots[i].name = robotName
                    rvizFrameName = CMD_INTERBOTIX_RVIZ_FRAME + "_" + str(sim.robots[i].id)
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_COMMENT_START + CMD_COMMON_ENTER)
                    # group open
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_GROUP_ROBOT_MODEL + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # group open - use_trajectory_controllers
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_INTERBOTIX_GROUP_USE_TRAJECTORY_CONTROLLERS + CMD_COMMON_ENTER)
                    # ros param - trajectory_controllers.yaml
                    f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_ROSPARAM_FILE_TRAJECTORY_CONTROLLERS_OPEN + robotName + CMD_INTERBOTIX_ROSPARAM_FILE_TRAJECTORY_CONTROLLERS_CLOSE + CMD_COMMON_ENTER)
                    # node - controller_spawner
                    f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # group open - use_position_controllers
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_INTERBOTIX_GROUP_USE_POSITION_CONTROLLERS + CMD_COMMON_ENTER)
                    # ros param - position_controllers.yaml
                    f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_ROSPARAM_POSITION_CONTROLLERS_OPEN + robotName + CMD_INTERBOTIX_ROSPARAM_POSITION_CONTROLLERS_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # node - controller_spawner dof 4
                    f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_4_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_4_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # node - controller_spawner dof 5
                    f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_5_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_5_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # node - controller_spawner dof 6
                    f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_6_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_6_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # node - controller_spawner unless locobot_base
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_UNLSESS_LOCOBOT_BASE_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_UNLSESS_LOCOBOT_BASE_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # include - xslocobot_description.launch
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_OPEN + robotName + CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_MIDDLE + rvizFrameName + CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # node - urdf_spawner
                    # xyz position
                    posXYZ = " -x " + str(posX) + " -y " + str(posY) + " -z " + str(posZ)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_NODE_URDF_SPAWNER_OPEN + robotName + CMD_INTERBOTIX_NODE_URDF_SPAWNER_MIDDLE + robotName + posXYZ + CMD_INTERBOTIX_NODE_URDF_SPAWNER_CLOSE + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)

                    # Interbotix end
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_COMMENT_END + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    continue

                ## 6. UNI050_BASE
                if sim.robots[i].type == ENUM_ROBOT_TYPE.UNI050_BASE :
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_UNI_COMMENT_START + CMD_COMMON_ENTER)
                    # Model names
                    robotName = CMD_UNI_DEFAULT_NAME + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                    robotName = "\"" + robotName + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Model Position
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    robotName = CMD_UNI_DEFAULT_NAME + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                    sim.robots[i].name = robotName
                    robotNamePosX = "\"" + robotName + CMD_UNI_DEFAULT_NAME_POSITION_X + "\""
                    robotNamePosY = "\"" + robotName + CMD_UNI_DEFAULT_NAME_POSITION_Y + "\""
                    robotNamePosZ = "\"" + robotName + CMD_UNI_DEFAULT_NAME_POSITION_Z + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Group
                    robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                    # robot_description
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_UNI_PARAM_NAME_ROBOT_DESCRIPTION + CMD_COMMON_ENTER)
                    # robot_state_publisher
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_UNI_NODE_PKG_ROBOT_STATE_PUBLISHER + CMD_COMMON_ENTER)
                    # spawn_model
                    robotNamePosX = robotName + CMD_UNI_DEFAULT_NAME_POSITION_X
                    robotNamePosY = robotName + CMD_UNI_DEFAULT_NAME_POSITION_Y
                    robotNamePosZ = robotName + CMD_UNI_DEFAULT_NAME_POSITION_Z
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_UNI_NODE_PKG_SPAWN_MODEL_OPEN + CMD_COMMON_SPACE + 
                            CMD_COMMON_MODEL + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE + 
                            CMD_COMMON_X + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotNamePosX + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE + 
                            CMD_COMMON_Y + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotNamePosY + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE +
                            CMD_COMMON_Z + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotNamePosZ + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE +
                            CMD_UNI_NODE_PKG_SPAWN_MODEL_CLOSE + CMD_COMMON_ENTER)
                    # Group - close
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    # UNI050_BASE end
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_UNI_COMMENT_END + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    continue          
                ## 7. Hello robot
                if sim.robots[i].type == ENUM_ROBOT_TYPE.HELLO_ROBOT_STRETCH :
                    ## TODO : Option 추가 필요
                    bDex_wrist = "false"
                    bGpu_lidar = "false"
                    bVisualize_lidar = "false"
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_COMMENT_START + CMD_COMMON_ENTER)
                    # Model names
                    robotName = CMD_HELLO_STRETCH2_MODEL_NAME + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                    robotName = "\"" + robotName + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Model Position
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    robotName = CMD_HELLO_STRETCH2_MODEL_NAME + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                    sim.robots[i].name = robotName
                    robotNamePosX = "\"" + robotName + CMD_HELLO_STRETCH2_POSITION_X + "\""
                    robotNamePosY = "\"" + robotName + CMD_HELLO_STRETCH2_POSITION_Y + "\""
                    robotNamePosZ = "\"" + robotName + CMD_HELLO_STRETCH2_POSITION_Z + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Group
                    robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                    # dex_wrist
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ARG_DEX_WRIST_OPEN + bDex_wrist + CMD_HELLO_STRETCH2_ARG_DEX_WRIST_CLOSE + CMD_COMMON_ENTER)
                    # gpu_lidar
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ARG_GPU_LIDAR_OPEN + bGpu_lidar + CMD_HELLO_STRETCH2_ARG_GPU_LIDAR_CLOSE + CMD_COMMON_ENTER)
                    # visualize_lidar
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ARG_VISUALIZE_LIDAR_OPEN + bVisualize_lidar + CMD_HELLO_STRETCH2_ARG_VISUALIZE_LIDAR_CLOSE + CMD_COMMON_ENTER)
                    # model_unlsee
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ARG_MODEL_UNLESS + CMD_COMMON_ENTER)
                    # model_if
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ARG_MODEL_IF + CMD_COMMON_ENTER + CMD_COMMON_ENTER)
                    # robot_description
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_NODE_DESCRIPTION + CMD_COMMON_ENTER)
                    # gazebo spawn
                    argRobotNamePosX = robotName + CMD_HELLO_STRETCH2_POSITION_X
                    argRobotNamePosY = robotName + CMD_HELLO_STRETCH2_POSITION_Y
                    argRobotNamePosZ = robotName + CMD_HELLO_STRETCH2_POSITION_Z
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_NODE_SPAWN_OPEN + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_SPACE
                            + CMD_HELLO_STRETCH2_NODE_SPAWN_PROPERTIES_1 + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE + CMD_HELLO_STRETCH2_NODE_SPAWN_PROPERTIES_2 + CMD_COMMON_SPACE 
                            + CMD_HELLO_STRETCH2_NODE_SPAWN_POSITION_X +  CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + argRobotNamePosX + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE 
                            + CMD_HELLO_STRETCH2_NODE_SPAWN_POSITION_Y +  CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + argRobotNamePosY + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE 
                            + CMD_HELLO_STRETCH2_NODE_SPAWN_POSITION_Z +  CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + argRobotNamePosZ + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE
                            + CMD_HELLO_STRETCH2_NODE_SPAWN_CLOSE + CMD_COMMON_ENTER + CMD_COMMON_ENTER)
                    # state_publisher
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_NODE_STATE_PUBLISHER_OPEN + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_HELLO_STRETCH2_PARAM_STATE_PUBLISHER_FREQUENCY + CMD_COMMON_ENTER)
                    f.write(CMD_HELLO_STRETCH2_NODE_STATE_PUBLISHER_CLOSE + CMD_COMMON_ENTER + CMD_COMMON_ENTER)
                    # controller_setting
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ROSPARAM_PARAM_LOAD_CONFIG_JOINT + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ROSPARAM_PARAM_LOAD_CONFIG_DRIVE_CONFIG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ROSPARAM_PARAM_LOAD_CONFIG_ARM + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ROSPARAM_PARAM_LOAD_CONFIG_HEAD + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ROSPARAM_PARAM_LOAD_CONFIG_GRIPPER + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_ROSPARAM_PARAM_LOAD_CONFIG_DEX_WRIST + CMD_COMMON_ENTER + CMD_COMMON_ENTER)
                    # controller_spawn
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_NODE_CONTROLLER_SPAWN_UNLESS + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_NODE_CONTROLLER_SPAWN_IF + CMD_COMMON_ENTER + CMD_COMMON_ENTER)
                    # ground_truth_odometry
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_NODE_GROUND_TRUTH_ODOM + CMD_COMMON_ENTER + CMD_COMMON_ENTER)
                    # Group - close
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    # UNI050_BASE end
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_HELLO_STRETCH2_COMMENT_END + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    continue

            # ROS SLAM
            elif sim.ros == ENUM_ROS_TYPE.SLAM:
                pass                                                                                    # TODO

            # ROS Navigation
            # 동일 제조사의 모델일 때만 실행 되도록 해야 할 듯..?
            elif sim.ros == ENUM_ROS_TYPE.NAVIGATION:
                ## 1. Locobot
                if sim.robots[i].type == ENUM_ROBOT_TYPE.LOCOBOT :
                    pass
                ## 2. Turtlebot3 - burger
                if sim.robots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER :
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_BURGER_COMMENT_START + CMD_COMMON_ENTER)
                    # Model names
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + str(sim.robots[i].id)
                    robotName = "\"" + robotName + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Model Position
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + str(sim.robots[i].id)
                    sim.robots[i].name = robotName
                    robotNamePosX = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_X + "\""
                    robotNamePosY = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Y + "\""
                    robotNamePosZ = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Z + "\""
                    robotNameYaw = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_YAW + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNameYaw + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + CMD_COMMON_DEFAULT_POS + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Group
                    robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                    # tf_prefix
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_PARAM_NAME_TF_PREFIX + robotNameRef + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # include file
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_ROS_NAVIGATION_TURTLEBOT3_INCLUDE_ONE_ROBOT_LAUNCH + CMD_COMMON_ENTER)
                    # model
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_TURTLEBOT3_MODEL + CMD_COMMON_SPACE + CMD_COMMON_VALUE + "\"" + CMD_TURTLEBOT3_MODEL_BURGER + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # robot_name
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_ROBOT_NAME + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + robotNameRef + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # x_pos
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_X_POS + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_X + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # y_pos
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_Y_POS + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Y + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # z_pos
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_Z_POS + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Z + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # map_file
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_MAP_FILE + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_MAP_FILE + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # move_forware_only
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_MOVE_FORWARD_ONLY + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_MOVE_FORWARD_ONLY + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)                  
                    # include close
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_INCLUDE + CMD_COMMON_ENTER)
                    # Group - Close
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    # Turtlebot3 - burger end
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_BURGER_COMMENT_END + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    continue
                ## 3. Turtlebot3 - waffle
                if sim.robots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE :
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_WAFFLE_COMMENT_START + CMD_COMMON_ENTER)
                    # Model names
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + str(sim.robots[i].id)
                    robotName = "\"" + robotName + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Model Position
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + str(sim.robots[i].id)
                    sim.robots[i].name = robotName
                    robotNamePosX = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_X + "\""
                    robotNamePosY = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Y + "\""
                    robotNamePosZ = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Z + "\""
                    robotNameYaw = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_YAW + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNameYaw + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + CMD_COMMON_DEFAULT_POS + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Group
                    robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                    # tf_prefix
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_PARAM_NAME_TF_PREFIX + robotNameRef + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # include file
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_ROS_NAVIGATION_TURTLEBOT3_INCLUDE_ONE_ROBOT_LAUNCH + CMD_COMMON_ENTER)
                    # model
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_TURTLEBOT3_MODEL + CMD_COMMON_SPACE + CMD_COMMON_VALUE + "\"" + CMD_TURTLEBOT3_MODEL_WAFFLE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # robot_name
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_ROBOT_NAME + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + robotNameRef + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # x_pos
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_X_POS + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_X + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # y_pos
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_Y_POS + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Y + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # z_pos
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_Z_POS + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Z + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # map_file
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_MAP_FILE + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_MAP_FILE + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    # move_forware_only
                    f.write(CMD_COMMON_SPACE_SIX + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + "\"" + CMD_ROS_NAVIGATION_MOVE_FORWARD_ONLY + "\"" + CMD_COMMON_SPACE + CMD_COMMON_VALUE + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_MOVE_FORWARD_ONLY + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)                  
                    # include close
                    f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_INCLUDE + CMD_COMMON_ENTER)
                    # Group - Close
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                    # Turtlebot3 - waffle end
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_WAFFLE_COMMENT_END + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    continue
   
                ## 4. Jetbot
                if sim.robots[i].type == ENUM_ROBOT_TYPE.JETBOT :                                       # TODO : Jetbot
                    continue

        # RViz                                                                                  
        # TODO : 이슈가 있다, RViz 자체는 현재 최대 2가지 로봇에 대해 설정해놓은 파일이 강제로 세팅 되어있다, RViz를 동적으로 만들수 있는 알고리즘 같은게 있어야 유동적 사용이 가능하다.
        if sim.ros == ENUM_ROS_TYPE.NAVIGATION:
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_ROS_NAVIGATION_COMMONET_RVIZ_START + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_IF + CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_OPEN_RVIZ + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_SPACE_FOUR + CMD_ROS_NAVIGATION_RVIZ_PKG + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_ROS_NAVIGATION_COMMONET_RVIZ_END + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_ENTER)

        # </Launch>
        f.write(CMD_COMMON_CLOSE_LAUNCH)
        f.close()
        return tmpFile
    
    # 협업 콜라보레이션으로 Gazebo 실행
    def StartROSCollaboration(self, collaboTask):
        # 먼저 locobot 경로에 파일 복사
        # launch
        for filename in os.listdir(PATH_ROS_COLLABORATION_TASK_LAUNCH):
            source_file = os.path.join(PATH_ROS_COLLABORATION_TASK_LAUNCH, filename)
            dest_file = os.path.join(PATH_ROS_INTERBOTIX_LAUNCH, filename)
        
            # 파일인지 확인 후 복사
            if os.path.isfile(source_file):
                shutil.copy(source_file, dest_file)

        # rviz
        for filename in os.listdir(PATH_ROS_COLLABORATION_TASK_RVIZ):
            source_file = os.path.join(PATH_ROS_COLLABORATION_TASK_RVIZ, filename)
            dest_file = os.path.join(PATH_ROS_INTERBOTIX_RVIZ, filename)
        
            # 파일인지 확인 후 복사
            if os.path.isfile(source_file):
                shutil.copy(source_file, dest_file)

        # 다음으로 COLLABORATION 타입에 따라 launch 실행
        # 먼저 shell 파일 생성
        PATH_SYSTEM_ROOT = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME
        tmpFile = PATH_SYSTEM_ROOT + "/shelltemp_task.sh"
        f = open(tmpFile, 'w+')
        f.write("#!/bin/bash" + CMD_COMMON_ENTER)
        cmdLine = ""
        # UNI050_BASE source 지정
        cmdLine = PATH_SOURCE_UNI
        f.write(cmdLine + CMD_COMMON_ENTER)

        # Hello Robot source 지정
        cmdLine = PATH_SOURCE_STRETCH2
        f.write(cmdLine + CMD_COMMON_ENTER)

        # locobot(interbotix) source 지정 — Relay nav launch가 interbotix_xslocobot_gazebo 를
        # $(find) 하므로 필수. GUI 를 어떤 셸에서 띄웠든 여기서 보장한다 (2026-08-08 실측:
        # 이 줄이 없으면 ResourceNotFound 로 relay launch 즉사)
        cmdLine = "source /root/interbotix_ws/devel/setup.bash"
        f.write(cmdLine + CMD_COMMON_ENTER)

        # # TODO : 일단은 aws-robomaker-warehouse 모델을 강제로 로드하고 있으므로 source 명령이 필요, 나중에 동적 맵 로딩이 가능하게 되면 제거
        # cmdLine = PATH_SOURCE_WAREHOUSE_TASK
        # f.write(cmdLine + CMD_COMMON_ENTER)

        # cmdLine = "source ~/.bashrc"
        # f.write(cmdLine + CMD_COMMON_ENTER)

        cmdLine = PATH_SOURCE_WAREHOUSE
        f.write(cmdLine + CMD_COMMON_ENTER)

        # 협력콜라보레이션 작업 타입 별 실행 구문 변경
        # Relay / 다목적 이동(MOVE) 은 동일한 warehouse+4로봇+항법 구성을 사용
        if collaboTask in (ENUM_ROS_COLLABORATION_TASK_TYPE.RELAY,
                           ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE,
                           ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE,
                           ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                           ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND):
            # use_rviz:=false → 로봇별/tb3 RViz 를 끄고, 통합 RViz 하나만
            # 2D 전용 설정(지도+경로+goal+로봇 위치)으로 띄운다 (2026-08-08)
            # RViz 2D 뷰는 체크박스 옵션 (기본 꺼짐 — 시각화 없이 실행)
            showRviz = 'true' if self.ui.chkRelayRviz.isChecked() else 'false'
            # ── 태스크별 배치 ──
            # Relay: 일렬(2.5m 간격 — 바톤 전달이 보이게)
            # 다목적 이동: 공동 출발지(베이스) 2×2 클러스터 — 베이스↔goal 왕복
            if collaboTask == ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE:
                lp = MULTIGOAL_BASE_POSITIONS
            elif collaboTask == ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE:
                lp = AVOID_POSITIONS      # 충돌회피: bnt 월드 A/B/C 영역 + 주차 1대
            elif collaboTask in (ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                                 ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND):
                lp = EXPLORE_POSITIONS    # 지도제작/물건찾기: 동일 배치 (2026-08-10)
            else:
                lp = RELAY_LINE_POSITIONS
            for rb in self.m_simulator.robots:
                if rb.name in lp:
                    rb.startX, rb.startY = lp[rb.name]
            relayArgs = ("robot_model:=locobot_wx250s use_lidar:=true use_position_controllers:=true rtabmap_args:=-d"
                         " use_rviz:=false rvizconfig:=/root/tesla/ros/navi/rviz/locobot/relay_2d.rviz"
                         f" show_rviz2d:={showRviz}"
                         f" loco0_x:={lp['locobot_0'][0]} loco0_y:={lp['locobot_0'][1]}"
                         f" loco1_x:={lp['locobot_1'][0]} loco1_y:={lp['locobot_1'][1]}"
                         f" tb3_0_x:={lp.get('tb3_burger_0', (0, -9))[0]} tb3_0_y:={lp.get('tb3_burger_0', (0, -9))[1]}"
                         f" tb3_1_x:={lp.get('tb3_burger_1', (0, -9.5))[0]} tb3_1_y:={lp.get('tb3_burger_1', (0, -9.5))[1]}")
            if collaboTask == ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE:
                # 충돌회피 전용 월드(bnt)+합성 지도, 로봇 3대(2 locobot + 1 tb3)
                relayArgs += (f" world_name:={AVOID_WORLD} map_file:={AVOID_MAP}"
                              " spawn_second_tb3:=false use_known_map:=true")
            elif collaboTask == ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP:
                # 지도제작: bnt + SLAM 모드 — locobot 2 + waffle 1 (burger 미스폰)
                wx, wy = EXPLORE_POSITIONS['tb3_waffle_0']
                # waffle SLAM 선택 (Nav 설정 콤보; 기본 slam_toolbox)
                _ws = str(self.m_settings.value('nav/SEARCH_MAKE_MAP/planner_waffle_slam')
                           or self.m_settings.value('nav/planner_waffle_slam') or '')
                _ws = ('gmapping' if 'gmapping' in _ws
                       else 'rtabmap' if 'rtabmap' in _ws else 'slam_toolbox')
                relayArgs += (f" world_name:={AVOID_WORLD}"
                              " spawn_tb3s:=false spawn_waffle:=true explore_nav:=true"
                              f" waffle_x:={wx} waffle_y:={wy} waffle_slam:={_ws}")
            elif collaboTask == ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND:
                # 물건찾기: desk 월드 + 알려진 지도 + 지도제작 로봇 편성.
                # 카메라 틸트 위로(-0.12) — desk 상판(0.8m)이 보이게 (2026-08-10)
                wx, wy = EXPLORE_POSITIONS['tb3_waffle_0']
                _ws = str(self.m_settings.value('nav/SEARCH_FIND/planner_waffle_slam')
                           or self.m_settings.value('nav/planner_waffle_slam') or '')
                _ws = ('gmapping' if 'gmapping' in _ws
                       else 'rtabmap' if 'rtabmap' in _ws else 'slam_toolbox')
                relayArgs += (f" world_name:={SEARCH_WORLD} map_file:={AVOID_MAP}"
                              " use_known_map:=true spawn_tb3s:=false"
                              " perceive_high:=true search_nav:=true"
                              " spawn_waffle:=true camera_tilt_angle:=-0.12"
                              f" waffle_x:={wx} waffle_y:={wy} waffle_slam:={_ws}")
            else:
                # Relay/다목적: World 패널에서 외벽-only(empty) 를 골랐으면 교체 (RTF↑)
                try:
                    subItem = self.ui.lstwWorldSubCategory.currentItem()
                    if subItem is not None and 'empty' in subItem.text():
                        relayArgs += (
                            " world_name:=/root/tesla/ros/navi/worlds/empty_warehouse_walls.world"
                            " map_file:=/root/tesla/ros/navi/maps/empty_warehouse/map.yaml")
                        print("### 외벽-only 월드 선택 (RTF 향상 모드)")
                except Exception as e:
                    print(f"월드 선택 확인 실패(기본 warehouse): {e}")
            # Nav 설정(다이얼로그) → 이번 판 오버라이드 생성 + 위치공유 on/off
            _navTask = task_nav_key(collaboTask)
            useMutual = nav_check_value(self.m_settings, 'mutual', _navTask)
            relayArgs += " mutual_obstacles:=" + ('true' if useMutual else 'false')
            try:
                generate_nav_overrides(
                    self.m_settings,
                    '/root/tesla/ros/navi/launch/locobot/nav_overrides.launch',
                    task_key=_navTask)
            except Exception as e:
                print(f"nav_overrides 생성 실패(기본값으로 진행): {e}")
            # 헬퍼 노드 로봇 목록 — 태스크별 실제 편성 (기본값은 burger 2대 편성)
            if collaboTask in (ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                               ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND):
                _task_robots = ' _robots:=locobot_0,locobot_1,tb3_waffle_0'
            elif collaboTask == ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE:
                _task_robots = ' _robots:=locobot_0,locobot_1,tb3_burger_0'
            else:
                _task_robots = ''
            # 헬퍼는 roslaunch(=roscore)보다 먼저 실행되므로 마스터 대기 필수 —
            # roscore 완전 종료 후 첫 Start 에서 즉사하던 문제 (2026-08-09 실측)
            _wait_master = ("( until rostopic list >/dev/null 2>&1; do sleep 2; done; "
                            "sleep 2; ")
            # ★ 이전 Start 의 헬퍼 잔존 정리 — Start 마다 누적돼 이름 쟁탈·CPU 잠식
            #   (yolo_detector 6개/map_nav_clear 8개 실측, 2026-08-10).
            #   ^python3 앵커 = bash 래퍼/자기 자신 오살 방지
            f.write("pkill -f '^python3 /root/tesla/ros/navi/scripts/"
                    "(goal_labels|map_nav_clear|object_spawner|yolo_detector|"
                    "traffic_zones|mutual_obstacles)\\.py' 2>/dev/null; sleep 1\n")
            # goal 위치에 로봇 이름 라벨 마커 (rviz 의 Goal Labels 표시가 구독)
            f.write(f"{_wait_master}python3 /root/tesla/ros/navi/scripts/goal_labels.py{_task_robots} ) &\n")
            if collaboTask in (ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                               ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND):
                # 병합 지도의 '자기-박제 벽' 제거본(/map_nav/<robot>) — locobot
                # 전역 costmap 이 자기 위치 lethal 로 계획 불능 되는 문제 (2026-08-09)
                f.write(f"{_wait_master}python3 /root/tesla/ros/navi/scripts/"
                        "map_nav_clear.py _robots:=locobot_0,locobot_1,tb3_waffle_0"
                        " _park_secs:=4.0 ) &\n")
            if collaboTask == ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND:
                # 물건찾기: desk 위 물체 스폰 + YOLO v8 감지 노드 (2026-08-10)
                f.write(f"{_wait_master}python3 /root/tesla/ros/navi/scripts/"
                        "object_spawner.py ) &\n")
                # ★PYTHONNOUSERSITE 금지: torch/torchvision/requests 가
                # user-site 에 있음 (2026-08-10 실측 — 켜면 import 불가)
                f.write(f"{_wait_master}python3 "
                        "/root/tesla/ros/navi/scripts/yolo_detector.py"
                        f" _targets:={SEARCH_TARGETS} ) &\n")
            if nav_check_value(self.m_settings, 'zones', _navTask):
                # 존-토큰 교통관제 — 좁은 구역(base/goal) 이동 직렬화 (2026-08-08)
                f.write(f"{_wait_master}python3 /root/tesla/ros/navi/scripts/traffic_zones.py ) &\n")
            if useMutual:
                # 그룹 위치공유 → 상호 costmap 장애물 (locobot 라이다가 burger 못 보는 문제)
                f.write(f"{_wait_master}python3 /root/tesla/ros/navi/scripts/mutual_obstacles.py{_task_robots} ) &\n")
            # 컨트롤러 준비되는 즉시 자동 unpause + 팔 내림 (협업 Start 전에 팔부터 정리)
            f.write("bash /root/tesla/ros/navi/sh/loco_ready_init.sh &\n")
            f.write(f"roslaunch {PATH_ROS_COLLABORATION_TASK_LAUNCH_RELAY} {relayArgs}\n")
            print("### value = " + f"roslaunch {PATH_ROS_COLLABORATION_TASK_LAUNCH_RELAY} {relayArgs}\n")

        f.close()   # ★ 원본 버그: 괄호 없으면 호출 안 됨 → 쓰기-열림 파일 실행 시 Text file busy
        # Executable 권한 설정
        os.system('chmod 777 ' + tmpFile)  
        
        ## Gazebo 실행
        exeSimulator = subprocess.Popen(tmpFile, shell=True, executable="/bin/bash")
        if exeSimulator.poll() is None:
            print("Gazebo 실행 성공.")
            self.m_exeSimulator = exeSimulator
            self.ui.btnStartSimulator.setEnabled(False)
            self.m_simulator.launchFileName = PATH_ROS_COLLABORATION_TASK_LAUNCH_RELAY
            self.disableRobotList()
        else:
            print("Gazebo 실행 실패.")


    # 실행중인 Gazebo에 로봇 모델 추가
    def AddModel(self):
        lstRobots = []
        lstAddedRobots = []
        self.SaveUIRobotInfoToSimRobotsInfo(lstRobots)
        arrInterbotixRobotIndex = []

        for idx in range(len(lstRobots)):
            item = self.ui.lstwRobots.item(idx)
            widget = self.ui.lstwRobots.itemWidget(item)

            # 새로 추가된 로봇 모델만 확인
            if widget.isEnabled():
                item = self.ui.lstwRobots.item(idx)
                widget = self.ui.lstwRobots.itemWidget(item)
                robot = Robot()
                # Check robot type and set id
                if widget.ui.lbRobotName.text() == CONST_LOCOBOT_NAME:
                    # TEST : 1차 릴리즈 버전에서는 Locobot 제외
                    pass
                    robot.type = ENUM_ROBOT_TYPE.LOCOBOT
                    robot.id = lstRobots[idx].id
                elif widget.ui.lbRobotName.text() == CONST_TURTLEBOT3_BUTGER_NAME:
                    robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER  
                    robot.id = lstRobots[idx].id
                elif widget.ui.lbRobotName.text() == CONST_TURTLEBOT3_WAFFLE_NAME:
                    robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE
                    robot.id = lstRobots[idx].id
                elif widget.ui.lbRobotName.text() == CONST_JETBOT_NAME:
                    robot.type = ENUM_ROBOT_TYPE.JETBOT
                    robot.id = lstRobots[idx].id
                elif widget.ui.lbRobotName.text() == CONST_INTERBOTIX_NAME:
                    robot.type = ENUM_ROBOT_TYPE.INTERBOTIX
                    robot.id = lstRobots[idx].id
                    arrInterbotixRobotIndex.append(robot.id)
                elif widget.ui.lbRobotName.text() == CONST_UNI_NAME:
                    robot.type = ENUM_ROBOT_TYPE.UNI050_BASE
                    robot.id = lstRobots[idx].id

                robot.startX = lstRobots[idx].startX
                robot.startY = lstRobots[idx].startY
                robot.startZ = lstRobots[idx].startZ

                # Check robot option
                robot.option.camera = widget.ui.ckbRobotOptionCamera.isChecked()
                robot.option.arm = widget.ui.ckbRobotOptionUseArm.isChecked()
                robot.option.base = widget.ui.ckbRobotOptionBase.isChecked()
                lstAddedRobots.append(robot)
                self.m_simulator.robots.append(robot)

        # Launch 파일 제작
        PATH_SYSTEM_ROOT = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME
        if os.path.isdir(PATH_SYSTEM_ROOT) == False :
            req = QtWidgets.QMessageBox.question(self, 'Add a model', 'There is no path to the last saved launch file.',QtWidgets.QMessageBox.Ok)
            return

        ## launch 파일 제작
        base_name, ext = os.path.splitext(self.m_simulator.launchFileName)
        launchFile = f"{base_name}_{self.m_simulator.addedLunchFileNumber}{ext}"
        f = open(launchFile, 'w')
   
        ##############################################
        ### Simulator 정보를 이용해 launch 파일 작성 시작 ##    
        ##############################################
        sim = Simulator()
        sim.robots = copy.deepcopy(lstAddedRobots)
        ## <Launch>
        f.write(CMD_COMMON_OPEN_LAUNCH + CMD_COMMON_ENTER)  
        f.write(CMD_COMMON_ENTER)

        # 먼저 Interbotix Arguments 입력
        # Interbotix Resources 설정 때문에 World 호출보다 먼저 해줘야한다
        interbotixRobotCount = 0
        robotCount = len(sim.robots)
        for i in range(0, robotCount):
            if sim.robots[i].type == ENUM_ROBOT_TYPE.INTERBOTIX :
                interbotixRobotCount = interbotixRobotCount + 1
        
        if interbotixRobotCount > 0 :
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_COMMENT_ARGUMENTS_START + CMD_COMMON_ENTER)
            # robot model
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_ROBOT_MODEL + "\"                       " + CMD_COMMON_DEFAULT + "\"" + CMD_INTERBOTIX_ROBOT_MODEL_LOCOBOT_WX250S + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # robot name
            for robotIdx in arrInterbotixRobotIndex:
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_ROBOT_NAME + "_" + str(robotIdx) + "\"                      " + CMD_COMMON_DEFAULT + "\"" + CMD_INTERBOTIX_ROBOT_NAME_DEFAULT + str(robotIdx) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # arm_model
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_ARM_MODEL + "\"                         " + CMD_INTERBOTIX_ARM_MODEL_VALUE + CMD_COMMON_ENTER)
            # show_lidar
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_SHOW_LIDAR + "\"                        " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # show_gripper_bar
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_SHOW_GRIPPER_BAR + "\"                  " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # show_gripper_fingers
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_SHOW_GRIPPER_FINGERS + "\"              " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # external_urdf_loc
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_EXTERNAL_URDF_LOC + "\"                 " + CMD_COMMON_DEFAULT + "\"" + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # use_rviz
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_USE_RVIZ + "\"                          " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_FALSE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # rviz_frame
            for robotIdx in arrInterbotixRobotIndex:
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_RVIZ_FRAME + "_" + str(robotIdx) + "\"                      " + CMD_INTERBOTIX_RVIZ_FRAME_VALUE_OPEN + CMD_INTERBOTIX_ROBOT_NAME +"_" + str(robotIdx) + CMD_INTERBOTIX_RVIZ_FRAME_VALUE_CLOSE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # use_position_controllers
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_USE_POSITION_CONTROLLERS + "\"          " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_FALSE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # use_trajectory_controllers
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_USE_TRAJECTORY_CONTROLLERS + "\"        " + CMD_COMMON_DEFAULT + "\"" + CMD_COMMON_TRUE + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            # dof
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + CMD_COMMON_SPACE + "\"" + CMD_INTERBOTIX_DOF + "\"                               " + CMD_COMMON_DEFAULT + "\"" + CMD_INTERBOTIX_DOF_VALUE_DEFAULT + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_ENTER)
            # gazebo resources path
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_ENV_GAZEBO_RESOURCE_PATH + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_ENTER)
            # locobot_gazebo_controllers.yaml
            for robotIdx in arrInterbotixRobotIndex:
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_ROSPARAM_FILE_LOCOBOT_GAZEBO_CONTROLLERS_OPEN + CMD_INTERBOTIX_ROBOT_NAME + "_" + str(robotIdx) + CMD_INTERBOTIX_ROSPARAM_FILE_LOCOBOT_GAZEBO_CONTROLLERS_CLOSE + CMD_COMMON_ENTER)

            # Interbotix Arguments end..
            f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_COMMENT_ARGUMENTS_END + CMD_COMMON_ENTER)
            f.write(CMD_COMMON_ENTER)

        ## 로봇 정보 입력 시작
        for i in range(0, robotCount):
            ## 1. Locobot
            if sim.robots[i].type == ENUM_ROBOT_TYPE.LOCOBOT :
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_LOCOBOT_COMMENT_START + CMD_COMMON_ENTER)
                # Model names
                robotName = CMD_LOCOBOT_MODEL + str(sim.robots[i].id)
                robotName = "\"" + robotName + "\""
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                # Model Position
                posX = sim.robots[i].startX
                posY = sim.robots[i].startY
                posZ = sim.robots[i].startZ
                robotName = CMD_LOCOBOT_MODEL + str(sim.robots[i].id)
                # Group
                robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                # Static transform to make camera work in sim
                f.write(CMD_COMMON_SPACE_FOUR + CMD_LOCOBOT_NODE_PKG_TF + CMD_COMMON_ENTER)
                # nodel info
                sim.robots[i].name = robotName
                f.write(CMD_COMMON_SPACE_FOUR + CMD_LOCOBOT_PARAM_NAME_ROBOT_DESCRIPTION + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_LOCOBOT_INCLUDE_FILE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_SIX + CMD_LOCOBOT_ARG_LOAD_ROBOT + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_INCLUDE + CMD_COMMON_ENTER)
                # model의 속성 작성 구문(문법 제작 방식이 복잡한 관계로 sim 객체에서 필요 정보들을 가져와 직접 정적인 구문을 만든다)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_LOCOBOT_OPEN_GROUP_NODE_NAME_SPAWN_URDF + " -x " + str(posX) + " -y " + str(posY) + " -z " + CMD_LOCOBOT_POSITION_Z_DEFAULT + CMD_COMMON_SPACE + CMD_LOCOBOT_OPEN_GROUP_MODEL + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET+ CMD_LOCOBOT_CLOSE_GROUP_NODE_NAME_SPAWN_URDF + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)

                # locobot end
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_LOCOBOT_COMMENT_END + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                continue
            ## 2. Turtlebot3 - burger
            if sim.robots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER :
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_BURGER_COMMENT_START + CMD_COMMON_ENTER)
                # Model names
                robotName = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                robotName = "\"" + robotName + "\""
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # Model Position
                posX = sim.robots[i].startX
                posY = sim.robots[i].startY
                posZ = sim.robots[i].startZ
                robotName = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                sim.robots[i].name = robotName
                robotNamePosX = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_X + "\""
                robotNamePosY = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Y + "\""
                robotNamePosZ = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Z + "\""
                robotNameYaw = "\"" + robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_YAW + "\""
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNameYaw + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + CMD_COMMON_DEFAULT_POS + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # Group
                robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_OPEN_GROUP_PARAM_NAME_ROBOT_DESCRIPTION + CMD_TURTLEBOT3_MODEL_BURGER + CMD_TURTLEBOT3_CLOSE_GROUP_PARAM_NAME_ROBOT_DESCRIPTION + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_PARAM_NAME_TF_PREFIX + robotNameRef + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_NODE_PKG_ROBOT_STATE_PUBLISHER + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_SIX + CMD_TURTLEBOT3_GROUP_PARAM_NAME_PUBLISH_FREQUENCY + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_NODE + CMD_COMMON_ENTER)
                # model의 속성 작성 구문(문법 제작 방식이 복잡한 관계로 sim 객체에서 필요 정보들을 가져와 직접 정적인 구문을 만든다)
                robotNamePosX = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_X
                robotNamePosY = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Y
                robotNamePosZ = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_POSITION_Z
                robotNameYaw = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_YAW
                modelProf = "args=\"-urdf -model $(arg " + robotName + ") -x $(arg " + robotNamePosX + ") -y $(arg " + robotNamePosY + ") -z $(arg " + robotNamePosZ + ") -Y $(arg " + robotNameYaw + ")"
                f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_OPEN_GROUP_NODE_NAME_SPAWN_URDF + modelProf + CMD_TURTLEBOT3_CLOSE_GROUP_NODE_NAME_SPAWN_URDF + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                # Turtlebot3 - burger end
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_BURGER_COMMENT_END + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                continue
            ## 3. Turtlebot3 - waffle
            if sim.robots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE :
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_WAFFLE_COMMENT_START + CMD_COMMON_ENTER)
                # Model names
                robotName = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                robotName = "\"" + robotName + "\""
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # Model Position
                posX = sim.robots[i].startX
                posY = sim.robots[i].startY
                posZ = sim.robots[i].startZ
                robotName = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                sim.robots[i].name = robotName
                robotNamePosX = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_X + "\""
                robotNamePosY = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Y + "\""
                robotNamePosZ = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Z + "\""
                robotNameYaw = "\"" + robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_YAW + "\""
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNameYaw + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + CMD_COMMON_DEFAULT_POS + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # Group
                robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_OPEN_GROUP_PARAM_NAME_ROBOT_DESCRIPTION + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_TURTLEBOT3_CLOSE_GROUP_PARAM_NAME_ROBOT_DESCRIPTION + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_PARAM_NAME_TF_PREFIX + robotNameRef + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_GROUP_NODE_PKG_ROBOT_STATE_PUBLISHER + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_SIX + CMD_TURTLEBOT3_GROUP_PARAM_NAME_PUBLISH_FREQUENCY + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_NODE + CMD_COMMON_ENTER)
                # model의 속성 작성 구문(문법 제작 방식이 복잡한 관계로 sim 객체에서 필요 정보들을 가져와 직접 정적인 구문을 만든다)
                robotNamePosX = robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_X
                robotNamePosY = robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Y
                robotNamePosZ = robotName + CMD_TURTLEBOT3_WAFFLE_DEFAULT_NAME_POSITION_Z
                robotNameYaw = robotName + CMD_TURTLEBOT3_BURGER_DEFAULT_NAME_YAW
                modelProf = "args=\"-urdf -model $(arg " + robotName + ") -x $(arg " + robotNamePosX + ") -y $(arg " + robotNamePosY + ") -z $(arg " + robotNamePosZ + ") -Y $(arg " + robotNameYaw + ")"
                f.write(CMD_COMMON_SPACE_FOUR + CMD_TURTLEBOT3_OPEN_GROUP_NODE_NAME_SPAWN_URDF + modelProf + CMD_TURTLEBOT3_CLOSE_GROUP_NODE_NAME_SPAWN_URDF + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                # Turtlebot3 - burger end
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_TURTLEBOT3_WAFFLE_COMMENT_END + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                continue

            ## 4. Jetbot
            if sim.robots[i].type == ENUM_ROBOT_TYPE.JETBOT :                                       # TODO : Jetbot
                continue

            ## 5. Interbotix
            if sim.robots[i].type == ENUM_ROBOT_TYPE.INTERBOTIX :
                # default value
                robotName = CMD_INTERBOTIX_ROBOT_NAME + "_" + str(sim.robots[i].id)
                sim.robots[i].name = robotName
                rvizFrameName = CMD_INTERBOTIX_RVIZ_FRAME + "_" + str(sim.robots[i].id)
                posX = sim.robots[i].startX
                posY = sim.robots[i].startY
                posZ = sim.robots[i].startZ
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_COMMENT_START + CMD_COMMON_ENTER)
                # group open
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_GROUP_ROBOT_MODEL + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # group open - use_trajectory_controllers
                f.write(CMD_COMMON_SPACE_FOUR + CMD_INTERBOTIX_GROUP_USE_TRAJECTORY_CONTROLLERS + CMD_COMMON_ENTER)
                # ros param - trajectory_controllers.yaml
                f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_ROSPARAM_FILE_TRAJECTORY_CONTROLLERS_OPEN + robotName + CMD_INTERBOTIX_ROSPARAM_FILE_TRAJECTORY_CONTROLLERS_CLOSE + CMD_COMMON_ENTER)
                # node - controller_spawner
                f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # group open - use_position_controllers
                f.write(CMD_COMMON_SPACE_FOUR + CMD_INTERBOTIX_GROUP_USE_POSITION_CONTROLLERS + CMD_COMMON_ENTER)
                # ros param - position_controllers.yaml
                f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_ROSPARAM_POSITION_CONTROLLERS_OPEN + robotName + CMD_INTERBOTIX_ROSPARAM_POSITION_CONTROLLERS_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # node - controller_spawner dof 4
                f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_4_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_4_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # node - controller_spawner dof 5
                f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_5_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_5_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # node - controller_spawner dof 6
                f.write(CMD_COMMON_SPACE_SIX + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_6_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_DOF_6_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_FOUR + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # node - controller_spawner unless locobot_base
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_UNLSESS_LOCOBOT_BASE_OPEN + robotName + CMD_INTERBOTIX_NODE_CONTROLLER_SPAWNER_UNLSESS_LOCOBOT_BASE_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # include - xslocobot_description.launch
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_OPEN + robotName + CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_MIDDLE + rvizFrameName + CMD_INTERBOTIX_INCLUDE_FILE_XSLOCOBOT_DESCRIPTION_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # node - urdf_spawner
                # xyz position
                posXYZ = " -x " + str(posX) + " -y " + str(posY) + " -z " + str(posZ)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_NODE_URDF_SPAWNER_OPEN + robotName + CMD_INTERBOTIX_NODE_URDF_SPAWNER_MIDDLE + robotName + posXYZ + CMD_INTERBOTIX_NODE_URDF_SPAWNER_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)

                # Interbotix end
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_INTERBOTIX_COMMENT_END + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                continue
            ## 6. UNI050_BASE
            if sim.robots[i].type == ENUM_ROBOT_TYPE.UNI050_BASE :
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_UNI_COMMENT_START + CMD_COMMON_ENTER)
                # Model names
                robotName = CMD_UNI_DEFAULT_NAME + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                robotName = "\"" + robotName + "\""
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # Model Position
                posX = sim.robots[i].startX
                posY = sim.robots[i].startY
                posZ = sim.robots[i].startZ
                robotName = CMD_UNI_DEFAULT_NAME + CMD_COMMON_UNDERBAR + str(sim.robots[i].id)
                sim.robots[i].name = robotName
                robotNamePosX = "\"" + robotName + CMD_UNI_DEFAULT_NAME_POSITION_X + "\""
                robotNamePosY = "\"" + robotName + CMD_UNI_DEFAULT_NAME_POSITION_Y + "\""
                robotNamePosZ = "\"" + robotName + CMD_UNI_DEFAULT_NAME_POSITION_Z + "\""
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosX + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posX) + "\"" + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosY + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posY) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotNamePosZ + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + "\"" + str(posZ) + "\""  + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                # Group
                robotNameRef = CMD_COMMON_OPEN_BRACKET_WITH_QUOTE + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET_WITH_QUOTE
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_GROUP + CMD_COMMON_SPACE + CMD_COMMON_NS + robotNameRef + CMD_COMMON_CLOSE + CMD_COMMON_ENTER)
                # robot_description
                f.write(CMD_COMMON_SPACE_FOUR + CMD_UNI_PARAM_NAME_ROBOT_DESCRIPTION + CMD_COMMON_ENTER)
                # robot_state_publisher
                f.write(CMD_COMMON_SPACE_FOUR + CMD_UNI_NODE_PKG_ROBOT_STATE_PUBLISHER + CMD_COMMON_ENTER)
                # spawn_model
                robotNamePosX = robotName + CMD_UNI_DEFAULT_NAME_POSITION_X
                robotNamePosY = robotName + CMD_UNI_DEFAULT_NAME_POSITION_Y
                robotNamePosZ = robotName + CMD_UNI_DEFAULT_NAME_POSITION_Z
                f.write(CMD_COMMON_SPACE_FOUR + CMD_UNI_NODE_PKG_SPAWN_MODEL_OPEN + CMD_COMMON_SPACE + 
                        CMD_COMMON_MODEL + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotName + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE + 
                        CMD_COMMON_X + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotNamePosX + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE + 
                        CMD_COMMON_Y + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotNamePosY + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE +
                        CMD_COMMON_Z + CMD_COMMON_SPACE + CMD_COMMON_OPEN_BRACKET + CMD_COMMON_ARG + CMD_COMMON_SPACE + robotNamePosZ + CMD_COMMON_CLOSE_BRACKET + CMD_COMMON_SPACE +
                        CMD_UNI_NODE_PKG_SPAWN_MODEL_CLOSE + CMD_COMMON_ENTER)
                # Group - close
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_CLOSE_GROUP + CMD_COMMON_ENTER)
                # UNI050_BASE end
                f.write(CMD_COMMON_SPACE_DOUBLE + CMD_UNI_COMMENT_END + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                continue     

        # </Launch>
        f.write(CMD_COMMON_CLOSE_LAUNCH)
        f.close()
       
        # 6. Launch 파일 실행
        PATH_SYSTEM_ROOT = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME
        tmpFile = PATH_SYSTEM_ROOT + "/shelltemp.sh"
        f = open(tmpFile, 'w+')
        f.write("#!/bin/bash" + CMD_COMMON_ENTER)
        cmdLine = ""

        # UNI050_BASE source 지정
        cmdLine = PATH_SOURCE_UNI
        f.write(cmdLine + CMD_COMMON_ENTER)

        # Hello Robot source 지정
        cmdLine = PATH_SOURCE_STRETCH2
        f.write(cmdLine + CMD_COMMON_ENTER)

        f.write("roslaunch " + launchFile)
        f.close()   # ★ 원본 버그: 괄호 없으면 호출 안 됨 → 쓰기-열림 파일 실행 시 Text file busy
        # Executable 권한 설정
        os.system('chmod 777 ' + tmpFile)  

        # Gazebo 실행
        exeSimulator = subprocess.Popen(tmpFile, shell=True, executable="/bin/bash")
        if exeSimulator.poll() is None:
            print("Gazebo 실행 성공.")
            self.disableRobotList()
            self.m_exeSimulator = exeSimulator
            self.ui.btnStartSimulator.setEnabled(False)
        else:
            print("Gazebo 실행 실패.")

    #######################################
    ############### ROS ###################
    #######################################

    # Teleop
    def StartTeleopDialog(self):
        # 로봇 정보가 없으면 종료
        if len(self.m_simulator.robots) <= 0 :
           req = QtWidgets.QMessageBox.question(self, 'Start simulator', self._msg('먼저 시뮬레이터를 시작해 주세요.', 'Please run the simulator first.'),QtWidgets.QMessageBox.Ok)
           return

        dlg = DialogTeleop(self.m_simulator)
        self._CenterDlg(dlg)
        dlg.showModal()

    # Slam
    def StartSlamDialog(self):
        # 로봇 정보가 없으면 종료
        if len(self.m_simulator.robots) <= 0 :
           req = QtWidgets.QMessageBox.question(self, 'Start simulator', self._msg('먼저 시뮬레이터를 시작해 주세요.', 'Please run the simulator first.'),QtWidgets.QMessageBox.Ok)
           return

        # 로봇 정보 저장
        self.m_simulator.robots.clear()
        lstRobots = []
        self.SaveUIRobotInfoToSimRobotsInfo(lstRobots)
        self.m_simulator.robots = copy.deepcopy(lstRobots)

        dlg = DialogROSI2I(self.m_simulator)
        self._CenterDlg(dlg)
        dlg.showModal()

    # Image-to-Image Enhancement dialog open
    def OpenROSI2IDialoglog(self):
        # 로봇 정보 저장
        self.m_simulator.robots.clear()
        lstRobots = []
        self.SaveUIRobotInfoToSimRobotsInfo(lstRobots)
        self.m_simulator.robots = copy.deepcopy(lstRobots)

        if len(self.m_simulator.robots) == 0:
            return

        # 현재 ROS 실행 중인지 점검
        try:
            rospy.get_master().getSystemState()
            print("Connected to the ROS master.")
        except (rospy.ROSException, ConnectionRefusedError) as e:
            error_message = "Unable to connect to the ROS master. Please ensure it is running."
            print(error_message)
            
            # 경고 메시지 표시
            QtWidgets.QMessageBox.critical(self, "Connection Error", error_message, QtWidgets.QMessageBox.Ok)
            return

        dlg = DialogROSI2I(self.m_simulator)
        self._CenterDlg(dlg)
        dlg.showModal()

    # Collaboration
    def _CenterDlg(self, w):
        """팝업/다이얼로그를 시뮬레이터 메인 창 가운데로 (부모 미지정 창 대응)."""
        try:
            w.adjustSize()
            g = self.frameGeometry()
            w.move(g.center().x() - w.width() // 2,
                   g.center().y() - w.height() // 2)
        except Exception:
            pass

    def OpenCollaborationSettingDialog(self):
        # 선택된 아이템 가져오기
        selected_items = self.ui.lstwRobotROSCollaborationTasks.selectedItems()
        item = selected_items[0]
        # 선택된 아이템의 행 번호
        row = self.ui.lstwRobotROSCollaborationTasks.row(item)
        if self.m_arrROSCollaborationTask[row].type == ENUM_ROS_COLLABORATION_TASK_TYPE.NONE:
            return

        # 로봇 정보 저장
        self.m_simulator.robots.clear()
        lstRobots = []
        self.SaveUIRobotInfoToSimRobotsInfo(lstRobots)
        self.m_simulator.robots = copy.deepcopy(lstRobots)

        dlg = DialogNavigation(self.m_simulator)
        dlg.finished.connect(self.onFinishedCollaborationDlg)
        self._CenterDlg(dlg)
        dlg.showModal()

    # Collaboration Task start
    def StartCollaborationTask(self):
        # 로봇 정보 저장
        self.m_simulator.robots.clear()
        lstRobots = []
        self.SaveUIRobotInfoToSimRobotsInfo(lstRobots)
        self.m_simulator.robots = copy.deepcopy(lstRobots)

        # ★ 위 재구성이 UI 패널의 옛 좌표로 startX/Y 를 덮는다 — RELAY 는 일렬 배치가
        #   체인 goal 계산의 기준이므로 다시 동기화 (2026-08-08 실측: 이게 없으면
        #   스폰은 일렬인데 goal 은 옛 좌표 기준으로 계산되는 불일치 발생)
        if self.m_simulator.ros_collaboration in (ENUM_ROS_COLLABORATION_TASK_TYPE.RELAY,
                                                  ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE,
                                                  ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE,
                                                  ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                                                  ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND):
            _ct = self.m_simulator.ros_collaboration
            lp = (MULTIGOAL_BASE_POSITIONS if _ct == ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE
                  else AVOID_POSITIONS if _ct == ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE
                  else EXPLORE_POSITIONS if _ct in (ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                                                    ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND)
                  else RELAY_LINE_POSITIONS)
            for rb in self.m_simulator.robots:
                if rb.name in lp:
                    rb.startX, rb.startY = lp[rb.name]

        # RViz 체크 상태를 지금 반영 — 시뮬 시작 때 안 켰어도 여기서 늦게 띄우고,
        # 체크를 껐으면 떠 있는 2D 뷰를 닫는다
        self.EnsureRelayRviz()

        # JnP 0.8.1 에이전트가 떠 있으면 다이얼로그가 task 발행(coalition 트리거) 모드로 동작
        # ★ 비모달(show) — 모달(exec)이면 메인 창이 잠겨 릴레이 중 Stop 을 못 누른다
        if getattr(self, 'm_dlgCollab', None) is not None:
            self.m_dlgCollab.close()
        # BASE 슬롯 상수 전체 전달 — 원 중심·legacy 홈 좌표 모두 이 상수로 고정
        # ★ 무조건 전달 (태스크 타입 조건 게이트는 다이얼로그 생성 시점에 타입이
        #   아직 안 잡혀 폴백(UI 좌표)이 발행되던 원인 — 2026-08-08 실측 -1.74,-0.65).
        #   사용은 다이얼로그의 다목적(MOVE) 분기에서만 하므로 항상 넘겨도 무해.
        basePos = dict(MULTIGOAL_BASE_POSITIONS)
        self.m_dlgCollab = DialogStartROSCollaborationTask(
            self.m_simulator, jnp081Active=self.m_startedJnp081,
            jnp021Active=self.m_startedJnp021,
            monitorOpener=self.ShowJnpMonitor, basePositions=basePos)
        self.m_dlgCollab.show()
        self._CenterDlg(self.m_dlgCollab)

    ## 시뮬레이션 정지 — Gazebo/ROS/JnP/RViz/에이전트 터미널 전부 정리, GUI 창은 유지
    ## (창만 닫으면 roslaunch 가 고아로 살아남아 다음 실행이 꼬인다 — stop_sim.sh 재사용)
    ## 팝업 메시지 언어 선택 헬퍼 — 하단 콤보(한국어/English) 상태에 따라 반환
    def _msg(self, ko, en):
        return ko if self.ui.cmbUiLang.currentIndex() == 0 else en

    def StopSimulator(self):
        req = QtWidgets.QMessageBox.question(
            self, self._msg('시뮬레이션 정지', 'Stop simulator'),
            self._msg('시뮬레이션을 정지할까요?\n(Gazebo/ROS 전부 종료, GUI는 유지)',
                      'Stop the simulation?\n(All Gazebo/ROS processes will be terminated; GUI stays open)'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if req != QtWidgets.QMessageBox.Yes:
            return
        # 정리(수 초) 동안 두 버튼 잠금 — 정리 중 Start 를 누르면 새 프로세스가
        # 정리 패턴에 맞아 같이 죽는 경합이 생긴다
        self.ui.btnStopSimulator.setEnabled(False)
        self.ui.btnStartSimulator.setEnabled(False)
        # Stop 시 JnP Monitor 창도 함께 닫기 (2026-08-10 지시 — 관찰 대상이
        # 사라지므로; close 가 tap 서브프로세스도 정리한다)
        if getattr(self, 'm_dlgJnpMonitor', None) is not None:
            try:
                self.m_dlgJnpMonitor.close()
            except Exception:
                pass
            self.m_dlgJnpMonitor = None
        script = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', '..', 'stop_sim.sh'))
        if os.path.isfile(script):
            self.m_procStop = QProcess(self)
            self.m_procStop.finished.connect(self._OnStopFinished)
            self.m_procStop.start('bash', [script])
        else:
            self._CleanupSimProcesses()
            self._OnStopFinished()

    ## Stop 정리 완료 — 버튼/로봇 목록 복구 (원본은 시작 성공 시 Start 를 영구
    ## 비활성화하는 1회용 설계였음 — Stop 이후 재시작 가능하도록 되살린다)
    def _OnStopFinished(self, *args):
        self.m_arrJnpProcess.clear()
        self.m_startedJnp081 = False
        self.ui.btnStartSimulator.setEnabled(True)
        self.ui.btnStopSimulator.setEnabled(True)
        self.enableRobotList()
        print('시뮬레이션 정리 완료 — 다시 Start 할 수 있습니다')

    ## 로봇 리스트 재활성화 (disableRobotList 의 역방향)
    def enableRobotList(self):
        for idx in range(self.ui.lstwRobots.count()):
            item = self.ui.lstwRobots.item(idx)
            widget = self.ui.lstwRobots.itemWidget(item)
            if widget:
                widget.setEnabled(True)

    ## 프로그램 종료 — 시뮬레이션 정리 후 GUI 까지 종료 (하단 Exit 버튼 / File>Exit)
    def ExitApplication(self):
        req = QtWidgets.QMessageBox.question(
            self, self._msg('종료', 'Exit'),
            self._msg('시뮬레이션을 정리하고 프로그램을 종료할까요?',
                      'Clean up the simulation and exit the program?'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if req != QtWidgets.QMessageBox.Yes:
            return
        self._CleanupSimProcesses()
        QtWidgets.QApplication.quit()

    ## 시뮬 스택 정리 공통부 (확인창 없음) — Stop/Exit 이 공유
    def _CleanupSimProcesses(self):
        script = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', '..', 'stop_sim.sh'))
        if os.path.isfile(script):
            subprocess.Popen(['bash', script])
        else:
            # 배포 위치에 스크립트가 없을 때의 최소 정리 (동일 패턴)
            for pat in ('ros[l]aunch', 'gz[s]erver', 'gz[c]lient', 'ros[m]aster',
                        'jnp_0.8.1/scripts/jnp_[a]gent', 'jnp_0.8.1/scripts/jnp_grou[p]',
                        'goal_label[s]', 'loco_ready_ini[t]',
                        'relay_runne[r]', 'multigoal_runne[r]',
                        'rviz -f map -d .*relay_2d[.]rviz', '[g]nome-terminal'):
                subprocess.run(['pkill', '-9', '-f', pat])
        self.m_arrJnpProcess.clear()
        self.m_startedJnp081 = False

    ## 협업용 RViz 2D 뷰 늦은 기동/종료 — 체크박스 상태를 협업 창 열 때마다 반영
    ## (시뮬 시작 시 show_rviz2d 로 띄우는 것과 별개로, 사후 체크/해제도 동작)
    def EnsureRelayRviz(self):
        # ★ 패턴은 반드시 rviz 실행 형태('rviz -f map -d ...')로 한정할 것.
        #   'relay_2d.rviz' 만으로 잡으면 roslaunch 명령줄(rvizconfig:= 인자)까지
        #   매칭되어 pkill 이 시뮬레이션 전체를 죽인다 (2026-08-08 실사고)
        RVIZ_PAT = 'rviz -f map -d .*relay_2d[.]rviz'
        running = subprocess.run(['pgrep', '-f', RVIZ_PAT],
                                 stdout=subprocess.PIPE).returncode == 0
        if self.ui.chkRelayRviz.isChecked():
            if not running:
                # 마스터가 없으면 띄우지 않는다 — 시뮬 시작 시 show_rviz2d 가 띄워주며,
                # 마스터 없이 띄우면 'waiting for master' 창만 뜬다 (2026-08-08 실측)
                try:
                    import rosgraph
                    if not rosgraph.is_master_online():
                        return
                except ImportError:
                    pass
                cmd = ("source /opt/ros/noetic/setup.bash; "
                       "rosrun rviz rviz -f map -d /root/tesla/ros/navi/rviz/locobot/relay_2d.rviz")
                subprocess.Popen(['bash', '-c', cmd])
        else:
            if running:
                subprocess.run(['pkill', '-f', RVIZ_PAT])

    # 협업태스크 다이얼로그 종료 시 실행
    def onFinishedCollaborationDlg(self):
        self.ChangeUIInfoToSettingInfo(self.m_simulator)

    # R-Viz
    def StartRVizDialog(self):
        # 로봇 정보가 없으면 종료
        if len(self.m_simulator.robots) <= 0 :
            req = QtWidgets.QMessageBox.question(self, 'Start simulator', self._msg('먼저 시뮬레이터를 시작해 주세요.', 'Please run the simulator first.'),QtWidgets.QMessageBox.Ok)
            return

        dlg = DialogRViz(self.m_simulator)
        self._CenterDlg(dlg)
        dlg.showModal()

    # Jnp 
    ## Jnp 활성화
    def StartJnp(self):
        if len(self.m_arrJnpProcess) > 0:
            self.CloseJnp(self.m_arrJnpProcess)

        ## JnP 버전 선택 (콤보박스: 0 = 기존 0.2.1, 1 = 0.8.1)
        # 0.8.1은 발견/설명까지만 상시 수행하고, 협업 태스크(goal)가 발행되면
        # coalition 형성 → task tree 할당/스케줄 실행 → goal 도달 시 해체한다
        useJnp081 = self.ui.cmbJnpVersion.currentIndex() == 1
        # 실제로 에이전트를 띄웠을 때만 0.8.1 시작 상태로 기록 (로봇 0대면 아무것도 안 뜸)
        self.m_startedJnp081 = useJnp081 and len(self.m_simulator.robots) > 0
        self.m_startedJnp021 = (not useJnp081) and len(self.m_simulator.robots) > 0
        pathSourceJnp = PATH_SOURCE_JNP081_SETUP if useJnp081 else PATH_SOURCE_JNP_SETUP

        ## 각 모델 별 Jnp 실행
        # ns는 기본 사용
        for i in range(0, len(self.m_simulator.robots)) :
            # 실행 전 source 지정
            command = pathSourceJnp + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE
            # 실행
            name = self.m_simulator.robots[i].name
            command = command + CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_JNP + CMD_COMMON_SPACE + CMD_ROS_JNP_JNP_AGENT + CMD_COMMON_SPACE + CMD_ROS_JNP_JNP_AGENT_NS + CMD_ROS_JNP_JNP_AGENT_NS_DEFAULT + CMD_COMMON_SPACE + CMD_ROS_JNP_JNP_AGENT_NAME + name
            if useJnp081:
                command = command + CMD_COMMON_SPACE + CMD_ROS_JNP081_AGENT_XML_ARG
            completeCmd = CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE
            process = subprocess.Popen([completeCmd], shell=True)
            self.m_arrJnpProcess.append(process)
            time.sleep(1)
            #cmd = subprocess.Popen(command, shell=True, executable="/bin/bash")

        atexit.register(self.CloseJnp, self.m_arrJnpProcess)

    ## JnP Monitor 창 (옵션) — 버튼을 누를 때만 열리는 비모달 그래픽 뷰
    def ShowJnpMonitor(self):
        if getattr(self, 'm_dlgJnpMonitor', None) is not None and self.m_dlgJnpMonitor.isVisible():
            self.m_dlgJnpMonitor.raise_()
            self.m_dlgJnpMonitor.activateWindow()
            return
        self.m_dlgJnpMonitor = DialogJnpMonitor(self)
        self.m_dlgJnpMonitor.show()
        self._CenterDlg(self.m_dlgJnpMonitor)

    ## Jnp 종료
    def CloseJnp(self, arrProcess):
        for process in arrProcess:
            try:
                # 프로세스가 종료되지 않았으면 종료 시도
                process.terminate()
                process.wait(timeout=5)  # 5초 대기
            except subprocess.TimeoutExpired:
                # 강제 종료 시도
                print("터미널 종료 실패, 강제 종료 시도")
                process.kill()

        subprocess.run(['pkill', '-f', 'gnome-terminal'])
        # 0.8.1 모드로 시작했을 때만, 0.8.1 경로 한정 패턴으로 잔여 정리
        # (광역 'jnp_agent.py' 패턴은 이 기계의 다른 JnP 프로세스까지 죽인다 — 리뷰 확정)
        if getattr(self, 'm_startedJnp081', False):
            subprocess.run(['pkill', '-f', 'jnp_0.8.1/scripts/jnp_group.py'])
            subprocess.run(['pkill', '-f', 'jnp_0.8.1/scripts/jnp_agent.py'])
        arrProcess.clear()
        self.m_startedJnp081 = False
        self.m_startedJnp021 = False

    # DQN 실행
    def StartROSDQN(Self):
        pass
    
    # DQN 실행 결과 가중치 파일 저장
    def SaveDQNWeightFile(self):
        path = self.m_settings.value(SETTING_PATH_DQN_WEIGHT)

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # 네이티브 대화상자 사용 여부 설정 (선택 사항)
        
        # QFileDialog를 사용하여 파일 저장 대화상자 열기
        file_name, _ = QFileDialog.getSaveFileName(None, "Save File", path, "All Files (*);;Text Files (*.txt)", options=options)
        
        if file_name:
            self.m_settings.setValue(SETTING_PATH_DQN_WEIGHT, path)
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("File Save")  # 타이틀 설정
            msg_box.setText(f"File has been saved successfully.\nPath: {path}")  # 내용 설정
            msg_box.setIcon(QtWidgets.QMessageBox.Information)  # 아이콘 설정
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)  # OK 버튼 추가
            
            msg_box.exec()  # 메시지 박스 실행

    # DQN 가중치 파일 로드
    def LoadDQNWeightFile(self):
        path = self.m_settings.value(SETTING_PATH_DQN_WEIGHT)

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # 네이티브 대화상자 사용 여부 설정 (선택 사항)
        
        # QFileDialog를 사용하여 파일 오픈 대화상자 열기
        file_name, _ = QFileDialog.getOpenFileName(None, "Open File", path, "All Files (*);;Text Files (*.txt)", options=options)
        
        if file_name:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("File Open")  # 타이틀 설정
            msg_box.setText(f"File has been opened successfully.\nPath: {path}")  # 내용 설정
            msg_box.setIcon(QtWidgets.QMessageBox.Information)  # 아이콘 설정
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)  # OK 버튼 추가
            
            msg_box.exec()  # 메시지 박스 실행

    #######################################
    ############### UI Event ##############
    #######################################

    # 라디오 버튼 - World 선택
    def WorldRadioButtonItemSelected(self):
        if  self.ui.rbWorldWarehouse.isChecked() == True:
            self.m_simulator.worldType = ENUM_WORLD.WAREHOUSE
        elif self.ui.rbWorldHospital.isChecked() == True:
            self.m_simulator.worldType = ENUM_WORLD.HOSPITAL    
        elif self.ui.rbWorldSmallHouse.isChecked() == True:
            self.m_simulator.worldType = ENUM_WORLD.SMALLHOUSE
        elif self.ui.rbWorldBookStore.isChecked() == True:
            self.m_simulator.worldType = ENUM_WORLD.BOOK_STORE

    # World Fire 옵션 선택
    def OpenWorldOptionFireDialog(self):
        if self.m_exeSimulator is None:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Warning")
            msg_box.setText("Gazebo를 먼저 실행 해 주세요")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
            return

        dlg = DialogWorldOptionFire()
        self._CenterDlg(dlg)
        dlg.showModal()

    # 라디오 버튼 - ROS 선택
    def ROSRadioButtonItemSelected(self):
        if self.ui.rbROSNone.isChecked() == True:
            self.m_simulator.ros = ENUM_ROS_TYPE.NONE
            self.ui.btnROSSlamEdit.setEnabled(False)
            self.ui.btnROSNavigationEdit.setEnabled(False)
        elif self.ui.rbROSSlam.isChecked() == True:
            self.m_simulator.ros = ENUM_ROS_TYPE.SLAM
            self.ui.btnROSSlamEdit.setEnabled(True)
            self.ui.btnROSNavigationEdit.setEnabled(False)
        elif self.ui.rbROSNavigation.isChecked() == True:
            self.m_simulator.ros = ENUM_ROS_TYPE.NAVIGATION
            self.ui.btnROSSlamEdit.setEnabled(False)
            self.ui.btnROSNavigationEdit.setEnabled(True)

    # 로봇 추가
    def AddRobot(self):
        # 실행 후 로봇 추가 형태라면 Add model 버튼 활성화
        for idx in range(self.ui.lstwRobots.count()):
            item = self.ui.lstwRobots.item(idx)
            widget = self.ui.lstwRobots.itemWidget(item)
            if not widget.isEnabled():
                self.ui.btnAddModel.setVisible(True)
                break

        # 최대 로봇 허용개수 초과
        if self.ui.lstwRobots.count() >= MAX_MODEL_COUNT_ROBOT :
            req = QtWidgets.QMessageBox.question(self, 'Add Robot', 'The maximum number of allowed robots has been exceeded. (Max : ' + str(MAX_MODEL_COUNT_ROBOT) + ')',QtWidgets.QMessageBox.Ok)
            return

        # 리스트뷰에 새로운 로봇 위젯 추가
        lstRobot = self.ui.lstwRobots
        item = QtWidgets.QListWidgetItem(lstRobot)
        # 로봇 위젯 생성
        custom_widget = WidgetRobotItem()
        item.setSizeHint(custom_widget.sizeHint())
        custom_widget.SetStartPosition(0.0, 0.0, 0.1)
        # 만약 두번째 이상 로봇이라면 위치값을 증분하여 표기
        if self.ui.lstwRobots.count() > 1:
            prevIdx = self.ui.lstwRobots.count() - 2
            prevItem = self.ui.lstwRobots.item(prevIdx)
            widget = self.ui.lstwRobots.itemWidget(prevItem)
            prevXpos = widget.ui.dsbRobotStartPosX.value()
            prevXstep = widget.ui.dsbRobotStartPosX.singleStep()
            prevYpos = widget.ui.dsbRobotStartPosY.value()
            prevYstep = widget.ui.dsbRobotStartPosY.singleStep()
            custom_widget.SetStartPosition(prevXpos + prevXstep, prevYpos + prevYstep, 0.1)

        # 리스트뷰에 로봇 위젯 셋
        lstRobot.addItem(item)
        lstRobot.setItemWidget(item, custom_widget)

    # 로봇 삭제
    def DeleteRobot(self):
        listItems=self.ui.lstwRobots.selectedItems()
        if not listItems: return        
        for item in listItems:
            # 로봇이 이미 로딩 된 상태라면 삭제 거부
            widget = self.ui.lstwRobots.itemWidget(item)
            if widget.isEnabled():
                self.ui.lstwRobots.takeItem(self.ui.lstwRobots.row(item))
                self.ui.lstwRobots.clearSelection()
            else:
                QtWidgets.QMessageBox.question(self, 'Execution error', 'It\'s already a spawned model.',QtWidgets.QMessageBox.Ok)

        # 실행 후 추가 로봇이 없다면 Add model 버튼 비활성화
        for idx in range(self.ui.lstwRobots.count()):
            isExistAddedModel = False
            item = self.ui.lstwRobots.item(idx)
            widget = self.ui.lstwRobots.itemWidget(item)
            if widget.isEnabled():
                isExistAddedModel = True
                break
            
        if not isExistAddedModel:
            self.ui.btnAddModel.setVisible(False)

    # 로봇 위치가 겹치는 곳이 있는지 확인
    def CheckRobotPosition(self, robots):
        # 한대일 경우는 위치 점검 배제
        if len(robots) <= 1:
            return True

        prevX = 0
        prevY = 0
        for i in range(0, len(robots)):
            if i == 0:
                prevX = robots[i].startX
                prevY = robots[i].startY
                continue
           
            # X Y 포지션이 일치할 경우 에러 발생
            if prevX == robots[i].startX and prevY == robots[i].startY:
                return False
           
            prevX = robots[i].startX
            prevY = robots[i].startY
        # 정상 동작
        return True

    def ChangedWolrdOptionPersonCheckbox(self, state):
        if state ==  Qt.Checked:
            self.ui.sbWorldOptionPersonCount.setEnabled(True)
            self.ui.chkWorldOptionRandomColor.setEnabled(True)
        else:
            self.ui.sbWorldOptionPersonCount.setEnabled(False)
            self.ui.chkWorldOptionRandomColor.setEnabled(False)
            self.ui.chkWorldOptionRandomColor.setChecked(False)

    ############################################
    ############### World Setting ##############
    ############################################

    # 월드의 데이터 구조 설정
    # 시뮬레이터 실행에 필요한 월드와 모델들은 미리 Gazebo 기본 경로해 옮겨놓은 상태라고 가정 한다.
    # World : /usr/local/share/gazebo-11/worlds
    # Moels : /home/tesla/.gazebo/models
    # 보통 시뮬레이터 실행시 월드가 없다고 나오거나 모델이 안보이면 위 경로에 파일들이 없거나 World내 모델 참조 경로등이 꼬인 상태이다.
    def SetWorld(self):
        if len(self.m_worlds) > 0:
            self.m_worlds.clear()

        # TODO : 현재는 사용 월드를 강제로 지정하지만 추후에는 자동화 시스템 적용 필요...
        ## House/Cafe
        world = World()
        world.categoryMain = ENUM_WORLD_CATEGORY_MAIN.HOUSE_CAFE
        # House/Cafe : cafe
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.CAFE
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.HOUSE_CAFE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.CAFE.value + "/" + ENUM_WORLD_CATEGORY_SUB.CAFE.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # House/Cafe : small house
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.SMALL_HOUSE
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.HOUSE_CAFE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.SMALL_HOUSE.value + "/" + ENUM_WORLD_CATEGORY_SUB.SMALL_HOUSE.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        self.m_worlds.append(world)

        ## Office
        world = World()
        world.categoryMain = ENUM_WORLD_CATEGORY_MAIN.OFFICE
        # Office : office_cpr
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.OFFICE_CPR
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.OFFICE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.OFFICE_CPR.value + "/" + ENUM_WORLD_CATEGORY_SUB.OFFICE_CPR.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Offce : office_cpr_construction
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.OFFICE_CPR_CONSTRUCTION
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.OFFICE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.OFFICE_CPR_CONSTRUCTION.value + "/" + ENUM_WORLD_CATEGORY_SUB.OFFICE_CPR_CONSTRUCTION.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Offce : office_small
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.OFFICE_SMALL
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.OFFICE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.OFFICE_SMALL.value + "/" + ENUM_WORLD_CATEGORY_SUB.OFFICE_SMALL.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Offce : office
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.OFFICE
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.OFFICE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.OFFICE.value + "/" + ENUM_WORLD_CATEGORY_SUB.OFFICE.value + ".png"
        world_sub.robotStartXYZ = [0.8, 0.8, 0.9,   0.5, 0.5, 0]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        self.m_worlds.append(world)

        ## Hospital
        world = World()
        world.categoryMain = ENUM_WORLD_CATEGORY_MAIN.HOSPITAL
        # Hospital : hospital
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.HOSPITAL
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.HOSPITAL.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.HOSPITAL.value + "/" + ENUM_WORLD_CATEGORY_SUB.HOSPITAL.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Hospital : hospital_2_floors
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.HOSPITAL_2_FLOORS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.HOSPITAL.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.HOSPITAL_2_FLOORS.value + "/" + ENUM_WORLD_CATEGORY_SUB.HOSPITAL_2_FLOORS.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Hospital : hospital_3_floors
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.HOISPITAL_3_FLOORS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.HOSPITAL.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.HOISPITAL_3_FLOORS.value + "/" + ENUM_WORLD_CATEGORY_SUB.HOISPITAL_3_FLOORS.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        self.m_worlds.append(world)

        ## Warehouse
        world = World()
        world.categoryMain = ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE
        # Warehouse : fetchit_challenge_arena_montreal2019
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : fetchit_challenge_arena_montreal2019_highlights
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019_HIGHTLIGHTS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019_HIGHTLIGHTS.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019_HIGHTLIGHTS.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : fetchit_challenge_arena_montreal2019_onlylights
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019_ONLYLIGHTS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019_ONLYLIGHTS.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ARENA_MONTREAL2019_ONLYLIGHTS.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : fetchit_challenge_assembly
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ASSEMBLY
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ASSEMBLY.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ASSEMBLY.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : fetchit_challenge_atrezzo
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ATREZZO
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ATREZZO.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_ATREZZO.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : fetchit_challenge_simple
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_SIMPLE
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_SIMPLE.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_SIMPLE.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : fetchit_challenge_simple_highlights
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_SIMPLE_HIGHLIGHTS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_SIMPLE_HIGHLIGHTS.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_SIMPLE_HIGHLIGHTS.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : fetchit_challenge_tests
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_TESTS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_TESTS.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_TESTS.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : fetchit_challenge_tests_lowlights
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_TESTS_LOWLIGHTS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_TESTS_LOWLIGHTS.value + "/" + ENUM_WORLD_CATEGORY_SUB.FETCHIT_CHALLENGE_TESTS_LOWLIGHTS.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : inventory
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.INVENTORY
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.INVENTORY.value + "/" + ENUM_WORLD_CATEGORY_SUB.INVENTORY.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Warehouse : warehouse
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.WAREHOUSE
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.WAREHOUSE.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.WAREHOUSE.value + "/" + ENUM_WORLD_CATEGORY_SUB.WAREHOUSE.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        self.m_worlds.append(world)

        ## Factory
        world = World()
        world.categoryMain = ENUM_WORLD_CATEGORY_MAIN.FACTORY
        # Factory : cyberzoo
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.CYBERZOO
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.CYBERZOO.value + "/" + ENUM_WORLD_CATEGORY_SUB.CYBERZOO.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : cyberzoo2019_orange_poles
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.CYBERZOO_ORANGE_POLES
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.CYBERZOO_ORANGE_POLES.value + "/" + ENUM_WORLD_CATEGORY_SUB.CYBERZOO_ORANGE_POLES.value + ".png"
        world_sub.robotStartXYZ = [0.7, 1, 0,	0.7, -0.5, 0]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : cyberzoo2019_orange_poles_panels
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.CYBERZOO2019_ORANGE_POLES_PANELS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.CYBERZOO2019_ORANGE_POLES_PANELS.value + "/" + ENUM_WORLD_CATEGORY_SUB.CYBERZOO2019_ORANGE_POLES_PANELS.value + ".png"
        world_sub.robotStartXYZ = [0.8,	1, 0,	1.3, 2.3, 0]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : cyberzoo2019_ralphthesis2020
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.CYBERZOO2019_RALPHTHESIS2020
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.CYBERZOO2019_RALPHTHESIS2020.value + "/" + ENUM_WORLD_CATEGORY_SUB.CYBERZOO2019_RALPHTHESIS2020.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : cyberzoo_4_panels
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.CYBERZOO_4_PANELS
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.CYBERZOO_4_PANELS.value + "/" + ENUM_WORLD_CATEGORY_SUB.CYBERZOO_4_PANELS.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : cyberzoo_orange_poles
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.CYBERZOO_ORANGE_POLES
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.CYBERZOO_ORANGE_POLES.value + "/" + ENUM_WORLD_CATEGORY_SUB.CYBERZOO_ORANGE_POLES.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : cyberzoo_panel
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.CYBERZOO_PANEL
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.CYBERZOO_PANEL.value + "/" + ENUM_WORLD_CATEGORY_SUB.CYBERZOO_PANEL.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : powerplant
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.POWERPLANT
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.POWERPLANT.value + "/" + ENUM_WORLD_CATEGORY_SUB.POWERPLANT.value + ".png"
        world_sub.robotStartXYZ = [1, 1, 0,	 0, 1, 0]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : workshop_example
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.WORKSHOP_EXAMPLE
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.WORKSHOP_EXAMPLE.value + "/" + ENUM_WORLD_CATEGORY_SUB.WORKSHOP_EXAMPLE.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,	 0, 1, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : workshop_example
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.WORKSHOP_EXAMPLE
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.WORKSHOP_EXAMPLE.value + "/" + ENUM_WORLD_CATEGORY_SUB.WORKSHOP_EXAMPLE.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,	 0, 1, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Factory : factory
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.FACTORY
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.FACTORY.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.FACTORY.value + "/" + ENUM_WORLD_CATEGORY_SUB.FACTORY.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,	 0, 1, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        self.m_worlds.append(world)

        ## Others
        world = World()
        world.categoryMain = ENUM_WORLD_CATEGORY_MAIN.OTHERS
        # Others : osrf_elevator
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.ORSF_ELVATOR
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.OTHERS.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.ORSF_ELVATOR.value + "/" + ENUM_WORLD_CATEGORY_SUB.ORSF_ELVATOR.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Others : willowgarage
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.WILLOWGARAGE
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.OTHERS.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.WILLOWGARAGE.value + "/" + ENUM_WORLD_CATEGORY_SUB.WILLOWGARAGE.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        # Others : distribution_center
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.DISTRIBUTION_CENTER
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.OTHERS.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.DISTRIBUTION_CENTER.value + "/" + ENUM_WORLD_CATEGORY_SUB.DISTRIBUTION_CENTER.value + ".png"
        world_sub.robotStartXYZ = [2, 3, 0,    2, 2, 0]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        self.m_worlds.append(world)

        ## Custom
        world = World()
        world.categoryMain = ENUM_WORLD_CATEGORY_MAIN.CUSTOM
        # Custom : collaoration
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.COLLABORATION
        defThumbPath = os.path.join(os.path.dirname(__file__), 'Resources/thumbnail/worlds/' + ENUM_WORLD_CATEGORY_MAIN.CUSTOM.value + "/")
        world_sub.thumbPath = defThumbPath + ENUM_WORLD_CATEGORY_SUB.COLLABORATION.value + "/" + ENUM_WORLD_CATEGORY_SUB.COLLABORATION.value + ".png"
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)
        # Custom : collaboration_empty — Relay/다목적용 외벽-only (RTF↑, 선택 가능)
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.COLLABORATION_EMPTY
        world_sub.thumbPath = (defThumbPath
                               + ENUM_WORLD_CATEGORY_SUB.COLLABORATION_EMPTY.value + "/"
                               + ENUM_WORLD_CATEGORY_SUB.COLLABORATION_EMPTY.value + ".png")
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)
        # Custom : collaboration_bnt — 충돌회피(bnt_partition_scaled) 표시용
        world_sub = World_Sub()
        world_sub.categorySub = ENUM_WORLD_CATEGORY_SUB.COLLABORATION_BNT
        world_sub.thumbPath = (defThumbPath
                               + ENUM_WORLD_CATEGORY_SUB.COLLABORATION_BNT.value + "/"
                               + ENUM_WORLD_CATEGORY_SUB.COLLABORATION_BNT.value + ".png")
        world_sub.robotStartXYZ = [0, 0, 0.5,   0.5, 0.5, 0.5]
        world_sub.extention = CONST_EXTENTION_WORLD
        world.arrCategorySubs.append(world_sub)

        self.m_worlds.append(world)

        self.InitWolrdToList()

    # 생성된 월드 정보를 토대로 GUI에 World리스트 박스를 만든다
    def InitWolrdToList(self):
        if len(self.m_worlds) < 0:
            return
       
        # Main category
        for world in self.m_worlds:
            self.ui.lstwWorldMainCategory.addItem(world.categoryMain.value)
            # Sub category
            for world_sub in world.arrCategorySubs:
                self.ui.lstwWorldSubCategory.addItem(world_sub.categorySub.value)
       
        # Select first item
        self.ui.lstwWorldMainCategory.setCurrentRow(0)
        self.ui.lstwWorldSubCategory.setCurrentRow(0)

    # 메인 카테고리 변경 이벤트
    def on_item_selection_changed_main_category(self):
        selected_items = self.ui.lstwWorldMainCategory.selectedItems()
        if selected_items:
            # 선택된 대분류 하위 월드 찾기
            for world in self.m_worlds:
                if world.categoryMain.value == selected_items[0].text():
                    self.ui.lstwWorldSubCategory.clear()
                    for world_sub in world.arrCategorySubs:
                        self.ui.lstwWorldSubCategory.addItem(world_sub.categorySub.value)
                        self.ui.lstwWorldSubCategory.setCurrentRow(0)

    # 서브 카테고리 변경 이벤트
    def on_item_selection_changed_sub_category(self):
        selected_items = self.ui.lstwWorldSubCategory.selectedItems()
        if selected_items:
            # 선택된 하위 월드로 이미지 변경
            for world in self.m_worlds:
                for world_sub in world.arrCategorySubs:
                    if world_sub.categorySub.value == selected_items[0].text():
                        fileName = world_sub.categorySub.value + world_sub.extention
                        if self.CheckWorldFile(fileName):
                            # Thumb 변경
                            thumbPath = world_sub.thumbPath
                            pixmap = QPixmap(thumbPath)
                            # scaled_pixmap = pixmap.scaledToWidth(self.ui.lbWorldImage.width())
                            scaled_pixmap = pixmap.scaled(self.ui.lbWorldImage.width(), self.ui.lbWorldImage.height(), Qt.IgnoreAspectRatio)
                            self.ui.lbWorldImage.setPixmap(scaled_pixmap)
                            self.setCurrentWorld(world.categoryMain, world_sub.categorySub.value)
                            self.m_simulator.worldFileType = world_sub.extention
                            # Start 버튼 활성화
                            self.ui.btnStartSimulator.setEnabled(True)
                        else :
                            thumbPath = ICON_THUMBNAIL_NONE
                            pixmap = QPixmap(thumbPath)
                            scaled_pixmap = pixmap.scaledToHeight(self.ui.lbWorldImage.height())
                            self.ui.lbWorldImage.setPixmap(scaled_pixmap)
                            self.ui.lbWorldImage.setAlignment(Qt.AlignHCenter)
                            self.setCurrentWorld(ENUM_WORLD_CATEGORY_MAIN.NONE, ENUM_WORLD_CATEGORY_SUB.NONE)
                            self.m_simulator.worldFileType = world_sub.extention
                            self.ui.btnStartSimulator.setEnabled(False)

    # 현재 world탭에서 선택한 world 정보를 simulator 메인 world에 입력
    def setCurrentWorld(self, categoryMain, categorySub):
        if self.m_simulator != None:
            self.m_simulator.categoryMain = categoryMain
            self.m_simulator.categorySub = categorySub  

    # World에 사람 모델을 추가 한다
    def addPersonToWorld(self, worldName, count):
        personCount = count

        # 먼저 원본 world 파일을 복사 한다.
        pathDefaultWorlds = PATH_DEFAULT_WORLDS
        if not os.path.exists(pathDefaultWorlds):
            pathDefaultWorlds = PATH_DEFAULT_WORLDS_OTHER

        worldPath = pathDefaultWorlds + "/" + worldName
        backupPath = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME
        backupFile = backupPath + "/" + worldName
        if not os.path.exists(backupPath):
            os.makedirs(backupPath)
       
        # 기존 파일이 있는지 확인
        if os.path.exists(backupFile):
            # 기존 파일 삭제
            os.remove(backupFile)
        shutil.copy(worldPath, backupFile)
       
        # 우선 world 파일을 열고 </world>를 찾아 윗단에 커서를 위치한다
        with open(backupFile, 'r') as file:
            lines = file.readlines()

        # </world>를 찾아서 그 위에 커서를 위치
        for i, line in enumerate(lines):
            if '</world>' in line:
                cursor_position = i
                break
        else:
            # </world>를 찾지 못한 경우
            cursor_position = len(lines)

        # 파일을 쓰기 모드로 연다
        with open(backupFile, 'w') as f:
            # 커서 위치까지의 내용을 쓰고
            f.writelines(lines[:cursor_position])

            # 원본 파일 수정 personCount만큼 생성
            for i in range(personCount):
                actorName = CMD_WORLD_PERSON_ACTOR + str(i)
                pluginName = CMD_WORLD_PERSON_ACTOR + str(i) + CMD_COMMON_UNDERBAR + CMD_WORLD_PERSON_ACTOR_PLUGIN
                actorPosX = int(CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_T_X) + i
                actorPosY = int(CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_T_Y) + i
                actorPosZ = CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_T_Z
                actorPos = str(actorPosX) + " " + str(actorPosY) + " " + str(actorPosZ) + " " + CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_R_X + " " + CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_R_Y + " " + CMD_WORLD_PERSON_ACTOR_ARG_POSE_DEFAULT_R_Z
                f.write(CMD_COMMON_ENTER)
                # <actor name="actor1">
                f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_PERSON_ACTOR_ARG_NAME_OPEN_LEFT + actorName + CMD_WORLD_PERSON_ACTOR_ARG_NAME_OPEN_RIGHT + CMD_COMMON_ENTER)
                #  <pose>0 1 1.25 0 0 0</pose>
                f.write(CMD_COMMON_SPACE_SIX + CMD_WORLD_PERSON_ACTOR_ARG_POSE_OPEN + actorPos + CMD_WORLD_PERSON_ACTOR_ARG_POSE_CLOSE + CMD_COMMON_ENTER)
                #  <skin>
                f.write(CMD_COMMON_SPACE_SIX +CMD_WORLD_PERSON_ACTOR_ARG_SKIN_OPEN + CMD_COMMON_ENTER)
                ## 여기서 현재 Person model의 컬러를 랜덤으로 할지에 대한 선택사항에 따라 file 경로를 다르게 표시한다
                # 랜덤 컬러 적용일 경우
                if self.ui.chkWorldOptionRandomColor.isChecked():
                    name, extension = os.path.splitext(NAME_MODEL_PERSON)
                    modelFileName = name + str(i) + extension
                    # <filename>file://media/models/walk.dae</filename>
                    f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_OPEN + modelFileName + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_CLOSE + CMD_COMMON_ENTER)
                # 랜덤 컬러 미적용일 경우
                else:
                    # <filename>file://media/models/walk.dae</filename>
                    f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_WALK + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_CLOSE + CMD_COMMON_ENTER)
                #    <scale>1.0</scale>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_SCALE_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_SCALE_DEFAULT + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_SCALE_CLOSE + CMD_COMMON_ENTER)
                #  </skin>
                f.write(CMD_COMMON_SPACE_SIX + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_CLOSE + CMD_COMMON_ENTER)
                #  <animation name="walking">
                f.write(CMD_COMMON_SPACE_SIX + CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_OPEN_DEFAULT + CMD_COMMON_ENTER)
                ## 여기서 현재 Person model의 컬러를 랜덤으로 할지에 대한 선택사항에 따라 file 경로를 다르게 표시한다
                # 랜덤 컬러 적용일 경우
                if self.ui.chkWorldOptionRandomColor.isChecked():
                    name, extension = os.path.splitext(NAME_MODEL_PERSON)
                    modelFileName = name + str(i) + extension
                    # <filename>file://media/models/walk.dae</filename>
                    f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_OPEN + modelFileName + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_CLOSE + CMD_COMMON_ENTER)
                # 랜덤 컬러 미적용일 경우
                else:
                    # <filename>file://media/models/walk.dae</filename>
                    f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_WALK + CMD_WORLD_PERSON_ACTOR_ARG_SKIN_FILENAME_CLOSE + CMD_COMMON_ENTER)
                #    <scale>1.000000</scale>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_SCALE_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_SCALE_DEFAULT + CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_SCALE_CLOSE + CMD_COMMON_ENTER)
                #    <interpolate_x>true</interpolate_x>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_INTERPOLATE_X_OPEN + CMD_COMMON_TRUE + CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_INTERPOLATE_X_CLOSE + CMD_COMMON_ENTER)
                #  </animation>
                f.write(CMD_COMMON_SPACE_SIX + CMD_WORLD_PERSON_ACTOR_ARG_ANIMATION_CLOSE + CMD_COMMON_ENTER)
                f.write(CMD_COMMON_ENTER)
                #  <plugin name="actor1_plugin" filename="libActorPlugin.so">
                f.write(CMD_COMMON_SPACE_SIX + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OPEN_LEFT + pluginName + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OPEN_RIGHT + CMD_COMMON_ENTER)
                #    <target>0 -5 1.2138</target>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_DEFAULT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_CLOSE + CMD_COMMON_ENTER)
                #    <target_weight>1.15</target_weight>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_WEIGHT_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_WEIGHT_DEFAULT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_TARGET_WEIGHT_CLOSE + CMD_COMMON_ENTER)
                #    <obstacle_weight>1.8</obstacle_weight>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OBSTACLE_WEIGHT_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OBSTACLE_WEIGHT_DEFAULT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_OBSTACLE_WEIGHT_CLOSE + CMD_COMMON_ENTER)
                #    <animation_factor>5.1</animation_factor>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_ANIMATION_FACTOR_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_ANIMATION_FACTOR_DEFAULT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_ANIMATION_FACTOR_CLOSE + CMD_COMMON_ENTER)
                #    <ignore_obstacles>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_OPEN + CMD_COMMON_ENTER)
                #      <model>ground_plane</model>
                f.write(CMD_COMMON_SPACE_TEN + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_MODEL_OPEN + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_MODEL_DEFAULT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_MODEL_CLOSE + CMD_COMMON_ENTER)
                #    </ignore_obstacles>
                f.write(CMD_COMMON_SPACE_EIGHT + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_IGNORE_OBSTACLES_CLOSE + CMD_COMMON_ENTER)
                #  </plugin>
                f.write(CMD_COMMON_SPACE_SIX + CMD_WORLD_PERSON_ACTOR_ARG_PLUGIN_CLOSE + CMD_COMMON_ENTER)
                #</actor>
                f.write(CMD_COMMON_SPACE_FOUR + CMD_WORLD_PERSON_ACTOR_ARG_NAME_CLOSE + CMD_COMMON_ENTER)
               
            # 나머지 내용을 쓰기
            f.writelines(lines[cursor_position:])

    # Person 추가로 변경된 World 파일을 원본 World 파일로 변경한다.
    def replaceWorldFile(self, worldName):
        pathDefaultWorlds = PATH_DEFAULT_WORLDS
        if not os.path.exists(pathDefaultWorlds):
            pathDefaultWorlds = PATH_DEFAULT_WORLDS_OTHER
        worldPath = pathDefaultWorlds + "/" + worldName
        backupPath = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME
        backupFile = backupPath + "/" + worldName

        try:
        # 파일 복사
            shutil.copy(backupFile, worldPath)
        except FileNotFoundError:
            print(f"복사할 파일이 없습니다: {backupFile}")
        except Exception as e:
            print(f"오류 발생: {e}")
       
    # Person Model의 색상을 랜덤하게 지정한다
    def setPersonColorRandom(self, count):
        personCount = count
        # 1. 우선 model의 count만큼 walk 파일을 launch 폴더 내에 복사한다
        backupPath = os.getcwd() + "/" + PATH_LAUNCH_FOLDER_NAME
        # 폴더 체크
        pathDefaultModelPerson = PATH_DEFAULT_MODEL_PERSON
        if not os.path.exists(pathDefaultModelPerson):
            pathDefaultModelPerson = PATH_DEFAULT_MODEL_PERSON_OTHER

        orgModelDaePath = pathDefaultModelPerson + "/" + NAME_MODEL_PERSON
        name, extension = os.path.splitext(NAME_MODEL_PERSON)
        for i in range(personCount):
            dstFileName = name + str(i) + extension
            dstFilePath = backupPath + "/" + dstFileName
            # 기존 파일이 있는지 확인
            if os.path.exists(dstFilePath):
                # 기존 파일 삭제
                os.remove(dstFilePath)
            shutil.copy(orgModelDaePath, dstFilePath)

            # 2. 이제 파일을 읽어서 항목중 상의, 하의의 Diffuse 속성을 랜덤하게 변경한다
            # 2-1. 먼저 상의 변경
            try:
                with open(dstFilePath, 'r') as file:
                    # 파일 전체 내용을 읽어옴
                    content = file.readlines()
                    # <effect id="sweater-green-effect">를 찾음
                    for i, line in enumerate(content):
                        if CMD_WORLD_PERSON_ACTOR_EFFECT_SWATER in line:
                            # 색상 요소 검색
                            for j in range(i+1, len(content)):
                                if CMD_WORLD_PERSON_ACTOR_EFFECT_EMISSION in content[j]:
                                    # <ambient> 단어 아래 한 줄을 삭제하고 새로운 color 태그 추가
                                    x = round(random.uniform(FLOAT_COLOR_X_MIN, FLOAT_COLOR_X_MAX), FLOAT_COLOR_DIGIT)
                                    y = round(random.uniform(FLOAT_COLOR_Y_MIN, FLOAT_COLOR_Y_MAX), FLOAT_COLOR_DIGIT)
                                    z = round(random.uniform(FLOAT_COLOR_Z_MIN, FLOAT_COLOR_Z_MAX), FLOAT_COLOR_DIGIT)
                                    a = FLOAT_COLOR_ALPHA
                                    newColor = "              " + CMD_WORLD_PERSON_ACTIR_EFFECT_EMISSION_COLOR_OPEN_LEFT + str(x) + " " + str(y) + " " + str(z) + " " + str(a) + CMD_WORLD_PERSON_ACTIR_EFFECT_COLOR_CLOSE + "\n"
                                    content.pop(j + 1)
                                    content.insert(j + 1, newColor)
                                    continue

                                if CMD_WORLD_PERSON_ACTOR_EFFECT_AMBIENT in content[j]:
                                    # <ambient> 단어 아래 한 줄을 삭제하고 새로운 color 태그 추가
                                    x = round(random.uniform(FLOAT_COLOR_X_MIN, FLOAT_COLOR_X_MAX), FLOAT_COLOR_DIGIT)
                                    y = round(random.uniform(FLOAT_COLOR_Y_MIN, FLOAT_COLOR_Y_MAX), FLOAT_COLOR_DIGIT)
                                    z = round(random.uniform(FLOAT_COLOR_Z_MIN, FLOAT_COLOR_Z_MAX), FLOAT_COLOR_DIGIT)
                                    a = FLOAT_COLOR_ALPHA
                                    newColor = "              " + CMD_WORLD_PERSON_ACTIR_EFFECT_AMBIENT_COLOR_OPEN_LEFT + str(x) + " " + str(y) + " " + str(z) + " " + str(a) + CMD_WORLD_PERSON_ACTIR_EFFECT_COLOR_CLOSE + "\n"
                                    content.pop(j + 1)
                                    content.insert(j + 1, newColor)
                                    continue                                  

                                if CMD_WORLD_PERSON_ACTOR_EFFECT_DIFFUSE in content[j]:
                                    # <deffuse> 단어 아래 한 줄을 삭제하고 새로운 color 태그 추가
                                    x = round(random.uniform(FLOAT_COLOR_X_MIN, FLOAT_COLOR_X_MAX), FLOAT_COLOR_DIGIT)
                                    y = round(random.uniform(FLOAT_COLOR_Y_MIN, FLOAT_COLOR_Y_MAX), FLOAT_COLOR_DIGIT)
                                    z = round(random.uniform(FLOAT_COLOR_Z_MIN, FLOAT_COLOR_Z_MAX), FLOAT_COLOR_DIGIT)
                                    a = FLOAT_COLOR_ALPHA
                                    newColor = "              " + CMD_WORLD_PERSON_ACTIR_EFFECT_DIFFUSE_COLOR_OPEN_LEFT + str(x) + " " + str(y) + " " + str(z) + " " + str(a) + CMD_WORLD_PERSON_ACTIR_EFFECT_COLOR_CLOSE + "\n"
                                    content.pop(j + 1)
                                    content.insert(j + 1, newColor)
                                    continue    

                                if CMD_WORLD_PERSON_ACTOR_EFFECT_SPECULAR in content[j]:
                                    # <specular> 단어 아래 한 줄을 삭제하고 새로운 color 태그 추가
                                    x = round(random.uniform(FLOAT_COLOR_X_MIN, FLOAT_COLOR_X_MAX), FLOAT_COLOR_DIGIT)
                                    y = round(random.uniform(FLOAT_COLOR_Y_MIN, FLOAT_COLOR_Y_MAX), FLOAT_COLOR_DIGIT)
                                    z = round(random.uniform(FLOAT_COLOR_Z_MIN, FLOAT_COLOR_Z_MAX), FLOAT_COLOR_DIGIT)
                                    a = FLOAT_COLOR_ALPHA
                                    newColor = "              " + CMD_WORLD_PERSON_ACTIR_EFFECT_SPECULAR_COLOR_OPEN_LEFT + str(x) + " " + str(y) + " " + str(z) + " " + str(a) + CMD_WORLD_PERSON_ACTIR_EFFECT_COLOR_CLOSE + "\n"
                                    content.pop(j + 1)
                                    content.insert(j + 1, newColor)
                                    break  

                    # 수정된 내용을 파일에 쓰기
                    with open(dstFilePath, 'w') as file:
                        file.writelines(content)
                    print(dstFilePath + " 업데이트 완료")
            except FileNotFoundError:
                print(f"파일을 찾을 수 없음: {dstFilePath}")

            # 2-2. 다음으로 하의 변경
            try:
                with open(dstFilePath, 'r') as file:
                    # 파일 전체 내용을 읽어옴
                    content = file.readlines()
                    # <effect id="jeans-blue-effect">를 찾음
                    for i, line in enumerate(content):
                        if CMD_WORLD_PERSON_ACTOR_EFFECT_JEAN in line:
                            # <diffuse>를 찾음
                            for j in range(i+1, len(content)):
                                if CMD_WORLD_PERSON_ACTOR_EFFECT_DIFFUSE in content[j]:
                                    # <diffuse> 단어 아래 한 줄을 삭제하고 새로운 color 태그 추가
                                    x = round(random.uniform(FLOAT_COLOR_X_MIN, FLOAT_COLOR_X_MAX), FLOAT_COLOR_DIGIT)
                                    y = round(random.uniform(FLOAT_COLOR_Y_MIN, FLOAT_COLOR_Y_MAX), FLOAT_COLOR_DIGIT)
                                    z = round(random.uniform(FLOAT_COLOR_Z_MIN, FLOAT_COLOR_Z_MAX), FLOAT_COLOR_DIGIT)
                                    a = FLOAT_COLOR_ALPHA
                                    newColor = "              " + CMD_WORLD_PERSON_ACTIR_EFFECT_DIFFUSE_COLOR_OPEN_LEFT + str(x) + " " + str(y) + " " + str(z) + " " + str(a) + CMD_WORLD_PERSON_ACTIR_EFFECT_COLOR_CLOSE + "\n"
                                    content.pop(j + 1)
                                    content.insert(j + 1, newColor)
                                    break

                    # 수정된 내용을 파일에 쓰기
                    with open(dstFilePath, 'w') as file:
                        file.writelines(content)
                    print(dstFilePath + " 업데이트 완료")
            except FileNotFoundError:
                print(f"파일을 찾을 수 없음: {dstFilePath}")

    # UI 로봇 정보를 파라미터 로봇리스트에 저장
    def SaveUIRobotInfoToSimRobotsInfo(self, lstRobots):
        # 기존 정보 삭제
        lstRobots.clear()

        # 리스트 정보 가져와서 로봇 배열에 입력
        idxLocobot = 0
        idxTurtlebot3Burger = 0
        idxTurtlebot3Waffle = 0
        idxJetbot = 0
        idxInterbotix = 0
        idxUni = 0
        idxStretch2 = 0
        for idx in range(self.ui.lstwRobots.count()):
            item = self.ui.lstwRobots.item(idx)
            widget = self.ui.lstwRobots.itemWidget(item)
            robot = Robot()
            # Check robot type and set id
            if widget.ui.lbRobotName.text() == CONST_LOCOBOT_NAME:
                # TEST : 1차 릴리즈 버전에서는 Locobot 제외
                pass
                robot.type = ENUM_ROBOT_TYPE.LOCOBOT
                robot.id = idxLocobot
                robot.name = CMD_LOCOBOT_MODEL + str(robot.id)
                idxLocobot = idxLocobot + 1
            elif widget.ui.lbRobotName.text() == CONST_TURTLEBOT3_BUTGER_NAME:
                robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER  
                robot.id = idxTurtlebot3Burger
                robot.name = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_UNDERBAR + str(robot.id)
                idxTurtlebot3Burger = idxTurtlebot3Burger + 1
            elif widget.ui.lbRobotName.text() == CONST_TURTLEBOT3_WAFFLE_NAME:
                robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE
                robot.id = idxTurtlebot3Waffle
                robot.name = CMD_TURTLEBOT3_DEFAULT_NAME + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_COMMON_UNDERBAR + str(robot.id)
                idxTurtlebot3Waffle = idxTurtlebot3Waffle + 1
            elif widget.ui.lbRobotName.text() == CONST_JETBOT_NAME:
                robot.type = ENUM_ROBOT_TYPE.JETBOT
                robot.id = idxJetbot
                robot.name = CMD_JETBOT_DEFAULT_NAME + str(robot.id)
                idxJetbot = idxJetbot + 1
            elif widget.ui.lbRobotName.text() == CONST_INTERBOTIX_NAME:
                robot.type = ENUM_ROBOT_TYPE.INTERBOTIX
                robot.id = idxInterbotix
                robot.name = CMD_LOCOBOT_MODEL + str(robot.id)
                idxInterbotix = idxInterbotix + 1
            elif widget.ui.lbRobotName.text() == CONST_UNI_NAME:
                robot.type = ENUM_ROBOT_TYPE.UNI050_BASE
                robot.id = idxUni
                robot.name = CMD_UNI_DEFAULT_NAME + CMD_COMMON_UNDERBAR + str(robot.id)
                idxUni = idxUni + 1         
            elif widget.ui.lbRobotName.text() == CONST_HELLO_STRETCH2_NAME:
                robot.type = ENUM_ROBOT_TYPE.HELLO_ROBOT_STRETCH
                robot.id = idxStretch2
                robot.name = CMD_HELLO_STRETCH2_MODEL_NAME + CMD_COMMON_UNDERBAR + str(robot.id)
                idxStretch2 = idxStretch2 + 1

            # TODO : Check starting position 현재 버전에선 일단 로봇의 위치는 미리 지정된 고정 위치로 지정한다
            # lastPosOffset = 0.5
            # for world in self.m_worlds:
            #     for world_sub in world.arrCategorySubs:
            #         if world_sub.categorySub.value == self.m_simulator.categorySub:
            #             # 만약 현재 world_sub의 저장된 고정 위치보다 많은수의 로봇이 올 경우 마지막 위치값에 계속 0.5를 더해 추가한다
            #             if idx >= len(world_sub.robotStartXYZ) / 3:
            #                 pos = int((len(world_sub.robotStartXYZ) / 3 -1) * 3)
            #                 robot.startX = world_sub.robotStartXYZ[int(pos)] + lastPosOffset
            #                 robot.startY = world_sub.robotStartXYZ[int(pos + 1)] + lastPosOffset
            #                 robot.startZ = 0.1
            #                 lastPosOffset = lastPosOffset + 0.5
            #                 break
            #             else:
            #                 pos = idx * 3
            #                 robot.startX = world_sub.robotStartXYZ[pos]
            #                 robot.startY = world_sub.robotStartXYZ[pos + 1]
            #                 robot.startZ = world_sub.robotStartXYZ[pos + 2]
            #                 break
            xPos = widget.ui.dsbRobotStartPosX.value()  
            robot.startX = f"{xPos:.1f}"
            yPos = widget.ui.dsbRobotStartPosY.value()  
            robot.startY = f"{yPos:.1f}"
            zPos = widget.ui.dsbRobotStartPosZ.value()  
            robot.startZ = f"{zPos:.1f}"

            # Check robot option
            robot.option.camera = widget.ui.ckbRobotOptionCamera.isChecked()
            robot.option.arm = widget.ui.ckbRobotOptionUseArm.isChecked()
            robot.option.base = widget.ui.ckbRobotOptionBase.isChecked()
            lstRobots.append(robot)            

    # 로봇 리스트의 활성화 로봇들을 편집 불가 상태로 비활성화 시킨다
    def disableRobotList(self):
        for idx in range(self.ui.lstwRobots.count()):
            item = self.ui.lstwRobots.item(idx)
            widget = self.ui.lstwRobots.itemWidget(item)
            if widget:
                widget.setEnabled(False)

    # XML 저장
    def saveFile(self):
        # save file
        root = ET.Element("Save")

        # 월드 타입
        elWorldType = ET.SubElement(root, "worldType")
        elWorldType.text = self.m_simulator.worldFileType

        # 월드 메인 카테고리
        elCategoryMain = ET.SubElement(root, "categoryMain")
        elCategoryMain.text = str(self.m_simulator.categoryMain)

        # 월드 서브 카테고리
        elCategorySub = ET.SubElement(root, "categorySub")
        elCategorySub.text = str(self.m_simulator.categorySub)

        # 월드 로봇 종류 지정
        self.m_simulator.robots.clear()
        lstRobots = []
        self.SaveUIRobotInfoToSimRobotsInfo(lstRobots)
        self.m_simulator.robots = copy.deepcopy(lstRobots)

        elRobots = ET.SubElement(root, "robots")
        robotCount = len(self.m_simulator.robots)
        for idx in range(robotCount):
            rlRobot = ET.SubElement(elRobots, "robot")
            #  로봇 id
            id = ET.SubElement(rlRobot, "id")
            id.text = str(self.m_simulator.robots[idx].id)
            #  로봇 name
            name = ET.SubElement(rlRobot, "name")
            name.text = str(self.m_simulator.robots[idx].name)
            #  로봇 type
            type = ET.SubElement(rlRobot, "type")
            type.text = str(self.m_simulator.robots[idx].type)
            #  로봇 startX
            startX = ET.SubElement(rlRobot, "startX")
            startX.text = str(self.m_simulator.robots[idx].startX)
            #  로봇 startY
            startY = ET.SubElement(rlRobot, "startY")
            startY.text = str(self.m_simulator.robots[idx].startY)
            #  로봇 startZ
            startZ = ET.SubElement(rlRobot, "startZ")
            startZ.text = str(self.m_simulator.robots[idx].startZ)
            #  TODO : 로봇 Option
            option = ET.SubElement(rlRobot, "option")
            
        # tkinter 초기화
        tkRoot = tk.Tk()
        tkRoot.withdraw()  # 메인 창 숨기기

        # 저장 다이얼로그 표시
        file_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
        if file_path:
            # 사용자가 입력한 파일 경로에서 파일명만 추출하여 사용
            filename = file_path.split("/")[-1]  # 파일 경로에서 마지막 요소가 파일명이므로 추출
            tree = ET.ElementTree(root)
            tree.write(filename)

    # XML 로드
    def loadFile(self):
        tkRoot = tk.Tk()
        tkRoot.withdraw()  # 메인 창 숨기기
        file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
        if file_path:
            if file_path.endswith('.xml'):
                ## 입력 시작
                # 입력 전 기존 패널 정보 및 로봇 정보 초기화
                self.ui.lstwRobots.clear()
                self.m_simulator.robots.clear()
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    # 정보 세팅 시작
                    self.m_simulator.worldType = root.find("worldType").text
                    self.m_simulator.categoryMain = root.find("categoryMain").text
                    categorySub = root.find("categorySub").text
                    robots = root.find("robots")
                    # 로봇 정보
                    for xmlRobot in root.findall(".//robot"):
                        robot = Robot()
                        # 로봇 id
                        id = xmlRobot.find("id").text
                        robot.id = int(id)
                        #  로봇 name
                        name = xmlRobot.find("name").text
                        robot.name = name
                        #  로봇 type
                        type = xmlRobot.find("type").text
                        robot.type = type
                        #  로봇 startX
                        startX = xmlRobot.find("startX").text
                        fStartX = float(startX)
                        strStartX = "{:.1f}".format(fStartX)
                        robot.startX = strStartX
                        #  로봇 startY
                        startY = xmlRobot.find("startY").text
                        fStartY = float(startY)
                        strStartY = "{:.1f}".format(fStartY)
                        robot.startY = strStartY
                        #  로봇 startZ  
                        startZ = xmlRobot.find("startZ").text
                        fStartZ = float(startZ)
                        strStartZ = "{:.1f}".format(fStartZ)
                        robot.startZ = strStartZ
                        #  TODO : 로봇 Option
                        # option = ET.SubElement(rlRobot, "option")
                        # 로봇 입력
                        self.m_simulator.robots.append(robot)
                    # print(f"Element: {elem.tag}, Attributes: {elem.attrib}, Text: {elem.text}")
                except ET.ParseError as e:
                    print(f"XML 분석 중 오류가 발생했습니다: {e}")

                ### 입력 완료 후 UI에 정보 세팅
                ## world
                for idxMain in range(0, len(self.m_worlds)):
                    if str(self.m_worlds[idxMain].categoryMain) == self.m_simulator.categoryMain:
                        self.ui.lstwWorldMainCategory.setCurrentRow(idxMain)
                        # Sub category
                        for idxSub in range(0, len(self.m_worlds[idxMain].arrCategorySubs)):
                            if str(self.m_worlds[idxMain].arrCategorySubs[idxSub].categorySub.value) == categorySub:
                                self.ui.lstwWorldSubCategory.setCurrentRow(idxSub)

                ## Robot
                for idxRobot in range(0, len(self.m_simulator.robots)):
                    # 리스트뷰에 새로운 로봇 위젯 추가
                    lstRobot = self.ui.lstwRobots
                    item = QtWidgets.QListWidgetItem(lstRobot)
                    lstRobot.addItem(item)
                    # 로봇 위젯 생성
                    row = WidgetRobotItem()
                    item.setSizeHint(row.sizeHint())
                    # 썸네일 변경
                    thumbIdx = 0
                    # if self.m_simulator.robots[idxRobot].type == str(ENUM_ROBOT_TYPE.LOCOBOT):
                    #     thumbIdx = 0
                    if self.m_simulator.robots[idxRobot].type == str(ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER):
                        thumbIdx = 0
                    elif self.m_simulator.robots[idxRobot].type == str(ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE):
                        thumbIdx = 1
                    row.ChangeCurrentThumbIdx(thumbIdx)
                    
                    # Starting xyz
                    row.SetStartPosition(float(self.m_simulator.robots[idxRobot].startX), float(self.m_simulator.robots[idxRobot].startY), float(self.m_simulator.robots[idxRobot].startZ))

                    # 리스트뷰에 로봇 위젯 셋
                    lstRobot.setItemWidget(item, row)
            else:
                print("잘못된 파일입니다. XML 파일을 선택하세요.")

    # DB Open
    def OpenDBDialog(self):
        req = QtWidgets.QMessageBox.question(self, 'Execution error', 'Service is being prepared.',QtWidgets.QMessageBox.Ok)
        return
        # dlg = DialogDBOpen()
        # dlg.showModal()
        pass

    # Collaboration task 아이템 선택 이벤트
    def on_item_selection_changed_collaboration_task(self):
        # 선택된 아이템 가져오기
        selected_items = self.ui.lstwRobotROSCollaborationTasks.selectedItems()
        if selected_items == None:
            return
        item = selected_items[0]
        # 선택된 아이템의 행 번호
        row = self.ui.lstwRobotROSCollaborationTasks.row(item)

        # TODO : 협업 태스크는 현재 고정상태의 로봇 조건을 갖추므로 기존 설정한 로봇 리스트가 있다면 지우고 고정시킨다.
        # None 일때는 실행 안함
        if self.m_arrROSCollaborationTask[row].type == ENUM_ROS_COLLABORATION_TASK_TYPE.NONE:
            self.ui.lstwRobots.clear()
            self.ui.btnAddRobot.setEnabled(True)
            self.ui.btnDeleteRobot.setEnabled(True)
            self.ui.btnAddModel.setEnabled(True)
            self.ui.lstwWorldMainCategory.setEnabled(True)
            self.ui.lstwWorldSubCategory.setEnabled(True)
            for _i2 in range(self.ui.lstwWorldSubCategory.count()):
                _it2 = self.ui.lstwWorldSubCategory.item(_i2)
                _it2.setFlags(_it2.flags() | Qt.ItemIsEnabled)
                _it2.setHidden(False)
        else:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setWindowTitle("Warning")
            msg_box.setText("You have selected a collaborative task.\n\n"
                            "The list will be deleted, and the robot will be fixed.\n\n"
                            "Are you sure?")
            # 버튼 추가
            msg_box.addButton(QtWidgets.QMessageBox.Cancel)
            msg_box.addButton(QtWidgets.QMessageBox.Ok)
            result = msg_box.exec()

            if result == QtWidgets.QMessageBox.Ok:
                # 먼저 로봇을 정보를 삭제 한다.
                self.ui.lstwRobots.clear()

                # 현재 해당 작업에 사용되는 맵은 launch 파일에 강제로 설정 되어있다(realay의 경우 aws robomaker)
                # 때문에 UI상 보이는 맵 상태만 Custom으로 변경 시키도록 한다
                worldMainCustomIdx = 0
                worldSubCollaborationIdx = 0
                # 태스크별 기본 월드 — 충돌회피=bnt 고정, Relay/다목적=외벽-only 기본
                # (warehouse 는 목록에서 수동 선택 가능 — 2026-08-09 지시)
                wantSub = (ENUM_WORLD_CATEGORY_SUB.COLLABORATION_BNT
                           if self.m_arrROSCollaborationTask[row].type
                           in (ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE,
                               ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                               ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND)
                           else ENUM_WORLD_CATEGORY_SUB.COLLABORATION_EMPTY)
                for i in range(0, len(self.m_worlds)) :
                    if self.m_worlds[i].categoryMain == ENUM_WORLD_CATEGORY_MAIN.CUSTOM:
                        worldMainCustomIdx = i
                        for j in range(0, len(self.m_worlds[i].arrCategorySubs)):
                            if self.m_worlds[i].arrCategorySubs[j].categorySub == wantSub:
                                worldSubCollaborationIdx = j
                                break
                self.ui.lstwWorldMainCategory.setCurrentRow(worldMainCustomIdx)
                self.ui.lstwWorldSubCategory.setCurrentRow(worldSubCollaborationIdx)

                ## TODO : 로봇 정보를 고정 시킨다. (현재 locobot 2대, turtlebot-burger 2대)
                # locobot_1
                lstRobot = self.ui.lstwRobots
                wItem = QtWidgets.QListWidgetItem(lstRobot)
                lstRobot.addItem(wItem)
                # 로봇 위젯 생성
                newItem = WidgetRobotItem()
                wItem.setSizeHint(newItem.sizeHint())
                newItem.ChageCurrentThumbIdxByName(CONST_INTERBOTIX_NAME)
                newItem.SetStartPosition(0.0, 0.0, 0.0)
                # 리스트뷰에 로봇 위젯 셋
                lstRobot.setItemWidget(wItem, newItem)

                # locobot_2
                lstRobot = self.ui.lstwRobots
                wItem = QtWidgets.QListWidgetItem(lstRobot)
                lstRobot.addItem(wItem)
                # 로봇 위젯 생성
                newItem = WidgetRobotItem()
                wItem.setSizeHint(newItem.sizeHint())
                newItem.ChageCurrentThumbIdxByName(CONST_INTERBOTIX_NAME)
                newItem.SetStartPosition(0.0, 0.5, 0.0)
                # 리스트뷰에 로봇 위젯 셋
                lstRobot.setItemWidget(wItem, newItem)                

                # 지도제작: waffle 1대 추가 (2026-08-09 — locobot 2 + waffle 1)
                if (self.m_arrROSCollaborationTask[row].type
                        in (ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                            ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND)):
                    lstRobot = self.ui.lstwRobots
                    wItemW = QtWidgets.QListWidgetItem(lstRobot)
                    lstRobot.addItem(wItemW)
                    newItemW = WidgetRobotItem()
                    wItemW.setSizeHint(newItemW.sizeHint())
                    try:
                        newItemW.ChageCurrentThumbIdxByName(CONST_TURTLEBOT3_WAFFLE_NAME)
                    except Exception:
                        newItemW.ChageCurrentThumbIdxByName(CONST_TURTLEBOT3_BUTGER_NAME)
                    newItemW.SetStartPosition(0.0, 0.0, 0.0)
                    lstRobot.setItemWidget(wItemW, newItemW)
                # tutlebot_1 — 지도제작(locobot 2대+waffle)에서는 burger 생략
                if (self.m_arrROSCollaborationTask[row].type
                        not in (ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                                ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND)):
                    lstRobot = self.ui.lstwRobots
                    wItem2 = QtWidgets.QListWidgetItem(lstRobot)
                    lstRobot.addItem(wItem2)
                    # 로봇 위젯 생성
                    newItem2 = WidgetRobotItem()
                    wItem2.setSizeHint(newItem2.sizeHint())
                    newItem2.ChageCurrentThumbIdxByName(CONST_TURTLEBOT3_BUTGER_NAME)
                    newItem2.SetStartPosition(1.0, 0.0, 0.0)
                    # 리스트뷰에 로봇 위젯 셋
                    lstRobot.setItemWidget(wItem2, newItem2)

                # tutlebot_2 — 충돌회피(3로봇: locobot 2 + tb3 1)에서는 생략 (2026-08-08)
                if (self.m_arrROSCollaborationTask[row].type
                        not in (ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE,
                                ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP,
                                ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND)):
                    lstRobot = self.ui.lstwRobots
                    wItem2 = QtWidgets.QListWidgetItem(lstRobot)
                    lstRobot.addItem(wItem2)
                    # 로봇 위젯 생성
                    newItem2 = WidgetRobotItem()
                    wItem2.setSizeHint(newItem2.sizeHint())
                    newItem2.ChageCurrentThumbIdxByName(CONST_TURTLEBOT3_BUTGER_NAME)
                    newItem2.SetStartPosition(1.0, 0.5, 0.0)
                    # 리스트뷰에 로봇 위젯 셋
                    lstRobot.setItemWidget(wItem2, newItem2)

                # 모든 로봇 정보는 수정 불가능 하도록 변경
                self.disableRobotList()
                self.ui.btnAddRobot.setEnabled(False)
                self.ui.btnDeleteRobot.setEnabled(False)
                self.ui.btnAddModel.setEnabled(False)
                self.ui.lstwWorldMainCategory.setEnabled(False)
                # Relay/다목적: warehouse ↔ 외벽-only(empty) 선택 허용 (2026-08-09, RTF↑)
                # 충돌회피는 bnt 고정
                _rm = (self.m_arrROSCollaborationTask[row].type
                       in (ENUM_ROS_COLLABORATION_TASK_TYPE.RELAY,
                           ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE))
                self.ui.lstwWorldSubCategory.setEnabled(_rm)
                # 태스크별 월드 목록 정리 (2026-08-09 지시):
                #  - Relay/다목적: warehouse ↔ empty 만 (bnt 숨김)
                #  - 충돌회피: bnt 만 표시
                _isAvoid = (self.m_arrROSCollaborationTask[row].type
                            in (ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE,
                                ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP))
                for _i2 in range(self.ui.lstwWorldSubCategory.count()):
                    _it2 = self.ui.lstwWorldSubCategory.item(_i2)
                    _isBnt = 'bnt' in _it2.text()
                    _it2.setHidden(_isBnt != _isAvoid)
                    _it2.setFlags(_it2.flags() | Qt.ItemIsEnabled)

                # 로봇 정보 저장
                self.m_simulator.robots.clear()
                lstRobots = []
                self.SaveUIRobotInfoToSimRobotsInfo(lstRobots)
                self.m_simulator.robots = copy.deepcopy(lstRobots)

                if selected_items:
                    self.m_simulator.ros_collaboration = self.m_arrROSCollaborationTask[row].type
                    self.m_prevSelectedCollaborationTask = row

            else:
                # 시그널 임시 차단
                self.ui.lstwRobotROSCollaborationTasks.blockSignals(True)
                self.ui.lstwRobotROSCollaborationTasks.setCurrentRow(self.m_prevSelectedCollaborationTask)
                self.ui.lstwRobotROSCollaborationTasks.blockSignals(False)

    # 협업태스크 Setting에서 변경된 로봇 정보를 UI에 갱신
    # 로봇 자체는 삭제 추가가 없기 때문에 사실상 Option 정보만 갱신 한다
    def ChangeUIInfoToSettingInfo(self, lstRobots):
        # 입력 시작
        lstwRobots = self.ui.lstwRobots
        for i in range(lstwRobots.count()):  # 리스트 아이템 개수만큼 반복
            robot = lstRobots.robots[i]
            item = self.ui.lstwRobots.item(i)
            widget = self.ui.lstwRobots.itemWidget(item)
            if isinstance(widget, WidgetRobotItem):
                widget.SetStartPosition(robot.startX, robot.startY, robot.startZ)
            

# 메인 실행
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

