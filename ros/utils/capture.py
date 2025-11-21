#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, threading, cv2, rospy
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge, CvBridgeError
import numpy as np

class CameraCapture:
    def __init__(self):
        self.bridge = CvBridge()
        self.lock = threading.Lock()
        self.latest_image = None
        self.count = 0

        # ./capture 폴더 생성
        self.save_dir = os.path.join(os.getcwd(), "capture")
        os.makedirs(self.save_dir, exist_ok=True)

        # 기본 토픽: Waffle Pi의 카메라 (raw or compressed 자동 대응)
        self.image_topic = "/tb3_waffle_pi_0/camera/rgb/image_raw"

        # raw/compressed 자동 구독
        self.sub = None
        self._subscribe_with_fallback(self.image_topic)

        # 2초마다 저장 타이머
        self.timer = rospy.Timer(rospy.Duration(2.0), self._save_image)
        rospy.loginfo(f"📸 Capturing every 2s → {self.save_dir}")

    def _subscribe_with_fallback(self, base_topic):
        # 1️⃣ raw 시도
        try:
            rospy.loginfo(f"Trying raw topic: {base_topic}")
            self.sub = rospy.Subscriber(base_topic, Image, self._cb_raw, queue_size=1)
            rospy.wait_for_message(base_topic, Image, timeout=2.0)
            rospy.loginfo(f"✅ Subscribed raw topic: {base_topic}")
            return
        except Exception:
            if self.sub: self.sub.unregister()

        # 2️⃣ compressed 시도
        comp_topic = base_topic.rstrip("/") + "/compressed"
        rospy.loginfo(f"Trying compressed topic: {comp_topic}")
        try:
            self.sub = rospy.Subscriber(comp_topic, CompressedImage, self._cb_compressed, queue_size=1)
            rospy.wait_for_message(comp_topic, CompressedImage, timeout=2.0)
            rospy.loginfo(f"✅ Subscribed compressed topic: {comp_topic}")
        except Exception:
            rospy.logwarn("❌ No image message received. Check topic name.")

    def _cb_raw(self, msg):
        try:
            img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            with self.lock:
                self.latest_image = img
        except CvBridgeError as e:
            rospy.logerr(f"CV Bridge error: {e}")

    def _cb_compressed(self, msg):
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            with self.lock:
                self.latest_image = img
        except Exception as e:
            rospy.logerr(f"Decode error: {e}")

    def _save_image(self, _):
        with self.lock:
            img = self.latest_image.copy() if self.latest_image is not None else None
        if img is None:
            rospy.logwarn_throttle(5.0, "No image received yet...")
            return

        filename = os.path.join(self.save_dir, f"capture_{self.count}.jpg")
        cv2.imwrite(filename, img)
        rospy.loginfo(f"💾 Saved {filename}")
        self.count += 1

    def shutdown(self):
        if self.sub: self.sub.unregister()
        self.timer.shutdown()
        rospy.loginfo("Shutting down camera capture.")

if __name__ == "__main__":
    rospy.init_node("tb3_waffle_pi_0_camera_capture", anonymous=True)
    node = CameraCapture()
    rospy.on_shutdown(node.shutdown)
    rospy.spin()

