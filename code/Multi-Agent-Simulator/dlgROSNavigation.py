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
import copy
import yaml

from constant import *
from simulator import *

class DialogNavigation(
    QtWidgets.QDialog):
    # Init
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSNavigation()
        self.ui.setupUi(self)

        self.m_orgRosInfo = rosInfo
        self.m_simulator = copy.deepcopy(rosInfo)
        self.m_currentSimulatorIdx = 0
        # 기본 맵 저장 경로
        self.m_mapDefaultPath = ""

        # Preference
        self.settings = QSettings(SETTING_COMPANY, SETTING_APP)  # 설정 파일 이름 설정
        self.Load_Map_Path()

        # UI 생성
        self.CreateSelectRobotPanel()

        # 이벤트 연결
        self.ui.btnROSNaviMapOpen.clicked.connect(self.OpenMap)
        self.ui.btnROSNavigationStart.clicked.connect(self.Setting)
        self.ui.btnROSNavigationCancel.clicked.connect(self.Cancel)
        self.ui.cbROSNaviRobots.currentIndexChanged.connect(self.onRobotChanged)
        self.ui.ledtROSNaviRobotsPosX.textChanged.connect(self.onRobotPosXChanged)
        self.ui.ledtROSNaviRobotsPosY.textChanged.connect(self.onRobotPosYChanged)
        self.ui.ledtROSNaviRobotsPosZ.textChanged.connect(self.onRobotPosZChanged)

    # 로봇 정보를 이용해 로봇에 Navigation 정보를 입력한다
    def CreateSelectRobotPanel(self):
        # 1. 로봇 대수 별로 콤보박스 생성
        robotCount = len(self.m_simulator.robots)
        for i in range(0, robotCount):
            name = self.m_simulator.robots[i].name
            self.ui.cbROSNaviRobots.addItem(name)

        # 2. Option 설정
        self.m_currentSimulatorIdx = 0
        posX = float(self.m_simulator.robots[0].startX)
        posY = float(self.m_simulator.robots[0].startY)
        posZ = float(self.m_simulator.robots[0].startZ)
        self.ui.ledtROSNaviRobotsPosX.setText(f"{posX:.1f}")
        self.ui.ledtROSNaviRobotsPosY.setText(f"{posY:.1f}")
        self.ui.ledtROSNaviRobotsPosZ.setText(f"{posZ:.1f}")

        # 3. Navigation 맵 설정
        mapPath = self.m_simulator.ros_navigation_map_path
        if mapPath:
            with open(mapPath, "r") as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
                if "image" in yaml_data:
                    file_directory = os.path.dirname(mapPath)
                    image_path = os.path.join(file_directory, yaml_data["image"])
                    image = QImage(image_path)
                    pixmap = QPixmap.fromImage(image, Qt.ImageConversionFlag.AutoColor)
                    label_size = self.ui.lbROSNavigationMapImg.size()
                    scaled_pixmap = pixmap.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.ui.lbROSNavigationMapImg.setPixmap(scaled_pixmap)
                    self.adjustSize()

            # 경로 입력
            self.ui.ledtROSNaviMapPath.setText(mapPath)
            self.Savel_Map_Path(mapPath)

    # 로봇 정보 변경
    def onRobotChanged(self, index):
        self.m_currentSimulatorIdx = index
        # X,Y,Z 포지션 정보 업데이트
        posX = float(self.m_simulator.robots[index].startX)
        posY = float(self.m_simulator.robots[index].startY)
        posZ = float(self.m_simulator.robots[index].startZ)
        self.ui.ledtROSNaviRobotsPosX.setText(f"{posX:.1f}")
        self.ui.ledtROSNaviRobotsPosY.setText(f"{posY:.1f}")
        self.ui.ledtROSNaviRobotsPosZ.setText(f"{posZ:.1f}")
    
    # X,Y,Z 값 변경
    def onRobotPosXChanged(self, text):
        if self.CheckIsNumber(text):
            self.m_simulator.robots[self.m_currentSimulatorIdx].startX = text
        else:
            self.ShowWarningMsg("You can only enter numbers.")
    def onRobotPosYChanged(self, text):
        if self.CheckIsNumber(text):
            self.m_simulator.robots[self.m_currentSimulatorIdx].startY = text
        else:
            self.ShowWarningMsg("You can only enter numbers.")
    def onRobotPosZChanged(self, text):
        if self.CheckIsNumber(text):
            self.m_simulator.robots[self.m_currentSimulatorIdx].startZ = text
        else:
            self.ShowWarningMsg("You can only enter numbers.")

    # 숫자인지 점검
    def CheckIsNumber(self, text):
        try:
            # float로 변환 가능하면 숫자
            float(text)
            return True
        except ValueError:
            # 변환할 수 없으면 숫자가 아님
            return False

    # 경고창 출력
    def ShowWarningMsg(self, msg):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Warning")
        msg_box.setText(msg)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

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
                    file_directory = os.path.dirname(file_name)
                    image_path = os.path.join(file_directory, yaml_data["image"])
                    image = QImage(image_path)
                    pixmap = QPixmap.fromImage(image, Qt.ImageConversionFlag.AutoColor)
                    pixmapScaled = pixmap.scaled(self.ui.lbROSNavigationMapImg.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.ui.lbROSNavigationMapImg.setPixmap(pixmapScaled)
            # 경로 입력
            self.ui.ledtROSNaviMapPath.setText(file_name)
            self.Savel_Map_Path(file_name)
              
    # 세팅 정보 저장
    def Setting(self):
        # 맵 경로 획득
        mapPath = self.ui.ledtROSNaviMapPath.text()
        if mapPath == "" :
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("맵 파일을 먼저 선택해 주세요")
            msg.setWindowTitle("경고")
            msg.exec_()
            return
        self.m_orgRosInfo.ros_navigation_map_path = mapPath

        # 내부 시뮬레이터 정보를 main 정보에 저장
        for i in range(0, len(self.m_simulator.robots)) :
            self.m_orgRosInfo.robots[i].startX = self.m_simulator.robots[i].startX
            self.m_orgRosInfo.robots[i].startY = self.m_simulator.robots[i].startY
            self.m_orgRosInfo.robots[i].startZ = self.m_simulator.robots[i].startZ

        self.close()

        # # 모델 리스트 획득
        # arrRobotsName = [self.ui.cbROSNaviRobots.itemText(index) for index in range(self.ui.cbROSNaviRobots.count())]
        
        # # 무결성 체크
        # # Navigation 같은 제조사의 로봇들 끼리만 동작 하도록 하는 것을 기본 전제로 한다
        # robotLabel = self.ui.cbROSNaviRobots.currentText()
        # robotName = robotLabel[:len(robotLabel) - 1]
        # robotIdx = robotLabel[-1:]

        # if robotName == CMD_LOCOBOT_MODEL:
        # # TODO : 로코봇 Navigation 실행
        #     pass
        # elif robotName == CMD_TURTLEBOT3_DEFAULT_NAME:
        #     # Buger
        #     if self.m_simulator.robots[int(robotIdx)].type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER:
        #         # 터틀봇 버거 Slam 실행
        #         command = CMD_ROS_COMMON_EXPORT + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_MODEL + CMD_TURTLEBOT3_MODEL_BURGER + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE
        #         # command = command + CMD_ROS_COMMON_ROS_NAMESPACE + label + CMD_COMMON_SPACE + CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP_KEY
        #         command = command + CMD_ROS_COMMON_ROSLAUNCH + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION_LAUNCH + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_MAP_FILE + CMD_COMMON_PARAM_INSERT + mapPath
        #         # os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)
            

        #     # Waffle
        #     elif self.m_simulator.robots[int(robotIdx)].type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE:
        #         # 터틀봇 Waffle Slam 실행
        #         command = CMD_ROS_COMMON_EXPORT + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_MODEL + CMD_TURTLEBOT3_MODEL_WAFFLE + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE
        #         # command = command + CMD_ROS_COMMON_ROS_NAMESPACE + label + CMD_COMMON_SPACE + CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP + CMD_COMMON_SPACE + CMD_ROS_TURTLEBOT3_TELEOP_KEY
        #         command = command + CMD_ROS_COMMON_ROSLAUNCH + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_TURTLEBOT3_NAVIGATION_LAUNCH + CMD_COMMON_SPACE + CMD_ROS_NAVIGATION_MAP_FILE + CMD_COMMON_PARAM_INSERT + mapPath
        #         # os.system(CMD_EXCUTE_CMD_OPEN + command + CMD_EXCUTE_CMD_CLOSE)

        # elif robotName == CMD_JETBOT_DEFAULT_NAME:
        #     # TODO : Jet bot....
        #     pass


    # 작업 취소
    def Cancel(self):
        self.close()

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
    def Savel_Map_Path(self, path):
        if path is not None:
            self.settings.setValue(SETTING_PATH_NAVIGATION_SAVED_MAP_PATH, path)

    def showModal(self):
        return super().exec_()