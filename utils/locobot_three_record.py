#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three TurtleBot3 Waffles: align, drive together, save three MP4 files."""

# ========================== USER SETTINGS ==========================
ROBOT_NAMES = ("tb3_waffle_0", "tb3_waffle_1", "tb3_waffle_2")

# (world x, world y, world z or None, yaw in degrees)
# Replace these example coordinates with your existing world coordinates.
INITIAL_POSES = {
    "tb3_waffle_0": (-5.0, -3.0, None, 0.0),
    "tb3_waffle_1": (-5.0,  3.0, None, 0.0),
    "tb3_waffle_2": ( 5.0,  0.0, None, 180.0),
}

TARGET_POSITION = (0.0, 0.0)
STOP_DISTANCE_M = 1.0

# Simulation seconds, measured AFTER alignment.
MIN_TRAVEL_SECONDS = 20.0
TARGET_TRAVEL_SECONDS = 25.0
MAX_TRAVEL_SECONDS = 30.0

# Gazebo simulation only; not a physical TurtleBot speed specification.
MAX_LINEAR_SPEED = 0.60
MAX_ANGULAR_SPEED = 0.60
GOAL_TOLERANCE = 0.08
HEADING_GAIN = 1.8
CONTROL_HZ = 60.0

ALIGN_TOLERANCE_DEG = 5.0
ALIGN_RECHECK_DEG = 8.0
ALIGN_STABLE_SECONDS = 0.3
ALIGN_TIMEOUT_SIM = 90.0
ALIGN_TIMEOUT_WALL = 180.0

VIDEO_FPS = 30.0
VIDEO_SIZE = (1920, 1080)
OUTPUT_FOLDER = "videos"

# Filenames are intentionally independent of the Gazebo model names.
OUTPUT_FILENAMES = {
    "tb3_waffle_0": "locobot_0.mp4",
    "tb3_waffle_1": "locobot_1.mp4",
    "tb3_waffle_2": "locobot_2.mp4",
}

OVERWRITE_VIDEOS = True

# Empty values enable topic discovery within each robot namespace.
CMD_TOPICS = {name: "" for name in ROBOT_NAMES}
IMAGE_TOPICS = {name: "" for name in ROBOT_NAMES}

STARTUP_TIMEOUT_WALL = 60.0
STALE_TIMEOUT_WALL = 10.0
CLOCK_TIMEOUT_WALL = 15.0
CAMERA_HISTORY_SIZE = 12
ENCODER_QUEUE_SIZE = 12
FRAME_DELAY_SIM = 0.10
# ===================================================================

import json
import math
import queue
import sys
import threading
import time

from collections import deque
from pathlib import Path

import cv2
import rosgraph
import rospy

from cv_bridge import CvBridge
from gazebo_msgs.msg import ModelState, ModelStates
from gazebo_msgs.srv import SetModelState
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image


def wrap_angle(value):
    return math.atan2(math.sin(value), math.cos(value))


def clamp(value, limit):
    return max(-limit, min(limit, value))


def stopping_goals(poses):
    ox, oy = TARGET_POSITION
    goals = {}

    for name in ROBOT_NAMES:
        dx = poses[name][0] - ox
        dy = poses[name][1] - oy
        distance = math.hypot(dx, dy)

        if distance <= STOP_DISTANCE_M + GOAL_TOLERANCE + 0.05:
            raise RuntimeError(
                name + " starts too close to the object."
            )

        goals[name] = (
            ox + STOP_DISTANCE_M * dx / distance,
            oy + STOP_DISTANCE_M * dy / distance,
        )

    return goals


def speed_plan(distances):
    if any(
        d <= GOAL_TOLERANCE + 0.05
        for d in distances.values()
    ):
        raise RuntimeError(
            "A robot starts too close to its stopping goal."
        )

    effective = {
        name: distance - GOAL_TOLERANCE * 0.5
        for name, distance in distances.items()
    }

    # Keep one second of recovery margin before the hard deadline.
    duration = max(
        TARGET_TRAVEL_SECONDS,
        max(effective.values()) / MAX_LINEAR_SPEED + 0.75,
    )

    if duration > MAX_TRAVEL_SECONDS - 1.0:
        raise RuntimeError(
            "Route too long for the configured speed and "
            "30-second limit. Required nominal duration: "
            "{:.2f}s. Shorten the route or review "
            "MAX_LINEAR_SPEED for this simulation."
            .format(duration)
        )

    return duration, {
        name: distance / duration
        for name, distance in effective.items()
    }


