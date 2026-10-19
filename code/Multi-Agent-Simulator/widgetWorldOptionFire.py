# -*- coding: utf-8 -*-
"""World Option - Fire: a single fire-source item in the Properties list.

The visual layout is editable with Qt Designer in widgetWorldOptionFire.ui.
"""

from PySide6 import QtCore, QtGui, QtWidgets
from ui_widgetWorldOptionFire import Ui_WidgetWorldOptionFire


class WidgetWorldOptionFire(QtWidgets.QWidget):
    # When the user edits an embedded control, the parent QListWidget should
    # select this row so that Delete acts on the item being edited.
    interacted = QtCore.Signal()

    # Field name -> (line editor, horizontal slider). The 'vSlider' prefix
    # follows this project's requested naming convention, even though these
    # sliders have Qt.Horizontal orientation.
    IGNITION_FIELDS = ('IgnStart', 'IgnEnd', 'IgnIntensity', 'IgnRate')

    def __init__(self, fire_id=0, parent=None):
        super().__init__(parent)
        self.ui = Ui_WidgetWorldOptionFire()
        self.ui.setupUi(self)
        self.SetFireID(fire_id)

        # A newly added fire source starts at the world origin.
        # When restoring saved data, SetFireData() can overwrite these defaults.
        for axis in ('X', 'Y', 'Z'):
            getattr(self.ui, 'leditWorldOptionFirePos' + axis).setText('0')

        self.installEventFilter(self)
        for child in self.findChildren(QtWidgets.QWidget):
            child.installEventFilter(self)

        # Prevent invalid position values (including partial numbers at save).
        for axis in ('X', 'Y', 'Z'):
            editor = getattr(self.ui, 'leditWorldOptionFirePos' + axis)
            validator = QtGui.QDoubleValidator(-100000.0, 100000.0, 3, editor)
            validator.setLocale(QtCore.QLocale.c())
            editor.setValidator(validator)

        for field in self.IGNITION_FIELDS:
            editor = getattr(self.ui, 'leditWorldOptionFire' + field)
            slider = getattr(self.ui, 'vSliderWorldOptionFire' + field)
            editor.setValidator(QtGui.QIntValidator(slider.minimum(), slider.maximum(), editor))
            slider.valueChanged.connect(
                lambda value, target=editor: target.setText(str(value)))
            editor.textChanged.connect(
                lambda text, name=field: self._OnIgnitionTextChanged(name, text))
            editor.editingFinished.connect(
                lambda name=field: self._NormalizeIgnitionValue(name))

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.FocusIn):
            self.interacted.emit()
        return super().eventFilter(watched, event)

    def SetFireID(self, fire_id):
        self.fire_id = int(fire_id)
        self.ui.lbWorldOptionFireID.setText(str(self.fire_id))

    def _OnIgnitionTextChanged(self, field, text):
        if not text:
            return  # User can temporarily empty an editor while typing.
        slider = getattr(self.ui, 'vSliderWorldOptionFire' + field)
        try:
            value = int(text)
        except ValueError:
            return
        if slider.minimum() <= value <= slider.maximum():
            slider.setValue(value)

    def _NormalizeIgnitionValue(self, field):
        editor = getattr(self.ui, 'leditWorldOptionFire' + field)
        slider = getattr(self.ui, 'vSliderWorldOptionFire' + field)
        # The slider is the source of truth if the editor is left blank.
        editor.setText(str(slider.value()))

    def SetIgnitionValue(self, field, value):
        if field not in self.IGNITION_FIELDS:
            raise ValueError('Unknown ignition field: ' + str(field))
        slider = getattr(self.ui, 'vSliderWorldOptionFire' + field)
        value = max(slider.minimum(), min(slider.maximum(), int(value)))
        slider.setValue(value)
        getattr(self.ui, 'leditWorldOptionFire' + field).setText(str(value))

    def GetIgnitionValue(self, field):
        if field not in self.IGNITION_FIELDS:
            raise ValueError('Unknown ignition field: ' + str(field))
        return getattr(self.ui, 'vSliderWorldOptionFire' + field).value()

    def GetFireData(self):
        """Return a ROS-independent fire-source configuration as a dict."""
        position = {}
        for axis in ('X', 'Y', 'Z'):
            text = getattr(self.ui, 'leditWorldOptionFirePos' + axis).text().strip()
            position[axis.lower()] = float(text)  # Invalid entries raise ValueError.
        return {
            'id': self.fire_id,
            'position': position,
            'ignition_start_sec': self.GetIgnitionValue('IgnStart'),
            'ignition_end_sec': self.GetIgnitionValue('IgnEnd'),
            'ignition_intensity': self.GetIgnitionValue('IgnIntensity'),
            'ignition_gradualness': self.GetIgnitionValue('IgnRate'),
        }

    def SetFireData(self, data):
        """Populate a list row from configuration previously confirmed."""
        self.SetFireID(data.get('id', self.fire_id))
        coords = data.get('position', {})
        for axis in ('X', 'Y', 'Z'):
            key = axis.lower()
            if key in coords:
                getattr(self.ui, 'leditWorldOptionFirePos' + axis).setText(str(coords[key]))
        for key, field in (
            ('ignition_start_sec', 'IgnStart'),
            ('ignition_end_sec', 'IgnEnd'),
            ('ignition_intensity', 'IgnIntensity'),
            ('ignition_gradualness', 'IgnRate'),
        ):
            if key in data:
                self.SetIgnitionValue(field, data[key])
