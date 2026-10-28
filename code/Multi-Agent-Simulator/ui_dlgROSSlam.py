# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgROSSlamkRWLTP.ui'
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
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_DlgROSSlam(object):
    def setupUi(self, DlgROSSlam):
        if not DlgROSSlam.objectName():
            DlgROSSlam.setObjectName(u"DlgROSSlam")
        DlgROSSlam.resize(614, 191)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DlgROSSlam.sizePolicy().hasHeightForWidth())
        DlgROSSlam.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(DlgROSSlam)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.fmain = QFrame(DlgROSSlam)
        self.fmain.setObjectName(u"fmain")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.fmain.sizePolicy().hasHeightForWidth())
        self.fmain.setSizePolicy(sizePolicy1)
        self.fmain.setFrameShape(QFrame.StyledPanel)
        self.fmain.setFrameShadow(QFrame.Raised)
        self.fmain.setLineWidth(0)
        self.verticalLayout_2 = QVBoxLayout(self.fmain)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_2 = QFrame(self.fmain)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy2)
        self.frame_2.setMinimumSize(QSize(0, 50))
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.frame_2.setLineWidth(0)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.groupBox_2 = QGroupBox(self.frame_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy3)
        self.verticalLayout_6 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.frame_3 = QFrame(self.groupBox_2)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.frame_3.setLineWidth(0)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, 0, 6, 0)
        self.label_2 = QLabel(self.frame_3)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_2)

        self.cbSlamRobot = QComboBox(self.frame_3)
        self.cbSlamRobot.setObjectName(u"cbSlamRobot")

        self.horizontalLayout_2.addWidget(self.cbSlamRobot)


        self.verticalLayout_6.addWidget(self.frame_3)

        self.frame_4 = QFrame(self.groupBox_2)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Raised)

        self.verticalLayout_6.addWidget(self.frame_4)


        self.horizontalLayout.addWidget(self.groupBox_2)

        self.groupBox = QGroupBox(self.frame_2)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy3.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy3)
        self.verticalLayout_5 = QVBoxLayout(self.groupBox)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.frame_5 = QFrame(self.groupBox)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(6, 0, 6, 0)
        self.label = QLabel(self.frame_5)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.label)

        self.cbSlamMethod = QComboBox(self.frame_5)
        self.cbSlamMethod.setObjectName(u"cbSlamMethod")

        self.horizontalLayout_6.addWidget(self.cbSlamMethod)


        self.verticalLayout_5.addWidget(self.frame_5)

        self.frame_6 = QFrame(self.groupBox)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Raised)

        self.verticalLayout_5.addWidget(self.frame_6)


        self.horizontalLayout.addWidget(self.groupBox)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.horizontalLayout_7.addLayout(self.horizontalLayout)


        self.verticalLayout_3.addWidget(self.frame_2)

        self.frame = QFrame(self.fmain)
        self.frame.setObjectName(u"frame")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy4)
        self.frame.setMinimumSize(QSize(407, 40))
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setLineWidth(0)
        self.horizontalLayout_4 = QHBoxLayout(self.frame)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(10)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(6, -1, -1, -1)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.btnROSSlamSaveMap = QPushButton(self.frame)
        self.btnROSSlamSaveMap.setObjectName(u"btnROSSlamSaveMap")
        self.btnROSSlamSaveMap.setEnabled(True)
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.btnROSSlamSaveMap.sizePolicy().hasHeightForWidth())
        self.btnROSSlamSaveMap.setSizePolicy(sizePolicy5)

        self.horizontalLayout_3.addWidget(self.btnROSSlamSaveMap)

        self.btnROSSlamStart = QPushButton(self.frame)
        self.btnROSSlamStart.setObjectName(u"btnROSSlamStart")
        sizePolicy5.setHeightForWidth(self.btnROSSlamStart.sizePolicy().hasHeightForWidth())
        self.btnROSSlamStart.setSizePolicy(sizePolicy5)

        self.horizontalLayout_3.addWidget(self.btnROSSlamStart)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)


        self.verticalLayout_3.addWidget(self.frame)


        self.verticalLayout_2.addLayout(self.verticalLayout_3)


        self.verticalLayout.addWidget(self.fmain)


        self.retranslateUi(DlgROSSlam)

        QMetaObject.connectSlotsByName(DlgROSSlam)
    # setupUi

    def retranslateUi(self, DlgROSSlam):
        DlgROSSlam.setWindowTitle(QCoreApplication.translate("DlgROSSlam", u"ROS-Slam", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("DlgROSSlam", u"Model", None))
        self.label_2.setText(QCoreApplication.translate("DlgROSSlam", u"Robot : ", None))
        self.groupBox.setTitle(QCoreApplication.translate("DlgROSSlam", u"Slam", None))
        self.label.setText(QCoreApplication.translate("DlgROSSlam", u"slam_method : ", None))
        self.btnROSSlamSaveMap.setText(QCoreApplication.translate("DlgROSSlam", u"Save Map", None))
        self.btnROSSlamStart.setText(QCoreApplication.translate("DlgROSSlam", u"Slam", None))
    # retranslateUi

