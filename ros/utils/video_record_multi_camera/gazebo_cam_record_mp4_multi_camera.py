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


WAYPOINTS = [
    [1.3, 6.7],
    [-3.5, 6.7],
    [-3.5, -4.7],
    [1.8, -4.7],
]


# ============================================================
# EASY CAMERA SELECTION
# ============================================================
# 전체 녹화:
ACTIVE_CAMERA_NAMES = ["ego_view", "top_view", "corner_2", "corner_4", "south_view"]

# ego-view만 녹화해서 FPS 테스트하려면 위 줄을 주석 처리하고 아래 줄 사용:
# ACTIVE_CAMERA_NAMES = ["ego_view"]


TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080


CAMERA_CONFIGS = {
    "ego_view": {
        "topic": "/tb3_waffle_pi_0/camera/rgb/image_raw",
        "filename": "ego_view.mp4",
        "resize": True,
    },

    "top_view": {
        "topic": "/recording_cameras/top_view/image_raw",
        "filename": "top_view.mp4",
        "resize": False,
    },

    "corner_2": {
        "topic": "/recording_cameras/corner_2/image_raw",
        "filename": "corner_2.mp4",
        "resize": False,
    },

    "corner_4": {
        "topic": "/recording_cameras/corner_4/image_raw",
        "filename": "corner_4.mp4",
        "resize": False,
    },

    "south_view": {
        "topic": "/recording_cameras/south_view/image_raw",
        "filename": "south_view.mp4",
        "resize": False,
    },
}


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


