# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgROSCollaborationTaskqPwQjv.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_DlgROSCollaborationTask(object):
    def setupUi(self, DlgROSCollaborationTask):
        if not DlgROSCollaborationTask.objectName():
            DlgROSCollaborationTask.setObjectName(u"DlgROSCollaborationTask")
        DlgROSCollaborationTask.resize(618, 300)
        self.verticalLayout = QVBoxLayout(DlgROSCollaborationTask)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(DlgROSCollaborationTask)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setSpacing(20)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(10)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lstwROSCollaborationTaskRobots = QListWidget(self.frame_2)
        self.lstwROSCollaborationTaskRobots.setObjectName(u"lstwROSCollaborationTaskRobots")
        self.lstwROSCollaborationTaskRobots.setStyleSheet(u"#lstwROSCollaborationTaskRobots {\n"
"    background: transparent;\n"
"    border: none;\n"
"}")

        self.verticalLayout_2.addWidget(self.lstwROSCollaborationTaskRobots)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.pteditROSCollaborationTaskMsg = QPlainTextEdit(self.frame_2)
        self.pteditROSCollaborationTaskMsg.setObjectName(u"pteditROSCollaborationTaskMsg")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pteditROSCollaborationTaskMsg.sizePolicy().hasHeightForWidth())
        self.pteditROSCollaborationTaskMsg.setSizePolicy(sizePolicy)
        self.pteditROSCollaborationTaskMsg.setMinimumSize(QSize(300, 0))
        self.pteditROSCollaborationTaskMsg.setStyleSheet(u"#pteditROSCollaborationTaskMsg {\n"
"    background: transparent;\n"
"    border: none;\n"
"}")
        self.pteditROSCollaborationTaskMsg.setFrameShape(QFrame.NoFrame)
        self.pteditROSCollaborationTaskMsg.setReadOnly(True)

        self.verticalLayout_5.addWidget(self.pteditROSCollaborationTaskMsg)


        self.horizontalLayout.addLayout(self.verticalLayout_5)


        self.verticalLayout_3.addWidget(self.frame_2)

        self.frame_3 = QFrame(self.frame)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame_3)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btnROSCollaborationTaskStart = QPushButton(self.frame_3)
        self.btnROSCollaborationTaskStart.setObjectName(u"btnROSCollaborationTaskStart")

        self.horizontalLayout_2.addWidget(self.btnROSCollaborationTaskStart)


        self.verticalLayout_6.addLayout(self.horizontalLayout_2)


        self.verticalLayout_3.addWidget(self.frame_3)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(DlgROSCollaborationTask)

        QMetaObject.connectSlotsByName(DlgROSCollaborationTask)
    # setupUi

    def retranslateUi(self, DlgROSCollaborationTask):
        DlgROSCollaborationTask.setWindowTitle(QCoreApplication.translate("DlgROSCollaborationTask", u"Start Collaboration Task", None))
        self.btnROSCollaborationTaskStart.setText(QCoreApplication.translate("DlgROSCollaborationTask", u"Start", None))
    # retranslateUi

