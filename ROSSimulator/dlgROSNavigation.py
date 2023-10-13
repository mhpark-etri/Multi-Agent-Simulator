######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : Navigation Dialog                                ##
######################################################
import os
from PySide6 import QtWidgets
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QFileDialog, QMessageBox
from ui_dlgROSNavigation import Ui_DlgROSNavigation
import yaml

from constant import *
from simulator import *

class DialogNavigation(
    QtWidgets.QDialog):
    # member
    m_simulator = Simulator()                       # Simulator
    # 기본 맵 저장 경로
    m_mapDefaultPath = ""

    # Init
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSNavigation()
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
            self.ui.cbROSNaviRobots.addItem(item)

        # 2. Option 설정

        # 이벤트 연결
        self.ui.btnROSNaviMapOpen.clicked.connect(self.OpenMap)
        self.ui.btnROSNavigationStart.clicked.connect(self.StartNavigation)


    # Navigation Map Open
    def OpenMap(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly 
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", self.m_mapDefaultPath, "YAML Files (*.yaml)", options=options
        )

        if file_name:
            print("Selected file:", file_name)
            # 이미지 열기
            with open(file_name, "r") as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
                if "image" in yaml_data:
                    image_path = yaml_data["image"]
                    image = QImage(image_path)
                    pixmap = QPixmap.fromImage(image, Qt.ImageConversionFlag.AutoColor)
                    pixmapScaled = pixmap.scaled(self.ui.lbROSNavigationMapImg.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.ui.lbROSNavigationMapImg.setPixmap(pixmapScaled)
            # 경로 입력
            self.ui.ledtROSNaviMapPath.setText(file_name)
              
    # Navigation 시작
    def StartNavigation(self):
        # 맵 경로 획득
        mapPath = self.ui.ledtROSNaviMapPath.text()
        if mapPath == "" :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("맵 파일을 먼저 선택해 주세요")
            msg.setWindowTitle("경고")
            msg.exec_()
            return

        # 모델 리스트 획득
        arrRobotsName = [self.ui.cbROSNaviRobots.itemText(index) for index in range(self.ui.cbROSNaviRobots.count())]
        
        # 무결성 체크
        # Slam은 같은 제조사의 로봇들 끼리만 동작 하도록 하는 것을 기본 전제로 한다
        robotLabel = self.ui.cbROSNaviRobots.currentText()
        robotName = robotLabel[:len(robotLabel) - 1]
        robotIdx = robotLabel[-1:]

        if robotName == CMD_LOCOBOT_MODEL:
        # TODO : 로코봇 Slam 실행
            pass
        elif robotName == CMD_TURTLEBOT3_DEFAULT_NAME:
            # Buger
            if self.m_simulator.robots[int(robotIdx)].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER:
                # 터틀봇 버거 Slam 실행
                command = CMD_ROS_COMMON_EXPORT + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_MODEL + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE
                # command = command + CMD_ROS_COMMON_ROS_NAMESPACE + label + CMD_COMMON_SPACE + CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP_KEY
                command = command + CMD_ROS_COMMON_ROSLAUNCH + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION_LAUNCH + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_MAP_FILE + CMD_COMMON_PARAM_INSERT + mapPath
                os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)

            # Waffle
            elif self.m_simulator.robots[int(robotIdx)].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE:
                # 터틀봇 Waffle Slam 실행
                command = CMD_ROS_COMMON_EXPORT + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_MODEL + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE
                # command = command + CMD_ROS_COMMON_ROS_NAMESPACE + label + CMD_COMMON_SPACE + CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP_KEY
                command = command + CMD_ROS_COMMON_ROSLAUNCH + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION_LAUNCH + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_MAP_FILE + CMD_COMMON_PARAM_INSERT + mapPath
                os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)

        elif robotName == CMD_JETBOT_DEFAULT_NAME:
            # TODO : Jet bot....
            pass

        # 마지막 열어본 파일 경로 저장


    # 마지막으로 저장 된 Map 파일 경로 호출
    def Load_Map_Path(self):

        lastSavedMathPath = self.settings.value(SETTING_PATH_NAVIGATION_SAVED_MAP_PATH)
        if lastSavedMathPath is not None:
            self.m_mapDefaultPath = lastSavedMathPath
        else:
            path = os.getcwd() + "/" + MAP_FOLDER_NAME
            os.makedirs(path, exist_ok=True)
            self.m_mapDefaultPath = path

    # 현재 Map 파일 경로 저장
    def Savel_Map_Path(self):
        if self.m_mapDefaultPath is not None:
            self.settings.setValue(SETTING_PATH_NAVIGATION_SAVED_MAP_PATH, self.m_mapDefaultPath)

    def showModal(self):
        return super().exec_()