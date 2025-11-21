# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgROSI2IPBUlIj.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDialog, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_DlgROSI2I(object):
    def setupUi(self, DlgROSI2I):
        if not DlgROSI2I.objectName():
            DlgROSI2I.setObjectName(u"DlgROSI2I")
        DlgROSI2I.resize(728, 639)
        self.verticalLayout = QVBoxLayout(DlgROSI2I)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(DlgROSI2I)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.frame_6 = QFrame(self.frame)
        self.frame_6.setObjectName(u"frame_6")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_6.sizePolicy().hasHeightForWidth())
        self.frame_6.setSizePolicy(sizePolicy)
        self.frame_6.setMinimumSize(QSize(270, 0))
        self.frame_6.setFrameShape(QFrame.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_15 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_13 = QVBoxLayout()
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.gbROSI2IRobot = QGroupBox(self.frame_6)
        self.gbROSI2IRobot.setObjectName(u"gbROSI2IRobot")
        self.gbROSI2IRobot.setStyleSheet(u"QGroupBox#gbROSI2IRobot {\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbROSI2IRobot::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top left;\n"
"	left: 30px;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}")
        self.verticalLayout_14 = QVBoxLayout(self.gbROSI2IRobot)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(-1, 15, -1, -1)
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.frame_7 = QFrame(self.gbROSI2IRobot)
        self.frame_7.setObjectName(u"frame_7")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_7.sizePolicy().hasHeightForWidth())
        self.frame_7.setSizePolicy(sizePolicy1)
        self.frame_7.setFrameShape(QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_10 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(9, 9, 9, 9)
        self.label_2 = QLabel(self.frame_7)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_10.addWidget(self.label_2)

        self.cbROSI2IName = QComboBox(self.frame_7)
        self.cbROSI2IName.setObjectName(u"cbROSI2IName")

        self.horizontalLayout_10.addWidget(self.cbROSI2IName)


        self.horizontalLayout_9.addWidget(self.frame_7)


        self.verticalLayout_15.addLayout(self.horizontalLayout_9)

        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.frame_8 = QFrame(self.gbROSI2IRobot)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setFrameShape(QFrame.StyledPanel)
        self.frame_8.setFrameShadow(QFrame.Raised)
        self.verticalLayout_17 = QVBoxLayout(self.frame_8)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.lbROSI2IRobotThumb = QLabel(self.frame_8)
        self.lbROSI2IRobotThumb.setObjectName(u"lbROSI2IRobotThumb")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lbROSI2IRobotThumb.sizePolicy().hasHeightForWidth())
        self.lbROSI2IRobotThumb.setSizePolicy(sizePolicy2)
        self.lbROSI2IRobotThumb.setMinimumSize(QSize(0, 200))
        self.lbROSI2IRobotThumb.setAlignment(Qt.AlignCenter)

        self.verticalLayout_17.addWidget(self.lbROSI2IRobotThumb)


        self.verticalLayout_16.addWidget(self.frame_8)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.frame_9 = QFrame(self.gbROSI2IRobot)
        self.frame_9.setObjectName(u"frame_9")
        sizePolicy1.setHeightForWidth(self.frame_9.sizePolicy().hasHeightForWidth())
        self.frame_9.setSizePolicy(sizePolicy1)
        self.frame_9.setMinimumSize(QSize(0, 0))
        self.frame_9.setFrameShape(QFrame.StyledPanel)
        self.frame_9.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_12 = QHBoxLayout(self.frame_9)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_4 = QLabel(self.frame_9)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_12.addWidget(self.label_4)

        self.lbROSI2INameSpace = QLabel(self.frame_9)
        self.lbROSI2INameSpace.setObjectName(u"lbROSI2INameSpace")

        self.horizontalLayout_12.addWidget(self.lbROSI2INameSpace)


        self.horizontalLayout_11.addWidget(self.frame_9)


        self.verticalLayout_16.addLayout(self.horizontalLayout_11)


        self.verticalLayout_15.addLayout(self.verticalLayout_16)


        self.verticalLayout_14.addLayout(self.verticalLayout_15)


        self.verticalLayout_13.addWidget(self.gbROSI2IRobot)

        self.gbROSI2IOption = QGroupBox(self.frame_6)
        self.gbROSI2IOption.setObjectName(u"gbROSI2IOption")
        self.gbROSI2IOption.setStyleSheet(u"QGroupBox#gbROSI2IOption {\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbROSI2IOption::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top left;\n"
"	left: 30px;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}")
        self.verticalLayout_18 = QVBoxLayout(self.gbROSI2IOption)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_19 = QVBoxLayout()
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(-1, 15, -1, -1)
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.frame_10 = QFrame(self.gbROSI2IOption)
        self.frame_10.setObjectName(u"frame_10")
        self.frame_10.setFrameShape(QFrame.StyledPanel)
        self.frame_10.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_14 = QHBoxLayout(self.frame_10)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.ckbROSI2IShowCamera = QCheckBox(self.frame_10)
        self.ckbROSI2IShowCamera.setObjectName(u"ckbROSI2IShowCamera")

        self.horizontalLayout_14.addWidget(self.ckbROSI2IShowCamera)


        self.horizontalLayout_13.addWidget(self.frame_10)


        self.verticalLayout_19.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.frame_2 = QFrame(self.gbROSI2IOption)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.ckbROSI2ICapture = QCheckBox(self.frame_2)
        self.ckbROSI2ICapture.setObjectName(u"ckbROSI2ICapture")

        self.verticalLayout_2.addWidget(self.ckbROSI2ICapture)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.btnROSI2ICapturePathOpen = QPushButton(self.frame_2)
        self.btnROSI2ICapturePathOpen.setObjectName(u"btnROSI2ICapturePathOpen")

        self.horizontalLayout_5.addWidget(self.btnROSI2ICapturePathOpen)

        self.leditROSI2ICapturePath = QLineEdit(self.frame_2)
        self.leditROSI2ICapturePath.setObjectName(u"leditROSI2ICapturePath")
        self.leditROSI2ICapturePath.setReadOnly(True)

        self.horizontalLayout_5.addWidget(self.leditROSI2ICapturePath)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)


        self.horizontalLayout_3.addWidget(self.frame_2)


        self.verticalLayout_19.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_19.addItem(self.verticalSpacer_2)


        self.verticalLayout_18.addLayout(self.verticalLayout_19)


        self.verticalLayout_13.addWidget(self.gbROSI2IOption)


        self.horizontalLayout_15.addLayout(self.verticalLayout_13)


        self.horizontalLayout.addWidget(self.frame_6)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.gbROSI2ITopicList = QGroupBox(self.frame)
        self.gbROSI2ITopicList.setObjectName(u"gbROSI2ITopicList")
        self.gbROSI2ITopicList.setStyleSheet(u"QGroupBox#gbROSI2ITopicList {\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbROSI2ITopicList::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top left;\n"
"	left: 30px;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}")
        self.verticalLayout_5 = QVBoxLayout(self.gbROSI2ITopicList)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(-1, 15, -1, -1)
        self.lstwROSI2ITopicList = QListWidget(self.gbROSI2ITopicList)
        self.lstwROSI2ITopicList.setObjectName(u"lstwROSI2ITopicList")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lstwROSI2ITopicList.sizePolicy().hasHeightForWidth())
        self.lstwROSI2ITopicList.setSizePolicy(sizePolicy3)
        self.lstwROSI2ITopicList.setSelectionMode(QAbstractItemView.SingleSelection)

        self.verticalLayout_4.addWidget(self.lstwROSI2ITopicList)


        self.verticalLayout_5.addLayout(self.verticalLayout_4)


        self.verticalLayout_3.addWidget(self.gbROSI2ITopicList)


        self.horizontalLayout.addLayout(self.verticalLayout_3)


        self.verticalLayout_6.addLayout(self.horizontalLayout)


        self.verticalLayout.addWidget(self.frame)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btnROSI2IStart = QPushButton(DlgROSI2I)
        self.btnROSI2IStart.setObjectName(u"btnROSI2IStart")
        self.btnROSI2IStart.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"margin-left: 10px;\n"
