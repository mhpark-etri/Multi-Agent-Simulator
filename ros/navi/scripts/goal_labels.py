#!/usr/bin/env python3
"""relay goal 표시기: 각 로봇의 move_base current_goal 에 대해
 - RViz(/relay_goal_labels MarkerArray):
     사각형(goal 위치) + 작은 화살표(goal 방향) + 로봇 이름 텍스트
 - Gazebo: 바닥에 로봇 색 사각판 모델을 스폰/이동해 goal 위치를 직접 표시
   (~gazebo_markers 파라미터, 기본 true)

shelltemp_task.sh 에서 roslaunch 직전에 백그라운드로 실행된다.
로봇 목록은 ~robots (기본: locobot_0,locobot_1,tb3_burger_0,tb3_burger_1).
"""
import time
import threading
import rospy
from geometry_msgs.msg import PoseStamped
import json
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray

# 경로 색과 맞춘 로봇별 색 (r, g, b)
COLORS = {
    'locobot_0': (0.0, 0.8, 0.0),
    'locobot_1': (0.0, 0.5, 1.0),
    'tb3_burger_0': (1.0, 0.6, 0.0),
    'tb3_burger_1': (1.0, 0.25, 0.25),
}
DEFAULT_COLOR = (1.0, 1.0, 1.0)
# 다목적 이동 goal 지점 색 (사각 판 + 물품 상자)
GOAL_COLORS = {'G1': (0.1, 0.9, 0.9), 'G2': (0.95, 0.4, 0.95),
               'G3': (0.9, 0.9, 0.2), 'G4': (0.5, 0.9, 0.3)}

# 남은 물품 수 (Gazebo) — 텍스트 렌더 불가라 7-세그먼트 숫자를 박스로 조립
SEG_POS = {   # (u,v,가로여부) — 숫자 높이 0.42m, 폭 0.24m
    'A': (0.0, 0.21, True), 'B': (0.12, 0.105, False), 'C': (0.12, -0.105, False),
    'D': (0.0, -0.21, True), 'E': (-0.12, -0.105, False), 'F': (-0.12, 0.105, False),
    'G': (0.0, 0.0, True)}
DIGIT_SEGS = {'0': 'ABCDEF', '1': 'BC', '2': 'ABGED', '3': 'ABGCD', '4': 'FGBC',
              '5': 'AFGCD', '6': 'AFGECD', '7': 'ABC', '8': 'ABCDEFG', '9': 'ABFGCD'}

def build_count_sdf(name, number):
    """검정 7-세그 숫자(바닥 평면)에 대한 멀티-visual 정적 모델 SDF."""
    vis = []
    text = str(max(0, int(number)))
    x0 = -0.17 * (len(text) - 1)          # 여러 자리면 가운데 정렬
    for i, ch in enumerate(text):
        for seg in DIGIT_SEGS.get(ch, ''):
            u, v, horiz = SEG_POS[seg]
            sx, sy = (0.24, 0.055) if horiz else (0.055, 0.19)
            vis.append(
                '<visual name="s%d%s"><pose>%.3f %.3f 0 0 0 0</pose>'
                '<geometry><box><size>%.3f %.3f 0.04</size></box></geometry>'
                '<material><ambient>0.05 0.05 0.05 1</ambient>'
                '<diffuse>0.05 0.05 0.05 1</diffuse></material></visual>'
                % (i, seg, x0 + i * 0.34 + u, v, sx, sy))
    return ('<?xml version="1.0"?><sdf version="1.6"><model name="%s">'
            '<static>true</static><link name="link">%s</link></model></sdf>'
            % (name, ''.join(vis)))

# Gazebo goal 판 모델 (visual 전용 — collision 없음, static)
# 두께 0.1m — 얇으면 바닥과 z-fighting 으로 안 보인다(2026-08-08 실측). 발광 최대.
# BASE(출발영역)용 큰 원판 (반경 1.3m)
SDF_BASE_TEMPLATE = """<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <static>true</static>
    <link name="link">
      <visual name="visual">
        <geometry><cylinder><radius>1.6</radius><length>0.04</length></cylinder></geometry>
        <material>
          <ambient>{cr} {cg} {cb} 1</ambient>
          <diffuse>{cr} {cg} {cb} 1</diffuse>
          <emissive>{er} {eg} {eb} 1</emissive>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""

SDF_TEMPLATE = """<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <static>true</static>
    <link name="link">
      <visual name="visual">
        <geometry><cylinder><radius>0.2</radius><length>0.1</length></cylinder></geometry>
        <material>
          <ambient>{r} {g} {b} 1</ambient>
          <diffuse>{r} {g} {b} 1</diffuse>
          <emissive>{re} {ge} {be} 1</emissive>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""


