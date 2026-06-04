#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import threading
import math

import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist

import cv2


# =========================
# EDIT HERE: Waypoints (odom frame)
# =========================
WAYPOINTS = [
    [1.3, 6.7],
    [-3.5, 6.7],
    [-3.5, -4.7],
    [1.8, -4.7],
]


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def yaw_from_quat(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def angle_diff(a, b):
    d = a - b
    while d > math.pi:
        d -= 2.0 * math.pi
    while d < -math.pi:
        d += 2.0 * math.pi
    return d


class RecorderAndMover:
    def __init__(self):
        # =========================
        # Recording config
        # =========================
        self.image_topic = "/tb3_waffle_pi_0/camera/rgb/image_raw"

        # 📁 output path: ./video/tb3_waffle_pi_cam.mp4
        base_dir = os.getcwd()
        video_dir = os.path.join(base_dir, "video")
        os.makedirs(video_dir, exist_ok=True)
        self.output_path = os.path.join(video_dir, "tb3_waffle_pi_cam.mp4")

        self.fps = 30.0
        self.start_delay = 5.0
        self.duration = 120.0

        # Optional resize (0 => original)
        self.out_width = 0
        self.out_height = 0

        # MP4 codec preference
        self.codec_list = ["avc1", "mp4v"]

        # =========================
        # Motion config
        # =========================
        self.odom_topic = "/tb3_waffle_pi_0/odom"
        self.cmd_vel_topic = "/tb3_waffle_pi_0/cmd_vel"

        self.waypoints = WAYPOINTS[:]
        self.move_delay_after_record_start = 2.0  # seconds

        # Controller tuning
        self.control_hz = 20.0
        self.k_lin = 0.6
        self.k_ang = 1.8
        self.max_lin = 0.22
        self.max_ang = 1.5

        # Tolerances
        self.dist_tol = 0.08   # meters
        self.yaw_tol = 0.12    # radians

        # =========================
        # State
        # =========================
        self.bridge = CvBridge()

        self._img_lock = threading.Lock()
        self._latest_frame = None
        self._writer = None

        self._recording = False
        self._record_end_wall = None

        self._pose_lock = threading.Lock()
        self._x = None
        self._y = None
        self._yaw = None

        self._moving = False
        self._wp_idx = 0

        # =========================
        # ROS I/O
        # =========================
        rospy.Subscriber(
            self.image_topic, Image, self._image_cb,
            queue_size=1, buff_size=2**24
        )
        rospy.Subscriber(
            self.odom_topic, Odometry, self._odom_cb,
            queue_size=1
        )
        self.pub_cmd = rospy.Publisher(self.cmd_vel_topic, Twist, queue_size=1)

        self._rec_timer = rospy.Timer(rospy.Duration(1.0 / self.fps), self._rec_tick)
        self._ctrl_timer = rospy.Timer(rospy.Duration(1.0 / self.control_hz), self._ctrl_tick)

        rospy.loginfo("=== RecorderAndMover ===")
        rospy.loginfo("Output video: %s", self.output_path)
        rospy.loginfo("Waypoints: %s", self.waypoints)

        threading.Thread(target=self._timing_thread, daemon=True).start()

    # -------------------------
    # Callbacks
    # -------------------------
    def _image_cb(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            with self._img_lock:
                self._latest_frame = frame
        except Exception:
            pass

    def _odom_cb(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        with self._pose_lock:
            self._x = p.x
            self._y = p.y
            self._yaw = yaw_from_quat(q)

    # -------------------------
    # Recording
    # -------------------------
    def _ensure_writer(self, frame):
        if self._writer is not None:
            return True

        h, w = frame.shape[:2]
        for codec in self.codec_list:
            writer = cv2.VideoWriter(
                self.output_path,
                cv2.VideoWriter_fourcc(*codec),
                self.fps,
                (w, h)
            )
            if writer.isOpened():
                self._writer = writer
                rospy.loginfo("VideoWriter opened with codec=%s", codec)
                return True
        return False

    def _rec_tick(self, _):
        if not self._recording:
            return

        if time.time() >= self._record_end_wall:
            self._stop_recording()
            self._stop_robot()
            rospy.signal_shutdown("Done")
            return

        with self._img_lock:
            if self._latest_frame is None:
                return
            frame = self._latest_frame.copy()

        if self._ensure_writer(frame):
            self._writer.write(frame)

    def _start_recording(self):
        self._recording = True
        self._record_end_wall = time.time() + self.duration
        rospy.loginfo("Recording started")

    def _stop_recording(self):
        if self._writer:
            self._writer.release()
        rospy.loginfo("Recording saved to %s", self.output_path)

    # -------------------------
    # Motion
    # -------------------------
    def _ctrl_tick(self, _):
        if not self._moving:
            return

        with self._pose_lock:
            if self._x is None:
                return
            x, y, yaw = self._x, self._y, self._yaw

        tx, ty = self.waypoints[self._wp_idx]
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)

        if dist < self.dist_tol:
            self._wp_idx = (self._wp_idx + 1) % len(self.waypoints)
            self._stop_robot()
            return

        target_yaw = math.atan2(dy, dx)
        yaw_err = angle_diff(target_yaw, yaw)

        cmd = Twist()
        if abs(yaw_err) > self.yaw_tol:
            cmd.angular.z = clamp(self.k_ang * yaw_err, -self.max_ang, self.max_ang)
        else:
            cmd.linear.x = clamp(self.k_lin * dist, 0, self.max_lin)
            cmd.angular.z = clamp(self.k_ang * yaw_err, -self.max_ang, self.max_ang)

        self.pub_cmd.publish(cmd)

    def _stop_robot(self):
        self.pub_cmd.publish(Twist())

    # -------------------------
    # Timing
    # -------------------------
    def _timing_thread(self):
        time.sleep(self.start_delay)
        self._start_recording()
        time.sleep(self.move_delay_after_record_start)
        self._moving = True


def main():
    rospy.init_node("tb3_waffle_pi_rec_and_move")
    RecorderAndMover()
    rospy.spin()


if __name__ == "__main__":
    main()