def linear_command(distance, elapsed, duration):
    # Recalculate from actual remaining distance.
    remaining = max(
        0.0,
        distance - GOAL_TOLERANCE * 0.5
    )

    speed = min(
        MAX_LINEAR_SPEED,
        remaining / max(duration - elapsed, 0.25)
    )

    if elapsed < MIN_TRAVEL_SECONDS:
        # Discourage arrival before the minimum travel time.
        early_limit = (
            max(0.0, distance - GOAL_TOLERANCE)
            / (MIN_TRAVEL_SECONDS - elapsed + 0.5)
        )

        speed = min(speed, early_limit)

    return speed


def discover_topics():
    master = rosgraph.Master(rospy.get_name())
    deadline = time.monotonic() + STARTUP_TIMEOUT_WALL
    commands, cameras = {}, {}

    while (
        not rospy.is_shutdown()
        and time.monotonic() < deadline
    ):
        publishers, subscribers, _ = master.getSystemState()

        published = {
            topic for topic, nodes in publishers if nodes
        }

        subscribed = {
            topic for topic, nodes in subscribers if nodes
        }

        types = dict(master.getTopicTypes())
        commands, cameras = {}, {}

        for name in ROBOT_NAMES:
            if CMD_TOPICS[name]:
                candidates = [CMD_TOPICS[name]]
            else:
                candidates = [
                    "/" + name + "/cmd_vel",
                    "/" + name + "/mobile_base/commands/velocity",
                ]

            for topic in candidates:
                if (
                    topic in subscribed
                    and types.get(topic) == "geometry_msgs/Twist"
                ):
                    commands[name] = topic
                    break

            if IMAGE_TOPICS[name]:
                candidates = [IMAGE_TOPICS[name]]
            else:
                candidates = [
                    "/" + name + "/camera/rgb/image_raw",
                    "/" + name + "/camera/image_raw",
                    "/" + name + "/camera/color/image_raw",
                ]

            for topic in candidates:
                if (
                    topic in published
                    and types.get(topic) == "sensor_msgs/Image"
                ):
                    cameras[name] = topic
                    break

        if len(commands) == len(ROBOT_NAMES) == len(cameras):
            if len(set(commands.values())) != len(ROBOT_NAMES):
                raise RuntimeError(
                    "Each robot needs a separate velocity topic."
                )

            if len(set(cameras.values())) != len(ROBOT_NAMES):
                raise RuntimeError(
                    "Each robot needs a separate camera topic."
                )

            for name in ROBOT_NAMES:
                others = dict(publishers).get(commands[name], [])

                if others:
                    raise RuntimeError(
                        "Stop other velocity publishers: {} -> {}"
                        .format(commands[name], others)
                    )

                rospy.loginfo(
                    "%s | cmd=%s | camera=%s",
                    name,
                    commands[name],
                    cameras[name]
                )

            return commands, cameras

        time.sleep(0.2)

    raise RuntimeError(
        "Topic discovery failed. "
        "Check ROBOT_NAMES and rostopic list. "
        "Found commands={}, cameras={}"
        .format(commands, cameras)
    )


class VideoSet:
    def __init__(self, folder):
        self.queue = queue.Queue(maxsize=ENCODER_QUEUE_SIZE)
        self.writers = {}
        self.counts = {name: 0 for name in ROBOT_NAMES}
        self.error = None

        try:
            for name in ROBOT_NAMES:
                writer = cv2.VideoWriter(
                    str(folder / OUTPUT_FILENAMES[name]),
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    VIDEO_FPS,
                    VIDEO_SIZE,
                )

                self.writers[name] = writer

                if not writer.isOpened():
                    raise RuntimeError(
                        "Cannot open MP4 writer: " + name
                    )

        except Exception:
            for writer in self.writers.values():
                writer.release()
            raise

        self.thread = threading.Thread(
            target=self._worker,
            daemon=True
        )

        self.thread.start()

    def _worker(self):
        try:
            while True:
                frames = self.queue.get()

                try:
                    if frames is None:
                        return

                    if self.error is None:
                        for name in ROBOT_NAMES:
                            self.writers[name].write(frames[name])
                            self.counts[name] += 1

                except Exception as exc:
                    self.error = str(exc)

                finally:
                    self.queue.task_done()

        finally:
            for writer in self.writers.values():
                writer.release()

    def submit(self, frames):
        if self.error:
            raise RuntimeError(
                "Video encoding failed: " + self.error
            )

        try:
            self.queue.put_nowait(frames)

        except queue.Full:
            raise RuntimeError(
                "Video encoder queue full; stopping all robots."
            )

    def close(self):
        try:
            self.queue.put(None, timeout=10.0)

        except queue.Full:
            raise RuntimeError(
                "Encoder did not drain; MP4 may be incomplete."
            )

        self.thread.join(timeout=30.0)

        if self.thread.is_alive():
            raise RuntimeError(
                "Encoder shutdown timeout; MP4 may be incomplete."
            )

        if self.error:
            raise RuntimeError(
                "Video encoding failed: " + self.error
            )


