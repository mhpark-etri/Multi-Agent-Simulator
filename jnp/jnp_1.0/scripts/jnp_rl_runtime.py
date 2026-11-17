# -*- coding: utf-8 -*-
"""[JnP-1.0 RL G2 2026-10-31] 로봇 쪽 정책 결정 자리.

DecisionCore(ROS 없음): 자기 지도·위치·받은 정보·훑은 곳으로 Observation 을 만들고, Action 을 '새 목표 / 제공 변경 / 구독 변경' 으로 푼다.
RobotPolicyRuntime(ROS): 에이전트 탐사 루프가 1초마다 tick() 을 부른다. 자기 지도(/<로봇>/map) 구독, 제공 항목 발행, 다른 에이전트 설명 조회·구독,
통신 기록표(~jnp_comm_log) 기록을 맡는다. 정책이 고른 목표는 state['tgt'] 에 넣어 기존 주행 코드가 그대로 따라가게 한다."""
import json
import math
import os
import threading
import time

from jnp_rl_api import GOAL_XY_MAX_M, Observation, RobotSpec, Candidate
from jnp_rl_frontier import candidates_from_grid
from jnp_rl_gridcheck import check_grid

DECIDE_PERIOD_S = 3.0      # 정책 호출 주기(sim초) — 중앙 피더와 같은 3초
REACH_M = 0.6              # 도착 판정 거리
STALL_S = 45.0             # 접근 없음 → 목표 포기


def goal_from_action(obs, c, act):
    """정책이 준 접근점을 검사해 (x, y) 를 돌려준다. 유한 좌표, 좌표계, 후보 대응, 자기 지도의 자유 칸을 본다. 맞지 않으면 ValueError(그 결정은 버린다)."""
    x, y = float(act.goal_xy[0]), float(act.goal_xy[1])
    if not (math.isfinite(x) and math.isfinite(y)):
        raise ValueError('접근점 좌표가 유한하지 않다 %r' % (act.goal_xy,))
    if getattr(act, 'goal_frame', None) != getattr(obs, 'grid_frame', None):
        raise ValueError('접근점 좌표계 %r 가 자기 지도 %r 와 다르다' % (getattr(act, 'goal_frame', None), getattr(obs, 'grid_frame', None)))
    if math.hypot(x - c.x, y - c.y) > GOAL_XY_MAX_M + 1e-6:
        raise ValueError('접근점이 후보에서 %.2f m 떨어졌다' % math.hypot(x - c.x, y - c.y))
    if obs.grid is None:
        raise ValueError('자기 지도가 없어 접근점을 확인할 수 없다')
    (res, ox, oy, w, h), data = obs.grid
    col, row = int(math.floor((x - ox) / res)), int(math.floor((y - oy) / res))
    if not (0 <= row < int(h) and 0 <= col < int(w)):
        raise ValueError('접근점이 자기 지도 밖이다')
    v = int(data[row * int(w) + col])
    if not 0 <= v < 50:
        raise ValueError('접근점이 자유 칸이 아니다(값 %d)' % v)
    return x, y


