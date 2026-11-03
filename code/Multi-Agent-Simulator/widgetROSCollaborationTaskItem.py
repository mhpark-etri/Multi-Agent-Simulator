######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : Collaboration ListWidget Item             ##
######################################################
from PySide6 import QtWidgets, QtGui
from ui_widgetROSCollaborationTaskItem import Ui_WidgetCollaborationTask


class widgetROSCollaborationTaskItem(QtWidgets.QWidget):
    # Init
    def __init__(self, parent=None):
        super(widgetROSCollaborationTaskItem, self).__init__(parent)
        self.ui = Ui_WidgetCollaborationTask()
        self.ui.setupUi(self)

    # Collaboration Task 내용 입력
    def AddCollaborationTask(self, name, path):
        pixmap = QtGui.QPixmap(str(path))
        self.ui.lbROSCollaborationTaskImage.setPixmap(pixmap)
        self.ui.lbROSCollaborationTaskName.setText(name)

    # Setting 버튼 활성, 비활성화
    def SetSettingButtonEnable(self, bValue):
        self.ui.btnROSCollaborationTaskSetting.setVisible(bValue)