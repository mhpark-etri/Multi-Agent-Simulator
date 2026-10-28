# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgDBOpen.ui'
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
    QLabel, QPushButton, QSizePolicy, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_DlgDBOpen(object):
    def setupUi(self, DlgDBOpen):
        if not DlgDBOpen.objectName():
            DlgDBOpen.setObjectName(u"DlgDBOpen")
        DlgDBOpen.resize(249, 127)
        self.horizontalLayout = QHBoxLayout(DlgDBOpen)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.frame = QFrame(DlgDBOpen)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.frame_4 = QFrame(self.frame)
        self.frame_4.setObjectName(u"frame_4")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_4.sizePolicy().hasHeightForWidth())
        self.frame_4.setSizePolicy(sizePolicy)
        self.frame_4.setMinimumSize(QSize(0, 20))
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.frame_4)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QSize(40, 0))

        self.horizontalLayout_7.addWidget(self.label)

        self.dlgEdtDBID = QTextEdit(self.frame_4)
        self.dlgEdtDBID.setObjectName(u"dlgEdtDBID")

        self.horizontalLayout_7.addWidget(self.dlgEdtDBID)


        self.horizontalLayout_4.addWidget(self.frame_4)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.frame_3 = QFrame(self.frame)
        self.frame_3.setObjectName(u"frame_3")
        sizePolicy.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy)
        self.frame_3.setMinimumSize(QSize(0, 20))
        self.frame_3.setFrameShape(QFrame.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.frame_3)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)
        self.label_2.setMinimumSize(QSize(40, 0))

        self.horizontalLayout_6.addWidget(self.label_2)

        self.dlgEdtDBPW = QTextEdit(self.frame_3)
        self.dlgEdtDBPW.setObjectName(u"dlgEdtDBPW")

        self.horizontalLayout_6.addWidget(self.dlgEdtDBPW)


        self.horizontalLayout_3.addWidget(self.frame_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy2)
        self.frame_2.setMinimumSize(QSize(0, 0))
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.dlgBtnDBOpen = QPushButton(self.frame_2)
        self.dlgBtnDBOpen.setObjectName(u"dlgBtnDBOpen")

        self.horizontalLayout_5.addWidget(self.dlgBtnDBOpen)

        self.dlgBtnDBClose = QPushButton(self.frame_2)
        self.dlgBtnDBClose.setObjectName(u"dlgBtnDBClose")

        self.horizontalLayout_5.addWidget(self.dlgBtnDBClose)


        self.horizontalLayout_2.addWidget(self.frame_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.verticalLayout_3.addLayout(self.verticalLayout_2)


        self.horizontalLayout.addWidget(self.frame)


        self.retranslateUi(DlgDBOpen)

        QMetaObject.connectSlotsByName(DlgDBOpen)
    # setupUi

    def retranslateUi(self, DlgDBOpen):
        DlgDBOpen.setWindowTitle(QCoreApplication.translate("DlgDBOpen", u"DB \uc5f0\uacb0", None))
        self.label.setText(QCoreApplication.translate("DlgDBOpen", u"ID : ", None))
        self.label_2.setText(QCoreApplication.translate("DlgDBOpen", u"PW : ", None))
        self.dlgBtnDBOpen.setText(QCoreApplication.translate("DlgDBOpen", u"\uc5f4\uae30", None))
        self.dlgBtnDBClose.setText(QCoreApplication.translate("DlgDBOpen", u"\uc885\ub8cc", None))
    # retranslateUi

