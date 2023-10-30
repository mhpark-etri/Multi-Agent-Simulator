# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainryoyzE.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLayout, QListView, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMenuBar,
    QPushButton, QRadioButton, QScrollArea, QSizePolicy,
    QSpacerItem, QStatusBar, QVBoxLayout, QWidget)
import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(1135, 1018)
        MainWindow.setMinimumSize(QSize(0, 0))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setAutoFillBackground(False)
        self.centralwidget.setStyleSheet(u"background-color: gray;")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 0, -1, 0)
        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMinimumSize(QSize(0, 250))
        self.groupBox.setStyleSheet(u"QGroupBox{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"    left: 30px;\n"
"}")
        self.horizontalLayout_2 = QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(10, 20, 10, 10)
        self.scrollArea = QScrollArea(self.groupBox)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setStyleSheet(u"background-color: #e6e6e6;\n"
"border-radius:5px;")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1095, 203))
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
        self.horizontalLayout.setContentsMargins(40, 10, 40, 10)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_2 = QFrame(self.frame_3)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.frame_2)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.frame_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(0, 0))
        self.label_2.setStyleSheet(u"    border: 1px solid 	white;")
        self.label_2.setPixmap(QPixmap(u":/thumbnail/Resources/thumbnail/icon_thumb_world_warehouse.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setWordWrap(False)
        self.label_2.setOpenExternalLinks(False)

        self.verticalLayout_9.addWidget(self.label_2)

        self.label = QLabel(self.frame_2)
        self.label.setObjectName(u"label")
        self.label.setStyleSheet(u"font: 700 12pt \"Umpush\";")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_9.addWidget(self.label)

        self.rbWorldWarehouse = QRadioButton(self.frame_2)
        self.rbWorldWarehouse.setObjectName(u"rbWorldWarehouse")
        self.rbWorldWarehouse.setLayoutDirection(Qt.LeftToRight)
        self.rbWorldWarehouse.setChecked(True)
        self.rbWorldWarehouse.setAutoExclusive(False)

        self.verticalLayout_9.addWidget(self.rbWorldWarehouse)

        self.verticalLayout_9.setStretch(0, 1)

        self.verticalLayout_3.addWidget(self.frame_2)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.frame_5 = QFrame(self.frame_3)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setEnabled(True)
        self.frame_5.setMinimumSize(QSize(0, 0))
        self.frame_5.setFrameShape(QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.frame_5)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.frame_5)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setEnabled(True)
        self.label_3.setStyleSheet(u"    border: 1px solid 	white;")
        self.label_3.setPixmap(QPixmap(u":/thumbnail/Resources/thumbnail/icon_thumb_world_hospital.png"))
        self.label_3.setScaledContents(True)

        self.verticalLayout_10.addWidget(self.label_3)

        self.label_4 = QLabel(self.frame_5)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setEnabled(True)
        self.label_4.setStyleSheet(u"font: 700 12pt \"Umpush\";")
        self.label_4.setScaledContents(False)
        self.label_4.setAlignment(Qt.AlignCenter)

        self.verticalLayout_10.addWidget(self.label_4)

        self.rbWorldHospital = QRadioButton(self.frame_5)
        self.rbWorldHospital.setObjectName(u"rbWorldHospital")
        self.rbWorldHospital.setEnabled(True)
        self.rbWorldHospital.setAutoExclusive(False)

        self.verticalLayout_10.addWidget(self.rbWorldHospital)

        self.verticalLayout_10.setStretch(0, 1)

        self.verticalLayout_4.addWidget(self.frame_5)


        self.horizontalLayout.addLayout(self.verticalLayout_4)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.frame_6 = QFrame(self.frame_3)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setEnabled(True)
        self.frame_6.setMinimumSize(QSize(0, 0))
        self.frame_6.setFrameShape(QFrame.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.verticalLayout_11 = QVBoxLayout(self.frame_6)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.frame_6)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setEnabled(True)
        self.label_5.setStyleSheet(u"    border: 1px solid 	white;")
        self.label_5.setPixmap(QPixmap(u":/thumbnail/Resources/thumbnail/icon_thumb_world_smallhouse.png"))
        self.label_5.setScaledContents(True)

        self.verticalLayout_11.addWidget(self.label_5)

        self.label_6 = QLabel(self.frame_6)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setEnabled(True)
        self.label_6.setStyleSheet(u"font: 700 12pt \"Umpush\";")
        self.label_6.setAlignment(Qt.AlignCenter)

        self.verticalLayout_11.addWidget(self.label_6)

        self.rbWorldSmallHouse = QRadioButton(self.frame_6)
        self.rbWorldSmallHouse.setObjectName(u"rbWorldSmallHouse")
        self.rbWorldSmallHouse.setEnabled(True)
        self.rbWorldSmallHouse.setAutoExclusive(False)

        self.verticalLayout_11.addWidget(self.rbWorldSmallHouse)

        self.verticalLayout_11.setStretch(0, 1)

        self.verticalLayout_5.addWidget(self.frame_6)


        self.horizontalLayout.addLayout(self.verticalLayout_5)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.frame_7 = QFrame(self.frame_3)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setEnabled(True)
        self.frame_7.setFrameShape(QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.verticalLayout_12 = QVBoxLayout(self.frame_7)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.frame_7)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setEnabled(True)
        self.label_7.setStyleSheet(u"    border: 1px solid 	white;")
        self.label_7.setPixmap(QPixmap(u":/thumbnail/Resources/thumbnail/icon_thumb_world_bookstore.png"))
        self.label_7.setScaledContents(True)

        self.verticalLayout_12.addWidget(self.label_7)

        self.label_8 = QLabel(self.frame_7)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setEnabled(True)
        self.label_8.setStyleSheet(u"font: 700 12pt \"Umpush\";")
        self.label_8.setAlignment(Qt.AlignCenter)

        self.verticalLayout_12.addWidget(self.label_8)

        self.rbWorldBookStore = QRadioButton(self.frame_7)
        self.rbWorldBookStore.setObjectName(u"rbWorldBookStore")
        self.rbWorldBookStore.setEnabled(True)
        self.rbWorldBookStore.setAutoExclusive(False)

        self.verticalLayout_12.addWidget(self.rbWorldBookStore)

        self.verticalLayout_12.setStretch(0, 1)

        self.verticalLayout_6.addWidget(self.frame_7)


        self.horizontalLayout.addLayout(self.verticalLayout_6)


        self.horizontalLayout_4.addLayout(self.horizontalLayout)


        self.horizontalLayout_3.addWidget(self.frame_3)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_2.addWidget(self.scrollArea)


        self.verticalLayout.addWidget(self.groupBox)

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
        self.groupBox_2 = QGroupBox(self.frame_19)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy1)
        self.groupBox_2.setMinimumSize(QSize(850, 0))
        self.groupBox_2.setLayoutDirection(Qt.LeftToRight)
        self.groupBox_2.setStyleSheet(u"QGroupBox{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"    left: 30px;\n"
"}")
        self.verticalLayout_7 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(9, 20, 9, 10)
        self.frame_21 = QFrame(self.groupBox_2)
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


        self.verticalLayout_7.addWidget(self.frame_21)

        self.frame_8 = QFrame(self.groupBox_2)
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


        self.horizontalLayout_29.addWidget(self.groupBox_2)

        self.groupBox_4 = QGroupBox(self.frame_19)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setStyleSheet(u"QGroupBox{\n"
"    border: 1px solid 	darkgray;\n"
"    background-color: #cccccc;\n"
"    margin-top: 15px;\n"
"    color: white;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 30px 5px 30px;\n"
"    top: -15px;\n"
"    left: 70px;\n"
"}")
        self.verticalLayout_19 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_19.setSpacing(0)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(-1, 20, 0, 10)
        self.scrollArea_9 = QScrollArea(self.groupBox_4)
        self.scrollArea_9.setObjectName(u"scrollArea_9")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.scrollArea_9.sizePolicy().hasHeightForWidth())
        self.scrollArea_9.setSizePolicy(sizePolicy2)
        self.scrollArea_9.setLayoutDirection(Qt.LeftToRight)
        self.scrollArea_9.setStyleSheet(u"background-color:transparent;\n"
"\n"
"")
        self.scrollArea_9.setWidgetResizable(True)
        self.scrollArea_9.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.scrollAreaWidgetContents_9 = QWidget()
        self.scrollAreaWidgetContents_9.setObjectName(u"scrollAreaWidgetContents_9")
        self.scrollAreaWidgetContents_9.setGeometry(QRect(0, 0, 234, 566))
        self.verticalLayout_21 = QVBoxLayout(self.scrollAreaWidgetContents_9)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.verticalLayout_21.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_21.setContentsMargins(0, -1, -1, -1)
        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(9, 9, 9, 9)
        self.btnROSTeleop = QPushButton(self.scrollAreaWidgetContents_9)
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

        self.verticalLayout_15.addWidget(self.btnROSTeleop)


        self.verticalLayout_21.addLayout(self.verticalLayout_15)

        self.frame_20 = QFrame(self.scrollAreaWidgetContents_9)
        self.frame_20.setObjectName(u"frame_20")
        self.frame_20.setStyleSheet(u"background-color: #e6e6e6;\n"
"border-radius:5px;")
        self.frame_20.setFrameShape(QFrame.StyledPanel)
        self.frame_20.setFrameShadow(QFrame.Raised)
        self.verticalLayout_30 = QVBoxLayout(self.frame_20)
        self.verticalLayout_30.setObjectName(u"verticalLayout_30")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.rbROSNone = QRadioButton(self.frame_20)
        self.rbROSNone.setObjectName(u"rbROSNone")
        self.rbROSNone.setMinimumSize(QSize(0, 40))

        self.horizontalLayout_9.addWidget(self.rbROSNone)


        self.verticalLayout_30.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.rbROSSlam = QRadioButton(self.frame_20)
        self.rbROSSlam.setObjectName(u"rbROSSlam")
        self.rbROSSlam.setMinimumSize(QSize(0, 40))
        self.rbROSSlam.setCheckable(False)

        self.horizontalLayout_7.addWidget(self.rbROSSlam)

        self.btnROSSlamEdit = QPushButton(self.frame_20)
        self.btnROSSlamEdit.setObjectName(u"btnROSSlamEdit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.btnROSSlamEdit.sizePolicy().hasHeightForWidth())
        self.btnROSSlamEdit.setSizePolicy(sizePolicy3)
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

        self.verticalLayout_30.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.rbROSNavigation = QRadioButton(self.frame_20)
        self.rbROSNavigation.setObjectName(u"rbROSNavigation")
        self.rbROSNavigation.setMinimumSize(QSize(0, 40))
        self.rbROSNavigation.setChecked(True)

        self.horizontalLayout_8.addWidget(self.rbROSNavigation)

        self.btnROSNavigationEdit = QPushButton(self.frame_20)
        self.btnROSNavigationEdit.setObjectName(u"btnROSNavigationEdit")
        sizePolicy3.setHeightForWidth(self.btnROSNavigationEdit.sizePolicy().hasHeightForWidth())
        self.btnROSNavigationEdit.setSizePolicy(sizePolicy3)
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


        self.verticalLayout_30.addLayout(self.horizontalLayout_8)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_30.addItem(self.verticalSpacer_3)


        self.verticalLayout_21.addWidget(self.frame_20)

        self.scrollArea_9.setWidget(self.scrollAreaWidgetContents_9)

        self.verticalLayout_19.addWidget(self.scrollArea_9)


        self.horizontalLayout_29.addWidget(self.groupBox_4)


        self.verticalLayout.addWidget(self.frame_19)

        self.frame_4 = QFrame(self.centralwidget)
        self.frame_4.setObjectName(u"frame_4")
        sizePolicy4 = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(25)
        sizePolicy4.setHeightForWidth(self.frame_4.sizePolicy().hasHeightForWidth())
        self.frame_4.setSizePolicy(sizePolicy4)
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
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.btnStartSimulator.sizePolicy().hasHeightForWidth())
        self.btnStartSimulator.setSizePolicy(sizePolicy5)
        self.btnStartSimulator.setMinimumSize(QSize(100, 0))
        self.btnStartSimulator.setStyleSheet(u"    color: white;")

        self.horizontalLayout_5.addWidget(self.btnStartSimulator)


        self.horizontalLayout_6.addLayout(self.horizontalLayout_5)


        self.verticalLayout.addWidget(self.frame_4)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1135, 27))
        self.menuFIle = QMenu(self.menubar)
        self.menuFIle.setObjectName(u"menuFIle")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        QWidget.setTabOrder(self.scrollArea, self.btnStartSimulator)

        self.menubar.addAction(self.menuFIle.menuAction())

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"3DAgent Simulator", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"World", None))
        self.label_2.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"warehouse", None))
        self.rbWorldWarehouse.setText("")
        self.label_3.setText("")
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"hospital", None))
        self.rbWorldHospital.setText("")
        self.label_5.setText("")
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"small house", None))
        self.rbWorldSmallHouse.setText("")
        self.label_7.setText("")
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"book store", None))
        self.rbWorldBookStore.setText("")
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Robot", None))
        self.btnAddRobot.setText(QCoreApplication.translate("MainWindow", u"Add", None))
        self.btnDeleteRobot.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"ROS", None))
        self.btnROSTeleop.setText(QCoreApplication.translate("MainWindow", u"Teleop", None))
        self.rbROSNone.setText(QCoreApplication.translate("MainWindow", u"None", None))
        self.rbROSSlam.setText(QCoreApplication.translate("MainWindow", u"Slam", None))
        self.btnROSSlamEdit.setText(QCoreApplication.translate("MainWindow", u"edit", None))
        self.rbROSNavigation.setText(QCoreApplication.translate("MainWindow", u"Navigation", None))
        self.btnROSNavigationEdit.setText(QCoreApplication.translate("MainWindow", u"edit", None))
        self.btnStartSimulator.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.menuFIle.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi
