import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
import tf
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import threading
import socket
import time
import json


class TaskRelay:
    def __init__(self):
        self.counter_flag = 0
        self.x = 0
        self.y = 0
        self.x1 = 0
        self.y1 = 0
        self.print_flag = 0
        self.dist1 = 0.0

        # 퍼블리셔 및 서브스크라이버 초기화
        self.pub = rospy.Publisher('/locobot_agent/description', String, queue_size=10)

        rospy.Subscriber("/locobot/odom", Odometry, self.callback1)
        rospy.Subscriber("new_agent_detected", String, self.callback2)

    def move_to_goal(self, agent, x_goal, y_goal, th_goal):
        client = actionlib.SimpleActionClient('/' + agent + '/move_base', MoveBaseAction)
        client.wait_for_server()

        # 목표 위치 및 자세 설정
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = x_goal
        goal.target_pose.pose.position.y = y_goal

        #print("[{0}] Go to x: {1} y: {2}".format(agent, x_goal, y_goal))
        print("[{0}] Go to x: {1} y: {2}".format(agent, x_goal, y_goal))

        q = tf.transformations.quaternion_from_euler(0, 0, th_goal)
        goal.target_pose.pose.orientation.x = q[0]
        goal.target_pose.pose.orientation.y = q[1]
        goal.target_pose.pose.orientation.z = q[2]
        goal.target_pose.pose.orientation.w = q[3]

        # 액션 서버에게 목표 전송
        client.send_goal(goal)
        wait = client.wait_for_result()

        if not wait:
            rospy.logerr("Action server not available!")
            rospy.signal_shutdown("Action server not available!")
            print("Action server not available!")
        else:
            result = client.get_result()
            if result:
                rospy.loginfo("[" + agent + "] Goal reached successfully!")
                print("[" + agent + "] Goal reached successfully!")
            return result 

    def callback1(self, data):
        self.x = data.pose.pose.position.x
        self.y = data.pose.pose.position.y
        if self.counter_flag == 1:
            self.get_position()
            del_x = (self.x - self.x1) ** 2
            del_y = (self.y - self.y1) ** 2
            self.dist1 = (del_x + del_y) ** (0.5)
            if self.dist1 < 1.0:
                if self.print_flag == 0:
                    print("dist: {}".format(self.dist1))
                    self.print_flag = 1

    def callback2(self, data):
        if data.data.startswith('new_/locobot_agent'):
            message_str = "name:locobot_agent\nmove_base,move_it,6dof robot arm, lidar, realsense camera\nport:9001"
            self.pub.publish(message_str)
        else:
            if not data.data.startswith("new_") and not data.data.startswith("/locobot_"): 
                counterpart = data.data
                rospy.Subscriber(data.data + "/description", String, self.callback3)
                pub2 = rospy.Publisher('new_agent_detected', String, queue_size=10)
                time.sleep(2)
                message_str = "new_" + counterpart
                pub2.publish(message_str)
        print("locobot callback: {}".format(data.data))

    def callback3(self, data):
        print("====  New Partner ====")
        print(data.data)
        self.counter_flag = 1

    def send_get_together(self):
        HOST = '127.0.0.1'
        PORT = 9003 
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(b'Hello, server')
            data = s.recv(1024)
            received_data = json.loads(data.decode())
            print(" === Start Go Together Task ===")

    def get_position(self):
        HOST = '127.0.0.1'
        PORT = 9002 
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(b'Hello, server')
            data = s.recv(1024)
            received_data = json.loads(data.decode())
            self.x1 = received_data['x']
            self.y1 = received_data['y']

    def position_server(self):
        HOST = '127.0.0.1'
        PORT = 9001 
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(None)
            s.bind((HOST, PORT))
            s.listen()
            print("Server started. Waiting for a connection...")
            while True:
                try:
                    conn, addr = s.accept()
                    with conn:
                        while True:
                            data = conn.recv(1024)
                            if not data:
                                break
                            send_str = '{"x": ' + str(self.x) + ', "y": ' + str(self.y) + '}'
                            conn.sendall(send_str.encode('utf-8'))
                except socket.timeout:
                    print(".")

    def init_movement(self):
        result = self.move_to_goal('locobot_0', 1.0, 1.0, 0.0)

        if result:
            rospy.loginfo("Goal reached successfully!")
            while True:
                if self.print_flag == 1:
                    print("---  Do you want to join the Group: Go Together ---")
                    self.send_get_together()
                    break
                else:
                    time.sleep(1)
        else:
            rospy.loginfo("Failed to reach the goal.")

        result = self.move_to_goal('locobot_1', 1.0, -1.0, 0.0)
        if result:
            rospy.loginfo("Goal reached successfully!")
        else:
            rospy.loginfo("Failed to reach the goal.")

    # 작업 시작
    def StartTask(self, robots):
        rospy.init_node('locobot_agent')
        for robot in robots:
            self.move_to_goal(robot.name, robot.moveToX, robot.moveToY, robot.moveToZ)
