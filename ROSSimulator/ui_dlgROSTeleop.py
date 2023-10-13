# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgROSTeleop.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QLayout,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_DlgROSTeleop(object):
    def setupUi(self, DlgROSTeleop):
        if not DlgROSTeleop.objectName():
            DlgROSTeleop.setObjectName(u"DlgROSTeleop")
        DlgROSTeleop.setWindowModality(Qt.NonModal)
        DlgROSTeleop.resize(199, 112)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DlgROSTeleop.sizePolicy().hasHeightForWidth())
        DlgROSTeleop.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(DlgROSTeleop)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.fmain = QFrame(DlgROSTeleop)
        self.fmain.setObjectName(u"fmain")
        sizePolicy.setHeightForWidth(self.fmain.sizePolicy().hasHeightForWidth())
        self.fmain.setSizePolicy(sizePolicy)
        self.fmain.setLayoutDirection(Qt.LeftToRight)
        self.fmain.setFrameShape(QFrame.StyledPanel)
        self.fmain.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.fmain)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_3.addWidget(self.fmain)


        self.retranslateUi(DlgROSTeleop)

        QMetaObject.connectSlotsByName(DlgROSTeleop)
    # setupUi

    def retranslateUi(self, DlgROSTeleop):
        DlgROSTeleop.setWindowTitle(QCoreApplication.translate("DlgROSTeleop", u"ROS - Teleop", None))
    # retranslateUi

