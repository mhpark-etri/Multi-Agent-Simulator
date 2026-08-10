#!/usr/bin/env python3
"""그룹 위치공유 → 상호 costmap 장애물 주입 노드 (협업 태스크 전용).

배경(2026-08-08 실측): locobot 라이다 스캔 평면은 바닥 0.657m — tb3 burger
전고 0.192m 가 절대 안 잡혀 locobot 이 burger 를 밀어붙인다. 그룹 멤버들이
서로 위치를 교환해 각 로봇의 local costmap 에 "상대 로봇 원통 점군"을 넣는다.

동작:
  - 5Hz 로 모든 로봇의 map→<r>/base_footprint TF 를 조회
  - 로봇 R 마다 자기를 제외한 나머지를 원통 점군(링 12점+중심, z 2층)으로
    /<r>/mutual_obstacles (PointCloud2, frame=map) 에 발행
  - R 중심 self_guard(0.30m) 이내 점은 드롭 — 밀착 시 자기 footprint 안
    마킹으로 DWA 가 회전 리커버리 루프에 빠지는 것 방지
  - 빈 점군도 매주기 발행 (버퍼 신선도 유지)
  - /mutual_obstacles/set_group ("그룹이름:이름,이름") 수신 시 그룹 구성 표시
    ※ 단순화 명시: 위치 취득은 sim TF 직접 조회이며, 장애물 주입은 안전상
    그룹 경계와 무관하게 전체 로봇 상호 적용이 기본(~group_only 로 제한 가능).
    JnP 그룹 메시지는 "멤버 간 위치 교환" 시맨틱 표시/제한용이다.

costmap 연결은 locobot_turtle_nav_sim2.launch 의 mutual_obstacles:=true 게이트
(peers 소스, marking true / clearing false / obstacle_range 100) — baseline 불변.
"""
import math
import rospy
import tf2_ros
from std_msgs.msg import Header, String
from sensor_msgs.msg import PointCloud2
from sensor_msgs import point_cloud2


def robot_radius(short):
    if 'locobot' in short:
        return 0.28
    if 'tb3' in short or 'burger' in short:
        return 0.16
    return 0.25


class MutualObstacles:
    def __init__(self):
        names = rospy.get_param('~robots',
                                'locobot_0,locobot_1,tb3_burger_0,tb3_burger_1')
        self.robots = [r.strip() for r in names.split(',') if r.strip()]
        self.frame = rospy.get_param('~frame', 'map')
        self.rate = float(rospy.get_param('~rate', 5.0))
        self.self_guard = float(rospy.get_param('~self_guard', 0.30))
        self.z_levels = (0.05, 0.15)
        # 기본: 전체 상호 공유 (그룹 간 충돌도 실재 — 베이스 공용). true 면
        # 같은 그룹 멤버끼리만 공유(set_group 수신 전에는 아무도 안 공유).
        self.group_only = bool(rospy.get_param('~group_only', False))
        self.groups = {}          # 그룹이름 → set(멤버)
        self.tf_buf = tf2_ros.Buffer(rospy.Duration(10.0))
        self.tf_lis = tf2_ros.TransformListener(self.tf_buf)
        self.pubs = {r: rospy.Publisher('/%s/mutual_obstacles' % r,
                                        PointCloud2, queue_size=1)
                     for r in self.robots}
        rospy.Subscriber('/mutual_obstacles/set_group', String,
                         self._group_cb, queue_size=4)
        self.warned = set()
        # 우선권(눈치싸움 해소): 둘 다 '이동 중'이고 2.2m 이내로 마주치면
        # 이름 순 우선(정렬 앞) 로봇은 상대를 장애물로 보지 않고 진행, 뒤 로봇만
        # 양보한다. 정지한 로봇은 누구에게나 항상 보임(안전 — 대기열 보호).
        self.prio = {r: i for i, r in enumerate(sorted(self.robots))}
        self.hist = {r: [] for r in self.robots}    # (t, x, y) 최근 1.2초
        rospy.Timer(rospy.Duration(1.0 / max(self.rate, 0.5)), self._tick)
        rospy.loginfo('mutual_obstacles: robots=%s frame=%s group_only=%s',
                      self.robots, self.frame, self.group_only)

    def _group_cb(self, msg):
        try:
            gname, names = msg.data.split(':', 1)
            members = {n.strip() for n in names.split(',') if n.strip()}
            self.groups[gname.strip()] = members
            rospy.loginfo('mutual_obstacles: 그룹 위치공유 %s = %s',
                          gname.strip(), sorted(members))
        except ValueError:
            rospy.logwarn('set_group 형식 오류: %s', msg.data)

    def _peers_of(self, r):
        if not self.group_only:
            return [m for m in self.robots if m != r]
        peers = set()
        for members in self.groups.values():
            if r in members:
                peers |= members
        peers.discard(r)
        return sorted(peers)

    def _tick(self, _ev):
        pos = {}
        for r in self.robots:
            try:
                t = self.tf_buf.lookup_transform(
                    self.frame, '%s/base_footprint' % r, rospy.Time(0),
                    rospy.Duration(0.2))
                pos[r] = (t.transform.translation.x, t.transform.translation.y)
            except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                    tf2_ros.ExtrapolationException) as e:
                if r not in self.warned:
                    self.warned.add(r)
                    rospy.logwarn('mutual_obstacles: %s TF 없음 (%s) — 뜰 때까지 스킵',
                                  r, type(e).__name__)
        now = rospy.Time.now().to_sec()
        moving = {}
        for r, p_ in pos.items():
            h = self.hist[r]
            h.append((now, p_[0], p_[1]))
            self.hist[r] = h = [e for e in h if now - e[0] <= 1.2]
            moving[r] = math.hypot(p_[0] - h[0][1], p_[1] - h[0][2]) > 0.06
        header = Header()
        header.frame_id = self.frame
        header.stamp = rospy.Time.now()
        for r in self.robots:
            pts = []
            rx, ry = pos.get(r, (None, None))
            for m in self._peers_of(r):
                if m not in pos:
                    continue
                mx, my = pos[m]
                if (rx is not None and moving.get(r) and moving.get(m)
                        and math.hypot(mx - rx, my - ry) < 2.2
                        and self.prio[r] < self.prio[m]):
                    rospy.loginfo_throttle(
                        5.0, '우선권: %s 가 %s 앞 통과 (%s 양보)', r, m, m)
                    continue        # 우선 로봇은 상대를 지우고 진행 — 상대만 양보
                rad = robot_radius(m)
                for z in self.z_levels:
                    for k in range(12):
                        a = k * math.pi / 6.0
                        px = mx + rad * math.cos(a)
                        py = my + rad * math.sin(a)
                        if rx is not None and math.hypot(px - rx, py - ry) < self.self_guard:
                            continue    # 수신 로봇 footprint 안 마킹 방지
                        pts.append((px, py, z))
                    if rx is None or math.hypot(mx - rx, my - ry) >= self.self_guard:
                        pts.append((mx, my, z))
            self.pubs[r].publish(point_cloud2.create_cloud_xyz32(header, pts))


if __name__ == '__main__':
    rospy.init_node('mutual_obstacles')
    MutualObstacles()
    rospy.spin()
