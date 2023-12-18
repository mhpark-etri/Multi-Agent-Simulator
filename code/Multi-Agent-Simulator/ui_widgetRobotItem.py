# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widgetRobotItem.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)
import resources_rc

class Ui_WidgetRobotItem(object):
    def setupUi(self, WidgetRobotItem):
        if not WidgetRobotItem.objectName():
            WidgetRobotItem.setObjectName(u"WidgetRobotItem")
        WidgetRobotItem.resize(793, 202)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(WidgetRobotItem.sizePolicy().hasHeightForWidth())
        WidgetRobotItem.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(WidgetRobotItem)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.scrollArea_6 = QScrollArea(WidgetRobotItem)
        self.scrollArea_6.setObjectName(u"scrollArea_6")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.scrollArea_6.sizePolicy().hasHeightForWidth())
        self.scrollArea_6.setSizePolicy(sizePolicy1)
        self.scrollArea_6.setMinimumSize(QSize(0, 0))
        self.scrollArea_6.setStyleSheet(u"background-color: #e6e6e6;\n"
"border-radius:5px;")
        self.scrollArea_6.setWidgetResizable(True)
        self.scrollAreaWidgetContents_6 = QWidget()
        self.scrollAreaWidgetContents_6.setObjectName(u"scrollAreaWidgetContents_6")
        self.scrollAreaWidgetContents_6.setGeometry(QRect(0, 0, 761, 192))
        sizePolicy1.setHeightForWidth(self.scrollAreaWidgetContents_6.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents_6.setSizePolicy(sizePolicy1)
        self.scrollAreaWidgetContents_6.setMinimumSize(QSize(0, 0))
        self.horizontalLayout_11 = QHBoxLayout(self.scrollAreaWidgetContents_6)
        self.horizontalLayout_11.setSpacing(0)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setSpacing(20)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.frame_10 = QFrame(self.scrollAreaWidgetContents_6)
        self.frame_10.setObjectName(u"frame_10")
        sizePolicy1.setHeightForWidth(self.frame_10.sizePolicy().hasHeightForWidth())
        self.frame_10.setSizePolicy(sizePolicy1)
        self.frame_10.setMinimumSize(QSize(0, 0))
        self.frame_10.setFrameShape(QFrame.StyledPanel)
        self.frame_10.setFrameShadow(QFrame.Raised)
        self.verticalLayout_13 = QVBoxLayout(self.frame_10)
        self.verticalLayout_13.setSpacing(6)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(10, 0, 10, 0)
        self.lbRobotThumb = QLabel(self.frame_10)
        self.lbRobotThumb.setObjectName(u"lbRobotThumb")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lbRobotThumb.sizePolicy().hasHeightForWidth())
        self.lbRobotThumb.setSizePolicy(sizePolicy2)
        self.lbRobotThumb.setMinimumSize(QSize(0, 120))
        self.lbRobotThumb.setScaledContents(False)
        self.lbRobotThumb.setAlignment(Qt.AlignCenter)

        self.verticalLayout_13.addWidget(self.lbRobotThumb)

        self.lbRobotName = QLabel(self.frame_10)
        self.lbRobotName.setObjectName(u"lbRobotName")
        sizePolicy2.setHeightForWidth(self.lbRobotName.sizePolicy().hasHeightForWidth())
        self.lbRobotName.setSizePolicy(sizePolicy2)
        self.lbRobotName.setMinimumSize(QSize(0, 15))
        font = QFont()
        font.setFamilies([u"Umpush"])
        font.setPointSize(11)
        font.setBold(False)
        font.setItalic(False)
        self.lbRobotName.setFont(font)
        self.lbRobotName.setStyleSheet(u"")
        self.lbRobotName.setAlignment(Qt.AlignCenter)

        self.verticalLayout_13.addWidget(self.lbRobotName)

        self.frame = QFrame(self.frame_10)
        self.frame.setObjectName(u"frame")
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setMinimumSize(QSize(0, 0))
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.btnSelectRobotLeft = QPushButton(self.frame)
        self.btnSelectRobotLeft.setObjectName(u"btnSelectRobotLeft")
        sizePolicy1.setHeightForWidth(self.btnSelectRobotLeft.sizePolicy().hasHeightForWidth())
        self.btnSelectRobotLeft.setSizePolicy(sizePolicy1)
        self.btnSelectRobotLeft.setMinimumSize(QSize(0, 0))
        font1 = QFont()
        font1.setPointSize(5)
        self.btnSelectRobotLeft.setFont(font1)
        self.btnSelectRobotLeft.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
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

        self.horizontalLayout_2.addWidget(self.btnSelectRobotLeft)

        self.horizontalSpacer = QSpacerItem(60, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btnSelectRobotRight = QPushButton(self.frame)
        self.btnSelectRobotRight.setObjectName(u"btnSelectRobotRight")
        sizePolicy1.setHeightForWidth(self.btnSelectRobotRight.sizePolicy().hasHeightForWidth())
        self.btnSelectRobotRight.setSizePolicy(sizePolicy1)
        self.btnSelectRobotRight.setMinimumSize(QSize(0, 0))
        self.btnSelectRobotRight.setFont(font1)
        self.btnSelectRobotRight.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
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

        self.horizontalLayout_2.addWidget(self.btnSelectRobotRight)


        self.verticalLayout_13.addWidget(self.frame)


        self.horizontalLayout_10.addWidget(self.frame_10)

        self.groupBox_11 = QGroupBox(self.scrollAreaWidgetContents_6)
        self.groupBox_11.setObjectName(u"groupBox_11")
        sizePolicy1.setHeightForWidth(self.groupBox_11.sizePolicy().hasHeightForWidth())
        self.groupBox_11.setSizePolicy(sizePolicy1)
        self.groupBox_11.setMinimumSize(QSize(0, 0))
        self.groupBox_11.setStyleSheet(u"QGroupBox{\n"
"    border: 1px solid 	#444444;\n"
"    border-radius : 0px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;\n"
"    padding: 30px 0 0 0;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    border: 1px solid #444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    subcontrol-position: top center;\n"
"    left: -5px;\n"
"	top: 10px;\n"
"}")
        self.groupBox_11.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)
        self.groupBox_11.setFlat(False)
        self.verticalLayout_14 = QVBoxLayout(self.groupBox_11)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.scrollArea_7 = QScrollArea(self.groupBox_11)
        self.scrollArea_7.setObjectName(u"scrollArea_7")
        sizePolicy1.setHeightForWidth(self.scrollArea_7.sizePolicy().hasHeightForWidth())
        self.scrollArea_7.setSizePolicy(sizePolicy1)
        self.scrollArea_7.setMinimumSize(QSize(0, 0))
        self.scrollArea_7.setStyleSheet(u"background-color:transparent;")
        self.scrollArea_7.setWidgetResizable(True)
        self.scrollAreaWidgetContents_7 = QWidget()
        self.scrollAreaWidgetContents_7.setObjectName(u"scrollAreaWidgetContents_7")
        self.scrollAreaWidgetContents_7.setGeometry(QRect(0, 0, 213, 122))
        self.horizontalLayout_18 = QHBoxLayout(self.scrollAreaWidgetContents_7)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.frame_72 = QFrame(self.scrollAreaWidgetContents_7)
        self.frame_72.setObjectName(u"frame_72")
        self.frame_72.setFrameShape(QFrame.StyledPanel)
        self.frame_72.setFrameShadow(QFrame.Raised)
        self.verticalLayout_45 = QVBoxLayout(self.frame_72)
        self.verticalLayout_45.setObjectName(u"verticalLayout_45")
        self.verticalLayout_45.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_26 = QVBoxLayout()
        self.verticalLayout_26.setObjectName(u"verticalLayout_26")
        self.frame_73 = QFrame(self.frame_72)
        self.frame_73.setObjectName(u"frame_73")
        self.frame_73.setFrameShape(QFrame.StyledPanel)
        self.frame_73.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_147 = QHBoxLayout(self.frame_73)
        self.horizontalLayout_147.setObjectName(u"horizontalLayout_147")
        self.horizontalLayout_147.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_148 = QHBoxLayout()
        self.horizontalLayout_148.setSpacing(5)
        self.horizontalLayout_148.setObjectName(u"horizontalLayout_148")
        self.horizontalLayout_148.setContentsMargins(5, 5, 5, 5)
        self.label_87 = QLabel(self.frame_73)
        self.label_87.setObjectName(u"label_87")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_87.sizePolicy().hasHeightForWidth())
        self.label_87.setSizePolicy(sizePolicy3)
        self.label_87.setMinimumSize(QSize(80, 0))
        self.label_87.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")
        self.label_87.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_148.addWidget(self.label_87)

        self.label_88 = QLabel(self.frame_73)
        self.label_88.setObjectName(u"label_88")
        sizePolicy3.setHeightForWidth(self.label_88.sizePolicy().hasHeightForWidth())
        self.label_88.setSizePolicy(sizePolicy3)
        self.label_88.setMinimumSize(QSize(40, 0))
        self.label_88.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")
        self.label_88.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_148.addWidget(self.label_88)

        self.dsbRobotStartPosX = QDoubleSpinBox(self.frame_73)
        self.dsbRobotStartPosX.setObjectName(u"dsbRobotStartPosX")
        sizePolicy1.setHeightForWidth(self.dsbRobotStartPosX.sizePolicy().hasHeightForWidth())
        self.dsbRobotStartPosX.setSizePolicy(sizePolicy1)
        self.dsbRobotStartPosX.setStyleSheet(u"QDoubleSpinBox{\n"
"border: 1px solid #444444;\n"
"border-radius : 5px;\n"
"background-color: #eeeeee;\n"
"}\n"
"")
        self.dsbRobotStartPosX.setAlignment(Qt.AlignCenter)
        self.dsbRobotStartPosX.setMinimum(-99.000000000000000)
        self.dsbRobotStartPosX.setMaximum(99.000000000000000)
        self.dsbRobotStartPosX.setSingleStep(0.500000000000000)

        self.horizontalLayout_148.addWidget(self.dsbRobotStartPosX)

        self.horizontalLayout_148.setStretch(2, 1)

        self.horizontalLayout_147.addLayout(self.horizontalLayout_148)


        self.verticalLayout_26.addWidget(self.frame_73)

        self.frame_74 = QFrame(self.frame_72)
        self.frame_74.setObjectName(u"frame_74")
        self.frame_74.setFrameShape(QFrame.StyledPanel)
        self.frame_74.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_149 = QHBoxLayout(self.frame_74)
        self.horizontalLayout_149.setObjectName(u"horizontalLayout_149")
        self.horizontalLayout_149.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_150 = QHBoxLayout()
        self.horizontalLayout_150.setSpacing(5)
        self.horizontalLayout_150.setObjectName(u"horizontalLayout_150")
        self.horizontalLayout_150.setContentsMargins(5, 5, 5, 5)
        self.label_89 = QLabel(self.frame_74)
        self.label_89.setObjectName(u"label_89")
        sizePolicy3.setHeightForWidth(self.label_89.sizePolicy().hasHeightForWidth())
        self.label_89.setSizePolicy(sizePolicy3)
        self.label_89.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_150.addWidget(self.label_89)

        self.label_90 = QLabel(self.frame_74)
        self.label_90.setObjectName(u"label_90")
        sizePolicy3.setHeightForWidth(self.label_90.sizePolicy().hasHeightForWidth())
        self.label_90.setSizePolicy(sizePolicy3)
        self.label_90.setMinimumSize(QSize(40, 0))
        self.label_90.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")
        self.label_90.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_150.addWidget(self.label_90)

        self.dsbRobotStartPosY = QDoubleSpinBox(self.frame_74)
        self.dsbRobotStartPosY.setObjectName(u"dsbRobotStartPosY")
        sizePolicy1.setHeightForWidth(self.dsbRobotStartPosY.sizePolicy().hasHeightForWidth())
        self.dsbRobotStartPosY.setSizePolicy(sizePolicy1)
        self.dsbRobotStartPosY.setStyleSheet(u"QDoubleSpinBox{\n"
"border: 1px solid #444444;\n"
"border-radius : 5px;\n"
"background-color: #eeeeee;\n"
"}\n"
"")
        self.dsbRobotStartPosY.setAlignment(Qt.AlignCenter)
        self.dsbRobotStartPosY.setMinimum(-99.000000000000000)
        self.dsbRobotStartPosY.setMaximum(99.000000000000000)
        self.dsbRobotStartPosY.setSingleStep(0.500000000000000)

        self.horizontalLayout_150.addWidget(self.dsbRobotStartPosY)

        self.horizontalLayout_150.setStretch(2, 1)

        self.horizontalLayout_149.addLayout(self.horizontalLayout_150)


        self.verticalLayout_26.addWidget(self.frame_74)

        self.frame_75 = QFrame(self.frame_72)
        self.frame_75.setObjectName(u"frame_75")
        self.frame_75.setFrameShape(QFrame.StyledPanel)
        self.frame_75.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_151 = QHBoxLayout(self.frame_75)
        self.horizontalLayout_151.setObjectName(u"horizontalLayout_151")
        self.horizontalLayout_151.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_152 = QHBoxLayout()
        self.horizontalLayout_152.setSpacing(5)
        self.horizontalLayout_152.setObjectName(u"horizontalLayout_152")
        self.horizontalLayout_152.setContentsMargins(5, 5, 5, 5)
        self.label_91 = QLabel(self.frame_75)
        self.label_91.setObjectName(u"label_91")
        sizePolicy3.setHeightForWidth(self.label_91.sizePolicy().hasHeightForWidth())
        self.label_91.setSizePolicy(sizePolicy3)
        self.label_91.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_152.addWidget(self.label_91)

        self.label_92 = QLabel(self.frame_75)
        self.label_92.setObjectName(u"label_92")
        sizePolicy3.setHeightForWidth(self.label_92.sizePolicy().hasHeightForWidth())
        self.label_92.setSizePolicy(sizePolicy3)
        self.label_92.setMinimumSize(QSize(40, 0))
        self.label_92.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")
        self.label_92.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_152.addWidget(self.label_92)

        self.dsbRobotStartPosZ = QDoubleSpinBox(self.frame_75)
        self.dsbRobotStartPosZ.setObjectName(u"dsbRobotStartPosZ")
        self.dsbRobotStartPosZ.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.dsbRobotStartPosZ.sizePolicy().hasHeightForWidth())
        self.dsbRobotStartPosZ.setSizePolicy(sizePolicy1)
        self.dsbRobotStartPosZ.setStyleSheet(u"QDoubleSpinBox{\n"
"border: 1px solid #444444;\n"
"border-radius : 5px;\n"
"background-color: #eeeeee;\n"
"}\n"
"")
        self.dsbRobotStartPosZ.setAlignment(Qt.AlignCenter)
        self.dsbRobotStartPosZ.setMinimum(-99.000000000000000)

        self.horizontalLayout_152.addWidget(self.dsbRobotStartPosZ)

        self.horizontalLayout_152.setStretch(2, 1)

        self.horizontalLayout_151.addLayout(self.horizontalLayout_152)


        self.verticalLayout_26.addWidget(self.frame_75)


        self.verticalLayout_45.addLayout(self.verticalLayout_26)


        self.verticalLayout_15.addWidget(self.frame_72)


        self.horizontalLayout_18.addLayout(self.verticalLayout_15)

        self.scrollArea_7.setWidget(self.scrollAreaWidgetContents_7)

        self.verticalLayout_14.addWidget(self.scrollArea_7)


        self.horizontalLayout_10.addWidget(self.groupBox_11)

        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents_6)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setStyleSheet(u"QGroupBox{\n"
"    border: 1px solid 	#444444;\n"
"    border-radius : 0px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;\n"
"    padding: 30px 0 0 0;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    border: 1px solid #444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    subcontrol-position: top center;\n"
"    left: -5px;\n"
"	top: 10px;\n"
"}")
        self.verticalLayout_20 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.scrollArea_8 = QScrollArea(self.groupBox_3)
        self.scrollArea_8.setObjectName(u"scrollArea_8")
        sizePolicy1.setHeightForWidth(self.scrollArea_8.sizePolicy().hasHeightForWidth())
        self.scrollArea_8.setSizePolicy(sizePolicy1)
        self.scrollArea_8.setStyleSheet(u"background-color:transparent;")
        self.scrollArea_8.setWidgetResizable(True)
        self.scrollAreaWidgetContents_8 = QWidget()
        self.scrollAreaWidgetContents_8.setObjectName(u"scrollAreaWidgetContents_8")
        self.scrollAreaWidgetContents_8.setGeometry(QRect(0, 0, 214, 122))
        self.horizontalLayout_28 = QHBoxLayout(self.scrollAreaWidgetContents_8)
        self.horizontalLayout_28.setObjectName(u"horizontalLayout_28")
        self.horizontalLayout_28.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_18 = QVBoxLayout()
        self.verticalLayout_18.setSpacing(6)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.frame_16 = QFrame(self.scrollAreaWidgetContents_8)
        self.frame_16.setObjectName(u"frame_16")
        self.frame_16.setFrameShape(QFrame.StyledPanel)
        self.frame_16.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_35 = QHBoxLayout(self.frame_16)
        self.horizontalLayout_35.setSpacing(0)
        self.horizontalLayout_35.setObjectName(u"horizontalLayout_35")
        self.horizontalLayout_35.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_30 = QHBoxLayout()
        self.horizontalLayout_30.setSpacing(5)
        self.horizontalLayout_30.setObjectName(u"horizontalLayout_30")
        self.label_18 = QLabel(self.frame_16)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")
        self.label_18.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_30.addWidget(self.label_18)

        self.ckbRobotOptionCamera = QCheckBox(self.frame_16)
        self.ckbRobotOptionCamera.setObjectName(u"ckbRobotOptionCamera")
        sizePolicy3.setHeightForWidth(self.ckbRobotOptionCamera.sizePolicy().hasHeightForWidth())
        self.ckbRobotOptionCamera.setSizePolicy(sizePolicy3)
        self.ckbRobotOptionCamera.setMinimumSize(QSize(30, 0))
        self.ckbRobotOptionCamera.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 0px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")

        self.horizontalLayout_30.addWidget(self.ckbRobotOptionCamera)


        self.horizontalLayout_35.addLayout(self.horizontalLayout_30)


        self.verticalLayout_18.addWidget(self.frame_16)

        self.frame_18 = QFrame(self.scrollAreaWidgetContents_8)
        self.frame_18.setObjectName(u"frame_18")
        self.frame_18.setEnabled(False)
        self.frame_18.setFrameShape(QFrame.StyledPanel)
        self.frame_18.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_37 = QHBoxLayout(self.frame_18)
        self.horizontalLayout_37.setSpacing(0)
        self.horizontalLayout_37.setObjectName(u"horizontalLayout_37")
        self.horizontalLayout_37.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_33 = QHBoxLayout()
        self.horizontalLayout_33.setSpacing(5)
        self.horizontalLayout_33.setObjectName(u"horizontalLayout_33")
        self.label_19 = QLabel(self.frame_18)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")
        self.label_19.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_33.addWidget(self.label_19)

        self.ckbRobotOptionUseArm = QCheckBox(self.frame_18)
        self.ckbRobotOptionUseArm.setObjectName(u"ckbRobotOptionUseArm")
        sizePolicy3.setHeightForWidth(self.ckbRobotOptionUseArm.sizePolicy().hasHeightForWidth())
        self.ckbRobotOptionUseArm.setSizePolicy(sizePolicy3)
        self.ckbRobotOptionUseArm.setMinimumSize(QSize(30, 0))
        self.ckbRobotOptionUseArm.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")

        self.horizontalLayout_33.addWidget(self.ckbRobotOptionUseArm)


        self.horizontalLayout_37.addLayout(self.horizontalLayout_33)


        self.verticalLayout_18.addWidget(self.frame_18)

        self.frame_17 = QFrame(self.scrollAreaWidgetContents_8)
        self.frame_17.setObjectName(u"frame_17")
        self.frame_17.setEnabled(False)
        self.frame_17.setFrameShape(QFrame.StyledPanel)
        self.frame_17.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_38 = QHBoxLayout(self.frame_17)
        self.horizontalLayout_38.setSpacing(0)
        self.horizontalLayout_38.setObjectName(u"horizontalLayout_38")
        self.horizontalLayout_38.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setSpacing(5)
        self.horizontalLayout_34.setObjectName(u"horizontalLayout_34")
        self.label_20 = QLabel(self.frame_17)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")
        self.label_20.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_34.addWidget(self.label_20)

        self.ckbRobotOptionBase = QCheckBox(self.frame_17)
        self.ckbRobotOptionBase.setObjectName(u"ckbRobotOptionBase")
        self.ckbRobotOptionBase.setEnabled(False)
        sizePolicy3.setHeightForWidth(self.ckbRobotOptionBase.sizePolicy().hasHeightForWidth())
        self.ckbRobotOptionBase.setSizePolicy(sizePolicy3)
        self.ckbRobotOptionBase.setMinimumSize(QSize(30, 0))
        self.ckbRobotOptionBase.setStyleSheet(u"    border: 1px solid 	#444444;\n"
"    border-radius : 5px;\n"
"    background-color: #eeeeee;\n"
"    color : #444444;")

        self.horizontalLayout_34.addWidget(self.ckbRobotOptionBase)


        self.horizontalLayout_38.addLayout(self.horizontalLayout_34)


        self.verticalLayout_18.addWidget(self.frame_17)


        self.horizontalLayout_28.addLayout(self.verticalLayout_18)

        self.scrollArea_8.setWidget(self.scrollAreaWidgetContents_8)

        self.verticalLayout_20.addWidget(self.scrollArea_8)


        self.horizontalLayout_10.addWidget(self.groupBox_3)


        self.horizontalLayout_11.addLayout(self.horizontalLayout_10)

        self.scrollArea_6.setWidget(self.scrollAreaWidgetContents_6)

        self.horizontalLayout.addWidget(self.scrollArea_6)


        self.retranslateUi(WidgetRobotItem)

        QMetaObject.connectSlotsByName(WidgetRobotItem)
    # setupUi

    def retranslateUi(self, WidgetRobotItem):
        WidgetRobotItem.setWindowTitle(QCoreApplication.translate("WidgetRobotItem", u"Form", None))
        self.lbRobotThumb.setText("")
        self.lbRobotName.setText(QCoreApplication.translate("WidgetRobotItem", u"LoCoBot", None))
        self.btnSelectRobotLeft.setText(QCoreApplication.translate("WidgetRobotItem", u"\u25c0", None))
        self.btnSelectRobotRight.setText(QCoreApplication.translate("WidgetRobotItem", u"\u25b6", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("WidgetRobotItem", u"Model", None))
        self.label_87.setText(QCoreApplication.translate("WidgetRobotItem", u"Start Pos", None))
        self.label_88.setText(QCoreApplication.translate("WidgetRobotItem", u"X : ", None))
        self.label_89.setText("")
        self.label_90.setText(QCoreApplication.translate("WidgetRobotItem", u"Y : ", None))
        self.label_91.setText("")
        self.label_92.setText(QCoreApplication.translate("WidgetRobotItem", u"Z : ", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("WidgetRobotItem", u"Option", None))
        self.label_18.setText(QCoreApplication.translate("WidgetRobotItem", u"camera", None))
        self.ckbRobotOptionCamera.setText("")
        self.label_19.setText(QCoreApplication.translate("WidgetRobotItem", u"use_arm", None))
        self.ckbRobotOptionUseArm.setText("")
        self.label_20.setText(QCoreApplication.translate("WidgetRobotItem", u"base", None))
        self.ckbRobotOptionBase.setText("")
    # retranslateUi

