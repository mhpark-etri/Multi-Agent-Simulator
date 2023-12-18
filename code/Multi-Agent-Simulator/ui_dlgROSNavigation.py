# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgROSNavigationrPsPXh.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_DlgROSNavigation(object):
    def setupUi(self, DlgROSNavigation):
        if not DlgROSNavigation.objectName():
            DlgROSNavigation.setObjectName(u"DlgROSNavigation")
        DlgROSNavigation.resize(716, 411)
        self.verticalLayout = QVBoxLayout(DlgROSNavigation)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(DlgROSNavigation)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_3 = QFrame(self.frame)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.scrollArea = QScrollArea(self.frame_3)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 338, 335))
        self.horizontalLayout_4 = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.frame_4 = QFrame(self.scrollAreaWidgetContents)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame_4)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.groupBox = QGroupBox(self.frame_4)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy1)
        self.groupBox.setMinimumSize(QSize(0, 0))
        self.horizontalLayout_6 = QHBoxLayout(self.groupBox)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.frame_5 = QFrame(self.groupBox)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label = QLabel(self.frame_5)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.label)

        self.cbROSNaviRobots = QComboBox(self.frame_5)
        self.cbROSNaviRobots.setObjectName(u"cbROSNaviRobots")

        self.horizontalLayout_7.addWidget(self.cbROSNaviRobots)


        self.horizontalLayout_6.addWidget(self.frame_5)


        self.verticalLayout_7.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.frame_4)
        self.groupBox_2.setObjectName(u"groupBox_2")

        self.verticalLayout_7.addWidget(self.groupBox_2)

        self.verticalLayout_7.setStretch(1, 1)

        self.verticalLayout_6.addLayout(self.verticalLayout_7)


        self.horizontalLayout_4.addWidget(self.frame_4)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_5.addWidget(self.scrollArea)


        self.horizontalLayout.addLayout(self.verticalLayout_5)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.lbROSNavigationMapImg = QLabel(self.frame_3)
        self.lbROSNavigationMapImg.setObjectName(u"lbROSNavigationMapImg")
        self.lbROSNavigationMapImg.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.lbROSNavigationMapImg)

        self.ledtROSNaviMapPath = QLineEdit(self.frame_3)
        self.ledtROSNaviMapPath.setObjectName(u"ledtROSNaviMapPath")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.ledtROSNaviMapPath.sizePolicy().hasHeightForWidth())
        self.ledtROSNaviMapPath.setSizePolicy(sizePolicy2)
        self.ledtROSNaviMapPath.setReadOnly(True)

        self.verticalLayout_4.addWidget(self.ledtROSNaviMapPath)

        self.btnROSNaviMapOpen = QPushButton(self.frame_3)
        self.btnROSNaviMapOpen.setObjectName(u"btnROSNaviMapOpen")

        self.verticalLayout_4.addWidget(self.btnROSNaviMapOpen)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addWidget(self.frame_3)

        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy2.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy2)
        self.frame_2.setMinimumSize(QSize(0, 40))
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.btnROSNavigationStart = QPushButton(self.frame_2)
        self.btnROSNavigationStart.setObjectName(u"btnROSNavigationStart")
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.btnROSNavigationStart.sizePolicy().hasHeightForWidth())
        self.btnROSNavigationStart.setSizePolicy(sizePolicy3)

        self.horizontalLayout_3.addWidget(self.btnROSNavigationStart)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_3)


        self.verticalLayout_2.addWidget(self.frame_2)


        self.verticalLayout_3.addLayout(self.verticalLayout_2)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(DlgROSNavigation)

        QMetaObject.connectSlotsByName(DlgROSNavigation)
    # setupUi

    def retranslateUi(self, DlgROSNavigation):
        DlgROSNavigation.setWindowTitle(QCoreApplication.translate("DlgROSNavigation", u"ROS-Navigation", None))
        self.groupBox.setTitle(QCoreApplication.translate("DlgROSNavigation", u"Model", None))
        self.label.setText(QCoreApplication.translate("DlgROSNavigation", u"Robot", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("DlgROSNavigation", u"Option", None))
        self.lbROSNavigationMapImg.setText(QCoreApplication.translate("DlgROSNavigation", u"No image loaded", None))
        self.btnROSNaviMapOpen.setText(QCoreApplication.translate("DlgROSNavigation", u"Open map", None))
        self.btnROSNavigationStart.setText(QCoreApplication.translate("DlgROSNavigation", u"Start", None))
    # retranslateUi

