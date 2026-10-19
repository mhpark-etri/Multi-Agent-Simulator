# -*- coding: utf-8 -*-
# UI layout for widgetWorldOptionFire.ui.
# Layout edits should be applied to the .ui source and mirrored here (pyside6-uic).
from PySide6 import QtCore, QtWidgets


class Ui_WidgetWorldOptionFire(object):
    def setupUi(self, WidgetWorldOptionFire):
        WidgetWorldOptionFire.setObjectName('WidgetWorldOptionFire')
        WidgetWorldOptionFire.resize(505, 187)
        WidgetWorldOptionFire.setMinimumSize(QtCore.QSize(0, 185))

        self.verticalLayoutWorldOptionFireItem = QtWidgets.QVBoxLayout(WidgetWorldOptionFire)
        self.verticalLayoutWorldOptionFireItem.setObjectName('verticalLayoutWorldOptionFireItem')
        self.verticalLayoutWorldOptionFireItem.setSpacing(0)
        self.verticalLayoutWorldOptionFireItem.setContentsMargins(1, 1, 1, 1)

        self.frameWorldOptionFireCard = QtWidgets.QFrame(WidgetWorldOptionFire)
        self.frameWorldOptionFireCard.setObjectName('frameWorldOptionFireCard')
        self.frameWorldOptionFireCard.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frameWorldOptionFireCard.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frameWorldOptionFireCard.setStyleSheet('''
QFrame#frameWorldOptionFireCard {
    background-color: #eeeeee;
    border: 1px solid #d3d3d3;
    border-radius: 8px;
}
QFrame#frameWorldOptionFireHeader, QFrame#frameWorldOptionFireIgnStart,
QFrame#frameWorldOptionFireIgnEnd, QFrame#frameWorldOptionFireIgnIntensity,
QFrame#frameWorldOptionFireIgnRate {
    background-color: #f8f8f8;
    border: 1px solid #e4e4e4;
    border-radius: 5px;
}
QLabel { border: none; background: transparent; color: #333333; }
QLineEdit { background: white; border: 1px solid #bcbcbc; border-radius: 2px; color: #333333; }
''')
        self.verticalLayoutWorldOptionFireCard = QtWidgets.QVBoxLayout(self.frameWorldOptionFireCard)
        self.verticalLayoutWorldOptionFireCard.setObjectName('verticalLayoutWorldOptionFireCard')
        self.verticalLayoutWorldOptionFireCard.setSpacing(5)
        self.verticalLayoutWorldOptionFireCard.setContentsMargins(10, 8, 10, 8)

        self.frameWorldOptionFireHeader = QtWidgets.QFrame(self.frameWorldOptionFireCard)
        self.frameWorldOptionFireHeader.setObjectName('frameWorldOptionFireHeader')
        self.frameWorldOptionFireHeader.setMinimumSize(QtCore.QSize(0, 31))
        self.horizontalLayoutWorldOptionFireHeader = QtWidgets.QHBoxLayout(self.frameWorldOptionFireHeader)
        self.horizontalLayoutWorldOptionFireHeader.setObjectName('horizontalLayoutWorldOptionFireHeader')
        self.horizontalLayoutWorldOptionFireHeader.setSpacing(5)
        self.horizontalLayoutWorldOptionFireHeader.setContentsMargins(8, 2, 8, 2)
        self.lbWorldOptionFireIDTitle = QtWidgets.QLabel(self.frameWorldOptionFireHeader)
        self.lbWorldOptionFireIDTitle.setObjectName('lbWorldOptionFireIDTitle')
        self.horizontalLayoutWorldOptionFireHeader.addWidget(self.lbWorldOptionFireIDTitle)
        self.lbWorldOptionFireID = QtWidgets.QLabel(self.frameWorldOptionFireHeader)
        self.lbWorldOptionFireID.setObjectName('lbWorldOptionFireID')
        self.lbWorldOptionFireID.setMinimumSize(QtCore.QSize(26, 0))
        self.lbWorldOptionFireID.setMaximumSize(QtCore.QSize(26, 16777215))
        self.lbWorldOptionFireID.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayoutWorldOptionFireHeader.addWidget(self.lbWorldOptionFireID)
        self.horizontalSpacerWorldOptionFireID = QtWidgets.QSpacerItem(
            12, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayoutWorldOptionFireHeader.addItem(self.horizontalSpacerWorldOptionFireID)
        self.lbWorldOptionFirePosition = QtWidgets.QLabel(self.frameWorldOptionFireHeader)
        self.lbWorldOptionFirePosition.setObjectName('lbWorldOptionFirePosition')
        self.lbWorldOptionFirePosition.setMinimumSize(QtCore.QSize(70, 0))
        self.lbWorldOptionFirePosition.setMaximumSize(QtCore.QSize(70, 16777215))
        self.horizontalLayoutWorldOptionFireHeader.addWidget(self.lbWorldOptionFirePosition)
        for axis in ('X', 'Y', 'Z'):
            label = QtWidgets.QLabel(self.frameWorldOptionFireHeader)
            label.setObjectName('lbWorldOptionFirePos' + axis)
            setattr(self, 'lbWorldOptionFirePos' + axis, label)
            self.horizontalLayoutWorldOptionFireHeader.addWidget(label)
            editor = QtWidgets.QLineEdit(self.frameWorldOptionFireHeader)
            editor.setObjectName('leditWorldOptionFirePos' + axis)
            editor.setMinimumSize(QtCore.QSize(43, 0))
            editor.setMaximumSize(QtCore.QSize(43, 16777215))
            editor.setAlignment(QtCore.Qt.AlignCenter)
            setattr(self, 'leditWorldOptionFirePos' + axis, editor)
            self.horizontalLayoutWorldOptionFireHeader.addWidget(editor)
        self.verticalLayoutWorldOptionFireCard.addWidget(self.frameWorldOptionFireHeader)

        self._ignition_fields = (
            ('IgnStart', 'Ignition Start Time(Sec)', 0, 1200),
            ('IgnEnd', 'Ignition End Time(Sec)', 1200, 1800),
            ('IgnIntensity', 'Ignition Intensity(0~100)', 50, 100),
            ('IgnRate', 'Ignition Gradualness(0~100)', 80, 100),
        )
        for field, label_text, default, maximum in self._ignition_fields:
            frame = QtWidgets.QFrame(self.frameWorldOptionFireCard)
            frame.setObjectName('frameWorldOptionFire' + field)
            frame.setMinimumSize(QtCore.QSize(0, 29))
            setattr(self, 'frameWorldOptionFire' + field, frame)
            line_layout = QtWidgets.QHBoxLayout(frame)
            line_layout.setObjectName('horizontalLayoutWorldOptionFire' + field)
            line_layout.setSpacing(6)
            line_layout.setContentsMargins(8, 1, 8, 1)
            setattr(self, 'horizontalLayoutWorldOptionFire' + field, line_layout)
            label = QtWidgets.QLabel(frame)
            label.setObjectName('lbWorldOptionFire' + field)
            label.setMinimumSize(QtCore.QSize(184, 0))
            label.setMaximumSize(QtCore.QSize(184, 16777215))
            label.setAlignment(QtCore.Qt.AlignCenter)
            setattr(self, 'lbWorldOptionFire' + field, label)
            line_layout.addWidget(label)
            editor = QtWidgets.QLineEdit(frame)
            editor.setObjectName('leditWorldOptionFire' + field)
            editor.setMinimumSize(QtCore.QSize(51, 0))
            editor.setMaximumSize(QtCore.QSize(51, 16777215))
            editor.setAlignment(QtCore.Qt.AlignCenter)
            setattr(self, 'leditWorldOptionFire' + field, editor)
            line_layout.addWidget(editor)
            slider = QtWidgets.QSlider(frame)
            slider.setObjectName('vSliderWorldOptionFire' + field)
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(maximum)
            slider.setSingleStep(1)
            slider.setPageStep(10 if maximum > 100 else 5)
            slider.setValue(default)
            setattr(self, 'vSliderWorldOptionFire' + field, slider)
            line_layout.addWidget(slider)
            self.verticalLayoutWorldOptionFireCard.addWidget(frame)
        self.verticalLayoutWorldOptionFireItem.addWidget(self.frameWorldOptionFireCard)

        self.retranslateUi(WidgetWorldOptionFire)
        QtCore.QMetaObject.connectSlotsByName(WidgetWorldOptionFire)

    def retranslateUi(self, WidgetWorldOptionFire):
        _translate = QtCore.QCoreApplication.translate
        WidgetWorldOptionFire.setWindowTitle(_translate('WidgetWorldOptionFire', 'Form - widgetWorldOptionFire.ui'))
        self.lbWorldOptionFireIDTitle.setText(_translate('WidgetWorldOptionFire', 'ID :'))
        self.lbWorldOptionFireID.setText(_translate('WidgetWorldOptionFire', '0'))
        self.lbWorldOptionFirePosition.setText(_translate('WidgetWorldOptionFire', 'Position'))
        for axis, default in (('X', '-10.0'), ('Y', '10'), ('Z', '0')):
            getattr(self, 'lbWorldOptionFirePos' + axis).setText(axis + ' :')
            getattr(self, 'leditWorldOptionFirePos' + axis).setText(default)
        labels = {
            'IgnStart': 'Ignition Start Time(Sec)',
            'IgnEnd': 'Ignition End Time(Sec)',
            'IgnIntensity': 'Ignition Intensity(0~100)',
            'IgnRate': 'Ignition Gradualness(0~100)',
        }
        for field, label in labels.items():
            getattr(self, 'lbWorldOptionFire' + field).setText(_translate('WidgetWorldOptionFire', label))
        for field, _, default, _ in self._ignition_fields:
            getattr(self, 'leditWorldOptionFire' + field).setText(str(default))
