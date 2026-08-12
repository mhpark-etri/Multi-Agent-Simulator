#!/usr/bin/env python3
"""분산탐색-물건찾기: YOLO v8 물체 탐지·지도좌표 보고 노드 (2026-08-10).

로봇 3대의 RGB 카메라를 라운드로빈으로 추론(CPU, yolov8n)하고, 대상 클래스
(bottle, apple)가 잡히면 bbox 중심의 depth 로 3D 복원 → TF 로 map 좌표 변환
→ /found_objects(latched JSON)와 /object_markers(RViz)로 보고한다.
같은 클래스가 0.6m 이내면 동일 물체로 중복 제거.

단순화 명시: CPU 추론(~1Hz/로봇), 합성 SDF 물체라 신뢰도 문턱을 낮게(0.25) 잡음.
"""
import json
import time

import numpy as np
import rospy
import tf2_ros
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray


ROBOT_TOPICS = {
    'locobot_0': ('/locobot_0/camera/color/image_raw',
                  '/locobot_0/camera/aligned_depth_to_color/image_raw',
                  '/locobot_0/camera/color/camera_info'),
    'locobot_1': ('/locobot_1/camera/color/image_raw',
                  '/locobot_1/camera/aligned_depth_to_color/image_raw',
                  '/locobot_1/camera/color/camera_info'),
    'tb3_waffle_0': ('/tb3_waffle_0/camera/rgb/image_raw',
                     '/tb3_waffle_0/camera/depth/image_raw',
                     '/tb3_waffle_0/camera/rgb/camera_info'),
}


