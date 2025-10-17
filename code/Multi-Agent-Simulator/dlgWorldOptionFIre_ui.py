# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgWorldOptionFIre.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_DlgWorldOptionFire(object):
    def setupUi(self, DlgWorldOptionFire):
        if not DlgWorldOptionFire.objectName():
            DlgWorldOptionFire.setObjectName(u"DlgWorldOptionFire")
        DlgWorldOptionFire.resize(400, 300)
        self.verticalLayout = QVBoxLayout(DlgWorldOptionFire)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(DlgWorldOptionFire)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalWidget = QWidget(self.frame)
        self.verticalWidget.setObjectName(u"verticalWidget")
        self.verticalLayout_2 = QVBoxLayout(self.verticalWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_2 = QFrame(self.verticalWidget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)

        self.verticalLayout_2.addWidget(self.frame_2)

        self.frame_3 = QFrame(self.verticalWidget)
        self.frame_3.setObjectName(u"frame_3")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy)
        self.frame_3.setMinimumSize(QSize(0, 40))
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btnWorldOptionFIreCancel = QPushButton(self.frame_3)
        self.btnWorldOptionFIreCancel.setObjectName(u"btnWorldOptionFIreCancel")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btnWorldOptionFIreCancel.sizePolicy().hasHeightForWidth())
        self.btnWorldOptionFIreCancel.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.btnWorldOptionFIreCancel)

        self.btnWorldOptionFIreOK = QPushButton(self.frame_3)
        self.btnWorldOptionFIreOK.setObjectName(u"btnWorldOptionFIreOK")
        sizePolicy1.setHeightForWidth(self.btnWorldOptionFIreOK.sizePolicy().hasHeightForWidth())
        self.btnWorldOptionFIreOK.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.btnWorldOptionFIreOK)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addWidget(self.frame_3)


        self.verticalLayout_3.addWidget(self.verticalWidget)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(DlgWorldOptionFire)

        QMetaObject.connectSlotsByName(DlgWorldOptionFire)
    # setupUi

    def retranslateUi(self, DlgWorldOptionFire):
        DlgWorldOptionFire.setWindowTitle(QCoreApplication.translate("DlgWorldOptionFire", u"World Option - Fire", None))
        self.btnWorldOptionFIreCancel.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Cancel", None))
        self.btnWorldOptionFIreOK.setText(QCoreApplication.translate("DlgWorldOptionFire", u"OK", None))
    # retranslateUi

