######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                      ##
## 설명 : Image-to-Image Enhancement 세팅 다이얼로그    ##
######################################################

import copy
import subprocess
import time
from pathlib import Path

import cv2
import rospy
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt, QThread, Signal, QMutex, QWaitCondition
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from dlgROSI2I_ui import Ui_DlgROSI2I
from constant import *
from simulator import *


PATH_I2I_SCRIPT = "/root/tesla/I2I_Simulator/infer.py"
PATH_I2I_RESULT_ORGIN = "/root/tesla/I2I_Simulator/result/origin"
PATH_I2I_RESULT_ENHANCED = "/root/tesla/I2I_Simulator/result/enhanced"


# -----------------------------------------------------------------------------
# 1) ROS 이미지 캡쳐 스레드 (topic 구독 → cv2 이미지 emit)
#    - rospy.spin() 대신 자체 루프로 살아있게 유지하여 stop()이 확실히 먹게 구성
#    - stop()에서 signal_shutdown 하지 않음 (프로세스 전체 ROS 종료 방지)
# -----------------------------------------------------------------------------
class EnhancedImageThread(QThread):
    image_received = Signal(object)   # cv2 image (numpy.ndarray)

    def __init__(self, topic_name: str, parent=None):
        super().__init__(parent)
        self.topic_name = topic_name
        self.bridge = CvBridge()
        self.running = True
        self._sub = None

    def run(self):
        # Subscriber 등록
        self._sub = rospy.Subscriber(self.topic_name, Image, self.callback, queue_size=1)

        rate = rospy.Rate(30)  # 30Hz 정도로 유지(콜백은 ROS 내부 스레드에서 들어옴)
        while self.running and not rospy.is_shutdown():
            try:
                rate.sleep()
            except rospy.ROSInterruptException:
                break

        # 종료 시 구독 해제
        if self._sub is not None:
            try:
                self._sub.unregister()
            except Exception:
                pass
            self._sub = None

    def callback(self, msg: Image):
        if not self.running:
            return
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            self.image_received.emit(cv_image)
        except Exception:
            # 변환 실패 시 무시 (필요하면 error signal 추가 가능)
            pass

    def stop(self):
        self.running = False


# -----------------------------------------------------------------------------
# 2) captured_jpg_list에 새로 append되는 이미지를 "계속" 처리하는 스레드
#    - 핵심: 리스트는 계속 append 되므로, 새 요소가 생기면 작업 지속
#    - 동기화: QMutex + QWaitCondition 사용 (폴링 X, CPU 낭비 최소)
# -----------------------------------------------------------------------------
class ImageEnhanceThread(QThread):
    # 처리된 결과를 UI로 넘기고 싶으면 사용(예: 원본 저장 경로, 인덱스)
    processed = Signal(str, int)   # (saved_origin_path, index)
    log = Signal(str)

    def __init__(self, shared_list, mutex: QMutex, cond: QWaitCondition,
                 origin_dir: str, enhanced_dir: str, script_path: str, parent=None):
        super().__init__(parent)
        self.shared_list = shared_list
        self.mutex = mutex
        self.cond = cond

        self.origin_dir = Path(origin_dir)
        self.enhanced_dir = Path(enhanced_dir)
        self.script_path = script_path

        self.running = True
        self.next_index = 0  # 여기부터 새 항목 처리

    def reset(self, clear_list: bool = False):
        """재시작/재사용 시 인덱스 및 (선택적으로) 리스트 초기화."""
        self.mutex.lock()
        try:
            if clear_list:
                self.shared_list.clear()
            self.next_index = 0
            self.cond.wakeAll()
        finally:
            self.mutex.unlock()

    def run(self):
        # 디렉토리 확보
        self.origin_dir.mkdir(parents=True, exist_ok=True)
        self.enhanced_dir.mkdir(parents=True, exist_ok=True)

        while self.running and not rospy.is_shutdown():
            # 1) 새 데이터 올 때까지 대기
            self.mutex.lock()
            try:
                while self.running and self.next_index >= len(self.shared_list):
                    self.cond.wait(self.mutex)

                if not self.running:
                    return

                img = self.shared_list[self.next_index]
                idx = self.next_index
                self.next_index += 1
            finally:
                self.mutex.unlock()

            # 2) 여기서 img 처리 (락 밖에서!)
            #    예시: origin 폴더에 jpg 저장 + (원하면) infer 스크립트 실행
            try:
                # 파일명(충돌 방지: index + timestamp)
                ts = int(time.time() * 1000)
                origin_path = self.origin_dir / f"origin_{idx:06d}_{ts}.jpg"

                # img가 numpy array(OpenCV)라면 imwrite 가능
                ok = cv2.imwrite(str(origin_path), img)
                if not ok:
                    self.log.emit(f"[WARN] 저장 실패: {origin_path}")
                    continue

                # ---- (선택) Enhance 스크립트 실행 ----
                # infer.py 인자 형식이 확실하지 않아 기본 형태만 예시로 둡니다.
                # 프로젝트 infer.py에 맞게 args를 수정하세요.
                #
                # 예)
                # cmd = ["python3", self.script_path, "--input", str(origin_path), "--output", str(self.enhanced_dir)]
                # subprocess.run(cmd, check=False)

                self.processed.emit(str(origin_path), idx)

            except Exception as e:
                self.log.emit(f"[ERROR] 처리 중 예외: {e}")

    def stop(self):
        self.running = False
        self.cond.wakeAll()


# -----------------------------------------------------------------------------
# 3) 메인 다이얼로그
# -----------------------------------------------------------------------------
class DialogROSI2I(QtWidgets.QDialog):
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSI2I()
        self.ui.setupUi(self)

        self.m_simulator = copy.deepcopy(rosInfo)

        # 공유 데이터(캡쳐된 이미지 리스트)
        self.captured_jpg_list = []

        # 스레드 동기화 도구
        self.captured_mutex = QMutex()
        self.captured_cond = QWaitCondition()

        # 스레드 핸들
        self.image_thread = None
        self.enhance_thread = None

        # ROS init (프로세스에서 1회만)
        # Qt 앱과 같이 쓸 때 보통 disable_signals=True가 안전합니다.
        if not rospy.core.is_initialized():
            rospy.init_node("dlg_ros_i2i", anonymous=True, disable_signals=True)

        # 이벤트 연결
        self.ui.cbROSI2IName.currentIndexChanged.connect(self.SetRobotInfo)
        self.ui.btnROSI2IStart.clicked.connect(self.StartROSI2I)

        # 초기엔 Start 불가
        self.ui.btnROSI2IStart.setEnabled(False)

    def showEvent(self, event):
        super().showEvent(event)
        self.SetRobotsInfoToCombo(self.m_simulator.robots)

    def closeEvent(self, event):
        # 다이얼로그가 닫힐 때 스레드 정리
        self.StopThreads()
        super().closeEvent(event)

    # 로봇 정보를 이용해 콤보박스에 정보 입력
    def SetRobotsInfoToCombo(self, robots):
        self.ui.cbROSI2IName.blockSignals(True)
        self.ui.cbROSI2IName.clear()
        for r in robots:
            self.ui.cbROSI2IName.addItem(r.name)
        self.ui.cbROSI2IName.blockSignals(False)

        # 첫번째 정보로 셋
        if robots:
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

        # thumb image
        pixmap = QtGui.QPixmap(thumbPath)
        label_size = self.ui.lbROSI2IRobotThumb.size()
        scaled_pixmap = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.ui.lbROSI2IRobotThumb.setPixmap(scaled_pixmap)

        # 네임스페이스
        self.ui.lbROSI2INameSpace.setText(robot.name)

        # topic list 가져오기
        try:
            topics = rospy.get_published_topics()
        except Exception:
            topics = []

        topic_prefix = "/" + robot.name
        filtered_topics = [t for t, _ in topics if t.startswith(topic_prefix)]

        bHasImageRaw = False
        self.ui.lstwROSI2ITopicList.clear()
        for topic in filtered_topics:
            item = QtWidgets.QListWidgetItem(topic)
            if topic.endswith("/image_raw"):
                item.setBackground(QColor("yellow"))
                bHasImageRaw = True
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.ui.lstwROSI2ITopicList.addItem(item)

        self.ui.btnROSI2IStart.setEnabled(bHasImageRaw)

    # I2I 작업 시작
    def StartROSI2I(self):
        # 저장 폴더 생성 보장
        path_origin = Path(PATH_I2I_RESULT_ORGIN)
        if path_origin.exists() and not path_origin.is_dir():
            raise RuntimeError(f"[ERROR] origin 경로는 존재하지만 폴더가 아님(파일 등): {path_origin}")
        path_origin.mkdir(parents=True, exist_ok=True)

        path_enhanced = Path(PATH_I2I_RESULT_ENHANCED)
        if path_enhanced.exists() and not path_enhanced.is_dir():
            raise RuntimeError(f"[ERROR] enhanced 경로는 존재하지만 폴더가 아님(파일 등): {path_enhanced}")
        path_enhanced.mkdir(parents=True, exist_ok=True)

        # 토픽 선택 확인
        selected_items = self.ui.lstwROSI2ITopicList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No topic selected")
            return
        topic = selected_items[0].text()

        # 이미 돌고 있던 스레드 있으면 종료(중복 방지)
        self.StopThreads()

        # 1) 리스트 처리(Enhance) 스레드 시작
        self.enhance_thread = ImageEnhanceThread(
            shared_list=self.captured_jpg_list,
            mutex=self.captured_mutex,
            cond=self.captured_cond,
            origin_dir=PATH_I2I_RESULT_ORGIN,
            enhanced_dir=PATH_I2I_RESULT_ENHANCED,
            script_path=PATH_I2I_SCRIPT,
            parent=self
        )
        self.enhance_thread.processed.connect(self.OnEnhancedOneProcessed)
        self.enhance_thread.log.connect(self.OnEnhanceLog)
        self.enhance_thread.finished.connect(self.OnImageEnhanceThreadFinished)
        self.enhance_thread.finished.connect(self.enhance_thread.deleteLater)
        self.enhance_thread.start()

        # 2) ROS 캡쳐 스레드 시작
        self.image_thread = EnhancedImageThread(topic, parent=self)
        self.image_thread.image_received.connect(self.OnImageReceived)
        self.image_thread.finished.connect(self.OnImageCaptureThreadFinished)
        self.image_thread.finished.connect(self.image_thread.deleteLater)
        self.image_thread.start()

        # 다이얼로그 닫기(OK)
        self.accept()

    # ROS로부터 이미지 수신 시: 리스트에 추가 + 조건변수로 enhance 스레드 깨우기
    def OnImageReceived(self, cv_image):
        self.captured_mutex.lock()
        try:
            # “캡쳐 순간”을 보존하려면 copy() 권장
            self.captured_jpg_list.append(cv_image.copy())
            self.captured_cond.wakeOne()
        finally:
            self.captured_mutex.unlock()

    # enhance 스레드가 이미지 1장 처리했을 때 콜백(원본 저장 경로, index)
    def OnEnhancedOneProcessed(self, origin_path: str, index: int):
        # 필요하면 UI 업데이트 / 로그 / 진행률 업데이트
        # print(f"[ENHANCE] processed index={index}, origin={origin_path}")
        pass

    def OnEnhanceLog(self, msg: str):
        print(msg)

    # 캡쳐 스레드 종료 시
    def OnImageCaptureThreadFinished(self):
        print("이미지 캡쳐 스레드 종료됨")
        # 캡쳐 스레드 종료했다고 리스트를 바로 clear 하면
        # Enhance 스레드가 아직 처리 중인 항목이 날아갈 수 있음
        # 필요하면 “전체 종료 시점”에만 clear 하도록 정책을 정하세요.

    # enhance 스레드 종료 시
    def OnImageEnhanceThreadFinished(self):
        print("이미지 Enhance 스레드 종료됨")

        # 여기서 전역 메모리 비활성화(원하면)
        self.captured_mutex.lock()
        try:
            self.captured_jpg_list.clear()
        finally:
            self.captured_mutex.unlock()

    def StopThreads(self):
        # 1) 캡쳐 스레드 종료
        if self.image_thread is not None and self.image_thread.isRunning():
            self.image_thread.stop()
            self.image_thread.wait()

        # 2) enhance 스레드 종료
        if self.enhance_thread is not None and self.enhance_thread.isRunning():
            self.enhance_thread.stop()
            self.enhance_thread.wait()

        self.image_thread = None
        self.enhance_thread = None

    def showModal(self):
        # PySide6에서는 exec()가 기본입니다.
        return super().exec()
