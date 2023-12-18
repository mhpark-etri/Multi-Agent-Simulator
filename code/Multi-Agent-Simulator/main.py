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
import threading
from datetime import datetime   
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from ui_main import Ui_MainWindow
from dlgROSTeleop import DialogTeleop
from dlgROSSlam import DialogSmal
from dlgROSNavigation import DialogNavigation
from dlgROSRViz import DialogRViz
from widgetRobotItem import WidgetRobotItem
import atexit
from PySide6.QtGui import QPixmap
import xml.etree.ElementTree as ET

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
MAX_MODEL_COUNT_ROBOT = 2  # Max robot model count
MAX_MODEL_COUNT_PERSON = 3 # Max person model count

PATH_DEFAULT_MODEL_PERSON = "/usr/local/share/gazebo-11/media/models"
PATH_DEFAULT_MODEL_PERSON_OTHER = "/usr/share/gazebo-11/media/models"
NAME_MODEL_PERSON = "walk.dae"
NAME_MODEL_PERSON_CLOTH_TOP = "sweater-green-effect"
NAME_MODEL_PERSON_CLOTH_BOTTOM = "jeans-blue-effect"
PATH_DEFAULT_WORLDS = "/usr/local/share/gazebo-11/worlds"
PATH_DEFAULT_WORLDS_OTHER = "/usr/share/gazebo-11/worlds"
NAME_BACKUP_WORLD = "backup_world"

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

    # Init
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 소멸자
        atexit.register(self.CleanUp)

        ## UI Event
        self.ui.btnStartSimulator.clicked.connect(self.StartSimualtor)
        # World radio button
        # self.btnGroupWorld = QtWidgets.QButtonGroup()
        # self.btnGroupWorld.setExclusive(True)
        # self.btnGroupWorld.addButton(self.ui.rbWorldWarehouse)
        # self.btnGroupWorld.addButton(self.ui.rbWorldHospital)
        # self.btnGroupWorld.addButton(self.ui.rbWorldSmallHouse)
        # self.btnGroupWorld.addButton(self.ui.rbWorldBookStore)
        # self.btnGroupWorld.buttonToggled.connect(self.WorldRadioButtonItemSelected)
        # Add & Delete Model
        self.ui.btnAddRobot.clicked.connect(self.AddRobot)
        self.ui.btnDeleteRobot.clicked.connect(self.DeleteRobot)
        self.ui.lstwWorldMainCategory.itemSelectionChanged.connect(self.on_item_selection_changed_main_category)
        self.ui.lstwWorldSubCategory.itemSelectionChanged.connect(self.on_item_selection_changed_sub_category)
        self.ui.sbWorldOptionPersonCount.setMaximum(MAX_MODEL_COUNT_PERSON)
        self.ui.chkWorldOptionPerson.stateChanged.connect(self.ChangedWolrdOptionPersonCheckbox)

        # ROS
        self.ui.btnROSTeleop.clicked.connect(self.StartTeleopDialog)
        self.ui.btnROSSlamEdit.clicked.connect(self.StartSlamDialog)
        self.ui.btnROSNavigationEdit.clicked.connect(self.StartNavigationDilaog)
        self.btnGroupROS = QtWidgets.QButtonGroup()
        self.btnGroupROS.setExclusive(True)
        self.btnGroupROS.addButton(self.ui.rbROSNone)
        self.btnGroupROS.addButton(self.ui.rbROSSlam)
        self.btnGroupROS.addButton(self.ui.rbROSNavigation)
        self.btnGroupROS.buttonToggled.connect(self.ROSRadioButtonItemSelected)

        # Set Default Init
        # ROS = None
        self.m_simulator.ros = ENUM_ROS_TYPE.NONE
        # World
        self.SetWorld()
        

    # DeInit
    def CleanUp(self):
        os.system("killall gzserver")
        os.system("pkill gnome-terminal")

    # 시뮬레이터 시작
    def StartSimualtor(self):
        # 시작전 서버 전부 비활성화
        os.system("killall gzserver")
        # Simulator 구조체 초기화
        if len(self.m_simulator.robots) > 0 :
            self.m_simulator.robots.clear()

        # 1. World 선택 
        # 하단 World 라디오 버튼 이벤트에 연결
        
        # 2. 로봇 생성(복수)
        lstRobots = []
        
        # 리스트 정보 가져와서 로봇 배열에 입력
        idxLocobot = 0
        idxTurtlebot3Burger = 0
        idxTurtlebot3Waffle = 0
        idxJetbot = 0
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
                idxLocobot = idxLocobot + 1
            elif widget.ui.lbRobotName.text() == CONST_TURTLEBOT3_BUTGER_NAME:
                robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER
                robot.id = idxTurtlebot3Burger
                idxTurtlebot3Burger = idxTurtlebot3Burger + 1
            elif widget.ui.lbRobotName.text() == CONST_TURTLEBOT3_WAFFLE_NAME:
                robot.type = ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE
                robot.id = idxTurtlebot3Waffle
                idxTurtlebot3Waffle = idxTurtlebot3Waffle + 1
            else:
                robot.type = ENUM_ROBOT_TYPE.JETBOT
                robot.id = idxJetbot
                idxJetbot = idxJetbot + 1

            # Check starting position
            # robot.startX = widget.ui.dsbRobotStartPosX.value()
            # robot.startY = widget.ui.dsbRobotStartPosY.value()
            # robot.startZ = widget.ui.dsbRobotStartPosZ.value()
            # TODO : Check starting position 현재 버전에선 일단 로봇의 위치는 미리 지정된 고정 위치로 지정한다
            for world in self.m_worlds:
                for world_sub in world.arrCategorySubs:
                    if world_sub.categorySub.value == self.m_simulator.categorySub:
                        pos = idx * 3
                        robot.startX = world_sub.robotStartXYZ[pos]
                        robot.startY = world_sub.robotStartXYZ[pos + 1]
                        robot.startZ = world_sub.robotStartXYZ[pos + 2]
                        break

            # Check robot option
            robot.option.camera = widget.ui.ckbRobotOptionCamera.isChecked()
            robot.option.arm = widget.ui.ckbRobotOptionUseArm.isChecked()
            robot.option.base = widget.ui.ckbRobotOptionBase.isChecked()
            lstRobots.append(robot)

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
        # world model 설정
        if self.m_simulator.worldType == ENUM_WORLD.WAREHOUSE :
            cmdLine = PATH_SOURCE_WAREHOUSE 
        elif self.m_simulator.worldType == ENUM_WORLD.HOSPITAL :
            cmdLine = PATH_SOURCE_HOSPITAL
        elif self.m_simulator.worldType == ENUM_WORLD.SMALLHOUSE :
            cmdLine = PATH_SOURCE_SMALL_HOUSE
        elif self.m_simulator.worldType == ENUM_WORLD.BOOK_STORE :
            cmdLine = PATH_SOURCE_BOOK_STORE
        f.write(cmdLine + CMD_COMMON_ENTER)

        f.write("roslaunch " + launchFile)
        f.close
        # Executable 권한 설정
        os.system('chmod 777 ' + tmpFile)   
        # roslaunch (shell)
        exeSimulator = subprocess.Popen(tmpFile, shell=True, executable="/bin/bash")

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
        f.write(CMD_COMMON_ENTER)
        f.write(CMD_COMMON_OPEN_LAUNCH + CMD_COMMON_ENTER)
        
        ## World 정보 입력
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
        robotCount = len(sim.robots)
        for i in range(0, robotCount):
            ## 분기 - ROS에 따른 조정
            # ROS 없음
            if sim.ros == ENUM_ROS_TYPE.NONE:
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
                    sim.robots[i].rosNamespace = robotName
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
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + str(sim.robots[i].id)
                    robotName = "\"" + robotName + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Model Position
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + str(sim.robots[i].id)
                    sim.robots[i].rosNamespace = robotName
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
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + str(sim.robots[i].id)
                    robotName = "\"" + robotName + "\""
                    f.write(CMD_COMMON_SPACE_DOUBLE + CMD_COMMON_OPEN_ARG + CMD_COMMON_SPACE + CMD_COMMON_NAME + robotName + CMD_COMMON_SPACE + CMD_COMMON_DEFAULT + robotName + CMD_COMMON_CLOSE_TAG + CMD_COMMON_ENTER)
                    f.write(CMD_COMMON_ENTER)
                    # Model Position
                    posX = sim.robots[i].startX
                    posY = sim.robots[i].startY
                    posZ = sim.robots[i].startZ
                    robotName = CMD_TURTLEBOT3_DEFAULT_NAME + str(sim.robots[i].id)
                    sim.robots[i].rosNamespace = robotName
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
                    sim.robots[i].rosNamespace = robotName
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
                    sim.robots[i].rosNamespace = robotName
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


    #######################################
    ############### ROS ###################
    #######################################

    # Teleop
    def StartTeleopDialog(self):
        # 로봇 정보가 없으면 종료
        if len(self.m_simulator.robots) <= 0 : 
           req = QtWidgets.QMessageBox.question(self, 'Start simulator', 'Please run the simulator first.',QtWidgets.QMessageBox.Ok)
           return

        dlg = DialogTeleop(self.m_simulator)
        dlg.showModal()

    # Slam
    def StartSlamDialog(self):
        # 로봇 정보가 없으면 종료
        if len(self.m_simulator.robots) <= 0 : 
           req = QtWidgets.QMessageBox.question(self, 'Start simulator', 'Please run the simulator first.',QtWidgets.QMessageBox.Ok)
           return

        dlg = DialogSmal(self.m_simulator)
        dlg.showModal()

    # Navigation
    def StartNavigationDilaog(self):
        # 로봇 정보가 없으면 종료
        if len(self.m_simulator.robots) <= 0 : 
           req = QtWidgets.QMessageBox.question(self, 'Start simulator', 'Please run the simulator first.',QtWidgets.QMessageBox.Ok)
           return

        dlg = DialogNavigation(self.m_simulator)
        dlg.showModal()

    # R-Viz
    def StartRVizDialog(self):
        # 로봇 정보가 없으면 종료
        if len(self.m_simulator.robots) <= 0 : 
            req = QtWidgets.QMessageBox.question(self, 'Start simulator', 'Please run the simulator first.',QtWidgets.QMessageBox.Ok)
            return

        dlg = DialogRViz(self.m_simulator)
        dlg.showModal()

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

    # 라디오 버튼 - ROS 선택
    def ROSRadioButtonItemSelected(self):
        if self.ui.rbROSNone.isChecked() == True:
            self.m_simulator.ros = ENUM_ROS_TYPE.NONE
        elif self.ui.rbROSSlam.isChecked() == True:
            self.m_simulator.ros = ENUM_ROS_TYPE.SLAM
        elif self.ui.rbROSNavigation.isChecked() == True:
            self.m_simulator.ros = ENUM_ROS_TYPE.NAVIGATION

    # 로봇 추가
    def AddRobot(self):
        # 최대 로봇 허용개수 초과
        if self.ui.lstwRobots.count() >= MAX_MODEL_COUNT_ROBOT : 
            req = QtWidgets.QMessageBox.question(self, 'Add Robot', 'The maximum number of allowed robots has been exceeded. (Max : ' + str(MAX_MODEL_COUNT_ROBOT) + ')',QtWidgets.QMessageBox.Ok)
            return

        # 리스트뷰에 새로운 로봇 위젯 추가
        lstRobot = self.ui.lstwRobots
        item = QtWidgets.QListWidgetItem(lstRobot)
        lstRobot.addItem(item)
        # 로봇 위젯 생성
        row = WidgetRobotItem()
        item.setSizeHint(row.sizeHint())
        # 만약 두번째 이상 로봇이라면 위치값을 증분하여 표기
        if self.ui.lstwRobots.count() > 1: 
            prevIdx = self.ui.lstwRobots.count() - 2
            prevItem = self.ui.lstwRobots.item(prevIdx)
            widget = self.ui.lstwRobots.itemWidget(prevItem)
            prevXpos = widget.ui.dsbRobotStartPosX.value()
            prevXstep = widget.ui.dsbRobotStartPosX.singleStep()
            prevYpos = widget.ui.dsbRobotStartPosY.value()
            prevYstep = widget.ui.dsbRobotStartPosY.singleStep()
            row.SetStartPosition(prevXpos + prevXstep, prevYpos + prevYstep)

        # 리스트뷰에 로봇 위젯 셋
        lstRobot.setItemWidget(item, row)

    # 로봇 삭제
    def DeleteRobot(self):
        listItems=self.ui.lstwRobots.selectedItems()
        if not listItems: return        
        for item in listItems:
            self.ui.lstwRobots.takeItem(self.ui.lstwRobots.row(item))
            self.ui.lstwRobots.clearSelection()

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
        world_sub.robotStartXYZ = [1, 1, 0,	  0, 1, 0]
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
                        thumbPath = world_sub.thumbPath
                        pixmap = QPixmap(thumbPath)
                        scaled_pixmap = pixmap.scaledToWidth(self.ui.lbWorldImage.width())
                        self.ui.lbWorldImage.setPixmap(scaled_pixmap)
                        self.setCurrentWorld(world.categoryMain, world_sub.categorySub.value)
                        self.m_simulator.worldFileType = world_sub.extention

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

# 메인 실행
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