class YoloDetector:
    def __init__(self):
        from ultralytics import YOLO
        model_path = rospy.get_param('~model', '/root/yolov8n.pt')
        self.model = YOLO(model_path)
        # 클래스명 공백은 '_' 로 받는다 (rosparam/셸 인자 공백 함정)
        self.targets = {t.strip().replace('_', ' ') for t in rospy.get_param(
            '~targets', 'sports_ball,orange').split(',') if t.strip()}
        self.conf = float(rospy.get_param('~conf', 0.25))
        names = rospy.get_param('~robots', 'locobot_0,locobot_1,tb3_waffle_0')
        self.robots = [r.strip() for r in names.split(',')
                       if r.strip() in ROBOT_TOPICS]
        self.bridge = CvBridge()
        self.buf = tf2_ros.Buffer(rospy.Duration(10.0))
        self.lis = tf2_ros.TransformListener(self.buf)
        # ★ 콜백 상태는 '구독 시작 전에' 만들어 둔다 — 구독을 먼저 걸면 첫 이미지가
        #   도착했을 때 아직 없는 속성을 건드려 죽는다 (신규 컨테이너 실측:
        #   AttributeError: no attribute '_rgb', 2026-08-12)
        self._rgb, self._dep = {}, {}
        self.last = {}          # robot -> (rgb_msg, depth_msg)
        self.info = {}          # robot -> CameraInfo
        self.found = []         # [{cls, x, y, z, robot, conf, stamp}]
        self.fpub = rospy.Publisher('/found_objects', String,
                                    queue_size=2, latch=True)
        self.mpub = rospy.Publisher('/object_markers', MarkerArray,
                                    queue_size=2, latch=True)
        for r in self.robots:
            rgb, depth, cinfo = ROBOT_TOPICS[r]
            rospy.Subscriber(rgb, Image,
                             (lambda rr: lambda m: self._img_cb(rr, m))(r),
                             queue_size=1, buff_size=2 ** 22)
            rospy.Subscriber(depth, Image,
                             (lambda rr: lambda m: self._dep_cb(rr, m))(r),
                             queue_size=1, buff_size=2 ** 22)
            rospy.Subscriber(cinfo, CameraInfo,
                             (lambda rr: lambda m: self.info.__setitem__(rr, m))(r),
                             queue_size=1)
        rospy.loginfo('yolo_detector: robots=%s targets=%s (CPU)',
                      self.robots, sorted(self.targets))

    def _img_cb(self, r, m):
        self._rgb[r] = m

    def _dep_cb(self, r, m):
        self._dep[r] = m

    def _depth_at(self, r, u, v, half_w=2, half_h=2):
        # bbox 중앙부를 넓게 샘플링해 '최근접면'(하위 20% 백분위)을 취한다 —
        # 중심 픽셀이 물체를 살짝 벗어나면 배경 벽 depth 로 오위치화
        # (2026-08-10 실측: 공이 벽 밖 (5.3,-4.5)에 찍힘)
        m = self._dep.get(r)
        if m is None:
            return None
        try:
            d = self.bridge.imgmsg_to_cv2(m)
        except Exception:
            return None
        if not (0 <= v < d.shape[0] and 0 <= u < d.shape[1]):
            return None
        win = d[max(0, v - half_h):v + half_h + 1,
                max(0, u - half_w):u + half_w + 1].astype(np.float32)
        win = win[np.isfinite(win)]
        win = win[win > 0]
        if win.size == 0:
            return None
        val = float(np.percentile(win, 20))
        return val / 1000.0 if val > 50.0 else val   # 16UC1(mm) vs 32FC1(m)

    def spin(self):
        rate = rospy.Rate(3.0)
        idx = 0
        while not rospy.is_shutdown():
            rate.sleep()
            if not self.robots:
                continue
            r = self.robots[idx % len(self.robots)]
            idx += 1
            msg = self._rgb.get(r)
            ci = self.info.get(r)
            if msg is None or ci is None:
                continue
            try:
                img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            except Exception:
                continue
            try:
                res = self.model.predict(img, conf=self.conf, verbose=False)[0]
            except Exception as e:
                rospy.logwarn_throttle(30, 'yolo 추론 실패: %s', e)
                continue
            _shot = None    # 이번 프레임 주석 이미지 (발견 시 1회 렌더)
            for b in res.boxes:
                cls = self.model.names[int(b.cls[0])]
                if cls not in self.targets:
                    continue
                if _shot is None:
                    try:
                        _shot = res.plot()
                    except Exception:
                        _shot = img
                conf = float(b.conf[0])
                x1, y1, x2, y2 = [float(v) for v in b.xyxy[0]]
                u, v = int((x1 + x2) / 2), int((y1 + y2) / 2)
                d = self._depth_at(r, u, v,
                                   half_w=max(2, int((x2 - x1) * 0.2)),
                                   half_h=max(2, int((y2 - y1) * 0.2)))
                if d is None or not (0.2 < d < 8.0):
                    continue
                fx, fy = ci.K[0], ci.K[4]
                cx, cy = ci.K[2], ci.K[5]
                # 광학 프레임: X우 Y하 Z전방
                ox = (u - cx) / fx * d
                oy = (v - cy) / fy * d
                try:
                    from geometry_msgs.msg import PointStamped
                    ps = PointStamped()
                    ps.header.frame_id = msg.header.frame_id
                    ps.header.stamp = rospy.Time(0)
                    ps.point.x, ps.point.y, ps.point.z = ox, oy, d
                    import tf2_geometry_msgs
                    mp = self.buf.transform(ps, 'map', rospy.Duration(0.5))
                except Exception as e:
                    rospy.logwarn_throttle(
                        20, 'yolo TF 변환 실패(%s): %s', msg.header.frame_id, e)
                    continue
                self._report(cls, mp.point.x, mp.point.y, mp.point.z, r,
                             conf, _shot)

    SNAP_DIR = '/root/tesla/ros/navi/found_objects'

    def _save_shot(self, shot, cls, robot):
        try:
            import cv2, os
            os.makedirs(self.SNAP_DIR, exist_ok=True)
            path = '%s/%s_%s_%d.jpg' % (self.SNAP_DIR, cls.replace(' ', '_'),
                                        robot, len(self.found))
            cv2.imwrite(path, shot)
            return path
        except Exception as e:
            rospy.logwarn('스냅샷 저장 실패: %s', e)
            return ''

    def _report(self, cls, x, y, z, robot, conf, shot=None):
        for f in self.found:
            if (f['cls'] == cls
                    and (f['x'] - x) ** 2 + (f['y'] - y) ** 2 < 0.6 ** 2):
                if conf > f['conf']:
                    f.update(x=x, y=y, z=z, conf=conf, robot=robot)
                    if shot is not None:            # 더 좋은 프레임으로 갱신
                        f['img'] = self._save_shot(shot, cls, robot) or f.get('img', '')
                    self._publish()
                return
        self.found.append({'cls': cls, 'x': round(x, 2), 'y': round(y, 2),
                           'z': round(z, 2), 'robot': robot,
                           'conf': round(conf, 2),
                           'img': (self._save_shot(shot, cls, robot)
                                   if shot is not None else ''),
                           'stamp': round(rospy.get_time(), 1)})
        print(f"[물건찾기] {robot} 발견: {cls} ({x:.2f},{y:.2f}) conf={conf:.2f}",
              flush=True)
        # 발견 '즉시' YOLO 결과(박스+conf) 팝업 (2026-08-10 지시)
        try:
            import subprocess
            img_p = self.found[-1].get('img')
            if img_p:
                subprocess.Popen(
                    ['python3', '/root/tesla/ros/navi/scripts/found_popup.py',
                     img_p, f"{cls} ({robot}, conf {conf:.2f})"])
        except Exception as e:
            rospy.logwarn('발견 팝업 실패: %s', e)
        self._publish()

    def _publish(self):
        self.fpub.publish(json.dumps(self.found, ensure_ascii=False))
        arr = MarkerArray()
        # 지도 바깥(상단) 노란색 발견 배너 (2026-08-10 지시) — bnt 지도 y최대
        # ~3.4 위인 y=4.2 에 큰 글씨로 발견 목록 표시
        if self.found:
            bn = Marker()
            bn.header.frame_id = 'map'
            bn.header.stamp = rospy.Time.now()
            bn.ns = 'found_banner'
            bn.id = 999
            bn.type = Marker.TEXT_VIEW_FACING
            bn.action = Marker.ADD
            bn.pose.position.x = 0.0
            bn.pose.position.y = 4.3
            bn.pose.position.z = 0.3
            bn.scale.z = 0.5
            bn.color.r, bn.color.g, bn.color.b, bn.color.a = 1.0, 0.85, 0.0, 1.0
            bn.text = 'Found Objects\n' + '\n'.join(
                f"{i+1}: {f['cls']} ({f['robot']})"
                for i, f in enumerate(self.found))
            bn.pose.position.y = 4.3 + 0.3 * len(self.found)
            arr.markers.append(bn)
        for i, f in enumerate(self.found):
            m = Marker()
            m.header.frame_id = 'map'
            m.header.stamp = rospy.Time.now()
            m.ns = 'objects'
            m.id = i
            m.type = Marker.SPHERE
            m.action = Marker.ADD
            m.pose.position.x, m.pose.position.y = f['x'], f['y']
            # 지도/검은 영역 위에서도 보이게 공중 부양 (2026-08-10 지시)
            m.pose.position.z = max(1.1, f['z'] + 0.3)
            m.pose.orientation.w = 1.0
            m.scale.x = m.scale.y = m.scale.z = 0.5
            if f['cls'] == 'apple':
                m.color.r, m.color.g, m.color.b, m.color.a = 0.9, 0.1, 0.1, 0.9
            else:
                m.color.r, m.color.g, m.color.b, m.color.a = 0.1, 0.4, 0.9, 0.9
            arr.markers.append(m)
            t = Marker()
            t.header.frame_id = 'map'
            t.header.stamp = rospy.Time.now()
            t.ns = 'object_labels'
            t.id = 100 + i
            t.type = Marker.TEXT_VIEW_FACING
            t.action = Marker.ADD
            t.pose.position.x, t.pose.position.y = f['x'], f['y']
            t.pose.position.z = max(1.1, f['z'] + 0.3) + 0.55
            t.scale.z = 0.4
            # 붉은 글씨 + 2줄 — 지도 위 가독성 (2026-08-10 지시)
            t.color.r, t.color.g, t.color.b = 0.85, 0.08, 0.08
            t.color.a = 1.0
            t.text = f"{f['cls']}\n({f['robot']})"
            arr.markers.append(t)
        self.mpub.publish(arr)


if __name__ == '__main__':
    rospy.init_node('yolo_detector')
    YoloDetector().spin()
