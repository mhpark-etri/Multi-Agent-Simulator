######################################################
## Teslasystem Co.,Ltd.                             ##
## Image-to-Image Enhancement: ROS camera -> captures ##
##                                    -> light_fire  ##
######################################################

import copy
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import rospy
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from dlgROSI2I_ui import Ui_DlgROSI2I
from constant import *
from simulator import *


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CAPTURE_DIRECTORY = PROJECT_ROOT / "captures"
AI_WORKER_SCRIPT = PROJECT_ROOT / "i2i_fire_worker.py"
DEFAULT_FIRE_MODULE_DIRECTORY = Path("/root/tesla/I2I_Simulator/light_fire_pkg")

# Optional environment overrides:
#   LIGHT_FIRE_PYTHON=/opt/conda/envs/lightfire/bin/python
#   LIGHT_FIRE_DEVICE=cuda (or cpu)
# The fire model DIRECTORY is always selected in this dialog's UI.
# The local package supplies model.py and its own weights directory.

try:
    DEFAULT_CAPTURE_DIRECTORY.mkdir(parents=True, exist_ok=True)
except OSError as exc:
    print("[I2I] Cannot create default captures directory: {}".format(exc))


def find_light_fire_python():
    explicit = os.environ.get("LIGHT_FIRE_PYTHON", "").strip()
    if explicit:
        executable = Path(explicit).expanduser()
        return str(executable) if executable.is_file() else None

    # Reuse an activated Conda environment only if it is 'lightfire'.
    active = Path(os.environ.get("CONDA_PREFIX", "")) if os.environ.get("CONDA_PREFIX") else None
    possible = []
    if active is not None and active.name == "lightfire":
        possible.append(active / "bin" / "python")
    for base in (
        "/opt/conda", "/root/miniconda3", "/root/anaconda3",
        "/home/tesla/miniconda3", "/home/tesla/anaconda3",
        "/root/tesla/miniconda3", "/root/tesla/anaconda3",
        "/opt/miniconda3", str(Path.home() / "miniconda3"),
        str(Path.home() / "anaconda3"), str(Path.home() / ".conda"),
    ):
        possible.append(Path(base) / "envs" / "lightfire" / "bin" / "python")
    return next((str(p) for p in possible if p.is_file()), None)


