# -*- coding: utf-8 -*-
"""Fire editor UI: emits start/stop requests to the MainWindow.

Start keeps the dialog open for live control. Stop leaves the editor open;
the window close button also requests particle cleanup before closing.
"""

from PySide6 import QtCore, QtWidgets
from ui_dlgWorldOptionFireEditor import Ui_DlgWorldOptionFireEditor
from widgetWorldOptionFire import WidgetWorldOptionFire


class DialogWorldOptionFireEditor(QtWidgets.QDialog):
    # MainWindow owns the QProcess; this dialog only requests operations.
    startRequested = QtCore.Signal(list)
    stopRequested = QtCore.Signal()
    MAX_FIRE_ITEMS = 10

    def __init__(self, parent=None, fire_options=None):
        super().__init__(parent)
        self.ui = Ui_DlgWorldOptionFireEditor()
        self.ui.setupUi(self)
        self.m_nextFireID = 0
        self.m_fireOptions = []
        self._fire_running = False
        self._stop_emitted = False
        self.SetFireProgress(0, 'Ready')

        self.ui.btnWorldOptionFireAdd.clicked.connect(lambda: self.AddFireItem())
        self.ui.btnWorldOptionFireDelete.clicked.connect(self.DeleteFireItem)
        self.ui.btnWorldOptionFireStop.clicked.connect(self.RequestStop)
        self.ui.btnWorldOptionFireStart.clicked.connect(self.ConfirmFireOptions)
        self.ui.btnWorldOptionFireSyncIgnStart.clicked.connect(
            lambda: self.SyncToSelectedItem('IgnStart'))
        self.ui.btnWorldOptionFireSyncIgnEnd.clicked.connect(
            lambda: self.SyncToSelectedItem('IgnEnd'))
        self.ui.btnWorldOptionFireSyncIgnIntensity.clicked.connect(
            lambda: self.SyncToSelectedItem('IgnIntensity'))
        self.ui.btnWorldOptionFireSyncIgnRate.clicked.connect(
            lambda: self.SyncToSelectedItem('IgnRate'))

        # Show ID 0 immediately, as in the supplied reference screenshot.
        # Confirmed data is restored when the dialog is reopened.
        if fire_options:
            for option in fire_options:
                self.AddFireItem(option)
        else:
            self.AddFireItem()
        self.ui.lstwWorldOptionFireProperties.setCurrentRow(0)
        self.SetFireRunning(False)

    def AddFireItem(self, fire_data=None):
        """Add one real QWidget into the QListWidget (rather than plain text)."""
        lst = self.ui.lstwWorldOptionFireProperties
        if lst.count() >= self.MAX_FIRE_ITEMS:
            return  # Never create more than 10 fire sources (including loaded ones).

        fire_id = self.m_nextFireID
        if isinstance(fire_data, dict):
            fire_id = int(fire_data.get('id', fire_id))
        self.m_nextFireID = max(self.m_nextFireID, fire_id + 1)

        widget = WidgetWorldOptionFire(fire_id)
        if isinstance(fire_data, dict):
            widget.SetFireData(fire_data)
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(QtCore.QSize(0, max(widget.sizeHint().height(), 185) + 7))
        lst.addItem(item)
        lst.setItemWidget(item, widget)
        widget.interacted.connect(lambda row_item=item: lst.setCurrentItem(row_item))
        lst.setCurrentItem(item)
        lst.scrollToItem(item)
        self.ui.btnWorldOptionFireAdd.setEnabled(lst.count() < self.MAX_FIRE_ITEMS)

    def DeleteFireItem(self):
        """Remove the selected source and its embedded QWidget safely."""
        lst = self.ui.lstwWorldOptionFireProperties
        row = lst.currentRow()
        if row < 0:
            return
        item = lst.item(row)
        widget = lst.itemWidget(item)
        lst.removeItemWidget(item)
        taken_item = lst.takeItem(row)
        del taken_item
        if widget is not None:
            widget.deleteLater()
        if lst.count() > 0:
            lst.setCurrentRow(min(row, lst.count() - 1))
        self.ui.btnWorldOptionFireAdd.setEnabled(lst.count() < self.MAX_FIRE_ITEMS)

    def SyncToSelectedItem(self, field):
        """Match the given field on every other item to the selected item."""
        lst = self.ui.lstwWorldOptionFireProperties
        if lst.count() < 2:
            return

        selected_row = lst.currentRow()
        if selected_row < 0:
            return

        selected_widget = lst.itemWidget(lst.item(selected_row))
        if selected_widget is None:
            return

        value = selected_widget.GetIgnitionValue(field)
        for row in range(lst.count()):
            if row == selected_row:
                continue
            widget = lst.itemWidget(lst.item(row))
            if widget is not None:
                widget.SetIgnitionValue(field, value)

    def GetFireOptions(self):
        """Return all current widget values for later Fire/ROS integration."""
        options = []
        lst = self.ui.lstwWorldOptionFireProperties
        for row in range(lst.count()):
            widget = lst.itemWidget(lst.item(row))
            if widget is not None:
                options.append(widget.GetFireData())
        return options

    def ConfirmFireOptions(self):
        """Validate inputs and request a start without closing the editor."""
        if self._fire_running:
            return
        if self.ui.lstwWorldOptionFireProperties.count() == 0:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Add at least one fire item.')
            return
        try:
            self.m_fireOptions = self.GetFireOptions()
        except ValueError:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Enter valid X/Y/Z coordinates.')
            return
        self.startRequested.emit(self.m_fireOptions)

    def ClearFireMessages(self):
        """Clear the visible log when a new fire session starts."""
        self.ui.pteWorldOptionFireMessages.clear()

    def LoadFireMessages(self, messages):
        """Restore recent messages when reopening the dialog."""
        recent = list(messages)[-300:]
        self.ui.pteWorldOptionFireMessages.setPlainText('\n'.join(recent))
        scrollbar = self.ui.pteWorldOptionFireMessages.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def AppendFireMessage(self, message):
        """Append a fire log line; QPlainTextEdit keeps only the newest 300 lines."""
        text = str(message)
        for line in text.splitlines():
            if line:
                self.ui.pteWorldOptionFireMessages.appendPlainText(line)
        scrollbar = self.ui.pteWorldOptionFireMessages.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def SetFireProgress(self, value, text=None):
        """Update the bottom progress bar; MainWindow owns progress semantics."""
        bar = self.ui.prgWorldOptionFireProgress
        bar.setRange(0, 100)
        bar.setValue(max(0, min(100, int(value))))
        if text is not None:
            bar.setFormat(str(text))

    def SetFireRunning(self, running):
        """Reflect the actual MainWindow QProcess state in the controls."""
        self._fire_running = bool(running)
        self._stop_emitted = False
        self.ui.gbWorldOptionFireProperties.setEnabled(not running)
        self.ui.btnWorldOptionFireStart.setEnabled(not running)
        self.ui.btnWorldOptionFireStop.setEnabled(bool(running))

    def SetFireStopping(self):
        """Disable repeated stop/start clicks while Gazebo models are removed."""
        self._stop_emitted = True
        self.ui.btnWorldOptionFireStart.setEnabled(False)
        self.ui.btnWorldOptionFireStop.setEnabled(False)
        self.SetFireProgress(0, 'Stopping fire... %p%')

    def RequestStop(self):
        """Request cleanup once; the parent handles SIGTERM and delete_model."""
        if self._fire_running and not self._stop_emitted:
            self.SetFireStopping()
            self.stopRequested.emit()

    def reject(self):
        """Escape has the same cleanup semantics as the title-bar close."""
        self.RequestStop()
        super().reject()

    def closeEvent(self, event):
        """X stops this fire session without shutting down Gazebo/ROS."""
        self.RequestStop()
        super().closeEvent(event)
