######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                      ## 
## 설명 : Image-to-Image Enhancement 세팅 다이얼로그    ##
######################################################
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox
from dlgROSI2I_ui import Ui_DlgROSI2I
import copy
import rospy
import socket
from flask import Flask, jsonify

from constant import *
from simulator import *

# Flask 애플리케이션 초기화
app = Flask(__name__)
# FlaskThread 인스턴스를 전역 변수로 선언
flask_thread = None
# FlaskThread 클래스 정의
class FlaskThread(QThread):
    def __init__(self, portNum, topicImageRaw):
        super().__init__()
        self.portNum = portNum  # 포트 번호 저장
        self.topicImageRaw = topicImageRaw  # 토픽 이미지를 저장

    def run(self):
        with app.app_context():
            app.run(debug=True, host='0.0.0.0', port=self.portNum, use_reloader=False)  # reloader를 비활성화합니다.

# API 경로를 수정하여 전달된 topic_image_raw를 사용합니다.
@app.route('/get_topic_image_raw', methods=['GET'])
def get_topic_image_raw():
    return jsonify({"message": flask_thread.topicImageRaw})  # FlaskThread 인스턴스의 topicImageRaw를 반환합니다.

class DialogROSI2I(
    QtWidgets.QDialog):
    # Init
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSI2I()
        self.ui.setupUi(self)

        self.m_simulator = copy.deepcopy(rosInfo)
        self.m_RESTportNum = 5000
        self.server_thread = None
        self.server_running = False  # 서버 상태 플래그

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
        selected_items = self.ui.lstwROSI2ITopicList.selectedItems()
        topicImageRaw = ""
        if selected_items:
            topicImageRaw = selected_items[0].text()
        else:
            # 선택된 아이템이 없을 때 경고 메시지 표시
            QtWidgets.QMessageBox.warning(self, 'Warning', "No item is selected. Please select a topic.", QtWidgets.QMessageBox.Ok)
            return
    
        ## Rest API 더이상 사용 안할 예정
        # # 1. Rest API Server 실행
        # if self.is_port_in_use(self.m_RESTportNum):
        #     QtWidgets.QMessageBox.warning(self, 'Warning', f"Server is already running on port {self.m_RESTportNum}.", QtWidgets.QMessageBox.Ok)
        #     return

        # if not self.server_running:
        #     # Flask 서버를 QThread로 실행
        #     global flask_thread  # 전역 변수를 사용합니다.
        #     flask_thread = FlaskThread(self.m_RESTportNum, topicImageRaw)
        #     flask_thread.start()
        #     self.server_running = True
        #     print(f"Server is running. Access it at http://localhost:{self.m_RESTportNum}/get_topic_image_raw")

        ## 변경된 부분 -> 스크립트 형태로 실행
        # 1. Image 저장 경로를 가져오고
        # 2. 해당 경로에 Image가 있을 때 마다 실행
        # 3. 텍스트 버퍼를 하나 만들어 거기에 작업했던 이미지 파일명을 저장 해두고 버퍼 비교해서 없으면 실행

        self.accept()

    def showModal(self):
        return super().exec_()
    

    ## Rest API 관련 ##
    # 서버가 이미 실행 중인지 확인
    def is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(('localhost', port)) == 0