class EnhancedImageThread(QThread):
    """Subscribe to one sensor_msgs/Image topic, saving frames at selected FPS.

    rospy callbacks run in the subscriber's thread, not the Qt event loop.
    The filename is local YYYYMMDD-HHMMSS.png; subsecond suffixes are added
    above 1 FPS to avoid overwriting distinct captures in the same second.
    """

    image_saved = Signal(str)
    log = Signal(str)

    def __init__(self, topic_name, capture_directory, fps, parent=None):
        super().__init__(parent)
        self.topic_name = topic_name
        self.capture_directory = Path(capture_directory)
        self.fps = int(fps)
        self.bridge = CvBridge()
        self._stop_event = threading.Event()
        self._next_due = 0.0
        self._sub = None
        self._callback_lock = threading.Lock()
        self._active_callbacks = 0
        self._callbacks_idle = threading.Event()
        self._callbacks_idle.set()

    def run(self):
        try:
            self._sub = rospy.Subscriber(
                self.topic_name, Image, self.callback,
                queue_size=1, buff_size=2 ** 24,
            )
            while not self._stop_event.wait(0.05) and not rospy.is_shutdown():
                pass
        except Exception as exc:
            self.log.emit("[Capture] ROS subscriber failed: {}".format(exc))
        finally:
            if self._sub is not None:
                try:
                    self._sub.unregister()
                except Exception:
                    pass
                self._sub = None
            # ROS callbacks run on ROS-managed threads, not on this QThread.
            # Wait for a callback already saving a PNG before declaring capture
            # finished and telling the AI worker to drain the input folder.
            self._callbacks_idle.wait()

    def callback(self, msg):
        with self._callback_lock:
            if self._stop_event.is_set():
                return
            now = time.monotonic()
            if now < self._next_due:
                return
            self._next_due = now + 1.0 / self.fps
            self._active_callbacks += 1
            self._callbacks_idle.clear()

        try:
            self._save_image(msg)
        finally:
            with self._callback_lock:
                self._active_callbacks -= 1
                if self._active_callbacks == 0:
                    self._callbacks_idle.set()

    def _save_image(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            timestamp = datetime.now()
            name = timestamp.strftime("%Y%m%d-%H%M%S")
            if self.fps > 1:
                name += timestamp.strftime("-%f")
            path = self.capture_directory / (name + ".png")
            if path.exists():
                path = self.capture_directory / (
                    timestamp.strftime("%Y%m%d-%H%M%S-%f") + ".png"
                )

            # Write to a hidden PNG in the SAME directory. The watcher reads
            # the final filename only after os.replace has completed.
            temporary = path.with_name("." + path.stem + ".tmp.png")
            try:
                if not cv2.imwrite(str(temporary), frame):
                    raise IOError("cv2.imwrite failed")
                os.replace(str(temporary), str(path))
            finally:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            self.image_saved.emit(str(path))
        except Exception as exc:
            self.log.emit("[Capture] Save failed: {}".format(exc))

    def stop(self):
        self._stop_event.set()


class DialogROSI2I(QtWidgets.QDialog):
    def __init__(self, rosInfo):
        super().__init__()
        self.ui = Ui_DlgROSI2I()
        self.ui.setupUi(self)
        self.m_simulator = copy.deepcopy(rosInfo)

        self.ui.leditROSI2ICapturePath.setText(str(DEFAULT_CAPTURE_DIRECTORY))
        self.ui.leditROSI2IFireModulePath.setText(str(DEFAULT_FIRE_MODULE_DIRECTORY))
        self.ui.ckbROSI2IShowCaptureFolder.setChecked(True)
        self.ui.ckbROSI2IShowResultFolder.setChecked(True)
        self.ui.pteROSI2IMessages.setReadOnly(True)
        self.ui.pteROSI2IMessages.setMaximumBlockCount(300)
        self.ui.leditROSI2ICaptureFPS.setValidator(QtGui.QIntValidator(1, 1000, self))
        self.ui.leditROSI2ICaptureFPS.setText("1")
        self.ui.leditROSI2ICaptureFPS.editingFinished.connect(self._NormalizeCaptureFPS)
        self.ui.btnROSI2ICapturePathOpen.clicked.connect(self.OpenCaptureFolderDialog)
        self.ui.btnROSI2IFireModulePathOpen.clicked.connect(self.OpenFireModuleFolderDialog)

        self.image_thread = None
        self.ai_process = None
        self._starting = False
        self._stopping = False
        self._close_after_stop = False
        self._drain_sent = False
        self._selected_topic = ""
        self._capture_directory = None
        self._output_directory = None
        self._capture_fps = 1
        self._show_capture_folder = True
        self._show_result_folder = True
        self._drain_total = None
        self._drain_done = 0
        self._worker_exit_code = None
        self._worker_out_buffer = ""
        self._worker_err_buffer = ""
        self._SetProgress(0, 100, "Ready")

        if not rospy.core.is_initialized():
            rospy.init_node("dlg_ros_i2i", anonymous=True, disable_signals=True)

        self.ui.cbROSI2IName.currentIndexChanged.connect(self.SetRobotInfo)
        self.ui.lstwROSI2ITopicList.itemSelectionChanged.connect(self._UpdateButtons)
        self.ui.btnROSI2IStart.clicked.connect(self.StartROSI2I)
        self.ui.btnROSI2IStop.clicked.connect(self.StopThreads)
        self._UpdateButtons()

    def OpenCaptureFolderDialog(self):
        path_text = self.ui.leditROSI2ICapturePath.text().strip()
        initial = path_text if Path(path_text).is_dir() else str(DEFAULT_CAPTURE_DIRECTORY)
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Capture Folder", initial,
            QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )
        if chosen:
            self.ui.leditROSI2ICapturePath.setText(str(Path(chosen).resolve()))

    def OpenFireModuleFolderDialog(self):
        """Select the folder containing the light_fire_pkg/model.py source."""
        text = self.ui.leditROSI2IFireModulePath.text().strip()
        candidate = Path(text).expanduser() if text else DEFAULT_FIRE_MODULE_DIRECTORY
        # QFileDialog may not open correctly with a non-existent initial path.
        while not candidate.is_dir() and candidate != candidate.parent:
            candidate = candidate.parent
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Fire Generation Module Folder", str(candidate),
            QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )
        if chosen:
            self.ui.leditROSI2IFireModulePath.setText(str(Path(chosen).resolve()))

    def _NormalizeCaptureFPS(self):
        value = self.ui.leditROSI2ICaptureFPS.text().strip()
        if not value.isdecimal() or not 1 <= int(value) <= 1000:
            self.ui.leditROSI2ICaptureFPS.setText("1")

    def _AppendMessage(self, message):
        """Append messages to the UI, retaining only the newest 300 lines."""
        text = str(message)
        for line in text.splitlines():
            if line.strip():
                self.ui.pteROSI2IMessages.appendPlainText(line)
        scrollbar = self.ui.pteROSI2IMessages.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _Log(self, message, error=False):
        self._AppendMessage(message)
        if error:
            print(str(message), file=sys.stderr)
        else:
            print(str(message))

    def _SetProgressBusy(self, text):
        bar = self.ui.prgROSI2IProgress
        bar.setRange(0, 0)
        bar.setFormat(str(text))

    def _SetProgress(self, value, total=100, text="%p%"):
        bar = self.ui.prgROSI2IProgress
        total = max(1, int(total))
        bar.setRange(0, total)
        bar.setValue(max(0, min(total, int(value))))
        bar.setFormat(str(text))

    def _OpenFolder(self, folder, description):
        """Open a container-local folder in a GUI file manager.

        In this Docker setup there is no host D-Bus session and no xdg-open
        handler. Launch a file manager directly through the already configured
        X11 display instead of relying on QDesktopServices/gio associations.
        """
        try:
            folder_path = Path(folder).expanduser().resolve()
            if not folder_path.is_dir():
                self._Log("[Folder WARNING] {} does not exist: {}".format(
                    description, folder_path), error=True)
                return

            managers = (
                ("thunar", []),
                ("pcmanfm", []),
                ("nemo", []),
                ("nautilus", ["--new-window"]),
                ("dolphin", []),
            )
            executable = None
            extra_args = []
            for name, args in managers:
                candidate = shutil.which(name)
                if candidate:
                    executable = candidate
                    extra_args = list(args)
                    break

            if executable is None:
                self._Log(
                    "[Folder ERROR] No GUI file manager is installed in the container. "
                    "Install one with: apt-get update && apt-get install -y thunar dbus-x11",
                    error=True,
                )
                return

            env = os.environ.copy()
            # The container uses X11 forwarded to the host desktop. Do not
            # require the host's D-Bus socket; create a private session bus
            # for the file manager when dbus-run-session is available.
            env.setdefault("DISPLAY", ":0")
            command = [executable] + extra_args + [str(folder_path)]
            dbus_runner = shutil.which("dbus-run-session")
            if not env.get("DBUS_SESSION_BUS_ADDRESS") and dbus_runner:
                command = [dbus_runner, "--"] + command

            subprocess.Popen(
                command,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
            self._Log("[Folder] Opening {} in {}: {}".format(
                description, Path(executable).name, folder_path))
        except Exception as exc:
            self._Log("[Folder ERROR] Could not open {}: {}".format(
                description, exc), error=True)

    def showEvent(self, event):
        super().showEvent(event)
        self.SetRobotsInfoToCombo(self.m_simulator.robots)

    def closeEvent(self, event):
        if self._starting or self._stopping or self.image_thread is not None or (
            self.ai_process is not None and self.ai_process.state() != QtCore.QProcess.ProcessState.NotRunning
        ):
            self._close_after_stop = True
            self.StopThreads()
            event.ignore()  # Wait for worker shutdown without blocking the GUI.
            return
        self._StopCapture()
        super().closeEvent(event)

    def SetRobotsInfoToCombo(self, robots):
        self.ui.cbROSI2IName.blockSignals(True)
        self.ui.cbROSI2IName.clear()
        for robot in robots:
            self.ui.cbROSI2IName.addItem(robot.name)
        self.ui.cbROSI2IName.blockSignals(False)
        if robots:
            self.SetRobotInfo(0)
        else:
            self.ui.lstwROSI2ITopicList.clear()
            self._UpdateButtons()

    def SetRobotInfo(self, index):
        if index < 0 or index >= len(self.m_simulator.robots):
            return
        if self._starting or self._stopping or self.image_thread is not None:
            return

        robot = self.m_simulator.robots[index]
        thumb_path = ""
        if robot.type == ENUM_ROBOT_TYPE.LOCOBOT:
            thumb_path = CONST_LOCOBOT_PATH
        elif robot.type == ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER:
            thumb_path = CONST_TURTLEBOT3_BURGER_PATH
        elif robot.type == ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE:
            thumb_path = CONST_TURTLEBOT3_WAFFLE_PATH
        elif robot.type == ENUM_ROBOT_TYPE.INTERBOTIX:
            thumb_path = CONST_INTERBOTIX_PATH
        elif robot.type == ENUM_ROBOT_TYPE.UNI050_BASE:
            thumb_path = CONST_UNI_PATH
        elif robot.type == ENUM_ROBOT_TYPE.HELLO_ROBOT_STRETCH:
            thumb_path = CONST_HELLO_STRETCH2_PATH

        pixmap = QtGui.QPixmap(thumb_path)
        self.ui.lbROSI2IRobotThumb.setPixmap(pixmap.scaled(
            self.ui.lbROSI2IRobotThumb.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        self.ui.lbROSI2INameSpace.setText(robot.name)

        try:
            topics = rospy.get_published_topics()
        except Exception as exc:
            self._Log("[I2I WARNING] Could not read ROS topics: {}".format(exc), error=True)
            topics = []

        self.ui.lstwROSI2ITopicList.clear()
        prefix = "/" + robot.name + "/"
        for topic, message_type in topics:
            if not topic.startswith(prefix):
                continue
            item = QtWidgets.QListWidgetItem(topic)
            if topic.endswith("/image_raw") and message_type == "sensor_msgs/Image":
                item.setBackground(QColor("yellow"))
                item.setData(Qt.ItemDataRole.UserRole, True)
            else:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.ui.lstwROSI2ITopicList.addItem(item)
        self._UpdateButtons()

    def _SelectedImageTopic(self):
        items = self.ui.lstwROSI2ITopicList.selectedItems()
        if items and bool(items[0].data(Qt.ItemDataRole.UserRole)):
            return items[0].text()
        return ""

    def _UpdateButtons(self):
        active = self._starting or self._stopping or self.image_thread is not None or (
            self.ai_process is not None and
            self.ai_process.state() != QtCore.QProcess.ProcessState.NotRunning
        )
        # Start is available only when the selected list item is the yellow
        # sensor_msgs/Image camera topic, as marked in SetRobotInfo().
        self.ui.btnROSI2IStart.setEnabled(not active and bool(self._SelectedImageTopic()))
        self.ui.btnROSI2IStop.setEnabled(active and not self._stopping)
        self.ui.btnROSI2IStop.setText("Stopping..." if self._stopping else "Stop")
        self.ui.cbROSI2IName.setEnabled(not active)
        self.ui.lstwROSI2ITopicList.setEnabled(not active)
        self.ui.gbROSI2ICapture.setEnabled(not active)
        self.ui.gbROSI2IFireModule.setEnabled(not active)

    def StartROSI2I(self):
        if self._starting or self._stopping or self.image_thread is not None:
            return
        topic = self._SelectedImageTopic()
        if not topic:
            QMessageBox.warning(self, "I2I", "Please select a yellow camera image topic.")
            return
        self._NormalizeCaptureFPS()
        fps = int(self.ui.leditROSI2ICaptureFPS.text())
        capture_dir = Path(self.ui.leditROSI2ICapturePath.text().strip()).expanduser()
        if not str(capture_dir).strip() or str(capture_dir) == ".":
            QMessageBox.warning(self, "I2I", "Please select a capture folder.")
            return
        capture_dir = capture_dir.resolve()
        output_dir = capture_dir.parent / "captures_I2I"

        package_text = self.ui.leditROSI2IFireModulePath.text().strip()
        if not package_text:
            QMessageBox.warning(self, "I2I", "Please select a Fire Generation Module folder.")
            return
        package_dir = Path(package_text).expanduser().resolve()
        if not (package_dir / "model.py").is_file():
            QMessageBox.warning(
                self, "I2I", "The selected Fire Generation Module folder is invalid.\n"
                "Could not find model.py in:\n{}".format(package_dir)
            )
            return
        interpreter = find_light_fire_python()
        if interpreter is None:
            QMessageBox.warning(
                self, "I2I", "The 'lightfire' Conda Python was not found.\n"
                "Set LIGHT_FIRE_PYTHON to the full path of its python executable."
            )
            return
        if not AI_WORKER_SCRIPT.is_file():
            QMessageBox.warning(self, "I2I", "Missing i2i_fire_worker.py beside dlgROSI2I.py")
            return
        try:
            capture_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            if capture_dir == output_dir:
                raise ValueError("Capture and output folders must differ")
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "I2I", "Cannot create output folders: {}".format(exc))
            return

        self._selected_topic = topic
        self._capture_directory = capture_dir
        self._output_directory = output_dir
        self._capture_fps = fps
        self._show_capture_folder = self.ui.ckbROSI2IShowCaptureFolder.isChecked()
        self._show_result_folder = self.ui.ckbROSI2IShowResultFolder.isChecked()
        self._close_after_stop = False
        self._starting = True
        self._stopping = False
        self._drain_sent = False
        self._drain_total = None
        self._drain_done = 0
        self._worker_exit_code = None
        self._worker_out_buffer = ""
        self._worker_err_buffer = ""
        self.ui.pteROSI2IMessages.clear()
        self._Log("[I2I] Start requested. Topic={}, FPS={}.".format(topic, fps))
        self._SetProgressBusy("Starting fire-generation model...")
        self._UpdateButtons()

        worker = QtCore.QProcess(self)
        worker.setWorkingDirectory(str(PROJECT_ROOT))
        worker.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.SeparateChannels)
        process_environment = QtCore.QProcessEnvironment.systemEnvironment()
        # ROS's PYTHONPATH targets a different Python from the Conda environment.
        for key in ("PYTHONPATH", "PYTHONHOME", "QT_QPA_PLATFORM_PLUGIN_PATH", "QT_PLUGIN_PATH"):
            process_environment.remove(key)
        worker.setProcessEnvironment(process_environment)
        worker.readyReadStandardOutput.connect(self._OnWorkerOutput)
        worker.readyReadStandardError.connect(self._OnWorkerError)
        worker.finished.connect(self._OnWorkerFinished)
        worker.errorOccurred.connect(self._OnWorkerProcessError)
        worker.started.connect(self._OnWorkerStarted)
        self.ai_process = worker

        arguments = [
            str(AI_WORKER_SCRIPT), "--input-dir", str(capture_dir),
            "--output-dir", str(output_dir),
            "--package-dir", str(package_dir),
            "--device", os.environ.get("LIGHT_FIRE_DEVICE", "cuda").strip() or "cuda",
        ]
        self._Log("[I2I] Starting fire-generation worker: {}".format(interpreter))
        worker.start(interpreter, arguments)
        # The ROS capture starts on I2I_WATCHING, after the worker has taken
        # a snapshot of pre-existing files. This avoids missing early captures.

    def _OnWorkerStarted(self):
        # Stop may have been clicked while QProcess was still in Starting state.
        if self._stopping and self.image_thread is None:
            self._RequestWorkerDrain()

    def _OnWorkerOutput(self):
        worker = self.ai_process
        if worker is None:
            return
        self._worker_out_buffer += bytes(worker.readAllStandardOutput()).decode("utf-8", "replace")
        while "\n" in self._worker_out_buffer:
            line, self._worker_out_buffer = self._worker_out_buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            if line == "I2I_WATCHING":
                self._Log("[I2I] Worker is watching for new capture images.")
                if self._starting and not self._stopping:
                    self._StartCapture()
                elif self._stopping and self.image_thread is None:
                    self._RequestWorkerDrain()
            elif line == "I2I_MODEL_READY":
                self._Log("[I2I] Fire-generation model loaded and ready.")
            elif line.startswith("I2I_DRAIN_TOTAL "):
                try:
                    total = max(0, int(line.split()[1]))
                except (IndexError, ValueError):
                    self._Log("[I2I WARNING] Invalid drain total: {}".format(line))
                    continue
                self._drain_total = total
                self._drain_done = 0
                if total == 0:
                    self._SetProgress(100, 100, "No pending images")
                    self._Log("[I2I] No pending images remain to convert.")
                else:
                    self._SetProgress(0, total, "Finishing images: %p%")
                    self._Log("[I2I] Finishing {} pending image(s) before Stop completes.".format(total))
            elif line.startswith("I2I_DRAIN_PROGRESS "):
                try:
                    done, total = (int(part) for part in line.split()[1:3])
                except (ValueError, IndexError):
                    self._Log("[I2I WARNING] Invalid drain progress: {}".format(line))
                    continue
                self._drain_done = max(0, done)
                if total > 0:
                    self._drain_total = max(total, self._drain_total or 0)
                    self._SetProgress(done, total, "Finishing images: %p%")
                else:
                    self._SetProgress(100, 100, "No pending images")
            else:
                self._Log(line)

    def _OnWorkerError(self):
        worker = self.ai_process
        if worker is None:
            return
        data = bytes(worker.readAllStandardError()).decode("utf-8", "replace")
        self._worker_err_buffer = (self._worker_err_buffer + data)[-12000:]
        for line in data.splitlines():
            if line.strip():
                self._Log(line, error=True)

    def _StartCapture(self):
        try:
            self.image_thread = EnhancedImageThread(
                self._selected_topic, self._capture_directory, self._capture_fps, self
            )
            self.image_thread.log.connect(self._OnCaptureLog)
            self.image_thread.image_saved.connect(self._OnImageSaved)
            self.image_thread.finished.connect(self._OnCaptureFinished)
            self.image_thread.start()
            self._starting = False
            self._SetProgressBusy("Capturing and generating fire images...")
            self._UpdateButtons()
            self._Log("[Capture] Started: topic={}, FPS={}, folder={}".format(
                self._selected_topic, self._capture_fps, self._capture_directory
            ))
            if self._show_capture_folder:
                self._OpenFolder(self._capture_directory, "capture folder")
            if self._show_result_folder:
                self._OpenFolder(self._output_directory, "I2I result folder")
        except Exception as exc:
            self._Log("[Capture ERROR] Cannot start ROS camera capture: {}".format(exc), error=True)
            QMessageBox.critical(self, "I2I", "Cannot start ROS camera capture: {}".format(exc))
            self.StopThreads()

    def _OnCaptureLog(self, message):
        self._Log(message)

    def _OnImageSaved(self, path):
        self._Log("[Capture] Saved {}".format(Path(path).name))

    def _OnCaptureFinished(self):
        capture = self.image_thread
        if capture is not None:
            self.image_thread = None
            capture.deleteLater()

        if not self._stopping:
            if self.ai_process is not None and (
                self.ai_process.state() != QtCore.QProcess.ProcessState.NotRunning
            ):
                self._Log("[Capture WARNING] ROS capture stopped unexpectedly.")
                self.StopThreads()
            else:
                self._CompleteStop()
        else:
            # Drain ONLY after the last camera callback finished writing PNG.
            self._RequestWorkerDrain()
        self._UpdateButtons()

    def StopThreads(self):
        """Stop ROS capture, then wait for ALL captured images to be converted.

        No timeout or forced kill is used. The dialog stays in its stopping
        state until the camera QThread and the AI QProcess have both exited.
        """
        if self._stopping:
            return
        if not self._starting and self.ai_process is None and self.image_thread is None:
            self._UpdateButtons()
            return

        self._stopping = True
        self._starting = False
        self._SetProgressBusy("Stopping capture; waiting for fire-image processing...")
        self._Log("[I2I] Stop requested. Capture will stop first; pending fire images will finish before shutdown.")
        self._StopCapture()
        if self.image_thread is None:
            self._RequestWorkerDrain()
        self._UpdateButtons()

    def _StopCapture(self):
        # Nonblocking: a callback can still be saving its last image.
        if self.image_thread is not None:
            self.image_thread.stop()

    def _RequestWorkerDrain(self):
        """Send DRAIN once, after camera save callbacks have fully stopped."""
        if self.image_thread is not None:
            return
        worker = self.ai_process
        if worker is None or worker.state() == QtCore.QProcess.ProcessState.NotRunning:
            self._CompleteStop()
        elif worker.state() == QtCore.QProcess.ProcessState.Starting:
            # _OnWorkerStarted will call this again when the pipe is ready.
            return
        elif not self._drain_sent:
            written = worker.write(b"DRAIN\n")
            if written < 0:
                self._Log("[I2I WARNING] Could not send DRAIN to the fire worker; it is still running.")
                return
            self._drain_sent = True
            self._SetProgressBusy("Finishing pending fire images...")
            self._Log("[I2I] Waiting for the fire worker to finish all pending captures...")

    def _OnWorkerFinished(self, exit_code, exit_status):
        self._OnWorkerOutput()
        self._OnWorkerError()
        unexpected = not self._stopping
        error_text = self._worker_err_buffer
        self._worker_exit_code = int(exit_code)
        self._starting = False
        self._stopping = True
        self._StopCapture()
        self._Log("[I2I] Fire-generation worker exited (code {}).".format(exit_code))
        self._CompleteStop()
        if exit_code != 0 or unexpected:
            QMessageBox.warning(
                self, "I2I process stopped",
                "Fire I2I worker exited (code {}).\n\n{}".format(
                    exit_code, error_text[-900:] or "Check the Messages panel for details."
                ),
            )

    def _OnWorkerProcessError(self, error):
        self._Log("[I2I ERROR] Worker process error: {}".format(error), error=True)
        if error == QtCore.QProcess.ProcessError.FailedToStart:
            self._worker_exit_code = 1
            self._stopping = True
            self._starting = False
            self._StopCapture()
            self._CompleteStop()
            QMessageBox.warning(self, "I2I", "Could not launch the lightfire Python process.")

    def _CompleteStop(self):
        if self.image_thread is not None:
            self._StopCapture()
            return
        if self.ai_process is not None and (
            self.ai_process.state() != QtCore.QProcess.ProcessState.NotRunning
        ):
            # Stop is not complete while any AI frame is still processing.
            return
        old = self.ai_process
        self.ai_process = None
        self._starting = False
        was_stopping = self._stopping
        self._stopping = False
        self._drain_sent = False
        if old is not None:
            old.deleteLater()
        if was_stopping:
            if self._worker_exit_code in (None, 0):
                self._SetProgress(100, 100, "Completed")
                self._Log("[I2I] Stop complete. All captured images have been processed.")
            else:
                self._SetProgress(100, 100, "Completed with errors")
                self._Log("[I2I WARNING] Processing finished with errors; review Messages above.")
        else:
            self._SetProgress(0, 100, "Ready")
        self._UpdateButtons()
        if self._close_after_stop:
            self._close_after_stop = False
            self.close()

    def showModal(self):
        return super().exec()