class CameraRecorder:
    def __init__(self, name, topic, output_path, fps, codec_list, resize=False):
        self.name = name
        self.topic = topic
        self.output_path = output_path
        self.fps = fps
        self.codec_list = codec_list
        self.resize = resize

        self.bridge = CvBridge()
        self.lock = threading.Lock()
        self.latest_frame = None

        self.writer = None
        self.frame_count = 0

        rospy.Subscriber(
            self.topic,
            Image,
            self._image_cb,
            queue_size=1,
            buff_size=2**24
        )

        rospy.loginfo("[%s] subscribed: %s", self.name, self.topic)
        rospy.loginfo("[%s] output: %s", self.name, self.output_path)

    def _image_cb(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="bgr8"
            )

            if self.resize:
                frame = cv2.resize(
                    frame,
                    (TARGET_WIDTH, TARGET_HEIGHT),
                    interpolation=cv2.INTER_LINEAR
                )

            with self.lock:
                self.latest_frame = frame

        except Exception as e:
            rospy.logwarn(
                "[%s] image conversion failed: %s",
                self.name,
                str(e)
            )

    def _ensure_writer(self, frame):
        if self.writer is not None:
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
                self.writer = writer

                rospy.loginfo(
                    "[%s] VideoWriter opened with codec=%s, size=%dx%d",
                    self.name,
                    codec,
                    w,
                    h
                )

                return True

        rospy.logerr(
            "[%s] failed to open VideoWriter: %s",
            self.name,
            self.output_path
        )

        return False

    def write_latest_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return False

            frame = self.latest_frame.copy()

        if self._ensure_writer(frame):
            self.writer.write(frame)
            self.frame_count += 1
            return True

        return False

    def release(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None

            rospy.loginfo(
                "[%s] saved: %s, frames=%d",
                self.name,
                self.output_path,
                self.frame_count
            )


class MultiViewRecorderAndMover:
    def __init__(self):
        base_dir = os.getcwd()
        video_dir = os.path.join(base_dir, "video")
        os.makedirs(video_dir, exist_ok=True)

        self.fps = 30.0
        self.start_delay = 5.0
        self.duration = 120.0

        self.codec_list = ["mp4v"]

        self.recorders = []

        for name in ACTIVE_CAMERA_NAMES:
            cfg = CAMERA_CONFIGS[name]
            output_path = os.path.join(video_dir, cfg["filename"])

            recorder = CameraRecorder(
                name=name,
                topic=cfg["topic"],
                output_path=output_path,
                fps=self.fps,
                codec_list=self.codec_list,
                resize=cfg.get("resize", False)
            )

            self.recorders.append(recorder)

        self.odom_topic = "/tb3_waffle_pi_0/odom"
        self.cmd_vel_topic = "/tb3_waffle_pi_0/cmd_vel"

        self.waypoints = WAYPOINTS[:]
        self.move_delay_after_record_start = 2.0

        self.control_hz = 20.0
        self.k_lin = 0.6
        self.k_ang = 1.8
        self.max_lin = 0.22
        self.max_ang = 1.5

        self.dist_tol = 0.08
        self.yaw_tol = 0.12

        self._recording = False
        self._record_end_wall = None

        self._pose_lock = threading.Lock()
        self._x = None
        self._y = None
        self._yaw = None

        self._moving = False
        self._wp_idx = 0

        rospy.Subscriber(
            self.odom_topic,
            Odometry,
            self._odom_cb,
            queue_size=1
        )

        self.pub_cmd = rospy.Publisher(
            self.cmd_vel_topic,
            Twist,
            queue_size=1
        )

        self._rec_timer = rospy.Timer(
            rospy.Duration(1.0 / self.fps),
            self._rec_tick
        )

        self._ctrl_timer = rospy.Timer(
            rospy.Duration(1.0 / self.control_hz),
            self._ctrl_tick
        )

        rospy.loginfo("=== MultiViewRecorderAndMover ===")
        rospy.loginfo("Output directory: %s", video_dir)
        rospy.loginfo("Active cameras: %s", ACTIVE_CAMERA_NAMES)
        rospy.loginfo("Camera count: %d", len(self.recorders))

        threading.Thread(
            target=self._timing_thread,
            daemon=True
        ).start()

    def _odom_cb(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation

        with self._pose_lock:
            self._x = p.x
            self._y = p.y
            self._yaw = yaw_from_quat(q)

    def _rec_tick(self, _):
        if not self._recording:
            return

        if time.time() >= self._record_end_wall:
            self._stop_recording()
            self._stop_robot()
            rospy.signal_shutdown("Done")
            return

        for recorder in self.recorders:
            recorder.write_latest_frame()

    def _start_recording(self):
        self._recording = True
        self._record_end_wall = time.time() + self.duration

        rospy.loginfo("Recording started")

    def _stop_recording(self):
        self._recording = False

        for recorder in self.recorders:
            recorder.release()

        rospy.loginfo("All recordings saved")

    def _ctrl_tick(self, _):
        if not self._moving:
            return

        with self._pose_lock:
            if self._x is None or self._y is None or self._yaw is None:
                return

            x = self._x
            y = self._y
            yaw = self._yaw

        tx, ty = self.waypoints[self._wp_idx]

        dx = tx - x
        dy = ty - y

        dist = math.hypot(dx, dy)

        if dist < self.dist_tol:
            self._wp_idx = (self._wp_idx + 1) % len(self.waypoints)
            self._stop_robot()
            return

        target_yaw = math.atan2(dy, dx)
        yaw_err = angle_diff(target_yaw, yaw)

        cmd = Twist()

        if abs(yaw_err) > self.yaw_tol:
            cmd.angular.z = clamp(
                self.k_ang * yaw_err,
                -self.max_ang,
                self.max_ang
            )
        else:
            cmd.linear.x = clamp(
                self.k_lin * dist,
                0,
                self.max_lin
            )

            cmd.angular.z = clamp(
                self.k_ang * yaw_err,
                -self.max_ang,
                self.max_ang
            )

        self.pub_cmd.publish(cmd)

    def _stop_robot(self):
        self.pub_cmd.publish(Twist())

    def _timing_thread(self):
        time.sleep(self.start_delay)

        self._start_recording()

        time.sleep(self.move_delay_after_record_start)

        self._moving = True

        rospy.loginfo("Robot movement started")


def main():
    rospy.init_node("tb3_waffle_pi_selected_view_rec_and_move")

    MultiViewRecorderAndMover()

    rospy.spin()


if __name__ == "__main__":
    main()
