# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widgetROSCollaborationTaskItemFITeCg.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_WidgetCollaborationTask(object):
    def setupUi(self, WidgetCollaborationTask):
        if not WidgetCollaborationTask.objectName():
            WidgetCollaborationTask.setObjectName(u"WidgetCollaborationTask")
        WidgetCollaborationTask.resize(94, 118)
        WidgetCollaborationTask.setStyleSheet(u"QWidget#WidgetCollaborationTask{\n"
"    border: 1px solid 	darkgray;\n"
"}")
        self.verticalLayout_2 = QVBoxLayout(WidgetCollaborationTask)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.fWidgetCollaborationTask = QFrame(WidgetCollaborationTask)
        self.fWidgetCollaborationTask.setObjectName(u"fWidgetCollaborationTask")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fWidgetCollaborationTask.sizePolicy().hasHeightForWidth())
        self.fWidgetCollaborationTask.setSizePolicy(sizePolicy)
        self.fWidgetCollaborationTask.setStyleSheet(u"QFrame#fWidgetCollaborationTask{\n"
"   border: 1px solid 	darkgray;\n"
"}")
        self.fWidgetCollaborationTask.setFrameShape(QFrame.StyledPanel)
        self.fWidgetCollaborationTask.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.fWidgetCollaborationTask)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbROSCollaborationTaskImage = QLabel(self.fWidgetCollaborationTask)
        self.lbROSCollaborationTaskImage.setObjectName(u"lbROSCollaborationTaskImage")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbROSCollaborationTaskImage.sizePolicy().hasHeightForWidth())
        self.lbROSCollaborationTaskImage.setSizePolicy(sizePolicy1)
        self.lbROSCollaborationTaskImage.setMinimumSize(QSize(0, 70))
        self.lbROSCollaborationTaskImage.setStyleSheet(u"")
        self.lbROSCollaborationTaskImage.setScaledContents(True)

        self.verticalLayout.addWidget(self.lbROSCollaborationTaskImage)

        self.lbROSCollaborationTaskName = QLabel(self.fWidgetCollaborationTask)
        self.lbROSCollaborationTaskName.setObjectName(u"lbROSCollaborationTaskName")
        sizePolicy1.setHeightForWidth(self.lbROSCollaborationTaskName.sizePolicy().hasHeightForWidth())
        self.lbROSCollaborationTaskName.setSizePolicy(sizePolicy1)
        self.lbROSCollaborationTaskName.setMinimumSize(QSize(0, 20))
        self.lbROSCollaborationTaskName.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbROSCollaborationTaskName)


        self.verticalLayout_3.addLayout(self.verticalLayout)


        self.verticalLayout_2.addWidget(self.fWidgetCollaborationTask)


        self.retranslateUi(WidgetCollaborationTask)

        QMetaObject.connectSlotsByName(WidgetCollaborationTask)
    # setupUi

    def retranslateUi(self, WidgetCollaborationTask):
        WidgetCollaborationTask.setWindowTitle(QCoreApplication.translate("WidgetCollaborationTask", u"Form", None))
        self.lbROSCollaborationTaskImage.setText("")
        self.lbROSCollaborationTaskName.setText(QCoreApplication.translate("WidgetCollaborationTask", u"None", None))
    # retranslateUi

