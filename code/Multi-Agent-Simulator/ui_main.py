# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainTnIaxE.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QListView,
    QListWidget, QListWidgetItem, QMainWindow, QMenu,
    QMenuBar, QPushButton, QRadioButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSpinBox, QStatusBar,
    QVBoxLayout, QWidget)
import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(1135, 1018)
        MainWindow.setMinimumSize(QSize(0, 0))
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave_as = QAction(MainWindow)
        self.actionSave_as.setObjectName(u"actionSave_as")
        self.actionExis = QAction(MainWindow)
        self.actionExis.setObjectName(u"actionExis")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionOpenDB = QAction(MainWindow)
        self.actionOpenDB.setObjectName(u"actionOpenDB")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setAutoFillBackground(False)
        self.centralwidget.setStyleSheet(u"background-color: gray;")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 0, -1, 0)
        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.gbWorld = QGroupBox(self.centralwidget)
        self.gbWorld.setObjectName(u"gbWorld")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gbWorld.sizePolicy().hasHeightForWidth())
        self.gbWorld.setSizePolicy(sizePolicy)
        self.gbWorld.setMinimumSize(QSize(0, 250))
        self.gbWorld.setStyleSheet(u"QGroupBox#gbWorld {\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbWorld::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top left;\n"
"	left: 30px;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}")
        self.horizontalLayout_2 = QHBoxLayout(self.gbWorld)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(10, 20, 10, 10)
        self.scrollArea = QScrollArea(self.gbWorld)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setStyleSheet(u"background-color: #e6e6e6;\n"
"border-radius:5px;")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1095, 214))
        self.horizontalLayout_3 = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.frame_3 = QFrame(self.scrollAreaWidgetContents)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setStyleSheet(u"")
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(40)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(40, 10, 10, 10)
        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.lstwWorldMainCategory = QListWidget(self.frame_3)
        self.lstwWorldMainCategory.setObjectName(u"lstwWorldMainCategory")
        self.lstwWorldMainCategory.setStyleSheet(u"QListWidget{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"}")

        self.horizontalLayout_11.addWidget(self.lstwWorldMainCategory)

        self.lstwWorldSubCategory = QListWidget(self.frame_3)
        self.lstwWorldSubCategory.setObjectName(u"lstwWorldSubCategory")
        self.lstwWorldSubCategory.setStyleSheet(u"QListWidget{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"}")

        self.horizontalLayout_11.addWidget(self.lstwWorldSubCategory)

        self.lbWorldImage = QLabel(self.frame_3)
        self.lbWorldImage.setObjectName(u"lbWorldImage")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbWorldImage.sizePolicy().hasHeightForWidth())
        self.lbWorldImage.setSizePolicy(sizePolicy1)
        self.lbWorldImage.setMinimumSize(QSize(300, 180))
        self.lbWorldImage.setStyleSheet(u"QLabel{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"}")
        self.lbWorldImage.setScaledContents(False)

        self.horizontalLayout_11.addWidget(self.lbWorldImage)


        self.horizontalLayout.addLayout(self.horizontalLayout_11)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupBox_5 = QGroupBox(self.frame_3)
        self.groupBox_5.setObjectName(u"groupBox_5")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.groupBox_5.sizePolicy().hasHeightForWidth())
        self.groupBox_5.setSizePolicy(sizePolicy2)
        self.groupBox_5.setMinimumSize(QSize(300, 0))
        self.groupBox_5.setStyleSheet(u"QGroupBox{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top center;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}")
        self.groupBox_5.setFlat(False)
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_5)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(-1, 20, -1, -1)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame = QFrame(self.groupBox_5)
        self.frame.setObjectName(u"frame")
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QSize(0, 40))
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_14 = QHBoxLayout(self.frame)
        self.horizontalLayout_14.setSpacing(0)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setSpacing(5)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.chkWorldOptionPerson = QCheckBox(self.frame)
        self.chkWorldOptionPerson.setObjectName(u"chkWorldOptionPerson")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.chkWorldOptionPerson.sizePolicy().hasHeightForWidth())
        self.chkWorldOptionPerson.setSizePolicy(sizePolicy3)
        self.chkWorldOptionPerson.setMinimumSize(QSize(0, 0))
        self.chkWorldOptionPerson.setChecked(False)

        self.horizontalLayout_18.addWidget(self.chkWorldOptionPerson)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setStyleSheet(u"background-color:transparent;")

        self.horizontalLayout_18.addWidget(self.label)

        self.sbWorldOptionPersonCount = QSpinBox(self.frame)
        self.sbWorldOptionPersonCount.setObjectName(u"sbWorldOptionPersonCount")
        self.sbWorldOptionPersonCount.setEnabled(False)
        sizePolicy4 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.sbWorldOptionPersonCount.sizePolicy().hasHeightForWidth())
        self.sbWorldOptionPersonCount.setSizePolicy(sizePolicy4)
        self.sbWorldOptionPersonCount.setMinimumSize(QSize(50, 0))
        self.sbWorldOptionPersonCount.setStyleSheet(u"            QSpinBox::up-button {\n"
"                width: 30px;\n"
"            }\n"
"\n"
"            QSpinBox::down-button {\n"
"                width: 30px;\n"
"            }")
        self.sbWorldOptionPersonCount.setMinimum(1)
        self.sbWorldOptionPersonCount.setValue(1)

        self.horizontalLayout_18.addWidget(self.sbWorldOptionPersonCount)


        self.horizontalLayout_10.addLayout(self.horizontalLayout_18)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.lbRandomColor = QLabel(self.frame)
        self.lbRandomColor.setObjectName(u"lbRandomColor")
        self.lbRandomColor.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_19.addWidget(self.lbRandomColor)

        self.chkWorldOptionRandomColor = QCheckBox(self.frame)
        self.chkWorldOptionRandomColor.setObjectName(u"chkWorldOptionRandomColor")
        self.chkWorldOptionRandomColor.setEnabled(False)
        sizePolicy3.setHeightForWidth(self.chkWorldOptionRandomColor.sizePolicy().hasHeightForWidth())
        self.chkWorldOptionRandomColor.setSizePolicy(sizePolicy3)

        self.horizontalLayout_19.addWidget(self.chkWorldOptionRandomColor)


        self.horizontalLayout_10.addLayout(self.horizontalLayout_19)


        self.horizontalLayout_14.addLayout(self.horizontalLayout_10)


        self.verticalLayout_3.addWidget(self.frame)

        self.frame_2 = QFrame(self.groupBox_5)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setMinimumSize(QSize(0, 40))
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_15 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_15.setSpacing(0)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setSpacing(5)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label_3 = QLabel(self.frame_2)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_16.addWidget(self.label_3)


        self.horizontalLayout_13.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label_2 = QLabel(self.frame_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_17.addWidget(self.label_2)

        self.checkBox = QCheckBox(self.frame_2)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setEnabled(False)
        sizePolicy3.setHeightForWidth(self.checkBox.sizePolicy().hasHeightForWidth())
        self.checkBox.setSizePolicy(sizePolicy3)

        self.horizontalLayout_17.addWidget(self.checkBox)


        self.horizontalLayout_13.addLayout(self.horizontalLayout_17)


        self.horizontalLayout_15.addLayout(self.horizontalLayout_13)


        self.verticalLayout_3.addWidget(self.frame_2)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_4)


        self.verticalLayout_5.addLayout(self.verticalLayout_3)


        self.verticalLayout_4.addWidget(self.groupBox_5)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.horizontalLayout_4.addLayout(self.horizontalLayout)


        self.horizontalLayout_3.addWidget(self.frame_3)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_2.addWidget(self.scrollArea)


        self.verticalLayout.addWidget(self.gbWorld)

        self.verticalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.frame_19 = QFrame(self.centralwidget)
        self.frame_19.setObjectName(u"frame_19")
        self.frame_19.setFrameShape(QFrame.NoFrame)
        self.frame_19.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_29 = QHBoxLayout(self.frame_19)
        self.horizontalLayout_29.setSpacing(20)
        self.horizontalLayout_29.setObjectName(u"horizontalLayout_29")
        self.horizontalLayout_29.setContentsMargins(0, 0, 0, 0)
        self.gbRobot = QGroupBox(self.frame_19)
        self.gbRobot.setObjectName(u"gbRobot")
        self.gbRobot.setEnabled(True)
        sizePolicy3.setHeightForWidth(self.gbRobot.sizePolicy().hasHeightForWidth())
        self.gbRobot.setSizePolicy(sizePolicy3)
        self.gbRobot.setMinimumSize(QSize(800, 0))
        self.gbRobot.setLayoutDirection(Qt.LeftToRight)
        self.gbRobot.setStyleSheet(u"QGroupBox#gbRobot{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobot::title {\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"    left: 30px;\n"
"}")
        self.verticalLayout_7 = QVBoxLayout(self.gbRobot)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(9, 20, 9, 10)
        self.frame_21 = QFrame(self.gbRobot)
        self.frame_21.setObjectName(u"frame_21")
        sizePolicy.setHeightForWidth(self.frame_21.sizePolicy().hasHeightForWidth())
        self.frame_21.setSizePolicy(sizePolicy)
        self.frame_21.setMinimumSize(QSize(0, 60))
        self.frame_21.setFrameShape(QFrame.StyledPanel)
        self.frame_21.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_12 = QHBoxLayout(self.frame_21)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(9, 0, 9, 0)
        self.btnAddRobot = QPushButton(self.frame_21)
        self.btnAddRobot.setObjectName(u"btnAddRobot")
        self.btnAddRobot.setMinimumSize(QSize(94, 40))
        self.btnAddRobot.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
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

        self.horizontalLayout_12.addWidget(self.btnAddRobot)

        self.btnDeleteRobot = QPushButton(self.frame_21)
        self.btnDeleteRobot.setObjectName(u"btnDeleteRobot")
        self.btnDeleteRobot.setMinimumSize(QSize(94, 40))
        self.btnDeleteRobot.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
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

        self.horizontalLayout_12.addWidget(self.btnDeleteRobot)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_2)

        self.btnAddModel = QPushButton(self.frame_21)
        self.btnAddModel.setObjectName(u"btnAddModel")
        self.btnAddModel.setMinimumSize(QSize(94, 40))
        self.btnAddModel.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
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

        self.horizontalLayout_12.addWidget(self.btnAddModel)


        self.verticalLayout_7.addWidget(self.frame_21)

        self.frame_8 = QFrame(self.gbRobot)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setStyleSheet(u"background-color:transparent;")
        self.frame_8.setFrameShape(QFrame.StyledPanel)
        self.frame_8.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_8)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, -1, 0, 0)
        self.lstwRobots = QListWidget(self.frame_8)
        self.lstwRobots.setObjectName(u"lstwRobots")
        self.lstwRobots.setStyleSheet(u"background-color: gray;")
        self.lstwRobots.setResizeMode(QListView.Adjust)

        self.verticalLayout_2.addWidget(self.lstwRobots)


        self.verticalLayout_7.addWidget(self.frame_8)


        self.horizontalLayout_29.addWidget(self.gbRobot)

        self.gbRobotROS = QGroupBox(self.frame_19)
        self.gbRobotROS.setObjectName(u"gbRobotROS")
        self.gbRobotROS.setStyleSheet(u"QGroupBox#gbRobotROS{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobotROS::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top center;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"}")
        self.verticalLayout_19 = QVBoxLayout(self.gbRobotROS)
        self.verticalLayout_19.setSpacing(0)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(-1, 20, 0, 10)
        self.scrollArea_9 = QScrollArea(self.gbRobotROS)
        self.scrollArea_9.setObjectName(u"scrollArea_9")
        sizePolicy5 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.scrollArea_9.sizePolicy().hasHeightForWidth())
        self.scrollArea_9.setSizePolicy(sizePolicy5)
        self.scrollArea_9.setLayoutDirection(Qt.LeftToRight)
        self.scrollArea_9.setStyleSheet(u"background-color:transparent;\n"
"\n"
"")
        self.scrollArea_9.setWidgetResizable(True)
        self.scrollArea_9.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.scrollAreaWidgetContents_9 = QWidget()
        self.scrollAreaWidgetContents_9.setObjectName(u"scrollAreaWidgetContents_9")
        self.scrollAreaWidgetContents_9.setGeometry(QRect(0, 0, 284, 560))
        self.verticalLayout_21 = QVBoxLayout(self.scrollAreaWidgetContents_9)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.verticalLayout_21.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_21.setContentsMargins(0, -1, -1, -1)
        self.frame_20 = QFrame(self.scrollAreaWidgetContents_9)
        self.frame_20.setObjectName(u"frame_20")
        self.frame_20.setStyleSheet(u"background-color: #e6e6e6;\n"
"border-radius:5px;")
        self.frame_20.setFrameShape(QFrame.StyledPanel)
        self.frame_20.setFrameShadow(QFrame.Raised)
        self.verticalLayout_30 = QVBoxLayout(self.frame_20)
        self.verticalLayout_30.setObjectName(u"verticalLayout_30")
        self.gbRobotROSControl = QGroupBox(self.frame_20)
        self.gbRobotROSControl.setObjectName(u"gbRobotROSControl")
        self.gbRobotROSControl.setStyleSheet(u"QGroupBox#gbRobotROSControl{\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	padding-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobotROSControl::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}")
        self.verticalLayout_6 = QVBoxLayout(self.gbRobotROSControl)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.btnROSTeleop = QPushButton(self.gbRobotROSControl)
        self.btnROSTeleop.setObjectName(u"btnROSTeleop")
        self.btnROSTeleop.setMinimumSize(QSize(94, 40))
        self.btnROSTeleop.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
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

        self.verticalLayout_8.addWidget(self.btnROSTeleop)


        self.verticalLayout_6.addLayout(self.verticalLayout_8)


        self.verticalLayout_30.addWidget(self.gbRobotROSControl)

        self.gbRobotROSNavigation = QGroupBox(self.frame_20)
        self.gbRobotROSNavigation.setObjectName(u"gbRobotROSNavigation")
        self.gbRobotROSNavigation.setStyleSheet(u"QGroupBox#gbRobotROSNavigation{\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	padding-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobotROSNavigation::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}")
        self.verticalLayout_10 = QVBoxLayout(self.gbRobotROSNavigation)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.rbROSNone = QRadioButton(self.gbRobotROSNavigation)
        self.rbROSNone.setObjectName(u"rbROSNone")
        self.rbROSNone.setMinimumSize(QSize(0, 40))
        self.rbROSNone.setChecked(True)

        self.horizontalLayout_9.addWidget(self.rbROSNone)


        self.verticalLayout_9.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.rbROSSlam = QRadioButton(self.gbRobotROSNavigation)
        self.rbROSSlam.setObjectName(u"rbROSSlam")
        self.rbROSSlam.setEnabled(False)
        self.rbROSSlam.setMinimumSize(QSize(0, 40))
        self.rbROSSlam.setCheckable(False)

        self.horizontalLayout_7.addWidget(self.rbROSSlam)

        self.btnROSSlamEdit = QPushButton(self.gbRobotROSNavigation)
        self.btnROSSlamEdit.setObjectName(u"btnROSSlamEdit")
        sizePolicy1.setHeightForWidth(self.btnROSSlamEdit.sizePolicy().hasHeightForWidth())
        self.btnROSSlamEdit.setSizePolicy(sizePolicy1)
        self.btnROSSlamEdit.setMinimumSize(QSize(94, 0))
        self.btnROSSlamEdit.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
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

        self.horizontalLayout_7.addWidget(self.btnROSSlamEdit)

        self.horizontalLayout_7.setStretch(0, 1)

        self.verticalLayout_9.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.rbROSNavigation = QRadioButton(self.gbRobotROSNavigation)
        self.rbROSNavigation.setObjectName(u"rbROSNavigation")
        self.rbROSNavigation.setEnabled(False)
        self.rbROSNavigation.setMinimumSize(QSize(0, 40))
        self.rbROSNavigation.setChecked(False)

        self.horizontalLayout_8.addWidget(self.rbROSNavigation)

        self.btnROSNavigationEdit = QPushButton(self.gbRobotROSNavigation)
        self.btnROSNavigationEdit.setObjectName(u"btnROSNavigationEdit")
        sizePolicy1.setHeightForWidth(self.btnROSNavigationEdit.sizePolicy().hasHeightForWidth())
        self.btnROSNavigationEdit.setSizePolicy(sizePolicy1)
        self.btnROSNavigationEdit.setMinimumSize(QSize(94, 0))
        self.btnROSNavigationEdit.setStyleSheet(u"QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 4px;\n"
"padding: 5px;\n"
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

        self.horizontalLayout_8.addWidget(self.btnROSNavigationEdit)


        self.verticalLayout_9.addLayout(self.horizontalLayout_8)


        self.verticalLayout_10.addLayout(self.verticalLayout_9)


        self.verticalLayout_30.addWidget(self.gbRobotROSNavigation)

        self.gbRobotROSJnp = QGroupBox(self.frame_20)
        self.gbRobotROSJnp.setObjectName(u"gbRobotROSJnp")
        self.gbRobotROSJnp.setStyleSheet(u"QGroupBox#gbRobotROSJnp{\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	padding-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox#gbRobotROSJnp::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}")
        self.gbRobotROSJnp.setCheckable(False)
        self.gbRobotROSJnp.setChecked(False)
        self.verticalLayout_12 = QVBoxLayout(self.gbRobotROSJnp)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.cbROSJnpOptionsEnable = QCheckBox(self.gbRobotROSJnp)
        self.cbROSJnpOptionsEnable.setObjectName(u"cbROSJnpOptionsEnable")
        self.cbROSJnpOptionsEnable.setEnabled(True)
        self.cbROSJnpOptionsEnable.setCheckable(True)
        self.cbROSJnpOptionsEnable.setChecked(False)

        self.verticalLayout_11.addWidget(self.cbROSJnpOptionsEnable)

        self.frmROSJnpOptions = QFrame(self.gbRobotROSJnp)
        self.frmROSJnpOptions.setObjectName(u"frmROSJnpOptions")
        self.frmROSJnpOptions.setFrameShape(QFrame.StyledPanel)
        self.frmROSJnpOptions.setFrameShadow(QFrame.Raised)
        self.verticalLayout_15 = QVBoxLayout(self.frmROSJnpOptions)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_14 = QVBoxLayout()
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(15, -1, -1, -1)
        self.cbROSJnpOptionTerminal = QCheckBox(self.frmROSJnpOptions)
        self.cbROSJnpOptionTerminal.setObjectName(u"cbROSJnpOptionTerminal")

        self.verticalLayout_14.addWidget(self.cbROSJnpOptionTerminal)


        self.verticalLayout_15.addLayout(self.verticalLayout_14)


        self.verticalLayout_11.addWidget(self.frmROSJnpOptions)


        self.verticalLayout_12.addLayout(self.verticalLayout_11)


        self.verticalLayout_30.addWidget(self.gbRobotROSJnp)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_30.addItem(self.verticalSpacer_3)


        self.verticalLayout_21.addWidget(self.frame_20)

        self.scrollArea_9.setWidget(self.scrollAreaWidgetContents_9)

        self.verticalLayout_19.addWidget(self.scrollArea_9)


        self.horizontalLayout_29.addWidget(self.gbRobotROS)


        self.verticalLayout.addWidget(self.frame_19)

        self.frame_4 = QFrame(self.centralwidget)
        self.frame_4.setObjectName(u"frame_4")
        sizePolicy6 = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(25)
        sizePolicy6.setHeightForWidth(self.frame_4.sizePolicy().hasHeightForWidth())
        self.frame_4.setSizePolicy(sizePolicy6)
        self.frame_4.setMinimumSize(QSize(0, 40))
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Plain)
        self.frame_4.setLineWidth(0)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 5)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer)

        self.btnStartSimulator = QPushButton(self.frame_4)
        self.btnStartSimulator.setObjectName(u"btnStartSimulator")
        sizePolicy7 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.btnStartSimulator.sizePolicy().hasHeightForWidth())
        self.btnStartSimulator.setSizePolicy(sizePolicy7)
        self.btnStartSimulator.setMinimumSize(QSize(100, 0))
        self.btnStartSimulator.setStyleSheet(u"    color: white;")

        self.horizontalLayout_5.addWidget(self.btnStartSimulator)


        self.horizontalLayout_6.addLayout(self.horizontalLayout_5)


        self.verticalLayout.addWidget(self.frame_4)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1135, 22))
        self.menuFIle = QMenu(self.menubar)
        self.menuFIle.setObjectName(u"menuFIle")
        self.menuDB = QMenu(self.menubar)
        self.menuDB.setObjectName(u"menuDB")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        QWidget.setTabOrder(self.scrollArea, self.btnStartSimulator)

        self.menubar.addAction(self.menuFIle.menuAction())
        self.menubar.addAction(self.menuDB.menuAction())
        self.menuFIle.addAction(self.actionOpen)
        self.menuFIle.addAction(self.actionSave)
        self.menuFIle.addAction(self.actionSave_as)
        self.menuFIle.addSeparator()
        self.menuFIle.addAction(self.actionExit)
        self.menuDB.addAction(self.actionOpenDB)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"3DAgent Simulator", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionSave_as.setText(QCoreApplication.translate("MainWindow", u"Save as", None))
        self.actionExis.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionOpenDB.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.gbWorld.setTitle(QCoreApplication.translate("MainWindow", u"World", None))
        self.lbWorldImage.setText("")
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Option", None))
        self.chkWorldOptionPerson.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Person", None))
        self.lbRandomColor.setText(QCoreApplication.translate("MainWindow", u"Random Color", None))
        self.chkWorldOptionRandomColor.setText("")
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Bulding", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Random Color", None))
        self.checkBox.setText("")
        self.gbRobot.setTitle(QCoreApplication.translate("MainWindow", u"Robot", None))
        self.btnAddRobot.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.btnDeleteRobot.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.btnAddModel.setText(QCoreApplication.translate("MainWindow", u"Add model", None))
        self.gbRobotROS.setTitle(QCoreApplication.translate("MainWindow", u"ROS", None))
        self.gbRobotROSControl.setTitle(QCoreApplication.translate("MainWindow", u"Control", None))
        self.btnROSTeleop.setText(QCoreApplication.translate("MainWindow", u"Teleop", None))
        self.gbRobotROSNavigation.setTitle(QCoreApplication.translate("MainWindow", u"Navigation", None))
        self.rbROSNone.setText(QCoreApplication.translate("MainWindow", u"None", None))
        self.rbROSSlam.setText(QCoreApplication.translate("MainWindow", u"Slam", None))
        self.btnROSSlamEdit.setText(QCoreApplication.translate("MainWindow", u"edit", None))
        self.rbROSNavigation.setText(QCoreApplication.translate("MainWindow", u"Navigation", None))
        self.btnROSNavigationEdit.setText(QCoreApplication.translate("MainWindow", u"edit", None))
        self.gbRobotROSJnp.setTitle(QCoreApplication.translate("MainWindow", u"Jnp", None))
        self.cbROSJnpOptionsEnable.setText(QCoreApplication.translate("MainWindow", u"Enable", None))
        self.cbROSJnpOptionTerminal.setText(QCoreApplication.translate("MainWindow", u"Run the script in terminal", None))
        self.btnStartSimulator.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.menuFIle.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuDB.setTitle(QCoreApplication.translate("MainWindow", u"DB", None))
    # retranslateUi

