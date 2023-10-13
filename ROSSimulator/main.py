######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : 3D Agent Simulator 프로그램의 main 스크립트 ##
######################################################
import os
import copy
import subprocess
import threading
from datetime import datetime   
from PySide6 import QtWidgets
from ui_main import Ui_MainWindow
from dlgROSTeleop import DialogTeleop
from dlgROSSlam import DialogSmal
from dlgROSNavigation import DialogNavigation
from dlgROSRViz import DialogRViz
from widgetRobotItem import WidgetRobotItem
import atexit

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
MAX_MODEL_COUNT = 2  # Max model count

class MainWindow(QtWidgets.QMainWindow):
    
    # member
    m_simulator = Simulator()               # Simulator 

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
        self.btnGroupWorld = QtWidgets.QButtonGroup()
        self.btnGroupWorld.setExclusive(True)
        self.btnGroupWorld.addButton(self.ui.rbWorldWarehouse)
        self.btnGroupWorld.addButton(self.ui.rbWorldHospital)
        self.btnGroupWorld.addButton(self.ui.rbWorldSmallHouse)
        self.btnGroupWorld.addButton(self.ui.rbWorldBookStore)
        self.btnGroupWorld.buttonToggled.connect(self.WorldRadioButtonItemSelected)
        # Add & Delete Model
        self.ui.btnAddRobot.clicked.connect(self.AddRobot)
        self.ui.btnDeleteRobot.clicked.connect(self.DeleteRobot)
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
        # ROS = Navigation
        self.m_simulator.ros = ENUM_ROS_TYPE.NAVIGATION

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
            robot.startX = widget.ui.dsbRobotStartPosX.value()
            robot.startY = widget.ui.dsbRobotStartPosY.value()
            robot.startZ = widget.ui.dsbRobotStartPosZ.value()
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

        # 3. Launch 파일 제작
        self.m_simulator.robots = copy.deepcopy(lstRobots)
        launchFile = self.MakeLaunch(self.m_simulator)

        # 4. Launch 파일 실행
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
        if self.ui.lstwRobots.count() >= MAX_MODEL_COUNT : 
            req = QtWidgets.QMessageBox.question(self, 'Add Robot', 'The maximum number of allowed robots has been exceeded. (Max : ' + str(MAX_MODEL_COUNT) + ')',QtWidgets.QMessageBox.Ok)
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

# 메인 실행
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
