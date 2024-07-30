#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist
import sys, select, termios, tty

def getKey():
    tty.setraw(sys.stdin.fileno())
    select.select([sys.stdin], [], [], 0)
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

if __name__ == "__main__":
    settings = termios.tcgetattr(sys.stdin)

    rospy.init_node('keyboard_teleop')
    pub = rospy.Publisher('cmd_vel', Twist, queue_size=10)

    speed = 0.5
    turn = 1.0
    x = 0
    th = 0
    status = 0

    try:
        print("Reading from the keyboard and Publishing to Twist!")
        print("Use arrow keys to move the robot")
        while(1):
            key = getKey()
            if key == 'w':
                x = 1
            elif key == 'x':
                x = -1
            elif key == 'a':
                th = 1
            elif key == 'd':
                th = -1
            elif key == ' ' or key == 's':
                x = 0
                th = 0
            elif key == '\x03':
                break

            twist = Twist()
            twist.linear.x = x * speed
            twist.angular.z = th * turn
            pub.publish(twist)

    except Exception as e:
        print(e)

    finally:
        twist = Twist()
        twist.linear.x = 0
        twist.angular.z = 0
        pub.publish(twist)

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

