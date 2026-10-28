# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgROSRViz.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_DlgROSRViz(object):
    def setupUi(self, DlgROSRViz):
        if not DlgROSRViz.objectName():
            DlgROSRViz.setObjectName(u"DlgROSRViz")
        DlgROSRViz.resize(199, 112)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DlgROSRViz.sizePolicy().hasHeightForWidth())
        DlgROSRViz.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(DlgROSRViz)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.fmain = QFrame(DlgROSRViz)
        self.fmain.setObjectName(u"fmain")
        sizePolicy.setHeightForWidth(self.fmain.sizePolicy().hasHeightForWidth())
        self.fmain.setSizePolicy(sizePolicy)
        self.fmain.setFrameShape(QFrame.StyledPanel)
        self.fmain.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.fmain)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.fmain)


        self.retranslateUi(DlgROSRViz)

        QMetaObject.connectSlotsByName(DlgROSRViz)
    # setupUi

    def retranslateUi(self, DlgROSRViz):
        DlgROSRViz.setWindowTitle(QCoreApplication.translate("DlgROSRViz", u"ROS - RViz", None))
    # retranslateUi