class DecisionCore(object):
    def __init__(self, robot, spec=None, mode='explore'):
        self.robot = str(robot).strip('/').split('/')[-1]
        self.spec = spec or RobotSpec.from_name(self.robot)
        self.mode = mode                 # 'explore' | 'search'
        self.route = []                  # 수색 모드: JnP 가 준 경유점 [(x, y), ...]
        self.visited = []
        self.target = None
        self.target_src = None      # 지금 목표의 원본 후보 (x, y). 접근점을 줄 때만 쓴다
        self.cancelled = False      # 이번 apply 가 정책의 취소로 목표를 버렸는가
        self.prog = None            # (t, dist) 마지막 접근 기록
        self.round_index = 0
        self.t0 = None
        self.t0_source = ''          # 'episode'(회차 명세의 태스크 발행 시각) | 'first_observation'(명세 없을 때의 대체)
        self.last_decide = -1e9

    def due(self, t):
        return t - self.last_decide >= DECIDE_PERIOD_S

    def set_t0(self, t0, source='episode'):
        """[R5 F1, 결정 (a) 2026-11-01] 회차 시계의 0초 = 태스크 발행 sim 시각(회차 명세 /lb/episode/t0). 모든 로봇·채점기가 같은 0초를 쓴다."""
        self.t0 = float(t0); self.t0_source = source

    def update_progress(self, t, my_pos):
        """도착·정체 판정. 도착이면 목표를 훑은 곳으로 옮기고 None. 반환: 'reached' | 'stalled' | None."""
        if self.target is None or my_pos is None:
            return None
        d = math.hypot(self.target[0] - my_pos[0], self.target[1] - my_pos[1])
        if d < REACH_M:
            self.visited.append(self.target); self.target = None; self.prog = None; self.target_src = None
            return 'reached'
        if self.prog is None or d < self.prog[1] - 0.3:
            self.prog = (t, d)
        elif t - self.prog[0] > STALL_S:
            self.target = None; self.prog = None; self.target_src = None
            return 'stalled'
        return None

    def observation(self, t, my_pos, grid, received, available, providing, subscribed, role='', teammates=(), detections=None, received_t=None,
                    received_meta=None, t_limit=None, grid_frame=None, grid_stamp=None):
        if self.t0 is None:
            self.t0 = t; self.t0_source = 'first_observation'
        done_pts = []
        for k, v in received.items():
            if k.endswith('/done_area') and isinstance(v, (list, tuple)):
                done_pts.extend([(p[0], p[1]) for p in v if isinstance(p, (list, tuple)) and len(p) >= 2])
        if self.mode == 'search':
            # 수색: 후보 = 아직 안 간 경유점(경로 순서 그대로). 지나간 지점(0.6 m 안)은 뺀다.
            cands = [Candidate(x=wx, y=wy, src_x=wx, src_y=wy, dist=math.hypot(wx - my_pos[0], wy - my_pos[1]), size=0)
                     for wx, wy in self.route if not any(math.hypot(wx - vx, wy - vy) < REACH_M for vx, vy in self.visited)]
        else:
            cands = candidates_from_grid(grid, my_pos, self.visited, done_pts) if grid is not None else []
        known = int(sum(1 for v in grid[1] if v != -1)) if grid is not None else 0
        self.round_index += 1; self.last_decide = t
        return Observation(t=t - self.t0, round_index=self.round_index, robot=self.robot, robot_spec=self.spec, my_pos=my_pos, received_t=dict(received_t or {}),
                           received_meta=dict(received_meta or {}), t_limit=t_limit, grid_frame=grid_frame, grid_stamp=grid_stamp,
                           candidates=cands, known_cells=known, grid=grid, visited=list(self.visited), need_goal=self.target is None,
                           current_goal=self.target, role=role, teammates=list(teammates), received=dict(received),
                           available=dict(available), providing=set(providing), subscribed=set(subscribed),
                           mode=self.mode, detections=list(detections or []), route=list(self.route))

    def apply(self, obs, act, providing, subscribed):
        """Action → (새 목표|None, 켤 항목, 끌 항목, 새 구독, 끊을 구독). 범위 밖 선택은 ValueError."""
        new_target = None
        self.cancelled = False
        ci = getattr(act, 'choice', None)
        cancel = bool(getattr(act, 'cancel_goal', False))
        if cancel and ci is not None:
            raise ValueError('choice 와 cancel_goal 을 함께 줄 수 없다')
        if getattr(act, 'goal_xy', None) is not None and ci is None:
            raise ValueError('goal_xy 는 choice 와 함께 준다')
        if ci is not None:
            ci = int(ci)
            if not (0 <= ci < len(obs.candidates)):
                raise ValueError('choice %r 가 후보 범위(0..%d) 밖' % (ci, len(obs.candidates) - 1))
            c = obs.candidates[ci]
            if getattr(act, 'goal_xy', None) is None:
                new_target = (c.x, c.y)
                self.target = new_target; self.target_src = None; self.prog = (obs.t + (self.t0 or 0), c.dist)
            else:
                new_target = goal_from_action(obs, c, act)      # 맞지 않으면 여기서 멈춘다. 지금 목표와 시계는 그대로다
                same = self.target_src is not None and math.hypot(c.x - self.target_src[0], c.y - self.target_src[1]) < 0.3
                self.target = new_target; self.target_src = (c.x, c.y)
                if not same or self.prog is None:               # 같은 후보의 접근점만 바꾸면 접근 시계를 되돌리지 않는다
                    self.prog = (obs.t + (self.t0 or 0), math.hypot(new_target[0] - obs.my_pos[0], new_target[1] - obs.my_pos[1]))
        elif cancel and self.target is not None:
            self.target = None; self.prog = None; self.target_src = None
            self.cancelled = True
        on, off = [], []
        for k, v in (getattr(act, 'provide', None) or {}).items():
            (on if v else off).append(k)
        want = getattr(act, 'subscribe', None)
        add = sorted(set(want) - set(subscribed)) if want is not None else []
        drop = sorted(set(subscribed) - set(want)) if want is not None else []
        return new_target, [k for k in on if k not in providing], [k for k in off if k in providing], add, drop