class Experiment:
    def __init__(self):
        self.lock = threading.Lock()
        self.bridge = CvBridge()

        self.poses = {}
        self.pose_wall = 0.0
        self.image_wall = {}

        self.history = {
            name: deque(maxlen=CAMERA_HISTORY_SIZE)
            for name in ROBOT_NAMES
        }

        self.image_ids = {name: 0 for name in ROBOT_NAMES}
        self.last_used = {name: None for name in ROBOT_NAMES}
        self.duplicates = {name: 0 for name in ROBOT_NAMES}

        self.input_error = None
        self.publishers = {}
        self.subscribers = []

        self.resolved_cmd = {}
        self.resolved_image = {}

        self.goals = {}
        self.recorder = None
        self.folder = None

        self.start_sim = None
        self.end_sim = None
        self.start_wall = None
        self.end_wall = None

        self.planned_duration = None
        self.frame_index = 0
        self.reason = "not_started"

        self.last_clock = 0.0
        self.clock_wall = time.monotonic()

        rospy.on_shutdown(self.stop_all)

    def model_callback(self, msg):
        poses = {}

        for name, pose in zip(msg.name, msg.pose):
            if name not in ROBOT_NAMES:
                continue

            q = pose.orientation

            yaw = math.atan2(
                2.0 * (q.w * q.z + q.x * q.y),
                1.0 - 2.0 * (q.y * q.y + q.z * q.z),
            )

            poses[name] = (
                pose.position.x,
                pose.position.y,
                pose.position.z,
                yaw
            )

        with self.lock:
            self.poses = poses
            self.pose_wall = time.monotonic()

    def image_callback(self, msg, name):
        try:
            if (msg.width, msg.height) != VIDEO_SIZE:
                raise RuntimeError(
                    "{} camera is {}x{}; required {}x{}. "
                    "Edit the camera xacro."
                    .format(
                        name,
                        msg.width,
                        msg.height,
                        *VIDEO_SIZE
                    )
                )

            stamp = msg.header.stamp.to_sec()

            if stamp <= 0.0:
                raise RuntimeError(
                    name + " has an invalid camera timestamp."
                )

            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="bgr8"
            )

            with self.lock:
                self.image_wall[name] = time.monotonic()

                if (
                    self.history[name]
                    and stamp <= self.history[name][-1][0]
                ):
                    return

                self.image_ids[name] += 1

                self.history[name].append(
                    (stamp, self.image_ids[name], frame)
                )

        except Exception as exc:
            with self.lock:
                self.input_error = str(exc)

    def stop_all(self):
        for publisher in self.publishers.values():
            try:
                publisher.publish(Twist())
            except Exception:
                pass

    def send(self, velocities):
        for name in ROBOT_NAMES:
            msg = Twist()
            msg.linear.x, msg.angular.z = velocities[name]
            self.publishers[name].publish(msg)

    def now(self):
        if rospy.is_shutdown():
            raise rospy.ROSInterruptException("ROS shutdown")

        now = rospy.get_time()
        wall = time.monotonic()

        if now < self.last_clock - 1e-6:
            raise RuntimeError(
                "Gazebo clock reset during execution."
            )

        if now > self.last_clock:
            self.last_clock = now
            self.clock_wall = wall

        elif wall - self.clock_wall > CLOCK_TIMEOUT_WALL:
            raise RuntimeError(
                "Gazebo clock stopped. Check Play/Pause."
            )

        return now

    def inputs(self):
        wall = time.monotonic()

        with self.lock:
            if self.input_error:
                raise RuntimeError(self.input_error)

            if any(
                name not in self.poses or not self.history[name]
                for name in ROBOT_NAMES
            ):
                raise RuntimeError(
                    "Missing robot states or camera images."
                )

            if wall - self.pose_wall > STALE_TIMEOUT_WALL:
                raise RuntimeError(
                    "Gazebo model states are stale."
                )

            for name in ROBOT_NAMES:
                if (
                    wall - self.image_wall[name]
                    > STALE_TIMEOUT_WALL
                ):
                    raise RuntimeError(
                        name + " camera is stale."
                    )

            return dict(self.poses)

    def prepare(self):
        if not rospy.get_param("/use_sim_time", False):
            raise RuntimeError(
                "This simulation script requires "
                "/use_sim_time=true."
            )

        if not (
            20.0 <= MIN_TRAVEL_SECONDS
            <= TARGET_TRAVEL_SECONDS
            <= MAX_TRAVEL_SECONDS
            <= 30.0
        ):
            raise ValueError(
                "Use 20 <= MIN <= TARGET <= MAX <= 30 seconds."
            )

        if not all(
            math.isfinite(v) and v > 0
            for v in (
                MAX_LINEAR_SPEED,
                MAX_ANGULAR_SPEED,
                GOAL_TOLERANCE,
                CONTROL_HZ,
                VIDEO_FPS,
                STOP_DISTANCE_M,
            )
        ):
            raise ValueError(
                "Rates, speeds and distances must be "
                "positive and finite."
            )

        if STOP_DISTANCE_M <= GOAL_TOLERANCE:
            raise ValueError(
                "STOP_DISTANCE_M must exceed GOAL_TOLERANCE."
            )

        if (
            len(TARGET_POSITION) != 2
            or not all(
                math.isfinite(v)
                for v in TARGET_POSITION
            )
        ):
            raise ValueError(
                "TARGET_POSITION must be a finite (x, y) pair."
            )

        for name in ROBOT_NAMES:
            x, y, z, yaw = INITIAL_POSES[name]

            if not all(
                math.isfinite(v)
                for v in (x, y, yaw)
            ):
                raise ValueError(
                    "Invalid initial pose: " + name
                )

            if z is not None and not math.isfinite(z):
                raise ValueError(
                    "Invalid z coordinate: " + name
                )

            filename = OUTPUT_FILENAMES[name]

            if (
                Path(filename).name != filename
                or not filename.endswith(".mp4")
            ):
                raise ValueError(
                    "Use a plain .mp4 filename for " + name
                )

        if len(set(OUTPUT_FILENAMES.values())) != len(ROBOT_NAMES):
            raise ValueError(
                "Output filenames must be different."
            )

        self.resolved_cmd, self.resolved_image = discover_topics()

        for name in ROBOT_NAMES:
            self.publishers[name] = rospy.Publisher(
                self.resolved_cmd[name],
                Twist,
                queue_size=1,
                tcp_nodelay=True
            )

            self.subscribers.append(
                rospy.Subscriber(
                    self.resolved_image[name],
                    Image,
                    self.image_callback,
                    callback_args=name,
                    queue_size=1,
                    buff_size=16 * 1024 * 1024,
                    tcp_nodelay=True,
                )
            )

        self.subscribers.append(
            rospy.Subscriber(
                "/gazebo/model_states",
                ModelStates,
                self.model_callback,
                queue_size=1
            )
        )

        deadline = time.monotonic() + STARTUP_TIMEOUT_WALL

        while (
            not rospy.is_shutdown()
            and time.monotonic() < deadline
        ):
            self.stop_all()

            with self.lock:
                if self.input_error:
                    raise RuntimeError(self.input_error)

                ready = all(
                    name in self.poses and self.history[name]
                    for name in ROBOT_NAMES
                )

            if (
                ready
                and rospy.get_time() > 0
                and all(
                    pub.get_num_connections() > 0
                    for pub in self.publishers.values()
                )
            ):
                self.last_clock = rospy.get_time()
                self.clock_wall = time.monotonic()
                return

            time.sleep(0.02)

        raise RuntimeError(
            "Startup timeout: check model names, "
            "cameras and Gazebo Play."
        )

    def hold(self, seconds):
        start = self.now()

        while self.now() - start < seconds:
            self.inputs()
            self.stop_all()
            time.sleep(1.0 / CONTROL_HZ)

    def reset_positions(self):
        self.hold(0.3)
        poses = self.inputs()

        rospy.wait_for_service(
            "/gazebo/set_model_state",
            timeout=15.0
        )

        set_state = rospy.ServiceProxy(
            "/gazebo/set_model_state",
            SetModelState
        )

        for name in ROBOT_NAMES:
            x, y, z, yaw_deg = INITIAL_POSES[name]

            state = ModelState()
            state.model_name = name
            state.reference_frame = "world"

            state.pose.position.x = x
            state.pose.position.y = y

            state.pose.position.z = (
                poses[name][2] if z is None else z
            )

            yaw = math.radians(yaw_deg)

            state.pose.orientation.z = math.sin(yaw / 2.0)
            state.pose.orientation.w = math.cos(yaw / 2.0)

            result = set_state(state)

            if not result.success:
                raise RuntimeError(
                    "Reposition failed for {}: {}"
                    .format(name, result.status_message)
                )

        self.hold(0.7)
        poses = self.inputs()

        for name in ROBOT_NAMES:
            x, y = INITIAL_POSES[name][:2]

            if math.hypot(
                poses[name][0] - x,
                poses[name][1] - y
            ) > 0.15:
                raise RuntimeError(
                    name + " did not settle at the initial position."
                )

        self.goals = stopping_goals(poses)

        for name in ROBOT_NAMES:
            rospy.loginfo(
                "%s | initial=(%.2f, %.2f) | stop=(%.2f, %.2f)",
                name,
                poses[name][0],
                poses[name][1],
                *self.goals[name]
            )

        speed_plan(self.distances(poses))

    def distances(self, poses):
        return {
            name: math.hypot(
                self.goals[name][0] - poses[name][0],
                self.goals[name][1] - poses[name][1]
            )
            for name in ROBOT_NAMES
        }

    def heading_error(self, name, pose):
        gx, gy = self.goals[name]

        return wrap_angle(
            math.atan2(
                gy - pose[1],
                gx - pose[0]
            ) - pose[3]
        )

    def align(self):
        rospy.loginfo(
            "ALIGN: all robots rotate first; recording is OFF."
        )

        start_sim = self.now()
        start_wall = time.monotonic()
        last_log = 0.0

        stable = {name: None for name in ROBOT_NAMES}
        ready = {name: False for name in ROBOT_NAMES}

        while True:
            now = self.now()
            poses = self.inputs()

            errors = {
                name: self.heading_error(name, poses[name])
                for name in ROBOT_NAMES
            }

            if (
                now - start_sim > ALIGN_TIMEOUT_SIM
                or time.monotonic() - start_wall > ALIGN_TIMEOUT_WALL
            ):
                raise RuntimeError(
                    "Alignment timeout: "
                    + str({
                        name: round(math.degrees(errors[name]), 2)
                        for name in ROBOT_NAMES
                    })
                )

            velocities = {}

            for name in ROBOT_NAMES:
                degrees = abs(math.degrees(errors[name]))

                if ready[name] and degrees > ALIGN_RECHECK_DEG:
                    ready[name] = False
                    stable[name] = None

                if ready[name]:
                    velocities[name] = (0.0, 0.0)

                elif degrees <= ALIGN_TOLERANCE_DEG:
                    velocities[name] = (0.0, 0.0)

                    if stable[name] is None:
                        stable[name] = now

                    if now - stable[name] >= ALIGN_STABLE_SECONDS:
                        ready[name] = True

                else:
                    stable[name] = None

                    velocities[name] = (
                        0.0,
                        clamp(
                            HEADING_GAIN * errors[name],
                            MAX_ANGULAR_SPEED
                        )
                    )

            self.send(velocities)

            if time.monotonic() - last_log >= 2.0:
                last_log = time.monotonic()

                rospy.loginfo(
                    "ALIGN | "
                    + " | ".join(
                        "{}: {:.1f}deg {}".format(
                            name,
                            math.degrees(errors[name]),
                            "READY" if ready[name] else "ROTATING"
                        )
                        for name in ROBOT_NAMES
                    )
                )

            if all(ready.values()):
                self.hold(0.25)
                poses = self.inputs()

                bad = [
                    name
                    for name in ROBOT_NAMES
                    if abs(
                        math.degrees(
                            self.heading_error(name, poses[name])
                        )
                    ) > ALIGN_RECHECK_DEG
                ]

                if not bad:
                    rospy.loginfo(
                        "All three robots aligned."
                    )
                    return

                for name in bad:
                    ready[name] = False
                    stable[name] = None

            time.sleep(1.0 / CONTROL_HZ)

    def open_output(self):
        folder = Path(OUTPUT_FOLDER).expanduser()

        if not folder.is_absolute():
            folder = (
                Path(__file__).resolve().parent
                / folder
            )

        folder.mkdir(parents=True, exist_ok=True)

        paths = [
            folder / OUTPUT_FILENAMES[name]
            for name in ROBOT_NAMES
        ]

        paths.append(folder / "session.json")

        existing = [
            str(path)
            for path in paths
            if path.exists()
        ]

        if existing and not OVERWRITE_VIDEOS:
            raise RuntimeError(
                "Output exists: " + ", ".join(existing)
            )

        if existing:
            rospy.logwarn(
                "Overwriting these outputs: %s",
                ", ".join(existing)
            )

        self.recorder = VideoSet(folder)
        self.folder = folder

    def emit_frames(self, until):
        count = max(
            1,
            int(
                math.ceil(
                    (until - self.start_sim) * VIDEO_FPS - 1e-9
                )
            )
        )

        while self.frame_index < count:
            stamp = (
                self.start_sim
                + self.frame_index / VIDEO_FPS
            )

            frames = {}
            ids = {}

            with self.lock:
                for name in ROBOT_NAMES:
                    entry = next(
                        (
                            item
                            for item in reversed(self.history[name])
                            if item[0] <= stamp + 1e-6
                        ),
                        None
                    )

                    if entry is None:
                        raise RuntimeError(
                            "Camera history overrun: " + name
                        )

                    if stamp - entry[0] > 1.0:
                        raise RuntimeError(
                            "Stale camera timestamp: " + name
                        )

                    _, ids[name], frames[name] = entry

            self.recorder.submit(frames)

            for name in ROBOT_NAMES:
                if ids[name] == self.last_used[name]:
                    self.duplicates[name] += 1

                self.last_used[name] = ids[name]

            self.frame_index += 1

    def finish(self, now, reason):
        self.stop_all()

        self.end_sim = min(
            now,
            self.start_sim + MAX_TRAVEL_SECONDS
        )

        self.end_wall = time.monotonic()
        self.reason = reason

        self.emit_frames(self.end_sim)

        rospy.loginfo(
            "STOP | %s | sim=%.3fs | wall=%.3fs",
            reason,
            self.end_sim - self.start_sim,
            self.end_wall - self.start_wall
        )

    def run(self):
        self.prepare()
        self.reset_positions()
        self.align()

        self.planned_duration, speeds = speed_plan(
            self.distances(self.inputs())
        )

        self.open_output()

        for name in ROBOT_NAMES:
            rospy.loginfo(
                "%s | nominal %.3f m/s | file=%s",
                name,
                speeds[name],
                self.folder / OUTPUT_FILENAMES[name]
            )

        rospy.loginfo(
            "Target %.2fs; allowed %.1f-%.1fs "
            "(SIMULATION TIME).",
            self.planned_duration,
            MIN_TRAVEL_SECONDS,
            MAX_TRAVEL_SECONDS
        )

        self.reason = "running"
        self.start_sim = self.now()
        self.start_wall = time.monotonic()

        self.send({
            name: (speeds[name], 0.0)
            for name in ROBOT_NAMES
        })

        self.emit_frames(self.start_sim)

        rospy.loginfo(
            "START: all three motion commands "
            "+ all three recordings."
        )

        last_log = 0.0

        while True:
            now = self.now()
            poses = self.inputs()

            elapsed = now - self.start_sim
            distances = self.distances(poses)

            arrived = [
                name
                for name in ROBOT_NAMES
                if distances[name] <= GOAL_TOLERANCE
            ]

            if arrived and elapsed <= MAX_TRAVEL_SECONDS:
                if elapsed < MIN_TRAVEL_SECONDS:
                    self.finish(
                        now,
                        "early_arrival:" + ",".join(arrived)
                    )

                    raise RuntimeError(
                        "Arrival before 20s; "
                        "check external motion/controllers."
                    )

                self.finish(
                    now,
                    "arrived:" + ",".join(arrived)
                )

                return

            if elapsed >= MAX_TRAVEL_SECONDS:
                self.finish(
                    now,
                    "timeout_no_arrival"
                )

                raise RuntimeError(
                    "30s elapsed without a confirmed arrival. "
                    "Remaining: " + str(distances)
                )

            velocities = {}

            for name in ROBOT_NAMES:
                error = self.heading_error(
                    name,
                    poses[name]
                )

                linear = linear_command(
                    distances[name],
                    elapsed,
                    self.planned_duration
                )

                linear *= max(0.0, math.cos(error))

                if abs(error) > math.radians(25.0):
                    linear = 0.0

                velocities[name] = (
                    linear,
                    clamp(
                        HEADING_GAIN * error,
                        MAX_ANGULAR_SPEED
                    )
                )

            self.send(velocities)

            if elapsed > FRAME_DELAY_SIM:
                self.emit_frames(
                    now - FRAME_DELAY_SIM
                )

            if self.recorder.error:
                raise RuntimeError(
                    self.recorder.error
                )

            wall_elapsed = (
                time.monotonic() - self.start_wall
            )

            if time.monotonic() - last_log >= 2.0:
                last_log = time.monotonic()

                rospy.loginfo(
                    "MOVE | sim=%.1fs | wall=%.1fs "
                    "| avg RTF=%.2f | %s",
                    elapsed,
                    wall_elapsed,
                    elapsed / max(wall_elapsed, 1e-6),
                    ", ".join(
                        "{}={:.2f}m".format(
                            name,
                            distances[name]
                        )
                        for name in ROBOT_NAMES
                    )
                )

            time.sleep(1.0 / CONTROL_HZ)

    def close(self):
        self.stop_all()

        if (
            self.start_sim is not None
            and self.end_sim is None
        ):
            self.end_sim = min(
                rospy.get_time(),
                self.start_sim + MAX_TRAVEL_SECONDS
            )

            self.end_wall = time.monotonic()

        for _ in range(5):
            self.stop_all()
            time.sleep(0.02)

        cleanup_error = None

        try:
            if self.recorder:
                try:
                    self.recorder.close()

                except Exception as exc:
                    cleanup_error = str(exc)

                metadata = {
                    "reason": self.reason,
                    "cleanup_error": cleanup_error,
                    "time_basis": "simulation",
                    "planned_duration": self.planned_duration,
                    "start_sim_time": self.start_sim,
                    "end_sim_time": self.end_sim,

                    "elapsed_sim": (
                        None
                        if self.start_sim is None
                        else self.end_sim - self.start_sim
                    ),

                    "elapsed_wall": (
                        None
                        if self.start_wall is None
                        else self.end_wall - self.start_wall
                    ),

                    "fps": VIDEO_FPS,
                    "size": VIDEO_SIZE,
                    "initial_poses": INITIAL_POSES,
                    "object_position": TARGET_POSITION,
                    "stop_distance_m": STOP_DISTANCE_M,
                    "stopping_goals": self.goals,
                    "velocity_topics": self.resolved_cmd,
                    "image_topics": self.resolved_image,
                    "output_files": OUTPUT_FILENAMES,
                    "frames": self.recorder.counts,
                    "repeated_source_frames": self.duplicates,
                }

                (self.folder / "session.json").write_text(
                    json.dumps(metadata, indent=2),
                    encoding="utf-8"
                )

                rospy.loginfo(
                    "Saved in %s | frames=%s",
                    self.folder,
                    self.recorder.counts
                )

        finally:
            for subscriber in self.subscribers:
                subscriber.unregister()

        if cleanup_error:
            raise RuntimeError(cleanup_error)


def main():
    rospy.init_node(
        "turtlebot_three_record",
        anonymous=False
    )

    cv2.setNumThreads(1)

    experiment = Experiment()
    result = 0

    try:
        experiment.run()

    except (
        KeyboardInterrupt,
        rospy.ROSInterruptException
    ):
        experiment.reason = "interrupted"

    except Exception as exc:
        if experiment.reason in (
            "running",
            "not_started"
        ):
            experiment.reason = "error:" + str(exc)

        rospy.logerr("%s", exc)
        result = 1

    finally:
        try:
            experiment.close()

        except Exception as exc:
            rospy.logerr(
                "Cleanup error: %s",
                exc
            )
            result = 1

    return result


if __name__ == "__main__":
    sys.exit(main())
