# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgWorldOptionFire.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_DlgWorldOptionFire(object):
    def setupUi(self, DlgWorldOptionFire):
        if not DlgWorldOptionFire.objectName():
            DlgWorldOptionFire.setObjectName(u"DlgWorldOptionFire")
        DlgWorldOptionFire.resize(432, 320)
        self.verticalLayout = QVBoxLayout(DlgWorldOptionFire)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(DlgWorldOptionFire)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(0, 0))
        self.frame.setFrameShape(QFrame.NoFrame)
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
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gbWorldOptionFireSetting = QGroupBox(self.frame_2)
        self.gbWorldOptionFireSetting.setObjectName(u"gbWorldOptionFireSetting")
        self.gbWorldOptionFireSetting.setStyleSheet(u"QGroupBox#gbWorldOptionFireSetting {\n"
"    border: 1px solid 	darkgray;\n"
"    margin-top: 15px;\n"
"	color:white\n"
"}\n"
"\n"
"QGroupBox#gbWorldOptionFireSetting::title {\n"
"    subcontrol-position: top left;\n"
"    border: 1px solid white;\n"
"    background-color: gray;\n"
"    padding: 5px 15px 5px 15px;\n"
"    top: -15px;\n"
"	left: 20px;\n"
"}")
        self.verticalLayout_6 = QVBoxLayout(self.gbWorldOptionFireSetting)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 20, -1, -1)
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.frame_6 = QFrame(self.gbWorldOptionFireSetting)
        self.frame_6.setObjectName(u"frame_6")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_6.sizePolicy().hasHeightForWidth())
        self.frame_6.setSizePolicy(sizePolicy)
        self.frame_6.setFrameShape(QFrame.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_11 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.frame_6)
        self.label_5.setObjectName(u"label_5")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy1)

        self.horizontalLayout_11.addWidget(self.label_5)

        self.leditWorldOptionFireSpawnParticlesPath = QLineEdit(self.frame_6)
        self.leditWorldOptionFireSpawnParticlesPath.setObjectName(u"leditWorldOptionFireSpawnParticlesPath")
        self.leditWorldOptionFireSpawnParticlesPath.setReadOnly(True)

        self.horizontalLayout_11.addWidget(self.leditWorldOptionFireSpawnParticlesPath)


        self.horizontalLayout_10.addWidget(self.frame_6)

        self.btnWorldOptionFireSpawnParticlesOpen = QPushButton(self.gbWorldOptionFireSetting)
        self.btnWorldOptionFireSpawnParticlesOpen.setObjectName(u"btnWorldOptionFireSpawnParticlesOpen")

        self.horizontalLayout_10.addWidget(self.btnWorldOptionFireSpawnParticlesOpen)


        self.verticalLayout_6.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.frame_5 = QFrame(self.gbWorldOptionFireSetting)
        self.frame_5.setObjectName(u"frame_5")
        sizePolicy.setHeightForWidth(self.frame_5.sizePolicy().hasHeightForWidth())
        self.frame_5.setSizePolicy(sizePolicy)
        self.frame_5.setFrameShape(QFrame.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_12 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.frame_5)
        self.label_6.setObjectName(u"label_6")
        sizePolicy1.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy1)

        self.horizontalLayout_12.addWidget(self.label_6)

        self.leditWorldOptionFireParticleEmitterPath = QLineEdit(self.frame_5)
        self.leditWorldOptionFireParticleEmitterPath.setObjectName(u"leditWorldOptionFireParticleEmitterPath")
        self.leditWorldOptionFireParticleEmitterPath.setReadOnly(True)

        self.horizontalLayout_12.addWidget(self.leditWorldOptionFireParticleEmitterPath)

        self.btnWorldOptionFireParticleEmitterOpen = QPushButton(self.frame_5)
        self.btnWorldOptionFireParticleEmitterOpen.setObjectName(u"btnWorldOptionFireParticleEmitterOpen")

        self.horizontalLayout_12.addWidget(self.btnWorldOptionFireParticleEmitterOpen)


        self.horizontalLayout_8.addWidget(self.frame_5)


        self.verticalLayout_6.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.frame_4 = QFrame(self.gbWorldOptionFireSetting)
        self.frame_4.setObjectName(u"frame_4")
        sizePolicy.setHeightForWidth(self.frame_4.sizePolicy().hasHeightForWidth())
        self.frame_4.setSizePolicy(sizePolicy)
        self.frame_4.setMinimumSize(QSize(200, 0))
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.frame_4)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)

        self.horizontalLayout_5.addWidget(self.label_2)

        self.leditWorldOptionFireSDFFilePath = QLineEdit(self.frame_4)
        self.leditWorldOptionFireSDFFilePath.setObjectName(u"leditWorldOptionFireSDFFilePath")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.leditWorldOptionFireSDFFilePath.sizePolicy().hasHeightForWidth())
        self.leditWorldOptionFireSDFFilePath.setSizePolicy(sizePolicy2)
        self.leditWorldOptionFireSDFFilePath.setReadOnly(True)

        self.horizontalLayout_5.addWidget(self.leditWorldOptionFireSDFFilePath)


        self.horizontalLayout_4.addWidget(self.frame_4)

        self.btnWorldOptionFireSDFPathOpen = QPushButton(self.gbWorldOptionFireSetting)
        self.btnWorldOptionFireSDFPathOpen.setObjectName(u"btnWorldOptionFireSDFPathOpen")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.btnWorldOptionFireSDFPathOpen.sizePolicy().hasHeightForWidth())
        self.btnWorldOptionFireSDFPathOpen.setSizePolicy(sizePolicy3)
        self.btnWorldOptionFireSDFPathOpen.setMinimumSize(QSize(20, 0))

        self.horizontalLayout_4.addWidget(self.btnWorldOptionFireSDFPathOpen)


        self.verticalLayout_6.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label = QLabel(self.gbWorldOptionFireSetting)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setMinimumSize(QSize(250, 0))

        self.horizontalLayout_3.addWidget(self.label)

        self.leditWorldOptionFireParticleCount = QLineEdit(self.gbWorldOptionFireSetting)
        self.leditWorldOptionFireParticleCount.setObjectName(u"leditWorldOptionFireParticleCount")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.leditWorldOptionFireParticleCount.sizePolicy().hasHeightForWidth())
        self.leditWorldOptionFireParticleCount.setSizePolicy(sizePolicy4)
        self.leditWorldOptionFireParticleCount.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.leditWorldOptionFireParticleCount)

        self.horizontalLayout_3.setStretch(1, 1)

        self.verticalLayout_6.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_3 = QLabel(self.gbWorldOptionFireSetting)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setMinimumSize(QSize(250, 0))

        self.horizontalLayout_6.addWidget(self.label_3)

        self.leditWorldOptionFireGroupCount = QLineEdit(self.gbWorldOptionFireSetting)
        self.leditWorldOptionFireGroupCount.setObjectName(u"leditWorldOptionFireGroupCount")
        self.leditWorldOptionFireGroupCount.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.leditWorldOptionFireGroupCount)


        self.verticalLayout_6.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_4 = QLabel(self.gbWorldOptionFireSetting)
        self.label_4.setObjectName(u"label_4")
        sizePolicy1.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy1)
        self.label_4.setMinimumSize(QSize(250, 0))

        self.horizontalLayout_7.addWidget(self.label_4)

        self.leditWorldOptionFireSpreadScale = QLineEdit(self.gbWorldOptionFireSetting)
        self.leditWorldOptionFireSpreadScale.setObjectName(u"leditWorldOptionFireSpreadScale")
        self.leditWorldOptionFireSpreadScale.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.leditWorldOptionFireSpreadScale)


        self.verticalLayout_6.addLayout(self.horizontalLayout_7)


        self.verticalLayout_4.addWidget(self.gbWorldOptionFireSetting)


        self.verticalLayout_2.addWidget(self.frame_2)

        self.frame_3 = QFrame(self.verticalWidget)
        self.frame_3.setObjectName(u"frame_3")
        sizePolicy4.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy4)
        self.frame_3.setMinimumSize(QSize(0, 40))
        self.frame_3.setFrameShape(QFrame.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btnWorldOptionFireCancel = QPushButton(self.frame_3)
        self.btnWorldOptionFireCancel.setObjectName(u"btnWorldOptionFireCancel")
        sizePolicy.setHeightForWidth(self.btnWorldOptionFireCancel.sizePolicy().hasHeightForWidth())
        self.btnWorldOptionFireCancel.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.btnWorldOptionFireCancel)

        self.btnWorldOptionFireStart = QPushButton(self.frame_3)
        self.btnWorldOptionFireStart.setObjectName(u"btnWorldOptionFireStart")
        sizePolicy.setHeightForWidth(self.btnWorldOptionFireStart.sizePolicy().hasHeightForWidth())
        self.btnWorldOptionFireStart.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.btnWorldOptionFireStart)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addWidget(self.frame_3)


        self.verticalLayout_3.addWidget(self.verticalWidget)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(DlgWorldOptionFire)

        QMetaObject.connectSlotsByName(DlgWorldOptionFire)
    # setupUi

    def retranslateUi(self, DlgWorldOptionFire):
        DlgWorldOptionFire.setWindowTitle(QCoreApplication.translate("DlgWorldOptionFire", u"World Option - Fire", None))
        self.gbWorldOptionFireSetting.setTitle(QCoreApplication.translate("DlgWorldOptionFire", u"Setting", None))
        self.label_5.setText(QCoreApplication.translate("DlgWorldOptionFire", u"spawn_particles.py : ", None))
        self.btnWorldOptionFireSpawnParticlesOpen.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Open", None))
        self.label_6.setText(QCoreApplication.translate("DlgWorldOptionFire", u"particle_emitter.py : ", None))
        self.btnWorldOptionFireParticleEmitterOpen.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Open", None))
        self.label_2.setText(QCoreApplication.translate("DlgWorldOptionFire", u"SDF File : ", None))
        self.btnWorldOptionFireSDFPathOpen.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Open", None))
        self.label.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Particle Count : ", None))
        self.label_3.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Group Count : ", None))
        self.label_4.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Spread Scale : ", None))
        self.btnWorldOptionFireCancel.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Cancel", None))
        self.btnWorldOptionFireStart.setText(QCoreApplication.translate("DlgWorldOptionFire", u"Start", None))
    # retranslateUi