class RobotPolicyRuntime(object):
    """ROS 쪽. 에이전트 탐사 루프가 만들고 tick(now, mypos, state) 을 부른다."""

    def __init__(self, node_name, policy_spec, log_path='', spec_override=None, rate_hz=2.0, mode='explore', on_provide=None):
        import rospy
        from nav_msgs.msg import OccupancyGrid
        from std_msgs.msg import String
        from jnp_rl_loader import load_policy
        from jnp_rl_meter import CommLog
        self.node = str(node_name).strip('/')
        self.robot = self.node.split('/')[-1]
        self.mode = mode
        self.core = DecisionCore(self.robot, RobotSpec.from_name(self.robot, spec_override), mode=mode)
        self.detections = []
        if mode == 'search':
            # 내 구역 경유점(JnP 그룹이 한 번 보내 줌) — 내 것, 통신 아님
            self._sub_route = rospy.Subscriber('/search_route/%s' % self.robot, String, self._route_cb, queue_size=1)
        # 내 탐지기 결과(채점 환경의 정답 기반 탐지기가 내 센서 역할) — 내 것, 통신 아님. 수색 모드이거나, 지도 없는 수색처럼 탐사 모드에서도
        # 탐지를 써야 하면(~jnp_use_detections) 받는다. 보고(Action.report)는 정책이 'detections' 제공을 켜야 나간다 [2026-11-07]
        self.use_detections = (mode == 'search') or bool(rospy.get_param('~jnp_use_detections', False))
        if self.use_detections:
            self._sub_det = rospy.Subscriber('/%s/gt_detections' % self.robot, String, self._det_cb, queue_size=1)
        self.policy = load_policy(policy_spec)
        self.log = CommLog(self.node, log_path or ('/tmp/jnp_comm_%s.jsonl' % self.robot),
                           run_id=(rospy.get_param('~jnp_run_id', '') or None), clock=rospy.get_time)   # [F7] 회차 ID·sim 시각
        # [R11 F1] 어떤 정책이 돌았는지 기록표에 남긴다(meta 줄, 바이트 0): 지정 문자열·클래스·정책의 manifest(규칙 파일 해시·상수·체크포인트 digest).
        # 실행기가 이 줄을 manifest.json 에 모으고, 기준 회차 집계가 '규칙 정책·같은 상수' 인지 검증한다. manifest() 가 없는 정책은 클래스 이름만 남는다.
        pm = {'spec': str(policy_spec), 'class': '%s.%s' % (type(self.policy).__module__, type(self.policy).__name__),
              'api_version': str(getattr(self.policy, 'api_version', ''))}
        try:
            m = self.policy.manifest() if callable(getattr(self.policy, 'manifest', None)) else None
            if isinstance(m, dict):
                pm['manifest'] = json.loads(json.dumps(m, default=str))
        except Exception as e:
            pm['manifest_error'] = str(e)
        self.policy_manifest = pm
        self.log.record('meta', 'policy_manifest', self.node, self.node, 0, extra={'policy': pm})
        print('[JnP-RL] %s: 정책 식별 %s' % (self.robot, json.dumps(pm, ensure_ascii=False, sort_keys=True)), flush=True)
        self.grid = None
        self.received, self.available, self.subs, self.providers = {}, {}, {}, {}
        self.received_t = {}                    # '에이전트/항목' → 마지막 수신 시각(sim) — 정책이 '팀원 done 뒤의 최종 지도'를 가린다
        self.desc_t = {}
        self.rate_hz = rate_hz
        self.on_provide = on_provide            # 제공 항목이 바뀌면 에이전트에 알려 설명(<provides>)에 광고하게 한다
        self._lock = threading.Lock()           # [R5 F7] 수신 보관(payload·메타·시각)을 원자적으로 갱신·복사한다
        self.received_meta = {}                 # '에이전트/항목' → {'stamp': 보낸 쪽 발행 시각, 'frame': 좌표계, 'seq': 번호}
        self.grid_frame, self.grid_stamp = None, None
        self._map_pub_stamp = None              # 내가 마지막으로 발행한 local_map 의 stamp — done 알림에 실어 host 가 최종본을 가린다(F7)
        self._rejected = {}
        self._episode = None                    # 회차 명세(/lb/episode: run_id·t0·T) — 읽히면 시계를 맞춘다(F1)
        aliases = [a.strip() for a in str(rospy.get_param('~jnp_frame_aliases', '') or '').split(',') if a.strip()]
        self.accept_frames = tuple(['map'] + aliases)   # [R5 F6, 결정 (c)] 빈 이름·다른 좌표계·돌아간 지도는 거부한다
        self._sub_map = rospy.Subscriber('/%s/map' % self.robot, OccupancyGrid, self._map_cb, queue_size=1)
        self.last_log_t = 0.0
        self._alive_timer = rospy.Timer(rospy.Duration(10.0), lambda _e: self.log.meta('alive'))   # [R5 F2] 계측기 생존 표시(10 s)
        rospy.on_shutdown(self.log.close)
        # [2026-11-04] 구독해 받은 동료 위치를 지역 지도와 속도 명령 점검에 쓴다. 기본 꺼짐. 켜면 위치 메시지 시각에 변환의 표본 시각을 적는다
        self.peer_guard = None
        self.yield_guard = None
        # [2026-11-04] 통행 양보(재난 대응 전용 시험 판). 기본 꺼짐. 받은 정보만 쓰는 정책 모드에서만 켠다. 켜면 동료 위치 반영도 이 기능이 함께 맡는다
        if bool(rospy.get_param('~jnp_peer_yield', False)) and not bool(rospy.get_param('~jnp_free_peer_tf', False)):
            raise RuntimeError('~jnp_peer_yield 는 운영 전용 기능이라 이 판에 없다. 이 값을 켜지 않는다')
        elif bool(rospy.get_param('~jnp_peer_guard', False)):
            raise RuntimeError('~jnp_peer_guard 는 운영 전용 기능이라 이 판에 없다. 이 값을 켜지 않는다')

    def _route_cb(self, m):
        try:
            self.core.route = [(float(p[0]), float(p[1])) for p in json.loads(m.data)]
            print('[JnP-RL] %s: 수색 경유점 %d개 받음' % (self.robot, len(self.core.route)), flush=True)
        except Exception as e:
            print('[JnP-RL] %s: 경유점 형식 오류: %s' % (self.robot, e), flush=True)

    def _det_cb(self, m):
        try:
            self.detections = json.loads(m.data)
        except Exception:
            self.detections = []

    def _reject(self, key, why):
        n = self._rejected.get((key, why), 0) + 1; self._rejected[(key, why)] = n
        if n <= 3:
            print('[JnP-RL] %s: %s 지도 거부(%d번째): %s' % (self.robot, key, n, why), flush=True)

    def _map_cb(self, m):
        # [R5 F6] 자기 지도도 같은 검사(좌표계 이름·2D 항등 자세·셀 값). 좌표계 이름과 stamp 를 함께 보관해 발행 때 'map' 으로 재표기하지 않는다
        info = (m.info.resolution, m.info.origin.position.x, m.info.origin.position.y, m.info.width, m.info.height)
        q = m.info.origin.orientation
        ok, why = check_grid(info, m.data, frame_id=m.header.frame_id, quat=(q.x, q.y, q.z, q.w), accept_frames=self.accept_frames)
        if not ok:
            self._reject('self/map', why)
            return
        with self._lock:
            self.grid = (info, m.data)
            self.grid_frame = m.header.frame_id; self.grid_stamp = m.header.stamp.to_sec()

    # ── 받은 정보 요약 ──
    def _on_item(self, agent, item, msg):
        import rospy
        key = '%s/%s' % (agent, item)
        now = rospy.get_time()
        if item == 'pose' and self.peer_guard is not None:
            self.peer_guard.on_pose(agent, msg)
        if item == 'goal' and getattr(msg.header, 'frame_id', '') == 'none':
            with self._lock:                        # [F1] 동료가 목표를 버렸다(도착·정체)는 알림 → 보관본 삭제
                self.received.pop(key, None); self.received_meta.pop(key, None); self.received_t[key] = now
            return
        meta = {}
        if item in ('pose', 'goal'):
            val = (msg.pose.position.x, msg.pose.position.y)
            meta = {'stamp': msg.header.stamp.to_sec(), 'frame': msg.header.frame_id}
        elif item in ('local_map', 'merged_map'):
            # [R4 F9·R5 F6] 좌표계 이름·2D 항등 자세·유한 기하·셀 값을 공통 검사로 거른다 — 돌아간/다른 틀의 지도는 map 틀로 조용히 붙이지 않는다
            info = (msg.info.resolution, msg.info.origin.position.x, msg.info.origin.position.y, msg.info.width, msg.info.height)
            q = msg.info.origin.orientation
            ok, why = check_grid(info, msg.data, frame_id=msg.header.frame_id, quat=(q.x, q.y, q.z, q.w), accept_frames=self.accept_frames)
            if not ok:
                with self._lock:
                    self.received.pop(key, None); self.received_meta.pop(key, None)
                self._reject(key, why)
                return
            val = (info, msg.data)
            meta = {'stamp': msg.header.stamp.to_sec(), 'frame': msg.header.frame_id, 'seq': int(getattr(msg.header, 'seq', 0) or 0)}
        else:   # custom·done·detections·assignment·done_area: JSON 이면 풀고 아니면 문자열 그대로
            try:
                val = json.loads(msg.data)
            except Exception:
                val = msg.data
        with self._lock:                            # [R5 F7-C] payload·메타를 먼저, 수신 시각은 마지막에 — 옛 payload 에 새 시각이 붙지 않는다
            self.received[key] = val; self.received_meta[key] = meta; self.received_t[key] = now

    def _peer_node(self, peer):
        """팀 명단의 로봇 이름 → 노드 이름. 내가 이름공간 안에서 돌면(예: etri/locobot_0) 팀원도 같은 이름공간으로 본다.
        [JnP-1.0 RL 2026-11-01] __ns:=etri 로 띄운 에이전트끼리 설명 조회·구독이 /locobot_1/… 로 가서 실패하던 것 수정."""
        peer = str(peer).strip('/')
        ns = self.node.rsplit('/', 1)[0] if '/' in self.node else ''
        return ('%s/%s' % (ns, peer)) if (ns and '/' not in peer) else peer

    def _discover(self, peers, now):
        """팀원의 설명을 읽어 광고 항목을 알아 둔다(30초마다). 설명 조회 바이트는 기록표에 적힌다."""
        from jnp_rl_link import query_description
        from jnp_rl_registry import parse_description_provides
        for p in peers:
            if now - self.desc_t.get(p, -1e9) < 30.0:
                continue
            self.desc_t[p] = now
            try:
                xml = query_description(self.node, self._peer_node(p), self.log, timeout=1.0)
                _v, prov = parse_description_provides(xml)
                self.available[p] = [x['name'] for x in (prov or [])]
            except Exception as e:
                print('[JnP-RL] %s: %s 설명 조회 실패(계속): %s' % (self.robot, p, e), flush=True)

    def _set_provide(self, on, off):
        import rospy
        from jnp_rl_link import start_pose_provider, Provider
        if self.peer_guard is not None and (on or off):
            self.peer_guard.note_provide(on, off)
        for it in off:
            pv = self.providers.pop(it, None)
            try:
                if isinstance(pv, tuple):
                    pv[1].shutdown()
            except Exception:
                pass
        for it in on:
            if it == 'pose':
                if self.peer_guard is not None:
                    self.providers[it] = start_pose_provider(self.node, self.rate_hz, stamp_from_tf=True, buf=self.peer_guard.buf)
                else:
                    self.providers[it] = start_pose_provider(self.node, self.rate_hz)
            elif it in ('goal', 'done_area', 'local_map', 'custom', 'done', 'merged_map', 'detections'):
                self.providers[it] = Provider(self.node, it, latch=True)
            else:
                print('[JnP-RL] 제공 항목 %s 는 아직 발행기 없음' % it, flush=True)
        if (on or off) and self.on_provide is not None:
            try:
                self.on_provide(sorted(self.providers))
            except Exception as e:
                print('[JnP-RL] 제공 항목 광고 갱신 실패(계속): %s' % e, flush=True)

    def _grid_msg(self, grid):
        import rospy
        from nav_msgs.msg import OccupancyGrid
        info, data = grid
        m = OccupancyGrid(); m.header.frame_id = 'map'; m.header.stamp = rospy.Time.now()
        m.info.resolution, m.info.width, m.info.height = info[0], info[3], info[4]
        m.info.origin.position.x, m.info.origin.position.y, m.info.origin.orientation.w = info[1], info[2], 1.0
        m.data = list(data)
        return m

    def _publish_action_items(self, act, now):
        """custom·merged_map·done — 정책이 이번 라운드에 준 내용을 제공이 켜져 있으면 발행한다."""
        from std_msgs.msg import String
        if 'custom' in self.providers and getattr(act, 'custom_payload', None) is not None:
            self.providers['custom'].publish(String(str(act.custom_payload)))
        if 'merged_map' in self.providers and getattr(act, 'merged_map', None) is not None and str(getattr(self, '_role', '') or '') != 'host':
            # [R7 F4] 결과물(merged_map)은 그룹이 정한 host 만 낸다 — 정책이 뭐라 하든 JnP 층에서 막는다
            if not getattr(self, '_nonhost_warned', False):
                self._nonhost_warned = True
                print('[JnP-RL] %s: host 가 아닌데 merged_map 을 내려 함(역할 %r) — 발행하지 않음' % (self.robot, getattr(self, '_role', '')), flush=True)
        elif 'merged_map' in self.providers and getattr(act, 'merged_map', None) is not None:
            gm = self._grid_msg(act.merged_map)
            self.providers['merged_map'].publish(gm)
            digest = None
            try:   # [R6 F6 → R8 F3] 발신 기록(meta 줄, 바이트 합계에 안 들어감): 결과물 내용 digest(seq 제외)·stamp 를 적어 채점기가 trusted 모니터의 수신과 결과물별로 대조한다
                import io
                from jnp_rl_gridcheck import message_digest
                buf = io.BytesIO(); gm.serialize(buf); raw = buf.getvalue()
                digest = message_digest(gm)
                self.log.record('meta', 'sent:merged_map', self.node, 'monitor', len(raw), extra={'digest': digest, 'stamp': gm.header.stamp.to_sec()})
            except Exception:
                pass
            try:   # [R5 F7] 그룹에 '결과물 제출' 사실을 알린다(JnP 편성 쪽 알림 — 참가자 통신 점수에 들지 않는 채널). 그룹은 이 알림이 있어야 병합 task 를 완료로 본다
                import rospy
                if getattr(self, '_result_pub', None) is None:
                    self._result_pub = rospy.Publisher('/jnp/explore_result', String, queue_size=1, latch=True)
                note = str(getattr(act, 'note', '') or '')
                self._result_pub.publish(String(json.dumps({'robot': self.robot, 't': now, 'note': note, 'partial': ('partial' in note),
                                                            'cells': int(len(act.merged_map[1])) if act.merged_map else 0,
                                                            'run_id': (self._episode or {}).get('run_id'), 'digest': digest})))   # [R8 F3] 회차·결과물 식별
            except Exception as e:
                print('[JnP-RL] %s: 결과 알림 실패(계속): %s' % (self.robot, e), flush=True)
        if 'detections' in self.providers and getattr(act, 'report', None) is not None:
            self.providers['detections'].publish(String(json.dumps(act.report)))
        if getattr(act, 'done', False) and 'done' in self.providers:
            # [R5 F7] 마지막으로 발행한 local_map 의 stamp 를 함께 알린다 — host 는 그 stamp 이상의 지도만 최종본으로 인정한다
            self.providers['done'].publish(String(json.dumps({'robot': self.robot, 't': now, 'reason': getattr(act, 'note', ''), 'map_stamp': self._map_pub_stamp})))

    def _publish_state_items(self, new_target, cleared=False):
        """goal·done_area·local_map 제공이 켜져 있으면 바뀐 것을 발행한다. cleared=True 면 '목표 없음'(frame 'none')을 알린다."""
        import rospy
        from geometry_msgs.msg import PoseStamped
        from std_msgs.msg import String
        from nav_msgs.msg import OccupancyGrid
        if 'goal' in self.providers and new_target is not None:
            m = PoseStamped(); m.header.frame_id = 'map'; m.header.stamp = rospy.Time.now()
            m.pose.position.x, m.pose.position.y, m.pose.orientation.w = new_target[0], new_target[1], 1.0
            self.providers['goal'].publish(m)
        elif 'goal' in self.providers and cleared:
            m = PoseStamped(); m.header.frame_id = 'none'; m.header.stamp = rospy.Time.now(); m.pose.orientation.w = 1.0
            self.providers['goal'].publish(m)   # [F1] 도착·정체로 목표를 버림 → 받는 쪽 보관본이 지워진다
        if 'done_area' in self.providers and self.core.visited:
            self.providers['done_area'].publish(String(json.dumps(self.core.visited)))
        if 'local_map' in self.providers and self.grid is not None:
            with self._lock:
                info, data = self.grid; frame = self.grid_frame or 'map'
            m = OccupancyGrid(); m.header.frame_id = frame; m.header.stamp = rospy.Time.now()   # [R5 F6] 받은 좌표계 이름 그대로(재표기 없음)
            m.info.resolution, m.info.width, m.info.height = info[0], info[3], info[4]
            m.info.origin.position.x, m.info.origin.position.y, m.info.origin.orientation.w = info[1], info[2], 1.0
            m.data = list(data)
            self._map_pub_stamp = m.header.stamp.to_sec()
            self.providers['local_map'].publish(m)

    def _set_subscribe(self, add, drop):
        from jnp_rl_link import describe_and_subscribe
        for key in drop:
            s = self.subs.pop(key, None)
            try:
                if s is not None:
                    s.unregister()
            except Exception:
                pass
            with self._lock:
                self.received.pop(key, None); self.received_t.pop(key, None); self.received_meta.pop(key, None)   # [F1] 구독을 끊으면 보관본도 지운다
            if self.peer_guard is not None and key.endswith('/pose'):
                self.peer_guard.set_subscribed(key.rpartition('/')[0], False)
        for key in add:
            agent, _, item = key.rpartition('/')
            pg = self.peer_guard if item == 'pose' else None
            if pg is not None:
                pg.set_subscribed(agent, True)      # 첫 수신을 놓치지 않도록 구독 전에 표시하고, 실패하면 되돌린다
            try:
                s = describe_and_subscribe(self.node, self._peer_node(agent), item, (lambda m, a=agent, i=item: self._on_item(a, i, m)), self.log, timeout=1.0)
                if s is not None:
                    self.subs[key] = s
                else:
                    if pg is not None:
                        pg.set_subscribed(agent, False)
                    print('[JnP-RL] %s: %s 는 %s 를 광고하지 않음' % (self.robot, agent, item), flush=True)
            except Exception as e:
                if pg is not None:
                    pg.set_subscribed(agent, False)
                print('[JnP-RL] %s: %s 구독 실패(계속): %s' % (self.robot, key, e), flush=True)

    def _episode_sync(self):
        """[R5 F1, 결정 (a)] 회차 명세(/lb/episode: run_id·t0=태스크 발행 sim 초·T)를 읽어 시계를 맞춘다. 아직 없으면 첫 관측 기준(표시)으로 두고 다음 틱에 다시 본다."""
        if self._episode is not None and self._episode.get('t0') is not None:
            return
        import rospy
        try:
            ep = rospy.get_param('/lb/episode', None)
        except Exception:
            ep = None
        if isinstance(ep, dict) and ep.get('t0') is not None:
            self._episode = dict(ep)
            try:
                self._episode['T'] = float(ep['T']) if ep.get('T') is not None else None
            except Exception:
                self._episode['T'] = None
            self.core.set_t0(float(ep['t0']), 'episode')
            print('[JnP-RL] %s: 회차 시계 맞춤 t0=%.1f s(태스크 발행 시각) T=%s run_id=%s' % (self.robot, float(ep['t0']), self._episode['T'], ep.get('run_id')), flush=True)
            try:   # [R11 F4] 내가 쓴 회차 시계(t0·T·run_id)를 기록표에 남긴다 — 채점기가 회차 명세·통신 구간과 대조해 생략·불일치를 막는다
                self.log.record('meta', 'episode_sync', self.node, self.node, 0,
                                extra={'t0': float(ep['t0']), 'T': self._episode['T'], 'episode_run_id': ep.get('run_id')})
            except Exception:
                pass
        elif self.core.t0 is not None and not getattr(self, '_t0_warned', False):
            self._t0_warned = True
            print('[JnP-RL] %s: 회차 명세(/lb/episode) 없음 — 시계는 첫 관측 기준(채점 시각과 다를 수 있음)' % self.robot, flush=True)

    def tick(self, now, my_pos, state):
        """1초마다. 정책 주기(3초)마다 결정하고 state['tgt'] 를 갱신한다. 반환: 이번에 정한 새 목표 또는 None."""
        if my_pos is None:
            return None
        ev = self.core.update_progress(now, my_pos)
        if ev is not None:
            state['tgt'] = None
            self._cleared = True
            print('[JnP-RL] %s: 목표 %s' % (self.robot, '도착' if ev == 'reached' else '정체 — 포기'), flush=True)
            if self.yield_guard is not None:
                self.yield_guard.note_policy_end(ev)
        if not self.core.due(now):
            return None
        team = state.get('team') or state.get('peers', [])
        self._role = str(state.get('role', '') or '')          # [R7 F4] 그룹이 정한 역할(merged_map 발신 제한에 쓴다)
        self._discover(team, now)
        self._episode_sync()
        with self._lock:                        # [R5 F7-C] payload·시각·메타를 한 번에 복사(콜백 사이의 반쪽 갱신을 보지 않는다)
            rcv, rt, rm, grid, g_frame, g_stamp = dict(self.received), dict(self.received_t), dict(self.received_meta), self.grid, getattr(self, 'grid_frame', None), getattr(self, 'grid_stamp', None)
        obs = self.core.observation(now, my_pos, grid, rcv, self.available, set(self.providers), set(self.subs),
                                    role=state.get('role', ''), teammates=list(team), detections=self.detections, received_t=rt,
                                    received_meta=rm, t_limit=(self._episode or {}).get('T'), grid_frame=g_frame, grid_stamp=g_stamp)
        try:
            act = self.policy.decide(obs)
            new_target, on, off, add, drop = self.core.apply(obs, act, set(self.providers), set(self.subs))
        except Exception as e:
            print('[JnP-RL] %s: 정책 오류 — 이번 라운드 건너뜀: %s' % (self.robot, e), flush=True)
            return None
        if self.core.cancelled:
            # [2026-11-05] 정책이 지금 목표를 취소했다. 정체 포기와 같은 길로 정리한다. 제어기 취소는 에이전트 고리가 양보 기계의 관문을 거쳐 낸다. 방문으로 세지 않는다
            state['tgt'] = None
            self._cleared = True
            print('[JnP-RL] %s: 목표 취소 — %s' % (self.robot, getattr(act, 'cancel_why', '')), flush=True)
            if self.yield_guard is not None:
                self.yield_guard.note_policy_end('cancelled', getattr(act, 'cancel_why', ''))
        if self.yield_guard is not None:
            self.yield_guard.set_route(getattr(self.policy, 'route_limit', None))
        self._set_provide(on, off)
        self._set_subscribe(add, drop)
        if new_target is not None:
            state['tgt'] = new_target
            print('[JnP-RL] %s: 목표 → (%.2f,%.2f) 후보 %d개 %s' % (self.robot, new_target[0], new_target[1], len(obs.candidates), getattr(act, 'note', '')), flush=True)
            if self.yield_guard is not None:
                self.yield_guard.note_policy_target(new_target[0], new_target[1], getattr(act, 'note', ''))
        elif obs.need_goal:
            if self.yield_guard is not None:
                self.yield_guard.note_policy_idle(getattr(act, 'note', ''))
            self._idle_n = getattr(self, '_idle_n', 0) + 1
            if self._idle_n % 10 == 1:
                print('[JnP-RL] %s: 목표 없이 대기(%d회째) 후보 %d개 구독 %d개 %s' % (self.robot, self._idle_n, len(obs.candidates), len(self.subs), getattr(act, 'note', '')), flush=True)
        self._publish_state_items(new_target, cleared=bool(getattr(self, '_cleared', False)))
        self._cleared = False
        self._publish_action_items(act, now)
        if getattr(act, 'done', False):
            if self.yield_guard is not None:
                self.yield_guard.note_policy_end('done')
            state['tgt'] = None
            state['done'] = True            # [RL G3] 탐사 루프 종료 → explore 액션 완료 → 그룹이 task 완료로 처리
            state['mine_done'] = True
            print('[JnP-RL] %s: 정책이 탐사 끝을 선언 %s' % (self.robot, getattr(act, 'note', '')), flush=True)
        return new_target
