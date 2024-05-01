######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : Slam Dialog                                ##
######################################################
import os
import copy
from PySide6 import QtWidgets
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog, QMessageBox
from ui_dlgROSSlam import Ui_DlgROSSlam
import time

from constant import *
from simulator import *

class DialogSmal(
    QtWidgets.QDialog):
    # member
    m_simulator = Simulator()                       # Simulator
    # 기본 맵 저장 경로
    m_mapDefaultPath = ""
    # Init
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSSlam()
        self.ui.setupUi(self)
        self.m_simulator = rosInfo

        # Preference
        self.settings = QSettings(SETTING_COMPANY, SETTING_APP)  # 설정 파일 이름 설정
        self.Load_Map_Path()

        # UI 생성
        self.CreateSelectRobotPanel(self.ui)

    # 로봇 정보를 이용해 로봇에 Slam 정보를 입력한다
    def CreateSelectRobotPanel(self, ui):
        # 1. 로봇 대수 별로 콤보박스 생성
        robotCount = len(self.m_simulator.robots)
        for i in range(0, robotCount):
            item = self.m_simulator.robots[i].rosNamespace
            self.ui.cbSlamRobot.addItem(item)

        # 2. Slam Method 타입 지정
        self.ui.cbSlamMethod.addItem(CMD_ROS_SLAM_METHOD_GMAPPING)

        # 이벤트 연결
        self.ui.btnROSSlamStart.clicked.connect(self.StartSlam)
        self.ui.btnROSSlamSaveMap.clicked.connect(self.SaveMap)

    # Slam 시작
    def StartSlam(self):
        # 모델 리스트 획득
        arrRobotsName = [self.ui.cbSlamRobot.itemText(index) for index in range(self.ui.cbSlamRobot.count())]
        
        # 무결성 체크
        # Slam은 같은 제조사의 로봇들 끼리만 동작 하도록 하는 것을 기본 전제로 한다
        robotLabel = self.ui.cbSlamRobot.currentText()
        robotName = robotLabel[:len(robotLabel) - 1]
        robotIdx = robotLabel[-1:]

        # Option 지정
        option_slam_method = self.ui.cbSlamMethod.currentText()

        # 로봇별 Smal 실행
        if robotName == CMD_LOCOBOT_MODEL:
            # TODO : 로코봇 Slam 실행
            pass
        elif robotName == CMD_TURTLEBOT3_DEFAULT_NAME: 
            # Buger (https://emanual.robotis.com/docs/en/platform/turtlebot3/slam_simulation/)
            if self.m_simulator.robots[int(robotIdx)].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER:
                # 각 터틀봇의 Slam 실행
                for i in range(0, len(self.m_simulator.robots)) :
                    if self.m_simulator.robots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER :
                         robotNamespace = self.m_simulator.robots[i].rosNamespace 
                         command = CMD_ROS_COMMON_EXPORT + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_MODEL + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE 
                         command = command + CMD_ROS_COMMON_ROS_NAMESPACE + robotNamespace + CMD_COMMON_SPACE + CMD_ROS_COMMON_ROSLAUNCH + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_SLAM + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_GMAPPING_LAUNCH + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_SET_BASE_FRAME + CMD_COMMON_PARAM_INSERT + robotNamespace + CMD_COMMON_SLASH + CMD_ROS_SLAM_TURTLEBOT3_BASE_FOORPRINT + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_SET_ODOM_FRAME + CMD_COMMON_PARAM_INSERT + robotNamespace + CMD_COMMON_SLASH + CMD_ROS_SLAM_TURTLEBOT3_ODOM + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_SET_MAP_FRAME + CMD_COMMON_PARAM_INSERT + CMD_ROS_SLAM_TURTLEBOT3_MAP
                         os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)

                # 각 터틀봇의 맵 머징
                time.sleep(10)
                command = CMD_ROS_COMMON_ROSLAUNCH + CMD_COMMON_SPACE + CMD_TURTLEBOT3_GAZEBO + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_MULTI_MAP_MERGE_LAUNCH
                os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)

                # RViz 실행
                time.sleep(10)
                command = CMD_ROS_SLAM_TURTLEBOT3_RVIZ_FULL
                os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)

            # Waffle
            elif self.m_simulator.robots[int(robotIdx)].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE:
                # 각 터틀봇의 Slam 실행
                for i in range(0, len(self.m_simulator.robots)) :
                    if self.m_simulator.robots[i].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE :
                         robotNamespace = self.m_simulator.robots[i].rosNamespace 
                         command = CMD_ROS_COMMON_EXPORT + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_MODEL + CMD_TURTLEBOT3_MODEL_WAFFLE+ CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE 
                         command = command + CMD_ROS_COMMON_ROS_NAMESPACE + robotNamespace + CMD_COMMON_SPACE + CMD_ROS_COMMON_ROSLAUNCH + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_SLAM + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_GMAPPING_LAUNCH + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_SET_BASE_FRAME + CMD_COMMON_PARAM_INSERT + robotNamespace + CMD_COMMON_SLASH + CMD_ROS_SLAM_TURTLEBOT3_BASE_FOORPRINT + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_SET_ODOM_FRAME + CMD_COMMON_PARAM_INSERT + robotNamespace + CMD_COMMON_SLASH + CMD_ROS_SLAM_TURTLEBOT3_ODOM + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_SET_MAP_FRAME + CMD_COMMON_PARAM_INSERT + CMD_ROS_SLAM_TURTLEBOT3_MAP
                         os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)

                # 각 터틀봇의 맵 머징
                time.sleep(10)
                command = CMD_ROS_COMMON_ROSLAUNCH + CMD_COMMON_SPACE + CMD_TURTLEBOT3_GAZEBO + CMD_COMMON_SPACE + CMD_ROS_SLAM_TURTLEBOT3_MULTI_MAP_MERGE_LAUNCH
                os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)

                # RViz 실행
                time.sleep(10)
                command = CMD_ROS_SLAM_TURTLEBOT3_RVIZ_FULL
                os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)


        elif robotName == CMD_JETBOT_DEFAULT_NAME:
            # TODO : Jet bot....
            pass

    # Save map
    def SaveMap(self):
        filePath = self.SetMapPath()
        if filePath:
            command = CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_SLAM_MAP_SERVER + CMD_COMMON_SPACE + CMD_ROS_SLAM_MAP_SAVER + CMD_COMMON_SPACE + CMD_ROS_SLAM_MAP_OPTION_FILE_PATH + CMD_COMMON_SPACE + filePath
            os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)
            # 최종 경로 저장
            self.Savel_Map_Path()

    # 맵 저장 다이얼로그 호출
    def SetMapPath(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", self.m_mapDefaultPath, "All Files (*)", options=options)

        if file_name:
            print("Selected File Path:", file_name)
            return file_name
        else :
            return "" 

    # 마지막으로 저장 된 Slam 경로 호출
    def Load_Map_Path(self):

        lastSavedMathPath = self.settings.value(SETTING_PATH_SLAM_SAVED_MAP_PATH)
        if lastSavedMathPath is not None:
            self.m_mapDefaultPath = lastSavedMathPath
        else:
            path = os.getcwd() + "/" + MAP_FOLDER_NAME
            os.makedirs(path, exist_ok=True)
            self.m_mapDefaultPath = path

    # 현재 슬램 경로 저장
    def Savel_Map_Path(self):
        if self.m_mapDefaultPath is not None:
            self.settings.setValue(SETTING_PATH_SLAM_SAVED_MAP_PATH, self.m_mapDefaultPath)

    def showModal(self):
        return super().exec_()