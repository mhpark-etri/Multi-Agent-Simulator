# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainDB.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLayout, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QSpacerItem, QStatusBar, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindowDB(object):
    def setupUi(self, MainWindowDB):
        if not MainWindowDB.objectName():
            MainWindowDB.setObjectName(u"MainWindowDB")
        MainWindowDB.resize(1000, 800)
        self.actionOpen = QAction(MainWindowDB)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionSave = QAction(MainWindowDB)
        self.actionSave.setObjectName(u"actionSave")
        self.actionExit = QAction(MainWindowDB)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindowDB)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setLayoutDirection(Qt.LeftToRight)
        self.layoutWidget = QWidget(self.centralwidget)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(-1, 5, 991, 741))
        self.verticalLayout_47 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_47.setObjectName(u"verticalLayout_47")
        self.verticalLayout_47.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_47.setContentsMargins(0, 0, 0, 0)
        self.frame_33 = QFrame(self.layoutWidget)
        self.frame_33.setObjectName(u"frame_33")
        self.frame_33.setFrameShape(QFrame.NoFrame)
        self.frame_33.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_34 = QHBoxLayout(self.frame_33)
        self.horizontalLayout_34.setSpacing(0)
        self.horizontalLayout_34.setObjectName(u"horizontalLayout_34")
        self.horizontalLayout_34.setContentsMargins(0, 0, -1, 0)
        self.horizontalLayout_35 = QHBoxLayout()
        self.horizontalLayout_35.setObjectName(u"horizontalLayout_35")
        self.frame_34 = QFrame(self.frame_33)
        self.frame_34.setObjectName(u"frame_34")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_34.sizePolicy().hasHeightForWidth())
        self.frame_34.setSizePolicy(sizePolicy1)
        self.frame_34.setMinimumSize(QSize(100, 0))
        self.frame_34.setFrameShape(QFrame.StyledPanel)
        self.frame_34.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_36 = QHBoxLayout(self.frame_34)
        self.horizontalLayout_36.setObjectName(u"horizontalLayout_36")
        self.horizontalLayout_36.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_44 = QVBoxLayout()
        self.verticalLayout_44.setObjectName(u"verticalLayout_44")
        self.label = QLabel(self.frame_34)
        self.label.setObjectName(u"label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy2)
        self.label.setMinimumSize(QSize(0, 20))
        self.label.setWordWrap(False)
        self.label.setIndent(10)

        self.verticalLayout_44.addWidget(self.label)

        self.listWidget = QListWidget(self.frame_34)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout_44.addWidget(self.listWidget)

        self.pushButton_25 = QPushButton(self.frame_34)
        self.pushButton_25.setObjectName(u"pushButton_25")

        self.verticalLayout_44.addWidget(self.pushButton_25)

        self.pushButton_26 = QPushButton(self.frame_34)
        self.pushButton_26.setObjectName(u"pushButton_26")

        self.verticalLayout_44.addWidget(self.pushButton_26)

        self.verticalSpacer_9 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_44.addItem(self.verticalSpacer_9)


        self.horizontalLayout_36.addLayout(self.verticalLayout_44)


        self.horizontalLayout_35.addWidget(self.frame_34)

        self.frame_35 = QFrame(self.frame_33)
        self.frame_35.setObjectName(u"frame_35")
        self.frame_35.setFrameShape(QFrame.NoFrame)
        self.frame_35.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_35)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_46 = QVBoxLayout()
        self.verticalLayout_46.setObjectName(u"verticalLayout_46")
        self.tbDB = QTableWidget(self.frame_35)
        if (self.tbDB.columnCount() < 20):
            self.tbDB.setColumnCount(20)
        if (self.tbDB.rowCount() < 50):
            self.tbDB.setRowCount(50)
        self.tbDB.setObjectName(u"tbDB")
        self.tbDB.setRowCount(50)
        self.tbDB.setColumnCount(20)
        self.tbDB.horizontalHeader().setVisible(True)
        self.tbDB.horizontalHeader().setCascadingSectionResizes(False)
        self.tbDB.horizontalHeader().setMinimumSectionSize(57)
        self.tbDB.horizontalHeader().setDefaultSectionSize(150)
        self.tbDB.horizontalHeader().setHighlightSections(True)
        self.tbDB.horizontalHeader().setProperty("showSortIndicator", False)
        self.tbDB.horizontalHeader().setStretchLastSection(False)
        self.tbDB.verticalHeader().setVisible(True)
        self.tbDB.verticalHeader().setCascadingSectionResizes(False)
        self.tbDB.verticalHeader().setDefaultSectionSize(30)
        self.tbDB.verticalHeader().setHighlightSections(True)
        self.tbDB.verticalHeader().setProperty("showSortIndicator", False)
        self.tbDB.verticalHeader().setStretchLastSection(False)

        self.verticalLayout_46.addWidget(self.tbDB)


        self.horizontalLayout.addLayout(self.verticalLayout_46)


        self.horizontalLayout_35.addWidget(self.frame_35)


        self.horizontalLayout_34.addLayout(self.horizontalLayout_35)


        self.verticalLayout_47.addWidget(self.frame_33)

        self.frame_36 = QFrame(self.layoutWidget)
        self.frame_36.setObjectName(u"frame_36")
        sizePolicy2.setHeightForWidth(self.frame_36.sizePolicy().hasHeightForWidth())
        self.frame_36.setSizePolicy(sizePolicy2)
        self.frame_36.setMinimumSize(QSize(0, 40))
        self.frame_36.setFrameShape(QFrame.NoFrame)
        self.frame_36.setFrameShadow(QFrame.Raised)
        self.verticalLayout_48 = QVBoxLayout(self.frame_36)
        self.verticalLayout_48.setObjectName(u"verticalLayout_48")
        self.verticalLayout_48.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_37 = QHBoxLayout()
        self.horizontalLayout_37.setObjectName(u"horizontalLayout_37")
        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_37.addItem(self.horizontalSpacer_9)

        self.pushButton_27 = QPushButton(self.frame_36)
        self.pushButton_27.setObjectName(u"pushButton_27")

        self.horizontalLayout_37.addWidget(self.pushButton_27)


        self.verticalLayout_48.addLayout(self.horizontalLayout_37)


        self.verticalLayout_47.addWidget(self.frame_36)

        MainWindowDB.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindowDB)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1000, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindowDB.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindowDB)
        self.statusbar.setObjectName(u"statusbar")
        MainWindowDB.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindowDB)

        QMetaObject.connectSlotsByName(MainWindowDB)
    # setupUi

    def retranslateUi(self, MainWindowDB):
        MainWindowDB.setWindowTitle(QCoreApplication.translate("MainWindowDB", u"\uc800\uc7a5\uc18c DB", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindowDB", u"Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindowDB", u"Save", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindowDB", u"Exit", None))
        self.label.setText(QCoreApplication.translate("MainWindowDB", u"Table", None))
        self.pushButton_25.setText(QCoreApplication.translate("MainWindowDB", u"\uc785\ub825", None))
        self.pushButton_26.setText(QCoreApplication.translate("MainWindowDB", u"\uc0ad\uc81c", None))
        self.pushButton_27.setText(QCoreApplication.translate("MainWindowDB", u"\ud655\uc778", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindowDB", u"File", None))
    # retranslateUi

