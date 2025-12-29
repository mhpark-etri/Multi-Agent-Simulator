######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                      ## 
## 설명 : Image-to-Image Enhancement 세팅 다이얼로그    ##
######################################################
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox
from dlgROSI2I_ui import Ui_DlgROSI2I
import copy
import socket
import rospy
from pathlib import Path

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from constant import *
from simulator import *

PATH_I2I_SCRIPT = "/root/tesla/I2I_Simulator/infer.py"
PATH_I2I_RESULT_ORGIN = "/root/tesla/I2I_Simulator/result/origin"
PATH_I2I_RESULT_ENHANCED = "/root/tesla/I2I_Simulator/result/enhanced"

## 이미지 캡쳐 스레드
class EnhancedImageThread(QThread):
    image_received = Signal(object)  # cv2 image 전달

    def __init__(self, topic_name):
        super().__init__()
        self.topic_name = topic_name
        self.bridge = CvBridge()
        self.running = True

    def run(self):
        rospy.Subscriber(self.topic_name, Image, self.callback)
        rospy.spin()

    def callback(self, msg):
        if not self.running:
            return
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.image_received.emit(cv_image)

    def stop(self):
        self.running = False
        rospy.signal_shutdown("Thread stopped")

## 메인 클래스
class DialogROSI2I(
    QtWidgets.QDialog):
    # Init
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSI2I()
        self.ui.setupUi(self)

        self.m_simulator = copy.deepcopy(rosInfo)
        self.enhanced_jpg_list = []

        # 이벤트 연결
        self.ui.cbROSI2IName.currentIndexChanged.connect(self.SetRobotInfo)
        self.ui.btnROSI2IStart.clicked.connect(self.StartROSI2I)
        
        # 초기엔 Start 불가
        self.ui.btnROSI2IStart.setEnabled(False)

    # Dialog 활성화
    def showEvent(self, event):
        super().showEvent(event)

        self.SetRobotsInfoToCombo(self.m_simulator.robots)

    # 로봇 정보를 이용해 콤보박스에 정보 입력
    def SetRobotsInfoToCombo(self, robots):
        for i in range(len(robots)):
            # 로봇명
            name = robots[i].name
            self.ui.cbROSI2IName.addItem(name)

        # 첫번째 정보로 셋
        self.SetRobotInfo(0)

    # 로봇 정보 패널에 입력
    def SetRobotInfo(self, index):
        robot = self.m_simulator.robots[index]

        # 썸네일
        thumbPath = ENUM_ROBOT_TYPE.LOCOBOT
        if robot.type == ENUM_ROBOT_TYPE.LOCOBOT:
            thumbPath = CONST_LOCOBOT_PATH
        elif robot.type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER:
            thumbPath = CONST_TURTLEBOT3_BURGER_PATH
        elif robot.type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE:
            thumbPath = CONST_TURTLEBOT3_WAFFLE_PATH
        elif robot.type == ENUM_ROBOT_TYPE.INTERBOTIX:
            thumbPath = CONST_INTERBOTIX_PATH
        elif robot.type == ENUM_ROBOT_TYPE.UNI050_BASE:
            thumbPath = CONST_UNI_PATH 
        elif robot.type == ENUM_ROBOT_TYPE.HELLO_ROBOT_STRETCH:
            thumbPath = CONST_HELLO_STRETCH2_PATH

        # Set thumb image and robot name
        pixmap = QtGui.QPixmap(thumbPath)
        label_size = self.ui.lbROSI2IRobotThumb.size()
        scaled_pixmap = pixmap.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.ui.lbROSI2IRobotThumb.setPixmap(scaled_pixmap)

        # 네임스페이스 (현재는 로봇 이름이 곧 네임스페이스다)
        self.ui.lbROSI2INameSpace.setText(robot.name)

        # 모든 topic list 가져오기
        rospy.init_node('topic_list_printer', anonymous=True)
        topics = rospy.get_published_topics()
        topicName = "/" + robot.name
        filtered_topics = [topic for topic, _ in topics if topic.startswith(topicName)]

        # topic list widget에 입력
        bHasImageRaw = False
        self.ui.lstwROSI2ITopicList.clear()  # 기존 목록을 지워 초기화
        for topic in filtered_topics:
            print("topic : " + str(topic))
            item = QtWidgets.QListWidgetItem(topic)
            # 특정 토픽 이름 포함 시 강조
            if topic.endswith("/image_raw"):
                item.setBackground(QColor("yellow"))  # 배경색을 노란색으로 설정
                bHasImageRaw = True
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)  # 선택 불가능하게 설정
            self.ui.lstwROSI2ITopicList.addItem(item)

        # topic List 중 image_raw가 없다면 실행 불가
        if bHasImageRaw == True :
            self.ui.btnROSI2IStart.setEnabled(True)
        else:
            self.ui.btnROSI2IStart.setEnabled(False)

    # I2I 작업 시작
    def StartROSI2I(self):
        ## 변경된 부분 -> 스크립트 형태로 실행
        # 1. Image 저장 경로를 가져오고
        path_origin = Path(PATH_I2I_RESULT_ORGIN)
        if path_origin.exists():
            if path_origin.is_dir():
                print(f"[OK] origin 폴더가 이미 존재: {path_origin}")
            else:
                raise RuntimeError(f"[ERROR] origin 경로는 존재하지만 폴더가 아님(파일 등): {path_origin}")
        else:
            # 중간 경로까지 함께 생성, 이미 있으면 에러 없이 통과
            path_origin.mkdir(parents=True, exist_ok=True)
            print(f"[CREATE] origin 폴더 생성: {path_origin}")

        path_enhanced = Path(PATH_I2I_RESULT_ENHANCED)
        if path_enhanced.exists():
            if path_enhanced.is_dir():
                print(f"[OK] enhanced 폴더가 이미 존재: {path_enhanced}")
            else:
                raise RuntimeError(f"[ERROR] enhanced 경로는 존재하지만 폴더가 아님(파일 등): {path_enhanced}")
        else:
            # 중간 경로까지 함께 생성, 이미 있으면 에러 없이 통과
            path_enhanced.mkdir(parents=True, exist_ok=True)
            print(f"[CREATE] enhanced 폴더 생성: {path_enhanced}")

        selected_items = self.ui.lstwROSI2ITopicList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No topic selected")
            return

        ## 로봇 카메라 이미지 저장 스레드 시작
        topic = selected_items[0].text()

        self.image_thread = EnhancedImageThread(topic)
        self.image_thread.image_received.connect(self.OnImageReceived)
        self.image_thread.start()

        self.accept()

    # 이미지 처리 루틴
    def OnImageReceived(self, cv_image):
        # 스크립트 실행
        path_script = PATH_I2I_SCRIPT
        pass

    def showModal(self):
        return super().exec_()