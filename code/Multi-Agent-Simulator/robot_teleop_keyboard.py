#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROS1 keyboard teleoperation for one named Gazebo robot.

This script is intentionally independent of the Qt and third-party teleop
packages.  It only needs rospy + geometry_msgs and an interactive terminal.
Before publishing, it checks the ROS master for a *subscriber* to a Twist
velocity topic belonging to the requested robot.  It will not publish to the
root /cmd_vel topic and accidentally move a different robot.

Examples (started automatically by dlgROSTeleop.py):
    python3 robot_teleop_keyboard.py --robot tb3_burger_0 --model TURTLEBOT3_BURGER
    python3 robot_teleop_keyboard.py --robot locobot_0 --model INTERBOTIX
"""
import argparse
import os
import re
import select
import signal
import sys
import termios
import time
import tty

# Fixed conservative base-only speed. Arm/joint teleoperation is out of scope.
LINEAR_SPEED = 0.20              # meters/sec
ANGULAR_SPEED = 0.65            # radians/sec
COMMAND_RATE = 10.0             # Twist messages/sec
KEY_TIMEOUT = 0.65              # dead-man: stop soon after the last key
DISCOVERY_TIMEOUT = 20.0        # seconds to wait for a ROS controller subscriber


def candidate_topics(name, model):
    """Prioritized robot-specific Twist interfaces (never global /cmd_vel)."""
    ns = '/' + name.strip('/')
    if model in ('TURTLEBOT3_BURGER', 'TURTLEBOT3_WAFFLE', 'JETBOT'):
        suffixes = ('cmd_vel', 'mobile_base/commands/velocity')
    elif model in ('LOCOBOT', 'INTERBOTIX'):
        # Interbotix Kobuki uses .../mobile_base/commands/velocity; some
        # alternate bases use .../mobile_base/cmd_vel or .../cmd_vel.
        suffixes = ('mobile_base/commands/velocity', 'mobile_base/cmd_vel',
                    'cmd_vel')
    elif model == 'HELLO_ROBOT_STRETCH':
        suffixes = ('stretch_diff_drive_controller/cmd_vel', 'cmd_vel',
                    'diff_drive_controller/cmd_vel')
    elif model == 'UNI050_BASE':
        suffixes = ('cmd_vel', 'diff_drive_controller/cmd_vel',
                    'base_controller/cmd_vel')
    else:
        suffixes = ('cmd_vel',)
    return [ns + '/' + suffix for suffix in suffixes]


def select_topic(name, model, subscriber_topics, topic_types):
    """Find a subscribed geometry_msgs/Twist topic for exactly this robot.

    A subscriber must actually exist.  Merely seeing another node's published
    /cmd_vel could otherwise make the teleop appear to work while doing nothing.
    """
    candidates = candidate_topics(name, model)
    ns = '/' + name + '/'
    # Unknown but appropriately namespaced controllers can also be detected.
    additional = sorted(topic for topic in subscriber_topics
                        if topic.startswith(ns) and
                        (topic.endswith('/cmd_vel') or
                         topic.endswith('/commands/velocity'))
                        and topic not in candidates)
    for topic in candidates + additional:
        if topic not in subscriber_topics:
            continue
        if topic_types.get(topic, 'geometry_msgs/Twist') != 'geometry_msgs/Twist':
            continue
        return topic
    return None


def discover_topic(master, name, model, timeout=DISCOVERY_TIMEOUT,
                   monotonic=time.monotonic, sleep=time.sleep):
    """Wait briefly for ros_control controllers to register their subscribers."""
    deadline = monotonic() + timeout
    last_error = None
    while monotonic() <= deadline:
        try:
            # rosgraph.Master.getSystemState -> (publishers, subscribers, services)
            _publishers, subscribers, _services = master.getSystemState()
            registered = {topic for topic, clients in subscribers if clients}
            types = dict(master.getTopicTypes())
            topic = select_topic(name, model, registered, types)
            if topic:
                return topic
        except Exception as exc:
            last_error = exc
        sleep(0.35)
    if last_error is not None:
        raise RuntimeError('Could not contact ROS master: {}'.format(last_error))
    raise RuntimeError(
        'No geometry_msgs/Twist subscriber found for {} ({}).\n'
        'Checked: {}\n'
        'Check that the robot is spawned and its base controller is running.\n'
        'You can inspect topics using: rostopic info /<robot>/cmd_vel'.format(
            name, model, ', '.join(candidate_topics(name, model))))


def _read_key(fd, timeout):
    """Read one key sequence without blocking ROS velocity publishing."""
    if not select.select([fd], [], [], timeout)[0]:
        return ''
    ch = os.read(fd, 1).decode('ascii', errors='ignore')
    if ch == '\x1b':  # arrows: ESC [ A/B/C/D
        if select.select([fd], [], [], 0.02)[0]:
            nxt = os.read(fd, 1)
            if nxt == b'[' and select.select([fd], [], [], 0.02)[0]:
                arrow = os.read(fd, 1)
                return {b'A': 'w', b'B': 's', b'C': 'd', b'D': 'a'}.get(arrow, '')
        return ''
    return ch.lower()


def keyboard_loop(rospy, twist_type, topic, robot_name,
                  command_rate=COMMAND_RATE, key_timeout=KEY_TIMEOUT):
    """Publish at a fixed wall-clock rate with a key-release safety timeout."""
    if not sys.stdin.isatty():
        raise RuntimeError('Teleop requires an interactive keyboard terminal.')
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    publisher = rospy.Publisher(topic, twist_type, queue_size=1)
    time.sleep(0.3)  # allow ROS subscriber connection to establish

    def send(linear, angular):
        msg = twist_type()
        msg.linear.x = linear
        msg.angular.z = angular
        publisher.publish(msg)

    last_key_time = 0.0
    velocity = (0.0, 0.0)
    next_publish = time.monotonic()
    period = 1.0 / command_rate
    print('\nRobot: {}'.format(robot_name))
    print('Publishing Twist: {}'.format(topic))
    print('W/UP: forward | S/DOWN: backward | A/LEFT: turn left | D/RIGHT: turn right')
    print('X or SPACE: stop | Q: quit | Ctrl+C: quit')
    print('Keep pressing / hold a movement key to keep moving (dead-man {:.2f}s).'.format(
        key_timeout))
    print('Click this terminal to focus keyboard control.\n')

    try:
        tty.setcbreak(fd)
        while not rospy.is_shutdown():
            now = time.monotonic()
            key = _read_key(fd, min(0.05, max(0.0, next_publish - now)))
            if key in ('q', '\x03'):
                break
            if key in ('x', ' '):
                velocity = (0.0, 0.0)
                last_key_time = 0.0
                send(0.0, 0.0)
            elif key in ('w', 'i'):
                velocity = (LINEAR_SPEED, 0.0)
                last_key_time = time.monotonic()
            elif key in ('s', ',',):
                velocity = (-LINEAR_SPEED, 0.0)
                last_key_time = time.monotonic()
            elif key in ('a', 'j'):
                velocity = (0.0, ANGULAR_SPEED)
                last_key_time = time.monotonic()
            elif key in ('d', 'l'):
                velocity = (0.0, -ANGULAR_SPEED)
                last_key_time = time.monotonic()

            now = time.monotonic()
            if now >= next_publish:
                if not last_key_time or now - last_key_time > key_timeout:
                    velocity = (0.0, 0.0)
                send(*velocity)
                next_publish = now + period
    finally:
        # Stop movement even when the user closes the console or presses Ctrl+C.
        try:
            send(0.0, 0.0)
            time.sleep(0.05)
            send(0.0, 0.0)
        except Exception as exc:
            print('Warning: final stop could not be sent: {}'.format(exc))
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main(argv=None):
    parser = argparse.ArgumentParser(description='ROS1 keyboard teleop for one Gazebo robot')
    parser.add_argument('--robot', required=True, help='e.g. tb3_burger_0')
    parser.add_argument('--model', required=True,
                        choices=('LOCOBOT', 'TURTLEBOT3_BURGER', 'TURTLEBOT3_WAFFLE',
                                 'JETBOT', 'INTERBOTIX', 'UNI050_BASE', 'HELLO_ROBOT_STRETCH'))
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', args.robot):
        parser.error('Invalid ROS namespace: {}'.format(args.robot))

    try:
        import rospy
        import rosgraph
        from geometry_msgs.msg import Twist
    except ImportError as exc:
        print('ROS1 Noetic Python modules are unavailable: {}'.format(exc),
              file=sys.stderr)
        return 1

    rospy.init_node('keyboard_teleop_' + args.robot, anonymous=True)

    # Closing a GNOME Terminal normally sends SIGHUP.  Convert that signal to
    # an orderly exit so keyboard_loop's finally block publishes zero velocity.
    if hasattr(signal, 'SIGHUP'):
        def on_terminal_closed(_signum, _frame):
            raise KeyboardInterrupt()
        signal.signal(signal.SIGHUP, on_terminal_closed)

    print('Waiting for the base controller of {} ...'.format(args.robot))
    try:
        master = rosgraph.Master('/keyboard_teleop_' + args.robot)
        topic = discover_topic(master, args.robot, args.model)
        keyboard_loop(rospy, Twist, topic, args.robot)
    except (RuntimeError, OSError) as exc:
        print('\n[Teleop ERROR] {}'.format(exc), file=sys.stderr)
        return 1
    except rospy.ROSInterruptException:
        pass
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
