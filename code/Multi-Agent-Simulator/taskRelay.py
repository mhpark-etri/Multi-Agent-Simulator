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

    # 작업 시작 — 연쇄 릴레이 (2026-08-08)
    # robot1 이 robot2 위치 '근처'로, robot2 가 robot3 위치 근처로, ...
    # 마지막 로봇만 자신의 Move-To(최종 목표)로 이동한다.
    def StartTask(self, robots):
        import math
        from geometry_msgs.msg import PoseStamped
        # ★ 백그라운드 스레드에서 호출되므로 signal 핸들러 등록 불가(disable_signals)
        #   + 두 번째 실행에서 init_node 중복 호출이 되지 않게 가드
        if not rospy.core.is_initialized():
            rospy.init_node('locobot_agent', disable_signals=True)
        n = len(robots)
        # ── 체인 goal 전체를 먼저 계산 ──
        plans = []
        for i in range(n):
            cur = robots[i]
            if i < n - 1:
                nxt = robots[i + 1]
                cx, cy = float(cur.startX), float(cur.startY)
                nx, ny = float(nxt.startX), float(nxt.startY)
                dx, dy = nx - cx, ny - cy
                d = math.hypot(dx, dy) or 1.0
                # 다음 로봇 0.9m 앞에서 정지 (로봇 반경+inflation 여유), 진행 방향을 바라봄
                gx = nx - 0.9 * dx / d
                gy = ny - 0.9 * dy / d
                th = math.atan2(dy, dx)
            else:
                gx, gy, th = float(cur.moveToX), float(cur.moveToY), 0.0
            plans.append((cur.name, gx, gy, th))
        # ── 계획 전체를 미리 발행 → RViz/Gazebo 에 4개 목표가 시작 즉시 표시됨 ──
        self._plan_pubs = []
        for name, gx, gy, th in plans:
            pub = rospy.Publisher('/relay_plan/' + name, PoseStamped,
                                  queue_size=1, latch=True)
            ps = PoseStamped()
            ps.header.frame_id = 'map'
            ps.header.stamp = rospy.Time.now()
            ps.pose.position.x = gx
            ps.pose.position.y = gy
            q = tf.transformations.quaternion_from_euler(0, 0, th)
            ps.pose.orientation.x, ps.pose.orientation.y = q[0], q[1]
            ps.pose.orientation.z, ps.pose.orientation.w = q[2], q[3]
            pub.publish(ps)
            self._plan_pubs.append(pub)     # latch 유지를 위해 보관
        rospy.sleep(0.5)
        # ── 순차 주행 ──
        for i, (name, gx, gy, th) in enumerate(plans):
            tgt = robots[i + 1].name + " 위치 근처" if i < n - 1 else "최종 목표"
            print(f"[RELAY {i+1}/{n}] {name} → {tgt} ({gx:.2f},{gy:.2f})")
            self.move_to_goal(name, gx, gy, th)
