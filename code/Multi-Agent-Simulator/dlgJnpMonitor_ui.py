# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgJnpMonitor.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGraphicsView, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPlainTextEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_DlgJnpMonitor(object):
    def setupUi(self, DlgJnpMonitor):
        if not DlgJnpMonitor.objectName():
            DlgJnpMonitor.setObjectName(u"DlgJnpMonitor")
        DlgJnpMonitor.resize(1000, 660)
        self.verticalLayout = QVBoxLayout(DlgJnpMonitor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.hlCoalitionBar = QHBoxLayout()
        self.hlCoalitionBar.setObjectName(u"hlCoalitionBar")
        self.lbJnpCoalition = QLabel(DlgJnpMonitor)
        self.lbJnpCoalition.setObjectName(u"lbJnpCoalition")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbJnpCoalition.sizePolicy().hasHeightForWidth())
        self.lbJnpCoalition.setSizePolicy(sizePolicy)
        self.lbJnpCoalition.setStyleSheet(u"QLabel { background-color: #2b2b2b; color: #e8e8e8; border-radius: 4px; padding: 8px; font-size: 13px; }")

        self.hlCoalitionBar.addWidget(self.lbJnpCoalition)

        self.lbSimStats = QLabel(DlgJnpMonitor)
        self.lbSimStats.setObjectName(u"lbSimStats")
        self.lbSimStats.setStyleSheet(u"QLabel { color: #000000; font-size: 13px; font-weight: bold; padding: 4px; }")

        self.hlCoalitionBar.addWidget(self.lbSimStats)

        self.btnDissolveGroup = QPushButton(DlgJnpMonitor)
        self.btnDissolveGroup.setObjectName(u"btnDissolveGroup")
        self.btnDissolveGroup.setMinimumSize(QSize(110, 0))

        self.hlCoalitionBar.addWidget(self.btnDissolveGroup)


        self.verticalLayout.addLayout(self.hlCoalitionBar)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayoutAgents = QVBoxLayout()
        self.verticalLayoutAgents.setObjectName(u"verticalLayoutAgents")
        self.lbAgentsTitle = QLabel(DlgJnpMonitor)
        self.lbAgentsTitle.setObjectName(u"lbAgentsTitle")

        self.verticalLayoutAgents.addWidget(self.lbAgentsTitle)

        self.lstJnpAgents = QListWidget(DlgJnpMonitor)
        self.lstJnpAgents.setObjectName(u"lstJnpAgents")
        self.lstJnpAgents.setMaximumSize(QSize(240, 16777215))

        self.verticalLayoutAgents.addWidget(self.lstJnpAgents)


        self.horizontalLayout.addLayout(self.verticalLayoutAgents)

        self.verticalLayoutTree = QVBoxLayout()
        self.verticalLayoutTree.setObjectName(u"verticalLayoutTree")
        self.lbTreeTitle = QLabel(DlgJnpMonitor)
        self.lbTreeTitle.setObjectName(u"lbTreeTitle")

        self.verticalLayoutTree.addWidget(self.lbTreeTitle)

        self.gvJnpTree = QGraphicsView(DlgJnpMonitor)
        self.gvJnpTree.setObjectName(u"gvJnpTree")
        self.gvJnpTree.setRenderHints(QPainter.Antialiasing|QPainter.TextAntialiasing)

        self.verticalLayoutTree.addWidget(self.gvJnpTree)


        self.horizontalLayout.addLayout(self.verticalLayoutTree)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.pteJnpLog = QPlainTextEdit(DlgJnpMonitor)
        self.pteJnpLog.setObjectName(u"pteJnpLog")
        self.pteJnpLog.setMaximumSize(QSize(16777215, 150))
        self.pteJnpLog.setReadOnly(True)

        self.verticalLayout.addWidget(self.pteJnpLog)


        self.retranslateUi(DlgJnpMonitor)

        QMetaObject.connectSlotsByName(DlgJnpMonitor)
    # setupUi

    def retranslateUi(self, DlgJnpMonitor):
        DlgJnpMonitor.setWindowTitle(QCoreApplication.translate("DlgJnpMonitor", u"JnP Monitor", None))
        self.lbJnpCoalition.setText(QCoreApplication.translate("DlgJnpMonitor", u"Coalition: (\uc5c6\uc74c) \u2014 JnP \uc5d0\uc774\uc804\ud2b8\ub97c \uc2dc\uc791\ud558\uace0 \ud611\uc5c5 \ud0dc\uc2a4\ud06c\ub97c \ubc1c\ud589\ud558\uba74 \uc5ec\uae30\uc5d0 \ud45c\uc2dc\ub429\ub2c8\ub2e4", None))
        self.lbSimStats.setText(QCoreApplication.translate("DlgJnpMonitor", u"RTF -- | Sim -- | Real --", None))
#if QT_CONFIG(tooltip)
        self.btnDissolveGroup.setToolTip(QCoreApplication.translate("DlgJnpMonitor", u"\uc644\ub8cc \ud6c4 \uc720\uc9c0 \uc911\uc778 \uadf8\ub8f9\uc744 \ud574\uc81c\ud569\ub2c8\ub2e4 (\uba64\ubc84\ub4e4\uc758 \uc18c\uc18d\uc744 \ud480\uace0 \uadf8\ub8f9 \ub178\ub4dc \uc885\ub8cc)", None))
#endif // QT_CONFIG(tooltip)
        self.btnDissolveGroup.setText(QCoreApplication.translate("DlgJnpMonitor", u"Group \ud574\uc81c", None))
        self.lbAgentsTitle.setText(QCoreApplication.translate("DlgJnpMonitor", u"Agents (Discovery)", None))
        self.lbTreeTitle.setText(QCoreApplication.translate("DlgJnpMonitor", u"Task Tree (Scheduling)", None))
        self.pteJnpLog.setPlaceholderText(QCoreApplication.translate("DlgJnpMonitor", u"JnP \uc774\ubca4\ud2b8 \ub85c\uadf8 (discovery / task / coalition / \ud574\uccb4)", None))
    # retranslateUi

