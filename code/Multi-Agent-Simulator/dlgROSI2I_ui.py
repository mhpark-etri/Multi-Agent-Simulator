# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgROSI2I.ui'
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
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit,
    QPushButton, QProgressBar, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_DlgROSI2I(object):
    def setupUi(self, DlgROSI2I):
        if not DlgROSI2I.objectName():
            DlgROSI2I.setObjectName(u"DlgROSI2I")
        DlgROSI2I.resize(780, 850)
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
        self.gbROSI2ICapture = QGroupBox(self.gbROSI2IOption)
        self.gbROSI2ICapture.setObjectName(u"gbROSI2ICapture")
        self.gbROSI2ICapture.setStyleSheet(u"QGroupBox#gbROSI2ICapture {\n"
"    border: 1px solid darkgray;\n"
"    background-color: #d4d4d4;\n"
"    margin-top: 14px;\n"
"    color: #ffffff;\n"
"}\n"
"QGroupBox#gbROSI2ICapture::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top left;\n"
"    left: 8px;\n"
"    background-color: gray;\n"
"    padding: 4px 8px 4px 8px;\n"
"    top: -14px;\n"
"}")
        self.verticalLayoutROSI2ICapture = QVBoxLayout(self.gbROSI2ICapture)
        self.verticalLayoutROSI2ICapture.setObjectName(u"verticalLayoutROSI2ICapture")
        self.verticalLayoutROSI2ICapture.setContentsMargins(-1, 18, -1, -1)
        self.frame_2 = QFrame(self.gbROSI2ICapture)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lbROSI2ICaptureFolderPath = QLabel(self.frame_2)
        self.lbROSI2ICaptureFolderPath.setObjectName(u"lbROSI2ICaptureFolderPath")

        self.verticalLayout_2.addWidget(self.lbROSI2ICaptureFolderPath)

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

        self.ckbROSI2IShowCaptureFolder = QCheckBox(self.frame_2)
        self.ckbROSI2IShowCaptureFolder.setObjectName(u"ckbROSI2IShowCaptureFolder")
        self.ckbROSI2IShowCaptureFolder.setChecked(True)
        self.verticalLayout_2.addWidget(self.ckbROSI2IShowCaptureFolder)

        self.horizontalLayoutROSI2ICaptureFPS = QHBoxLayout()
        self.horizontalLayoutROSI2ICaptureFPS.setObjectName(u"horizontalLayoutROSI2ICaptureFPS")
        self.lbROSI2ICaptureFPS = QLabel(self.frame_2)
        self.lbROSI2ICaptureFPS.setObjectName(u"lbROSI2ICaptureFPS")

        self.horizontalLayoutROSI2ICaptureFPS.addWidget(self.lbROSI2ICaptureFPS)

        self.horizontalSpacerROSI2ICaptureFPS = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayoutROSI2ICaptureFPS.addItem(self.horizontalSpacerROSI2ICaptureFPS)

        self.leditROSI2ICaptureFPS = QLineEdit(self.frame_2)
        self.leditROSI2ICaptureFPS.setObjectName(u"leditROSI2ICaptureFPS")
        self.leditROSI2ICaptureFPS.setMaximumSize(QSize(90, 16777215))
        self.leditROSI2ICaptureFPS.setAlignment(Qt.AlignRight)

        self.horizontalLayoutROSI2ICaptureFPS.addWidget(self.leditROSI2ICaptureFPS)

        self.verticalLayout_2.addLayout(self.horizontalLayoutROSI2ICaptureFPS)

        self.verticalLayoutROSI2ICapture.addWidget(self.frame_2)
        self.verticalLayout_19.addWidget(self.gbROSI2ICapture)

        self.gbROSI2IFireModule = QGroupBox(self.gbROSI2IOption)
        self.gbROSI2IFireModule.setObjectName(u"gbROSI2IFireModule")
        self.gbROSI2IFireModule.setStyleSheet(u"QGroupBox#gbROSI2IFireModule {\n"
"    border: 1px solid darkgray;\n"
"    background-color: #d4d4d4;\n"
"    margin-top: 14px;\n"
"    color: #ffffff;\n"
"}\n"
"QGroupBox#gbROSI2IFireModule::title {\n"
"    border: 1px solid white;\n"
"    subcontrol-position: top left;\n"
"    left: 8px;\n"
"    background-color: gray;\n"
"    padding: 4px 8px 4px 8px;\n"
"    top: -14px;\n"
"}")
        self.verticalLayoutROSI2IFireModule = QVBoxLayout(self.gbROSI2IFireModule)
        self.verticalLayoutROSI2IFireModule.setObjectName(u"verticalLayoutROSI2IFireModule")
        self.verticalLayoutROSI2IFireModule.setContentsMargins(-1, 18, -1, -1)
        self.lbROSI2IFireModulePath = QLabel(self.gbROSI2IFireModule)
        self.lbROSI2IFireModulePath.setObjectName(u"lbROSI2IFireModulePath")

        self.verticalLayoutROSI2IFireModule.addWidget(self.lbROSI2IFireModulePath)

        self.horizontalLayoutROSI2IFireModulePath = QHBoxLayout()
        self.horizontalLayoutROSI2IFireModulePath.setObjectName(u"horizontalLayoutROSI2IFireModulePath")
        self.btnROSI2IFireModulePathOpen = QPushButton(self.gbROSI2IFireModule)
        self.btnROSI2IFireModulePathOpen.setObjectName(u"btnROSI2IFireModulePathOpen")

        self.horizontalLayoutROSI2IFireModulePath.addWidget(self.btnROSI2IFireModulePathOpen)

        self.leditROSI2IFireModulePath = QLineEdit(self.gbROSI2IFireModule)
        self.leditROSI2IFireModulePath.setObjectName(u"leditROSI2IFireModulePath")
        self.leditROSI2IFireModulePath.setReadOnly(True)

        self.horizontalLayoutROSI2IFireModulePath.addWidget(self.leditROSI2IFireModulePath)

        self.verticalLayoutROSI2IFireModule.addLayout(self.horizontalLayoutROSI2IFireModulePath)

        self.ckbROSI2IShowResultFolder = QCheckBox(self.gbROSI2IFireModule)
        self.ckbROSI2IShowResultFolder.setObjectName(u"ckbROSI2IShowResultFolder")
        self.ckbROSI2IShowResultFolder.setChecked(True)
        self.verticalLayoutROSI2IFireModule.addWidget(self.ckbROSI2IShowResultFolder)

        self.verticalLayout_19.addWidget(self.gbROSI2IFireModule)

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

        self.gbROSI2IMessages = QGroupBox(DlgROSI2I)
        self.gbROSI2IMessages.setObjectName(u"gbROSI2IMessages")
        self.gbROSI2IMessages.setMinimumSize(QSize(0, 145))
        self.gbROSI2IMessages.setStyleSheet(u"QGroupBox#gbROSI2IMessages {\n"
"    border: 1px solid #aaaaaa;\n"
"    margin-top: 16px;\n"
"}\n"
"QGroupBox#gbROSI2IMessages::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    left: 20px;\n"
"    padding: 5px 19px;\n"
"    background-color: #8b8b8b;\n"
"    color: white;\n"
"}\n"
"QPlainTextEdit#pteROSI2IMessages {\n"
"    background-color: #f4f4f4;\n"
"    color: #222222;\n"
"    border: 1px solid #929292;\n"
"    font-family: monospace;\n"
"    font-size: 9pt;\n"
"}")
        self.verticalLayoutROSI2IMessages = QVBoxLayout(self.gbROSI2IMessages)
        self.verticalLayoutROSI2IMessages.setObjectName(u"verticalLayoutROSI2IMessages")
        self.verticalLayoutROSI2IMessages.setContentsMargins(8, 20, 8, 8)
        self.pteROSI2IMessages = QPlainTextEdit(self.gbROSI2IMessages)
        self.pteROSI2IMessages.setObjectName(u"pteROSI2IMessages")
        self.pteROSI2IMessages.setMinimumSize(QSize(0, 105))
        self.pteROSI2IMessages.setReadOnly(True)
        self.pteROSI2IMessages.setMaximumBlockCount(300)
        self.pteROSI2IMessages.setPlaceholderText(QCoreApplication.translate("DlgROSI2I", u"Capture and I2I fire-generation messages will appear here.", None))
        self.verticalLayoutROSI2IMessages.addWidget(self.pteROSI2IMessages)
        self.verticalLayout.addWidget(self.gbROSI2IMessages)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.prgROSI2IProgress = QProgressBar(DlgROSI2I)
        self.prgROSI2IProgress.setObjectName(u"prgROSI2IProgress")
        sizePolicyProgress = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicyProgress.setHorizontalStretch(1)
        sizePolicyProgress.setVerticalStretch(0)
        sizePolicyProgress.setHeightForWidth(self.prgROSI2IProgress.sizePolicy().hasHeightForWidth())
        self.prgROSI2IProgress.setSizePolicy(sizePolicyProgress)
        self.prgROSI2IProgress.setMinimumSize(QSize(120, 24))
        self.prgROSI2IProgress.setMaximumSize(QSize(16777215, 24))
        self.prgROSI2IProgress.setValue(0)
        self.prgROSI2IProgress.setTextVisible(True)
        self.prgROSI2IProgress.setFormat(u"Ready")
        self.horizontalLayout_2.addWidget(self.prgROSI2IProgress, 1)

        self.btnROSI2IStop = QPushButton(DlgROSI2I)
        self.btnROSI2IStop.setObjectName(u"btnROSI2IStop")
        self.btnROSI2IStop.setMinimumSize(QSize(87, 29))
        self.btnROSI2IStop.setMaximumSize(QSize(87, 29))
        self.btnROSI2IStop.setEnabled(False)
        self.btnROSI2IStop.setStyleSheet(u"QPushButton {\n"
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

        self.horizontalLayout_2.addWidget(self.btnROSI2IStop)

        self.btnROSI2IStart = QPushButton(DlgROSI2I)
        self.btnROSI2IStart.setObjectName(u"btnROSI2IStart")
        self.btnROSI2IStart.setMinimumSize(QSize(87, 29))
        self.btnROSI2IStart.setMaximumSize(QSize(87, 29))
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
        self.gbROSI2ICapture.setTitle(QCoreApplication.translate("DlgROSI2I", u"Capture", None))
        self.ckbROSI2IShowCaptureFolder.setText(QCoreApplication.translate("DlgROSI2I", u"Show Capture Folder", None))
        self.lbROSI2ICaptureFolderPath.setText(QCoreApplication.translate("DlgROSI2I", u"Capture Folder Path :", None))
        self.btnROSI2ICapturePathOpen.setText(QCoreApplication.translate("DlgROSI2I", u"Open", None))
        self.lbROSI2ICaptureFPS.setText(QCoreApplication.translate("DlgROSI2I", u"Capture FPS :", None))
        self.leditROSI2ICaptureFPS.setText(QCoreApplication.translate("DlgROSI2I", u"1", None))
        self.gbROSI2IFireModule.setTitle(QCoreApplication.translate("DlgROSI2I", u"Fire Generation", None))
        self.lbROSI2IFireModulePath.setText(QCoreApplication.translate("DlgROSI2I", u"Fire Generation Module Path :", None))
        self.btnROSI2IFireModulePathOpen.setText(QCoreApplication.translate("DlgROSI2I", u"Open", None))
        self.ckbROSI2IShowResultFolder.setText(QCoreApplication.translate("DlgROSI2I", u"Show Result Folder", None))
        self.leditROSI2IFireModulePath.setText(QCoreApplication.translate("DlgROSI2I", u"/root/tesla/I2I_Simulator/light_fire_pkg", None))
        self.gbROSI2ITopicList.setTitle(QCoreApplication.translate("DlgROSI2I", u"Topic List", None))
        self.gbROSI2IMessages.setTitle(QCoreApplication.translate("DlgROSI2I", u"Messages", None))
        self.pteROSI2IMessages.setPlaceholderText(QCoreApplication.translate("DlgROSI2I", u"Capture and I2I fire-generation messages will appear here.", None))
        self.btnROSI2IStop.setText(QCoreApplication.translate("DlgROSI2I", u"Stop", None))
        self.btnROSI2IStart.setText(QCoreApplication.translate("DlgROSI2I", u"Start", None))
    # retranslateUi

