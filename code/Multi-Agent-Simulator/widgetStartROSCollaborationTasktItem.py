######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                      ## 
## 설명 : 협업 태스크 로봇 아이템                        ##
######################################################
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QMessageBox
from widgetStartROSCollaborationTaskItem_ui import Ui_WidgetStartROSCollaborationTaskItem

from constant import *
from simulator import *

class WidgetStartROSCollaborationTaskItem(QtWidgets.QWidget):
    # Init
    def __init__(self, parent = None):
        super(WidgetStartROSCollaborationTaskItem, self).__init__(parent)
        self.ui = Ui_WidgetStartROSCollaborationTaskItem()
        self.ui.setupUi(self)

        # Value init
        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToX.setText("0.0")
        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToY.setText("0.0")
        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToZ.setText("0.0")

        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToX.textChanged.connect(self.onRobotMoveToXChanged)
        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToY.textChanged.connect(self.onRobotMoveToYChanged)
        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToZ.textChanged.connect(self.onRobotMoveToZChanged)

    # 로봇 모델 정보를 리스트 아이템으로 입력
    def SetupListItem(self, modelType, modelName):
        lbThumb = ""
        lbName = modelName
        if modelType == ENUM_ROBOT_TYPE.LOCOBOT:
            lbThumb = CONST_LOCOBOT_PATH
        elif modelType == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER:
            lbThumb = CONST_TURTLEBOT3_BURGER_PATH
        elif modelType == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE:
            lbThumb = CONST_TURTLEBOT3_WAFFLE_PATH
        elif modelType == ENUM_ROBOT_TYPE.JETBOT:
            lbThumb = CONST_JETBOT_PATH
        elif modelType == ENUM_ROBOT_TYPE.INTERBOTIX:
            lbThumb = CONST_INTERBOTIX_PATH
        elif modelType == ENUM_ROBOT_TYPE.UNI050_BASE:
            lbThumb = CONST_UNI_PATH

        # 정보 입력
        pixmap = QtGui.QPixmap(str(lbThumb))
        # QLabel의 크기에 맞춰 QPixmap 조정
        scaled_pixmap = pixmap.scaled(
        self.ui.lbWidgetStartROSCollaborationTaskItemThumbnail.size(),
        QtCore.Qt.KeepAspectRatio,  # 이미지 비율 유지
        QtCore.Qt.SmoothTransformation  # 부드럽게 스케일링
        )

        self.ui.lbWidgetStartROSCollaborationTaskItemThumbnail.setPixmap(scaled_pixmap)
        self.ui.lbWidgetStartROSCollaborationTaskItemName.setText(str(lbName))
            
    # Position 값 입력
    def SetRobotPosXYZ(self, x, y, z):
        self.ui.leditWidgetStartROSCollaborationTaskItemPositionX.setText(x)
        self.ui.leditWidgetStartROSCollaborationTaskItemPositionY.setText(y)
        self.ui.leditWidgetStartROSCollaborationTaskItemPositionZ.setText(z)

    # Move to Position 값 입력
    def SetRobotMoveToXYZ(self, x, y, z):
        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToX.setText(x)
        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToY.setText(y)
        self.ui.leditWidgetStartROSCollaborationTaskItemMoveToZ.setText(z)

    # Move to Position 값 변경 체크
    # X
    def onRobotMoveToXChanged(self, text):
        if self.CheckIsNumber(text) == False:
            self.ShowWarningMsg("You can only enter numbers.")
            
    # Y
    def onRobotMoveToYChanged(self, text):
        if self.CheckIsNumber(text) == False:
            self.ShowWarningMsg("You can only enter numbers.")
    # Z
    def onRobotMoveToZChanged(self, text):
        if self.CheckIsNumber(text) == False:
            self.ShowWarningMsg("You can only enter numbers.")

    # Move to Poisition X 값 획득
    def GetRobotMoveToX(self):
        strX = self.ui.leditWidgetStartROSCollaborationTaskItemMoveToX.text()
        fX = round(float(strX), 1) 

        return fX
    
    # Move to Poisition Y 값 획득
    def GetRobotMoveToY(self):
        strY = self.ui.leditWidgetStartROSCollaborationTaskItemMoveToY.text()
        fY = round(float(strY), 1) 
        return fY
    
    # Move to Poisition Z 값 획득
    def GetRobotMoveToZ(self):
        strZ = self.ui.leditWidgetStartROSCollaborationTaskItemMoveToZ.text()
        fZ = round(float(strZ), 1) 
        return fZ

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