"margin-right: 10px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
"min-width: 80px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #bbb);\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"background: qradialgradient(cx: 0.4, cy: -0.1,\n"
"fx: 0.4, fy: -0.1,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #ddd);\n"
"}")

        self.horizontalLayout_2.addWidget(self.btnROSI2IStart)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(DlgROSI2I)

        QMetaObject.connectSlotsByName(DlgROSI2I)
    # setupUi

    def retranslateUi(self, DlgROSI2I):
        DlgROSI2I.setWindowTitle(QCoreApplication.translate("DlgROSI2I", u"Image-to-Image Enhancement", None))
        self.gbROSI2IRobot.setTitle(QCoreApplication.translate("DlgROSI2I", u"Robot", None))
        self.label_2.setText(QCoreApplication.translate("DlgROSI2I", u"Name : ", None))
        self.lbROSI2IRobotThumb.setText("")
        self.label_4.setText(QCoreApplication.translate("DlgROSI2I", u"Name Space : ", None))
        self.lbROSI2INameSpace.setText("")
        self.gbROSI2IOption.setTitle(QCoreApplication.translate("DlgROSI2I", u"Option", None))
        self.ckbROSI2IShowCamera.setText(QCoreApplication.translate("DlgROSI2I", u"Show Camera", None))
        self.ckbROSI2ICapture.setText(QCoreApplication.translate("DlgROSI2I", u"Capture", None))
        self.btnROSI2ICapturePathOpen.setText(QCoreApplication.translate("DlgROSI2I", u"Open", None))
        self.gbROSI2ITopicList.setTitle(QCoreApplication.translate("DlgROSI2I", u"Topic List", None))
        self.btnROSI2IStart.setText(QCoreApplication.translate("DlgROSI2I", u"Start", None))
    # retranslateUi

