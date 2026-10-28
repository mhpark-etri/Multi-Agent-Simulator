######################################################
## Teslasystem Co.,Ltd.                             ##
## Description: ROS keyboard teleoperation selector  ##
######################################################
"""Open an independent keyboard-teleop terminal for the selected robot.

The existing Qt Designer dialog is preserved.  Its robot buttons are generated
from Simulator.robots, but the robot *object* decides the model/namespace:
we never infer robot type from a truncated button label or its list index.
"""
import os
import re
import shlex
import shutil
import subprocess

from PySide6 import QtWidgets
from PySide6.QtCore import QCoreApplication, QSize

from ui_dlgROSTeleop import Ui_DlgROSTeleop
from simulator import ENUM_ROBOT_TYPE


# ROS workspaces used by the simulator.  Load the same overlay in each new
# terminal, because opening a GNOME terminal does not run main.py's shelltemp.sh.
ROS_SETUP = '/opt/ros/noetic/setup.bash'
ROBOT_WORKSPACE = {
    ENUM_ROBOT_TYPE.INTERBOTIX: '/root/interbotix_ws/devel/setup.bash',
    ENUM_ROBOT_TYPE.LOCOBOT: '/root/interbotix_ws/devel/setup.bash',
    ENUM_ROBOT_TYPE.UNI050_BASE: '/root/catkin_ws_ai_bot/devel/setup.bash',
    ENUM_ROBOT_TYPE.HELLO_ROBOT_STRETCH: '/root/catkin_ws_stretch2/devel/setup.bash',
}

ROBOT_LABELS = {
    ENUM_ROBOT_TYPE.LOCOBOT: 'LoCoBot',
    ENUM_ROBOT_TYPE.TURTLEBOT3_BURGER: 'TurtleBot3 Burger',
    ENUM_ROBOT_TYPE.TURTLEBOT3_WAFFLE: 'TurtleBot3 Waffle',
    ENUM_ROBOT_TYPE.JETBOT: 'JetBot',
    ENUM_ROBOT_TYPE.INTERBOTIX: 'LoCoBot wx250s',
    ENUM_ROBOT_TYPE.UNI050_BASE: 'UNI050_BASE',
    ENUM_ROBOT_TYPE.HELLO_ROBOT_STRETCH: 'Stretch2',
}


class DialogTeleop(QtWidgets.QDialog):
    def __init__(self, rosInfo, parent=None):
        super().__init__(parent)
        self.ui = Ui_DlgROSTeleop()
        self.ui.setupUi(self)
        self.m_simulator = rosInfo
        self.CreateSelectRobotPanel(self.ui)
        self.setMinimumWidth(295)
        self.adjustSize()

    def CreateSelectRobotPanel(self, ui):
        """One button per robot; attach explicit namespace and type to button."""
        for robot in self.m_simulator.robots:
            name = str(robot.name)
            robot_type = robot.type
            button = QtWidgets.QPushButton(ui.fmain)
            button.setObjectName('btnTeleop_' + name)
            button.setMinimumSize(QSize(0, 40))
            button.setText(QCoreApplication.translate(
                'DlgROSTeleop', '{}  ({})'.format(
                    name, ROBOT_LABELS.get(robot_type, str(robot_type))), None))
            button.setProperty('teleopRobotName', name)
            button.setProperty('teleopRobotType', robot_type.name)
            ui.verticalLayout.addWidget(button)
            button.clicked.connect(self.StartTeleop)

    @staticmethod
    def build_terminal_command(robot_name, robot_type, script_path):
        """Build argv for GNOME Terminal without handing unescaped input to bash."""
        if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', robot_name):
            raise ValueError('Invalid ROS robot namespace: {}'.format(robot_name))
        if robot_type not in ENUM_ROBOT_TYPE.__members__:
            raise ValueError('Unknown robot model: {}'.format(robot_type))

        # Source the ROS environment in the terminal, even if main.py was
        # started from a shell with a different set of overlay workspaces.
        parts = [
            'if [ -f {0} ]; then source {0}; fi'.format(shlex.quote(ROS_SETUP))
        ]
        workspace = ROBOT_WORKSPACE.get(ENUM_ROBOT_TYPE[robot_type])
        if workspace:
            parts.append(
                'if [ -f {0} ]; then source {0}; fi'.format(shlex.quote(workspace))
            )

        parts.append('python3 {script} --robot {name} --model {model}'.format(
            script=shlex.quote(script_path), name=shlex.quote(robot_name),
            model=shlex.quote(robot_type)))
        parts.append('result=$?')
        parts.append('printf "\\nTeleop finished (exit code: %s).\\n" "$result"')
        parts.append('read -r -p "Press Enter to close this terminal..." _')
        command = '; '.join(parts)
        return ['gnome-terminal', '--title', 'Teleop - ' + robot_name,
                '--', 'bash', '-c', command]

    def StartTeleop(self):
        """Open an isolated console for the clicked robot; never block Qt."""
        button = self.sender()
        if button is None:
            return
        robot_name = str(button.property('teleopRobotName') or '')
        robot_type = str(button.property('teleopRobotType') or '')
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'robot_teleop_keyboard.py')
        if not os.path.isfile(script):
            QtWidgets.QMessageBox.warning(
                self, 'ROS Teleop', 'Missing keyboard control script:\n' + script)
            return
        if not shutil.which('gnome-terminal'):
            QtWidgets.QMessageBox.warning(
                self, 'ROS Teleop',
                "Cannot find 'gnome-terminal'. Install gnome-terminal "
                'in the environment running the GUI.')
            return
        try:
            command = self.build_terminal_command(robot_name, robot_type, script)
            subprocess.Popen(command, cwd=os.path.dirname(script))
        except (OSError, ValueError) as exc:
            QtWidgets.QMessageBox.warning(
                self, 'ROS Teleop', 'Could not open teleop terminal:\n' + str(exc))

    def showModal(self):
        return self.exec()
