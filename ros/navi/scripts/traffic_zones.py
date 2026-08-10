#!/usr/bin/env python3
"""존-토큰 교통관제 노드 (협업 태스크 전용) — 2026-08-08 지시.

배경: move_base 는 단일 로봇 플래너라 좁은 구역(베이스 원, goal 주변)에 여러 대가
몰리면 개별 계획이 서로 막힌다. 충돌·대치가 실제 발생하는 구역을 '존'으로 정의하고
존마다 동시 이동 1대 토큰을 발급해 그 구역의 '이동'을 직렬화한다 (정지 로봇은
토큰 불요 — 이동하려는 로봇만 획득).

존 정의 (자동):
  - base: /task_base(latched) 중심, 반경 ~base_radius (기본 2.2m)
  - <G이름>: /goal_items 의 각 goal 중심, 반경 ~goal_radius (기본 2.2m)

프로토콜 (에이전트/legacy runner 공통):
  - 존 안으로 들어가는(또는 존 안에서 시작하는) 주행 다리를 시작하기 전
    /zone_<이름>/acquire (std_srvs/Trigger) — success=false 면 2초 폴링 대기
  - 다리 완료(도착·정지) 또는 존 이탈 후 /zone_<이름>/release
  - 클라이언트는 토큰을 한 번에 하나만 보유 (존 간 이동은 경계 밖 중간점을
    거쳐 반납→획득 교대) — 교착 없음
  - 보유 시간초과(~hold_timeout, 기본 240 sim초) 시 자동 반납 (보유자 사망 대비)

노드가 없으면 클라이언트는 무-관제로 진행한다 (baseline 불변).
"""
import json
import threading
import rospy
from std_msgs.msg import String
from std_srvs.srv import Trigger, TriggerResponse
from geometry_msgs.msg import PoseStamped


class TrafficZones:
    def __init__(self):
        self.base_r = float(rospy.get_param('~base_radius', 2.2))
        self.goal_r = float(rospy.get_param('~goal_radius', 2.2))
        # 정상 최악 보유(스케줄러 trip 허용 600 sim초)보다 커야 산 보유자를
        # 강제 반납하지 않는다 (리뷰 결함 #2, 2026-08-08)
        self.hold_timeout = float(rospy.get_param('~hold_timeout', 900.0))
        self.lock = threading.Lock()
        self.zones = {}      # 이름 → {'x','y','r','busy'(bool),'since'(sim s)}
        self.srvs = {}       # 이름 → (acquire srv, release srv)
        self.pub = rospy.Publisher('/traffic_zones/status', String,
                                   queue_size=2, latch=True)
        rospy.Subscriber('/task_base', PoseStamped, self._base_cb, queue_size=2)
        rospy.Subscriber('/goal_items', String, self._items_cb, queue_size=8)
        rospy.loginfo('traffic_zones: base_r=%.1f goal_r=%.1f timeout=%.0fs',
                      self.base_r, self.goal_r, self.hold_timeout)

    def _ensure_zone(self, name, x, y, r):
        with self.lock:
            z = self.zones.get(name)
            if z is None:
                self.zones[name] = {'x': x, 'y': y, 'r': r,
                                    'busy': False, 'since': 0.0, 'owner': ''}
                self.srvs[name] = (
                    rospy.Service('/zone_%s/acquire' % name, Trigger,
                                  self._mk_acquire(name)),
                    rospy.Service('/zone_%s/release' % name, Trigger,
                                  self._mk_release(name)))
                rospy.loginfo('traffic_zones: 존 등록 %s (%.2f,%.2f r=%.1f)',
                              name, x, y, r)
            else:
                z['x'], z['y'], z['r'] = x, y, r   # goal 위치 갱신 허용
        self._publish()

    @staticmethod
    def _caller(req):
        """요청 노드 식별 (rospy connection header) — 소유자 검증용."""
        try:
            return req._connection_header.get('callerid', '')
        except AttributeError:
            return ''

    def _mk_acquire(self, name):
        def h(req):
            who = self._caller(req)
            with self.lock:
                z = self.zones[name]
                now = rospy.get_time()
                if z['busy'] and now - z['since'] > self.hold_timeout:
                    rospy.logwarn('zone %s: %s 보유 시간초과 — 자동 반납',
                                  name, z.get('owner', ''))
                    z['busy'] = False
                if z['busy']:
                    return TriggerResponse(success=False, message='busy')
                z['busy'] = True
                z['since'] = now
                z['owner'] = who
            self._publish()
            return TriggerResponse(success=True, message=name)
        return h

    def _mk_release(self, name):
        def h(req):
            who = self._caller(req)
            with self.lock:
                z = self.zones[name]
                # 소유자 검증 (리뷰 결함 #1/#6/#12): 획득자만 반납 가능 —
                # 시간초과 재배정 후 옛 보유자의 늦은 release 가 새 토큰을
                # 지우는 연쇄를 차단. owner 미기록('')이면 하위호환 허용.
                if z['busy'] and z.get('owner') and who and z['owner'] != who:
                    rospy.logwarn_throttle(
                        10.0, 'zone %s: 비소유자(%s) release 무시 (보유 %s)',
                        name, who, z['owner'])
                    return TriggerResponse(success=False, message='not-owner')
                z['busy'] = False
                z['owner'] = ''
            self._publish()
            return TriggerResponse(success=True, message=name)
        return h

    def _base_cb(self, msg):
        self._ensure_zone('base', msg.pose.position.x, msg.pose.position.y,
                          self.base_r)

    def _items_cb(self, msg):
        try:
            g, _left, xy = msg.data.split(':', 2)
            x, y = [float(v) for v in xy.split(',')[:2]]
            self._ensure_zone(g.strip(), x, y, self.goal_r)
        except (ValueError, IndexError):
            pass

    def _publish(self):
        with self.lock:
            st = {n: {'x': z['x'], 'y': z['y'], 'r': z['r'], 'busy': z['busy'],
                      'owner': z.get('owner', '')}
                  for n, z in self.zones.items()}
        self.pub.publish(json.dumps(st))


if __name__ == '__main__':
    rospy.init_node('traffic_zones')
    TrafficZones()
    rospy.spin()
