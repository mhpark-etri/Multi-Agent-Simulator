#!/usr/bin/env python3
"""병합 지도에서 '자기 자신이 벽으로 박제'된 셀을 지우는 nav 전용 지도 셔임.

정지한 로봇은 동료 SLAM 에 장애물로 기록되어 merged /map 에 벽이 된다. 전역
costmap 이 병합 지도를 쓰는 탐사 모드(explore_nav)에서 로봇 '자신의 위치'가
lethal 이 되어 어떤 goal 로도 계획 불능 (2026-08-09 실측: 시작 셀 코스트 100).
로봇별로 자기 footprint 원반만 free 로 되돌린 /map_nav/<robot> 을 발행한다.

2026-08-11 추가 — '주차된 동료' 전역 회피:
  위치공유(mutual_obstacles)는 **로컬 코스트맵(4m 창)에만** 주입돼서, 전역
  플래너는 세워둔 동료를 관통하는 경로를 그린다. 2m 안에 들어와서야 상대를
  보고, 좁은 통로면 우회로가 없어 밀어붙이다 충돌한다(locobot_1↔waffle 실측).
  → 일정 시간 이상 정지한 동료의 자리를 이 지도에 lethal 로 칠해 전역 경로가
  처음부터 우회하게 한다. 매 주기 병합 지도로 새로 그리므로 얼룩이 남지 않는다
  (전역 obstacle layer 에 peers 를 직접 넣으면 지나간 자리마다 지워지지 않는
  마킹이 쌓인다 — 그래서 그 방법은 쓰지 않는다).
"""
import rospy
import tf2_ros
from nav_msgs.msg import OccupancyGrid


class MapNavClear:
    def __init__(self):
        names = rospy.get_param('~robots', 'locobot_0,locobot_1')
        self.robots = [r.strip() for r in names.split(',') if r.strip()]
        self.r = float(rospy.get_param('~clear_radius', 0.40))
        # 주차 동료 마킹
        self.peer_r = float(rospy.get_param('~peer_radius', 0.30))
        self.park_secs = float(rospy.get_param('~park_secs', 8.0))
        self.park_move = float(rospy.get_param('~park_move', 0.15))
        self.mark_peers = bool(rospy.get_param('~mark_parked_peers', True))
        self.hist = {}          # robot -> [(t, x, y), ...] 최근 이력
        self.buf = tf2_ros.Buffer(rospy.Duration(10.0))
        self.lis = tf2_ros.TransformListener(self.buf)
        self.pubs = {r: rospy.Publisher('/map_nav/%s' % r, OccupancyGrid,
                                        queue_size=1, latch=True)
                     for r in self.robots}
        rospy.Subscriber('/map', OccupancyGrid, self.cb, queue_size=1)
        rospy.loginfo('map_nav_clear: robots=%s r=%.2f 주차동료마킹=%s(%.0fs)',
                      self.robots, self.r, self.mark_peers, self.park_secs)

    # ---------- 위치/정지 판정 ----------
    def _poses(self, frame):
        """로봇별 map 좌표 (실패하면 없음)."""
        out = {}
        for rb in self.robots:
            try:
                t = self.buf.lookup_transform(
                    frame, '%s/base_footprint' % rb, rospy.Time(0),
                    rospy.Duration(0.2))
                out[rb] = (t.transform.translation.x, t.transform.translation.y)
            except Exception:
                pass
        return out

    def _update_hist(self, poses):
        now = rospy.get_time()
        for rb, p in poses.items():
            h = self.hist.setdefault(rb, [])
            h.append((now, p[0], p[1]))
            # 판정 창의 2배까지만 보관
            self.hist[rb] = [e for e in h if now - e[0] <= self.park_secs * 2]

    def _parked(self, rb):
        """park_secs 동안 park_move 이하로 움직였으면 '주차'."""
        now = rospy.get_time()
        h = [e for e in self.hist.get(rb, []) if now - e[0] <= self.park_secs]
        if len(h) < 3 or (now - h[0][0]) < self.park_secs * 0.8:
            return False        # 이력이 짧으면 판정 보류 (기동 직후 오탐 방지)
        dx = max(e[1] for e in h) - min(e[1] for e in h)
        dy = max(e[2] for e in h) - min(e[2] for e in h)
        return (dx * dx + dy * dy) ** 0.5 <= self.park_move

    # ---------- 원반 칠하기 ----------
    @staticmethod
    def _disc(data, info, cx_m, cy_m, radius, value):
        res = info.resolution
        W, H = info.width, info.height
        cx = int((cx_m - info.origin.position.x) / res)
        cy = int((cy_m - info.origin.position.y) / res)
        n = max(1, int(radius / res))
        for dy in range(-n, n + 1):
            for dx in range(-n, n + 1):
                if dx * dx + dy * dy <= n * n:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < W and 0 <= y < H:
                        data[y * W + x] = value

    def cb(self, m):
        frame = m.header.frame_id or 'map'
        poses = self._poses(frame)
        self._update_hist(poses)
        parked = {rb for rb in poses if self.mark_peers and self._parked(rb)}
        for rb in self.robots:
            if rb not in poses:
                self.pubs[rb].publish(m)     # TF 없으면 원본 그대로
                continue
            data = list(m.data)
            # ① 주차된 '동료'를 장애물로 (전역 경로가 우회하도록)
            for pr in parked:
                if pr == rb:
                    continue
                self._disc(data, m.info, poses[pr][0], poses[pr][1],
                           self.peer_r, 100)
            # ② 자기 자리는 항상 free (①보다 뒤 — 겹쳐도 자기 발밑은 열어둔다)
            self._disc(data, m.info, poses[rb][0], poses[rb][1], self.r, 0)
            o = OccupancyGrid()
            o.header = m.header
            o.info = m.info
            o.data = data
            self.pubs[rb].publish(o)


if __name__ == '__main__':
    rospy.init_node('map_nav_clear')
    MapNavClear()
    rospy.spin()