class GoalMarkers:
    def __init__(self):
        self.robots = [r.strip() for r in rospy.get_param(
            '~robots', 'locobot_0,locobot_1,tb3_burger_0,tb3_burger_1').split(',')
            if r.strip()]
        self.use_gazebo = bool(rospy.get_param('~gazebo_markers', True))
        self.pub = rospy.Publisher('/relay_goal_labels', MarkerArray,
                                   queue_size=1, latch=True)
        self.goals = {}
        self.spawned = set()
        self.active = None      # 마지막으로 goal 을 받은 로봇 = 현재 릴레이 다리
        self.is_relay = False   # RELAY 배너는 relay 계획을 실제로 받았을 때만
        for name in self.robots:
            rospy.Subscriber('/%s/move_base/current_goal' % name, PoseStamped,
                             self._make_cb(name), queue_size=2)
            # 계획 발행(taskRelay 가 시작 시 체인 전체를 latch) — 목표를 미리 표시
            rospy.Subscriber('/relay_plan/%s' % name, PoseStamped,
                             self._make_cb(name, plan=True), queue_size=2)
        # (relay 표식은 _make_cb 의 plan 경로에서 self.is_relay=True 로 설정)
        # 베이스(공동 출발지) 표시 — 다목적 이동 등에서 /task_base 로 latch 발행됨
        self.base = None
        rospy.Subscriber('/task_base', PoseStamped, self._base_cb, queue_size=1)
        # goal 별 남은 물품 수 — 'G1:2:x,y' 형식 (/goal_items)
        self.items = {}
        rospy.Subscriber('/goal_items', String, self._items_cb, queue_size=4)
        # 충돌회피: 병목 상태 (/bottleneck/status latched JSON — 그룹이 발행)
        self.bt = None
        rospy.Subscriber('/bottleneck/status', String, self._bt_cb, queue_size=2)
        # 동적 충돌 coalition 우선순위 표시 (/conflict_display: {'group','ranks'})
        self.conflicts = {}      # group키 → {'ranks':{로봇:순위}, 't':수신시각}
        self.rpos = {}           # 로봇 → (x,y)  (우선순위 숫자를 로봇 위에 띄우기 위함)
        from nav_msgs.msg import Odometry
        for _r in self.robots:
            rospy.Subscriber('/%s/odom' % _r, Odometry,
                             (lambda rr: lambda m: self.rpos.__setitem__(
                                 rr, (m.pose.pose.position.x,
                                      m.pose.pose.position.y)))(_r))
        # 배경 적응 글자색: 지도(밝음) 위=검정, 지도 밖(어두운 뷰포트)=흰색
        # (2026-08-10 지시). /map latched 로 지도 범위만 저장.
        from nav_msgs.msg import OccupancyGrid as _OG
        self.map_ext = None
        def _map_cb(m):
            self.map_ext = (m.info.origin.position.x, m.info.origin.position.y,
                            m.info.width * m.info.resolution,
                            m.info.height * m.info.resolution)
        rospy.Subscriber('/map', _OG, _map_cb, queue_size=1)
        rospy.Subscriber('/conflict_display', String, self._conflict_cb,
                         queue_size=6)
        threading.Thread(target=self._conflict_loop, daemon=True).start()

        # RTF 측정 — 벽시계 5초마다 1회 (sim 시간 Δ / 벽시계 Δ). 성능 부담 없음.
        # rospy.Timer 는 use_sim_time 에선 sim 초 단위라 벽시계 주기가 아님 → 스레드 사용
        self.rtf_text = ''
        threading.Thread(target=self._rtf_loop, daemon=True).start()

    def _txt_rgb(self, x, y):
        e = self.map_ext
        if e and e[0] <= x <= e[0] + e[2] and e[1] <= y <= e[1] + e[3]:
            return (0.05, 0.05, 0.05)
        return (1.0, 1.0, 1.0)

    def _rtf_loop(self):
        last_w, last_s = time.time(), rospy.get_time()
        while not rospy.is_shutdown():
            time.sleep(5.0)
            w, s = time.time(), rospy.get_time()
            dw, ds = w - last_w, s - last_s
            last_w, last_s = w, s
            if dw > 0:
                self.rtf_text = 'RTF %.2f' % (ds / dw) if ds > 0 else 'RTF -- (paused)'
                self.publish_markers()

    def _make_cb(self, name, plan=False):
        def cb(msg):
            if plan:
                self.is_relay = True    # 진짜 relay 계획을 받은 경우만 배너 허용
            self.goals[name] = msg
            if not plan:
                self.active = name      # 실제 주행 goal = 이 로봇이 지금 이동하는 다리
            self.publish_markers()
            if self.use_gazebo:
                self.update_gazebo(name, msg)
        return cb

    def _base_cb(self, msg):
        self.base = msg
        self.publish_markers()
        if self.use_gazebo:
            self.update_gazebo('base', msg)     # 흰색 판 (goal_marker_base)

    def _bt_cb(self, msg):
        try:
            d = json.loads(msg.data)
            self.bt = d
            self.publish_markers()
            if self.use_gazebo and not getattr(self, '_bt_spawned', False):
                ps = PoseStamped()
                ps.header.frame_id = 'map'
                ps.pose.position.x = float(d['center'][0])
                ps.pose.position.y = float(d['center'][1])
                ps.pose.orientation.w = 1.0
                self.update_gazebo('bottleneck', ps)   # 붉은 원판 (base 템플릿 재사용)
                self._bt_spawned = True
        except (ValueError, KeyError, TypeError):
            pass

    def _conflict_cb(self, msg):
        try:
            d = json.loads(msg.data)
            g = d.get('group', '?')
            ranks = d.get('ranks') or {}
            if ranks:
                self.conflicts[g] = {'ranks': ranks, 't': time.time(),
                                     'mid': d.get('mid')}
            else:
                self.conflicts.pop(g, None)
                # Gazebo 숫자 제거
                for r in list(getattr(self, '_prio_models', {})):
                    self._prio_clear(r)
            self.publish_markers()
        except (ValueError, TypeError):
            pass

    def _conflict_loop(self):
        # 로봇이 움직이므로 우선순위 숫자를 1초마다 로봇 위치로 갱신
        while not rospy.is_shutdown():
            time.sleep(1.0)
            # 오래된 항목 자동 소거 (해산 발행 유실 대비)
            for g in [g for g, v in self.conflicts.items()
                      if time.time() - v['t'] > 90.0]:
                self.conflicts.pop(g, None)
            if self.conflicts or getattr(self, '_prio_models', None):
                self.publish_markers()
                if self.use_gazebo:
                    self._prio_gazebo_sync()

    def _active_ranks(self):
        ranks = {}
        for v in self.conflicts.values():
            for r, k in v['ranks'].items():
                ranks[r] = min(k, ranks.get(r, 9))
        return ranks

    def _prio_gazebo_sync(self):
        """Gazebo: 우선순위 7-세그 숫자를 로봇 옆에 스폰/이동, 해소 시 제거."""
        if not hasattr(self, '_prio_models'):
            self._prio_models = {}    # 로봇 → (rank, 모델이름)
        ranks = self._active_ranks()
        try:
            from gazebo_msgs.srv import SpawnModel, DeleteModel, SetModelState
            from gazebo_msgs.msg import ModelState
            for r in list(self._prio_models):
                if r not in ranks:
                    self._prio_clear(r)
            for r, k in ranks.items():
                px = self.rpos.get(r)
                if px is None:
                    continue
                cur = self._prio_models.get(r)
                name = f'prio_{r}_{k}'
                if cur is None or cur[0] != k:
                    if cur is not None:
                        self._prio_clear(r)
                    rospy.wait_for_service('/gazebo/spawn_sdf_model', timeout=2.0)
                    sp = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)
                    ps = PoseStamped()
                    ps.pose.position.x = px[0] + 0.45
                    ps.pose.position.y = px[1]
                    ps.pose.position.z = 0.03
                    ps.pose.orientation.w = 1.0
                    sp(name, build_count_sdf(name, k), '', ps.pose, 'world')
                    self._prio_models[r] = (k, name)
                else:
                    rospy.wait_for_service('/gazebo/set_model_state', timeout=2.0)
                    mv = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
                    st = ModelState()
                    st.model_name = cur[1]
                    st.pose.position.x = px[0] + 0.45
                    st.pose.position.y = px[1]
                    st.pose.position.z = 0.03
                    st.pose.orientation.w = 1.0
                    st.reference_frame = 'world'
                    mv(st)
        except Exception as e:
            rospy.logwarn_throttle(30.0, '우선순위 숫자 표시 실패: %s', e)

    def _prio_clear(self, r):
        try:
            from gazebo_msgs.srv import DeleteModel
            cur = self._prio_models.pop(r, None)
            if cur:
                rospy.wait_for_service('/gazebo/delete_model', timeout=2.0)
                rospy.ServiceProxy('/gazebo/delete_model', DeleteModel)(cur[1])
        except Exception:
            pass

    def _items_cb(self, msg):
        try:
            g, left, xy = msg.data.split(':', 2)
            x, y = [float(v) for v in xy.split(',')[:2]]
            g = g.strip()
            self.is_relay = False      # 다목적 이동 신호 — RELAY 배너 해제
            self.items[g] = (int(left), x, y)
            self.publish_markers()
            if self.use_gazebo:
                # goal 지점 판 (상시 표시)
                ps = PoseStamped()
                ps.header.frame_id = 'map'
                ps.pose.position.x = x
                ps.pose.position.y = y
                ps.pose.orientation.w = 1.0
                self.update_gazebo(g, ps)
                # 남은 물품 = 검정 숫자 판 (goal 옆 바닥, 감소 시 교체)
                self._sync_item_number(g, int(left), x, y)
        except (ValueError, IndexError):
            pass

    def _count_offset(self, x, y, dist=0.9):
        """베이스 반대쪽(goal 너머)으로 숫자/텍스트를 비켜 놓을 오프셋."""
        if self.base is not None:
            dx = x - self.base.pose.position.x
            dy = y - self.base.pose.position.y
            dd = (dx * dx + dy * dy) ** 0.5
            if dd > 0.1:
                return dist * dx / dd, dist * dy / dd
        return 0.0, dist

    def _sync_item_number(self, g, left, x, y):
        """Gazebo 바닥에 남은 물품 수를 7-세그 숫자로 표시, 변할 때 교체."""
        if not hasattr(self, 'gz_counts'):
            self.gz_counts = {}     # goal → (표시값, 모델이름)
        prev = self.gz_counts.get(g)
        if prev is not None and prev[0] == left:
            return
        try:
            from gazebo_msgs.srv import SpawnModel, DeleteModel
            ox, oy = self._count_offset(x, y)
            name = f'count_{g}_{left}'
            rospy.wait_for_service('/gazebo/spawn_sdf_model', timeout=3.0)
            spawn = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)
            ps = PoseStamped()
            ps.pose.position.x = x + ox
            ps.pose.position.y = y + oy
            ps.pose.position.z = 0.03
            ps.pose.orientation.w = 1.0
            spawn(name, build_count_sdf(name, left), '', ps.pose, 'world')
            if prev is not None:            # 새 숫자 먼저, 옛 숫자 삭제는 나중
                rospy.wait_for_service('/gazebo/delete_model', timeout=3.0)
                rospy.ServiceProxy('/gazebo/delete_model', DeleteModel)(prev[1])
            self.gz_counts[g] = (left, name)
        except Exception as e:
            rospy.logwarn_throttle(30.0, '물품 숫자 갱신 실패(%s): %s', g, e)

    # ---------- RViz 마커 ----------
    def _base(self, name, g, mid, mtype):
        m = Marker()
        m.header.frame_id = g.header.frame_id or 'map'
        m.header.stamp = rospy.Time.now()
        m.ns = 'relay_goal'
        m.id = mid
        m.type = mtype
        m.action = Marker.ADD
        m.pose.position.x = g.pose.position.x
        m.pose.position.y = g.pose.position.y
        m.pose.orientation = g.pose.orientation
        r, gc, b = COLORS.get(name, GOAL_COLORS.get(name, DEFAULT_COLOR))
        m.color.r, m.color.g, m.color.b, m.color.a = r, gc, b, 0.95
        return m

    def publish_markers(self):
        arr = MarkerArray()
        for i, name in enumerate(self.robots):
            if name not in self.goals:
                continue
            g = self.goals[name]
            # ① goal 위치 = 납작한 사각형
            sq = self._base(name, g, i * 3, Marker.CYLINDER)   # goal 원형 표시 (2026-08-08 지시)
            sq.pose.position.z = 0.02
            sq.pose.orientation.x = sq.pose.orientation.y = 0.0  # 바닥에 평평하게
            sq.scale.x, sq.scale.y, sq.scale.z = 0.4, 0.4, 0.02
            arr.markers.append(sq)
            # ② goal 방향 = 작은 화살표 (로봇 화살표보다 확실히 작게)
            ar = self._base(name, g, i * 3 + 1, Marker.ARROW)
            ar.pose.position.z = 0.06
            ar.scale.x, ar.scale.y, ar.scale.z = 0.3, 0.04, 0.04
            arr.markers.append(ar)
            # ③ 로봇 이름 라벨
            tx = self._base(name, g, i * 3 + 2, Marker.TEXT_VIEW_FACING)
            tx.pose.position.y -= 0.5      # goal 원 아래로 — 겹침 해소 (2026-08-09)
            tx.pose.position.z = 0.3
            tx.scale.z = 0.3
            tx.text = name + " goal"
            arr.markers.append(tx)
        # 베이스(공동 출발지) — 붉은 원 + BASE 라벨
        if self.base is not None:
            b = self.base
            sq = Marker()
            sq.header.frame_id = b.header.frame_id or 'map'
            sq.header.stamp = rospy.Time.now()
            sq.ns = 'relay_goal'
            sq.id = 960
            sq.type = Marker.CYLINDER
            sq.action = Marker.ADD
            sq.pose.position.x = b.pose.position.x
            sq.pose.position.y = b.pose.position.y
            sq.pose.position.z = 0.02
            sq.pose.orientation.w = 1.0
            sq.scale.x, sq.scale.y, sq.scale.z = 3.2, 3.2, 0.03   # 지름 3.2m 원 영역 (1.5m 간격 클러스터)
            sq.color.r, sq.color.g, sq.color.b = 0.9, 0.15, 0.15
            sq.color.a = 0.45      # 반투명 영역 표시
            arr.markers.append(sq)
            tx = Marker()
            tx.header.frame_id = sq.header.frame_id
            tx.header.stamp = sq.header.stamp
            tx.ns = 'relay_goal'
            tx.id = 961
            tx.type = Marker.TEXT_VIEW_FACING
            tx.action = Marker.ADD
            tx.pose.position.x = b.pose.position.x
            tx.pose.position.y = b.pose.position.y
            tx.pose.position.z = 0.55
            tx.pose.orientation.w = 1.0
            tx.scale.z = 0.35
            tx.color.r, tx.color.g, tx.color.b = self._txt_rgb(
                tx.pose.position.x, tx.pose.position.y)
            tx.color.a = 1.0
            tx.text = 'BASE'
            arr.markers.append(tx)
        # 동적 coalition 우선순위 — 로봇 위 큰 숫자 (1=우선 통과)
        used_dyn = set()
        for j2, (rb, rk) in enumerate(sorted(self._active_ranks().items())):
            rp = self.rpos.get(rb)
            if rp is None:
                continue
            pm = Marker()
            pm.header.frame_id = 'map'
            pm.header.stamp = rospy.Time.now()
            pm.ns = 'relay_goal'
            pm.id = 1000 + j2
            used_dyn.add(pm.id)
            pm.type = Marker.TEXT_VIEW_FACING
            pm.action = Marker.ADD
            pm.pose.position.x, pm.pose.position.y = rp[0], rp[1]
            pm.pose.position.z = 0.9
            pm.pose.orientation.w = 1.0
            pm.scale.z = 0.6
            if rk == 1:
                pm.color.r, pm.color.g, pm.color.b = 0.1, 0.7, 0.1   # 우선=초록
            else:
                pm.color.r, pm.color.g, pm.color.b = 0.85, 0.1, 0.1  # 대기=빨강
            pm.color.a = 1.0
            pm.text = str(rk)
            arr.markers.append(pm)
        # 병목(충돌 예측) 지점 — 사각형 + '병목 (bottleneck)' 라벨
        for j3, (gk, v) in enumerate(sorted(self.conflicts.items())):
            mid = v.get('mid')
            if not mid:
                continue
            bx, by = float(mid[0]), float(mid[1])
            bq = Marker()
            bq.header.frame_id = 'map'
            bq.header.stamp = rospy.Time.now()
            bq.ns = 'relay_goal'
            bq.id = 1100 + j3 * 2
            used_dyn.add(bq.id)
            bq.type = Marker.CUBE
            bq.action = Marker.ADD
            bq.pose.position.x, bq.pose.position.y, bq.pose.position.z = bx, by, 0.02
            bq.pose.orientation.w = 1.0
            bq.scale.x = bq.scale.y = 0.9
            bq.scale.z = 0.03
            bq.color.r, bq.color.g, bq.color.b, bq.color.a = 0.9, 0.35, 0.1, 0.5
            arr.markers.append(bq)
            bt2 = Marker()
            bt2.header.frame_id = 'map'
            bt2.header.stamp = rospy.Time.now()
            bt2.ns = 'relay_goal'
            bt2.id = 1101 + j3 * 2
            used_dyn.add(bt2.id)
            bt2.type = Marker.TEXT_VIEW_FACING
            bt2.action = Marker.ADD
            bt2.pose.position.x, bt2.pose.position.y = bx, by - 0.65
            bt2.pose.position.z = 0.3
            bt2.pose.orientation.w = 1.0
            bt2.scale.z = 0.32
            bt2.color.r, bt2.color.g, bt2.color.b, bt2.color.a = 0.8, 0.2, 0.05, 1.0
            bt2.text = "병목 (bottleneck)"
            arr.markers.append(bt2)
        # 소멸된 동적 마커(우선순위 숫자·병목 표식)는 DELETE — 잔상 방지 (2026-08-09)
        for old_id in getattr(self, '_dyn_prev', set()) - used_dyn:
            dm = Marker()
            dm.header.frame_id = 'map'
            dm.ns = 'relay_goal'
            dm.id = old_id
            dm.action = Marker.DELETE
            arr.markers.append(dm)
        self._dyn_prev = used_dyn
        # 충돌회피 병목 — 붉은 원 + 통과 순서 텍스트
        if self.bt:
            cx, cy = float(self.bt['center'][0]), float(self.bt['center'][1])
            rr = float(self.bt.get('r', 1.35))
            c = Marker()
            c.header.frame_id = 'map'
            c.header.stamp = rospy.Time.now()
            c.ns = 'relay_goal'
            c.id = 990
            c.type = Marker.CYLINDER
            c.action = Marker.ADD
            c.pose.position.x, c.pose.position.y, c.pose.position.z = cx, cy, 0.02
            c.pose.orientation.w = 1.0
            c.scale.x = c.scale.y = rr * 2.0
            c.scale.z = 0.03
            c.color.r, c.color.g, c.color.b, c.color.a = 0.95, 0.65, 0.2, 0.35
            arr.markers.append(c)
            tx2 = Marker()
            tx2.header.frame_id = 'map'
            tx2.header.stamp = rospy.Time.now()
            tx2.ns = 'relay_goal'
            tx2.id = 991
            tx2.type = Marker.TEXT_VIEW_FACING
            tx2.action = Marker.ADD
            tx2.pose.position.x, tx2.pose.position.y, tx2.pose.position.z = cx, cy + rr + 0.4, 0.6
            tx2.pose.orientation.w = 1.0
            tx2.scale.z = 0.4
            tx2.color.r, tx2.color.g, tx2.color.b = self._txt_rgb(
                tx2.pose.position.x, tx2.pose.position.y)
            tx2.color.a = 1.0
            # 각 로봇의 최종 goal — 로봇 색 원 + 라벨 (2026-08-09 지시)
            for k, (nm, txy) in enumerate(sorted(self.bt.get('targets', {}).items())):
                fx, fy = float(txy[0]), float(txy[1])
                fr, fg, fb = COLORS.get(nm, DEFAULT_COLOR)
                fc = Marker()
                fc.header.frame_id = 'map'
                fc.header.stamp = rospy.Time.now()
                fc.ns = 'relay_goal'
                fc.id = 992 + k * 2
                fc.type = Marker.CYLINDER
                fc.action = Marker.ADD
                fc.pose.position.x, fc.pose.position.y, fc.pose.position.z = fx, fy, 0.02
                fc.pose.orientation.w = 1.0
                fc.scale.x = fc.scale.y = 0.55
                fc.scale.z = 0.03
                fc.color.r, fc.color.g, fc.color.b, fc.color.a = fr, fg, fb, 0.85
                arr.markers.append(fc)
                ft = Marker()
                ft.header.frame_id = 'map'
                ft.header.stamp = rospy.Time.now()
                ft.ns = 'relay_goal'
                ft.id = 993 + k * 2
                ft.type = Marker.TEXT_VIEW_FACING
                ft.action = Marker.ADD
                ft.pose.position.x, ft.pose.position.y, ft.pose.position.z = fx, fy + 0.45, 0.4
                ft.pose.orientation.w = 1.0
                ft.scale.z = 0.3
                ft.color.r, ft.color.g, ft.color.b, ft.color.a = fr, fg, fb, 1.0
                ft.text = f"{nm} 최종 goal"
                arr.markers.append(ft)
            cur = self.bt.get('current')
            order = self.bt.get('order', [])
            done = self.bt.get('passed', [])
            tx2.text = ("통과: " + " > ".join(order) if order else "통과 완료")                 + (f" | 현재: {cur}" if cur else "")                 + (f" | 완료 {len(done)}" if done else "")
            arr.markers.append(tx2)
        # 다목적 goal 지점 — 색 사각형 판 상시 표시
        for j, (g, (left, x, y)) in enumerate(sorted(self.items.items())):
            gr, gg, gb = GOAL_COLORS.get(g, DEFAULT_COLOR)
            sq = Marker()
            sq.header.frame_id = 'map'
            sq.header.stamp = rospy.Time.now()
            sq.ns = 'relay_goal'
            sq.id = 980 + j
            sq.type = Marker.CUBE
            sq.action = Marker.ADD
            sq.pose.position.x, sq.pose.position.y, sq.pose.position.z = x, y, 0.02
            sq.pose.orientation.w = 1.0
            sq.scale.x, sq.scale.y, sq.scale.z = 0.6, 0.6, 0.03
            sq.color.r, sq.color.g, sq.color.b = gr, gg, gb
            sq.color.a = 0.55 if left > 0 else 0.25
            arr.markers.append(sq)
        # goal 별 남은 물품 수 — goal 위에 크게 표시, 0이면 회색 완료 표기
        for j, (g, (left, x, y)) in enumerate(sorted(self.items.items())):
            it = Marker()
            it.header.frame_id = 'map'
            it.header.stamp = rospy.Time.now()
            it.ns = 'relay_goal'
            it.id = 970 + j
            it.type = Marker.TEXT_VIEW_FACING
            it.action = Marker.ADD
            ox, oy = self._count_offset(x, y)
            it.pose.position.x, it.pose.position.y, it.pose.position.z = x + ox, y + oy, 0.35
            it.pose.orientation.w = 1.0
            it.scale.z = 0.5
            # 배경 적응 (2026-08-10 지시): 지도 위=검정 / 지도 밖(어두운 뷰포트)=흰색.
            # 다목적 이동은 map_server 를 안 띄워 항상 어두운 배경 → 흰색.
            _c9 = self._txt_rgb(it.pose.position.x, it.pose.position.y)[0]
            if left > 0:
                it.color.r = it.color.g = it.color.b = _c9
            else:
                # 완료 — 배경 쪽으로 30% 흐리게 (밝은 배경=짙은 회색, 어두운 배경=밝은 회색)
                it.color.r = it.color.g = it.color.b = _c9 * 0.7 + (1.0 - _c9) * 0.3
            it.color.a = 1.0
            it.text = f"{g}: {left}" if left > 0 else f"{g}: 0 (done)"
            arr.markers.append(it)
        # RTF 표시 — 라인 상단 고정 위치, 5초마다 갱신
        if self.rtf_text:
            rt = Marker()
            rt.header.frame_id = 'map'
            rt.header.stamp = rospy.Time.now()
            rt.ns = 'relay_goal'
            rt.id = 950
            rt.type = Marker.TEXT_VIEW_FACING
            rt.action = Marker.ADD
            # 지도 '아래' 로 이동 — 상단 Found Objects 배너와 겹침 (2026-08-10 지시)
            rt.pose.position.x, rt.pose.position.y, rt.pose.position.z = 1.0, -5.4, 0.3
            rt.pose.orientation.w = 1.0
            rt.scale.z = 0.5
            rt.color.r, rt.color.g, rt.color.b = self._txt_rgb(
                rt.pose.position.x, rt.pose.position.y)
            rt.color.a = 1.0
            rt.text = self.rtf_text
            arr.markers.append(rt)
        # 릴레이 단계 배너 — relay 계획을 받은 세션에서만 (다목적 이동 등에선 미표시)
        if self.is_relay and self.active and self.active in self.goals:
            order = [r for r in self.robots if r in self.goals]
            step = order.index(self.active) + 1 if self.active in order else 0
            bn = self._base(self.active, self.goals[self.active], 900,
                            Marker.TEXT_VIEW_FACING)
            bn.pose.position.z = 1.1
            bn.scale.z = 0.45
            bn.text = "RELAY %d/%d: %s moving" % (step, len(self.robots), self.active)
            arr.markers.append(bn)
        self.pub.publish(arr)

    # ---------- Gazebo 사각판 ----------
    def update_gazebo(self, name, g):
        try:
            from gazebo_msgs.srv import SpawnModel, SetModelState
            from gazebo_msgs.msg import ModelState
            model = 'goal_marker_%s' % name
            r, gc, b = COLORS.get(name, GOAL_COLORS.get(name, DEFAULT_COLOR))
            if model not in self.spawned:
                try:
                    rospy.wait_for_service('/gazebo/spawn_sdf_model', timeout=3.0)
                    spawn = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)
                    if name in ('base', 'bottleneck'):
                        if name == 'bottleneck':
                            # 병목: 은은한 주황 (빨강은 부담 — 2026-08-08 지시)
                            col = dict(cr=0.95, cg=0.65, cb=0.25,
                                       er=0.4, eg=0.27, eb=0.1)
                        else:
                            col = dict(cr=0.9, cg=0.1, cb=0.1,
                                       er=0.6, eg=0.05, eb=0.05)
                        sdf = SDF_BASE_TEMPLATE.format(name=model, **col)
                    else:
                        sdf = SDF_TEMPLATE.format(name=model, r=r, g=gc, b=b,
                                                  re=r, ge=gc, be=b)
                    pose = g.pose
                    pose.position.z = 0.05
                    resp = spawn(model, sdf, '', pose, 'map')
                    self.spawned.add(model)   # 이미 존재(재실행)해도 이동으로 폴백
                    if not resp.success:
                        rospy.loginfo('%s spawn: %s (이동으로 폴백)', model, resp.status_message)
                except Exception as e:
                    rospy.logwarn_throttle(30.0, 'gazebo goal 스폰 실패(%s): %s', model, e)
                    return
            # 존재하면 위치 이동
            try:
                rospy.wait_for_service('/gazebo/set_model_state', timeout=2.0)
                move = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
                st = ModelState()
                st.model_name = model
                st.pose = g.pose
                st.pose.position.z = 0.05
                st.reference_frame = 'world'
                move(st)
            except Exception as e:
                rospy.logwarn_throttle(30.0, 'gazebo goal 이동 실패(%s): %s', model, e)
        except ImportError:
            pass    # gazebo_msgs 없음 — RViz 마커만


def main():
    rospy.init_node('relay_goal_labels')
    gm = GoalMarkers()
    rospy.loginfo('relay_goal_labels: %s goal 마커(RViz 사각형+화살표+라벨%s) 발행 중',
                  ','.join(gm.robots), ', Gazebo 판' if gm.use_gazebo else '')
    rospy.spin()


if __name__ == '__main__':
    main()
