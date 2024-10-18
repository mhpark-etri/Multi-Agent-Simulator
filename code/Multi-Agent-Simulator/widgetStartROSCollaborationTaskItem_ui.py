# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widgetStartROSCollaborationTaskItem.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_WidgetStartROSCollaborationTaskItem(object):
    def setupUi(self, WidgetStartROSCollaborationTaskItem):
        if not WidgetStartROSCollaborationTaskItem.objectName():
            WidgetStartROSCollaborationTaskItem.setObjectName(u"WidgetStartROSCollaborationTaskItem")
        WidgetStartROSCollaborationTaskItem.resize(220, 503)
        self.verticalLayout = QVBoxLayout(WidgetStartROSCollaborationTaskItem)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(WidgetStartROSCollaborationTaskItem)
        self.frame.setObjectName(u"frame")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.lbWidgetStartROSCollaborationTaskItemThumbnail = QLabel(self.frame_2)
        self.lbWidgetStartROSCollaborationTaskItemThumbnail.setObjectName(u"lbWidgetStartROSCollaborationTaskItemThumbnail")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbWidgetStartROSCollaborationTaskItemThumbnail.sizePolicy().hasHeightForWidth())
        self.lbWidgetStartROSCollaborationTaskItemThumbnail.setSizePolicy(sizePolicy1)
        self.lbWidgetStartROSCollaborationTaskItemThumbnail.setMinimumSize(QSize(180, 160))
        self.lbWidgetStartROSCollaborationTaskItemThumbnail.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.lbWidgetStartROSCollaborationTaskItemThumbnail)

        self.lbWidgetStartROSCollaborationTaskItemName = QLabel(self.frame_2)
        self.lbWidgetStartROSCollaborationTaskItemName.setObjectName(u"lbWidgetStartROSCollaborationTaskItemName")
        sizePolicy.setHeightForWidth(self.lbWidgetStartROSCollaborationTaskItemName.sizePolicy().hasHeightForWidth())
        self.lbWidgetStartROSCollaborationTaskItemName.setSizePolicy(sizePolicy)
        self.lbWidgetStartROSCollaborationTaskItemName.setMinimumSize(QSize(0, 0))
        self.lbWidgetStartROSCollaborationTaskItemName.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.lbWidgetStartROSCollaborationTaskItemName)


        self.verticalLayout_2.addWidget(self.frame_2)

        self.frame_3 = QFrame(self.frame)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.frame_3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.gbWidgetStartROSCollaborationTaskItemPosition = QGroupBox(self.frame_3)
        self.gbWidgetStartROSCollaborationTaskItemPosition.setObjectName(u"gbWidgetStartROSCollaborationTaskItemPosition")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.gbWidgetStartROSCollaborationTaskItemPosition.sizePolicy().hasHeightForWidth())
        self.gbWidgetStartROSCollaborationTaskItemPosition.setSizePolicy(sizePolicy2)
        self.gbWidgetStartROSCollaborationTaskItemPosition.setStyleSheet(u"QGroupBox#gbWidgetStartROSCollaborationTaskItemPosition {\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	color:white\n"
"}\n"
"\n"
"QGroupBox#gbWidgetStartROSCollaborationTaskItemPosition::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}")
        self.verticalLayout_7 = QVBoxLayout(self.gbWidgetStartROSCollaborationTaskItemPosition)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.frame_7 = QFrame(self.gbWidgetStartROSCollaborationTaskItemPosition)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.NoFrame)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_7)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 15, 0, 0)
        self.label_6 = QLabel(self.frame_7)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout.addWidget(self.label_6)

        self.leditWidgetStartROSCollaborationTaskItemPositionX = QLabel(self.frame_7)
        self.leditWidgetStartROSCollaborationTaskItemPositionX.setObjectName(u"leditWidgetStartROSCollaborationTaskItemPositionX")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.leditWidgetStartROSCollaborationTaskItemPositionX.sizePolicy().hasHeightForWidth())
        self.leditWidgetStartROSCollaborationTaskItemPositionX.setSizePolicy(sizePolicy3)

        self.horizontalLayout.addWidget(self.leditWidgetStartROSCollaborationTaskItemPositionX)


        self.verticalLayout_7.addWidget(self.frame_7)

        self.frame_8 = QFrame(self.gbWidgetStartROSCollaborationTaskItemPosition)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setFrameShape(QFrame.NoFrame)
        self.frame_8.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_8)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.frame_8)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_5.addWidget(self.label_5)

        self.leditWidgetStartROSCollaborationTaskItemPositionY = QLabel(self.frame_8)
        self.leditWidgetStartROSCollaborationTaskItemPositionY.setObjectName(u"leditWidgetStartROSCollaborationTaskItemPositionY")
        sizePolicy3.setHeightForWidth(self.leditWidgetStartROSCollaborationTaskItemPositionY.sizePolicy().hasHeightForWidth())
        self.leditWidgetStartROSCollaborationTaskItemPositionY.setSizePolicy(sizePolicy3)

        self.horizontalLayout_5.addWidget(self.leditWidgetStartROSCollaborationTaskItemPositionY)


        self.verticalLayout_7.addWidget(self.frame_8)

        self.frame_9 = QFrame(self.gbWidgetStartROSCollaborationTaskItemPosition)
        self.frame_9.setObjectName(u"frame_9")
        self.frame_9.setFrameShape(QFrame.NoFrame)
        self.frame_9.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_9)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_4 = QLabel(self.frame_9)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_6.addWidget(self.label_4)

        self.leditWidgetStartROSCollaborationTaskItemPositionZ = QLabel(self.frame_9)
        self.leditWidgetStartROSCollaborationTaskItemPositionZ.setObjectName(u"leditWidgetStartROSCollaborationTaskItemPositionZ")
        sizePolicy3.setHeightForWidth(self.leditWidgetStartROSCollaborationTaskItemPositionZ.sizePolicy().hasHeightForWidth())
        self.leditWidgetStartROSCollaborationTaskItemPositionZ.setSizePolicy(sizePolicy3)

        self.horizontalLayout_6.addWidget(self.leditWidgetStartROSCollaborationTaskItemPositionZ)


        self.verticalLayout_7.addWidget(self.frame_9)


        self.verticalLayout_5.addWidget(self.gbWidgetStartROSCollaborationTaskItemPosition)

        self.gbWidgetStartROSCollaborationTaskItemMoveTo = QGroupBox(self.frame_3)
        self.gbWidgetStartROSCollaborationTaskItemMoveTo.setObjectName(u"gbWidgetStartROSCollaborationTaskItemMoveTo")
        sizePolicy2.setHeightForWidth(self.gbWidgetStartROSCollaborationTaskItemMoveTo.sizePolicy().hasHeightForWidth())
        self.gbWidgetStartROSCollaborationTaskItemMoveTo.setSizePolicy(sizePolicy2)
        self.gbWidgetStartROSCollaborationTaskItemMoveTo.setStyleSheet(u"QGroupBox#gbWidgetStartROSCollaborationTaskItemMoveTo {\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	color:white\n"
"}\n"
"\n"
"QGroupBox#gbWidgetStartROSCollaborationTaskItemMoveTo::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}")
        self.verticalLayout_6 = QVBoxLayout(self.gbWidgetStartROSCollaborationTaskItemMoveTo)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.frame_4 = QFrame(self.gbWidgetStartROSCollaborationTaskItemMoveTo)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 15, 0, 0)
        self.label = QLabel(self.frame_4)
        self.label.setObjectName(u"label")

        self.horizontalLayout_3.addWidget(self.label)

        self.leditWidgetStartROSCollaborationTaskItemMoveToX = QLineEdit(self.frame_4)
        self.leditWidgetStartROSCollaborationTaskItemMoveToX.setObjectName(u"leditWidgetStartROSCollaborationTaskItemMoveToX")

        self.horizontalLayout_3.addWidget(self.leditWidgetStartROSCollaborationTaskItemMoveToX)


        self.verticalLayout_6.addWidget(self.frame_4)

        self.frame_5 = QFrame(self.gbWidgetStartROSCollaborationTaskItemMoveTo)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.frame_5)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.leditWidgetStartROSCollaborationTaskItemMoveToY = QLineEdit(self.frame_5)
        self.leditWidgetStartROSCollaborationTaskItemMoveToY.setObjectName(u"leditWidgetStartROSCollaborationTaskItemMoveToY")

        self.horizontalLayout_2.addWidget(self.leditWidgetStartROSCollaborationTaskItemMoveToY)


        self.verticalLayout_6.addWidget(self.frame_5)

        self.frame_6 = QFrame(self.gbWidgetStartROSCollaborationTaskItemMoveTo)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.frame_6)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.leditWidgetStartROSCollaborationTaskItemMoveToZ = QLineEdit(self.frame_6)
        self.leditWidgetStartROSCollaborationTaskItemMoveToZ.setObjectName(u"leditWidgetStartROSCollaborationTaskItemMoveToZ")
        self.leditWidgetStartROSCollaborationTaskItemMoveToZ.setEnabled(False)

        self.horizontalLayout_4.addWidget(self.leditWidgetStartROSCollaborationTaskItemMoveToZ)


        self.verticalLayout_6.addWidget(self.frame_6)


        self.verticalLayout_5.addWidget(self.gbWidgetStartROSCollaborationTaskItemMoveTo)


        self.verticalLayout_2.addWidget(self.frame_3)


        self.verticalLayout_3.addLayout(self.verticalLayout_2)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(WidgetStartROSCollaborationTaskItem)

        QMetaObject.connectSlotsByName(WidgetStartROSCollaborationTaskItem)
    # setupUi

    def retranslateUi(self, WidgetStartROSCollaborationTaskItem):
        WidgetStartROSCollaborationTaskItem.setWindowTitle(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Form", None))
        self.lbWidgetStartROSCollaborationTaskItemThumbnail.setText("")
        self.lbWidgetStartROSCollaborationTaskItemName.setText("")
        self.gbWidgetStartROSCollaborationTaskItemPosition.setTitle(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Position", None))
        self.label_6.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Position X : ", None))
        self.leditWidgetStartROSCollaborationTaskItemPositionX.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"0.0", None))
        self.label_5.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Position Y : ", None))
        self.leditWidgetStartROSCollaborationTaskItemPositionY.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"0.0", None))
        self.label_4.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Position Z : ", None))
        self.leditWidgetStartROSCollaborationTaskItemPositionZ.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"0.0", None))
        self.gbWidgetStartROSCollaborationTaskItemMoveTo.setTitle(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Move to", None))
        self.label.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Move X : ", None))
        self.label_2.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Move Y : ", None))
        self.label_3.setText(QCoreApplication.translate("WidgetStartROSCollaborationTaskItem", u"Move Z : ", None))
    # retranslateUi

