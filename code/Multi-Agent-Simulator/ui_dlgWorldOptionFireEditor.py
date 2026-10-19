# -*- coding: utf-8 -*-
# UI layout for dlgWorldOptionFireEditor.ui.
# Layout edits should be applied to the .ui source and mirrored here (pyside6-uic).
from PySide6 import QtCore, QtWidgets


class Ui_DlgWorldOptionFireEditor(object):
    def setupUi(self, DlgWorldOptionFireEditor):
        DlgWorldOptionFireEditor.setObjectName('DlgWorldOptionFireEditor')
        DlgWorldOptionFireEditor.resize(568, 650)
        DlgWorldOptionFireEditor.setMinimumSize(QtCore.QSize(530, 490))

        self.verticalLayoutWorldOptionFireEditor = QtWidgets.QVBoxLayout(DlgWorldOptionFireEditor)
        self.verticalLayoutWorldOptionFireEditor.setObjectName('verticalLayoutWorldOptionFireEditor')
        self.verticalLayoutWorldOptionFireEditor.setSpacing(11)
        self.verticalLayoutWorldOptionFireEditor.setContentsMargins(18, 28, 18, 12)

        self.gbWorldOptionFireProperties = QtWidgets.QGroupBox(DlgWorldOptionFireEditor)
        self.gbWorldOptionFireProperties.setObjectName('gbWorldOptionFireProperties')
        self.gbWorldOptionFireProperties.setStyleSheet('''
QGroupBox#gbWorldOptionFireProperties {
    border: 1px solid #aaaaaa;
    margin-top: 16px;
}
QGroupBox#gbWorldOptionFireProperties::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 20px;
    padding: 5px 19px;
    background-color: #8b8b8b;
    color: white;
}
QListWidget#lstwWorldOptionFireProperties {
    background-color: #858585;
    border: 1px solid #929292;
    outline: none;
}
QListWidget#lstwWorldOptionFireProperties::item {
    border: 2px solid transparent;
    padding: 3px;
}
QListWidget#lstwWorldOptionFireProperties::item:selected {
    background-color: #2389bf;
    border-color: #2389bf;
}
''')
        self.verticalLayoutWorldOptionFireProperties = QtWidgets.QVBoxLayout(self.gbWorldOptionFireProperties)
        self.verticalLayoutWorldOptionFireProperties.setObjectName('verticalLayoutWorldOptionFireProperties')
        self.verticalLayoutWorldOptionFireProperties.setSpacing(7)
        self.verticalLayoutWorldOptionFireProperties.setContentsMargins(10, 22, 10, 8)

        self.horizontalLayoutWorldOptionFireActions = QtWidgets.QHBoxLayout()
        self.horizontalLayoutWorldOptionFireActions.setObjectName('horizontalLayoutWorldOptionFireActions')
        self.horizontalLayoutWorldOptionFireActions.setSpacing(7)
        self.horizontalLayoutWorldOptionFireActions.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacerWorldOptionFireActions = QtWidgets.QSpacerItem(
            1, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayoutWorldOptionFireActions.addItem(self.horizontalSpacerWorldOptionFireActions)
        self.btnWorldOptionFireAdd = QtWidgets.QPushButton(self.gbWorldOptionFireProperties)
        self.btnWorldOptionFireAdd.setObjectName('btnWorldOptionFireAdd')
        self.btnWorldOptionFireAdd.setMinimumSize(QtCore.QSize(87, 29))
        self.btnWorldOptionFireAdd.setMaximumSize(QtCore.QSize(87, 16777215))
        self.horizontalLayoutWorldOptionFireActions.addWidget(self.btnWorldOptionFireAdd)
        self.btnWorldOptionFireDelete = QtWidgets.QPushButton(self.gbWorldOptionFireProperties)
        self.btnWorldOptionFireDelete.setObjectName('btnWorldOptionFireDelete')
        self.btnWorldOptionFireDelete.setMinimumSize(QtCore.QSize(87, 29))
        self.btnWorldOptionFireDelete.setMaximumSize(QtCore.QSize(87, 16777215))
        self.horizontalLayoutWorldOptionFireActions.addWidget(self.btnWorldOptionFireDelete)
        self.verticalLayoutWorldOptionFireProperties.addLayout(self.horizontalLayoutWorldOptionFireActions)

        self.lstwWorldOptionFireProperties = QtWidgets.QListWidget(self.gbWorldOptionFireProperties)
        self.lstwWorldOptionFireProperties.setObjectName('lstwWorldOptionFireProperties')
        self.lstwWorldOptionFireProperties.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.lstwWorldOptionFireProperties.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.lstwWorldOptionFireProperties.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.verticalLayoutWorldOptionFireProperties.addWidget(self.lstwWorldOptionFireProperties)

        self.horizontalLayoutWorldOptionFireSync = QtWidgets.QHBoxLayout()
        self.horizontalLayoutWorldOptionFireSync.setObjectName('horizontalLayoutWorldOptionFireSync')
        self.horizontalLayoutWorldOptionFireSync.setSpacing(5)
        self.horizontalLayoutWorldOptionFireSync.setContentsMargins(0, 0, 0, 0)
        self.lbWorldOptionFireSyncToSelectedItem = QtWidgets.QLabel(self.gbWorldOptionFireProperties)
        self.lbWorldOptionFireSyncToSelectedItem.setObjectName('lbWorldOptionFireSyncToSelectedItem')
        self.horizontalLayoutWorldOptionFireSync.addWidget(self.lbWorldOptionFireSyncToSelectedItem)
        for name in ('btnWorldOptionFireSyncIgnStart', 'btnWorldOptionFireSyncIgnEnd',
                     'btnWorldOptionFireSyncIgnIntensity', 'btnWorldOptionFireSyncIgnRate'):
            button = QtWidgets.QPushButton(self.gbWorldOptionFireProperties)
            button.setObjectName(name)
            button.setMinimumSize(QtCore.QSize(0, 26))
            setattr(self, name, button)
            self.horizontalLayoutWorldOptionFireSync.addWidget(button)
        self.verticalLayoutWorldOptionFireProperties.addLayout(self.horizontalLayoutWorldOptionFireSync)
        self.verticalLayoutWorldOptionFireEditor.addWidget(self.gbWorldOptionFireProperties)

        self.horizontalLayoutWorldOptionFireBottom = QtWidgets.QHBoxLayout()
        self.horizontalLayoutWorldOptionFireBottom.setObjectName('horizontalLayoutWorldOptionFireBottom')
        self.horizontalLayoutWorldOptionFireBottom.setSpacing(10)
        self.horizontalLayoutWorldOptionFireBottom.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacerWorldOptionFireBottom = QtWidgets.QSpacerItem(
            3, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayoutWorldOptionFireBottom.addItem(self.horizontalSpacerWorldOptionFireBottom)
        self.btnWorldOptionFireStop = QtWidgets.QPushButton(DlgWorldOptionFireEditor)
        self.btnWorldOptionFireStop.setObjectName('btnWorldOptionFireStop')
        self.btnWorldOptionFireStop.setMinimumSize(QtCore.QSize(93, 43))
        self.btnWorldOptionFireStop.setMaximumSize(QtCore.QSize(93, 16777215))
        self.horizontalLayoutWorldOptionFireBottom.addWidget(self.btnWorldOptionFireStop)
        self.btnWorldOptionFireStart = QtWidgets.QPushButton(DlgWorldOptionFireEditor)
        self.btnWorldOptionFireStart.setObjectName('btnWorldOptionFireStart')
        self.btnWorldOptionFireStart.setMinimumSize(QtCore.QSize(93, 43))
        self.btnWorldOptionFireStart.setMaximumSize(QtCore.QSize(93, 16777215))
        self.horizontalLayoutWorldOptionFireBottom.addWidget(self.btnWorldOptionFireStart)
        self.verticalLayoutWorldOptionFireEditor.addLayout(self.horizontalLayoutWorldOptionFireBottom)

        self.retranslateUi(DlgWorldOptionFireEditor)
        QtCore.QMetaObject.connectSlotsByName(DlgWorldOptionFireEditor)

    def retranslateUi(self, DlgWorldOptionFireEditor):
        _translate = QtCore.QCoreApplication.translate
        DlgWorldOptionFireEditor.setWindowTitle(_translate('DlgWorldOptionFireEditor', 'World Option - Fire'))
        self.gbWorldOptionFireProperties.setTitle(_translate('DlgWorldOptionFireEditor', 'Properties'))
        self.btnWorldOptionFireAdd.setText(_translate('DlgWorldOptionFireEditor', 'Add'))
        self.btnWorldOptionFireDelete.setText(_translate('DlgWorldOptionFireEditor', 'Delete'))
        self.lbWorldOptionFireSyncToSelectedItem.setText(_translate('DlgWorldOptionFireEditor', 'Sync to Selected Item'))
        self.btnWorldOptionFireSyncIgnStart.setText(_translate('DlgWorldOptionFireEditor', 'Ign. Start'))
        self.btnWorldOptionFireSyncIgnEnd.setText(_translate('DlgWorldOptionFireEditor', 'Ign. End'))
        self.btnWorldOptionFireSyncIgnIntensity.setText(_translate('DlgWorldOptionFireEditor', 'Ign. Intensity'))
        self.btnWorldOptionFireSyncIgnRate.setText(_translate('DlgWorldOptionFireEditor', 'Ign. Rate'))
        self.btnWorldOptionFireStop.setText(_translate('DlgWorldOptionFireEditor', 'Stop'))
        self.btnWorldOptionFireStart.setText(_translate('DlgWorldOptionFireEditor', 'Start'))
