#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [JnP-1.0 RL G2 2026-10-31] 로봇 쪽 결정 자리 검사(ROS 없음): 자기 지도 프론티어 후보, 입력 만들기, 출력 적용, 로더. 기준 정책 검사는 test_rl_baseline_private.py 에 있다.
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import numpy as np                                   # noqa: E402
from jnp_rl_api import Action, Policy, Observation, RobotSpec   # noqa: E402,F401
from jnp_rl_frontier import candidates_from_grid     # noqa: E402
from jnp_rl_runtime import DecisionCore              # noqa: E402
from jnp_rl_loader import load_policy                # noqa: E402

FAIL = [0]


def ok(what, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + what + ((' — ' + str(detail)) if (detail and not cond) else ''), flush=True)
    if not cond:
        FAIL[0] += 1


def make_grid():
    """20×20, 0.5 m: 왼쪽 절반 자유(0), 오른쪽 절반 모름(-1), 가운데 세로 벽(100) 일부."""
    d = np.full((20, 20), -1, dtype=np.int16); d[:, :10] = 0; d[5:15, 9] = 100
    return ((0.5, 0.0, 0.0, 20, 20), d.ravel().tolist()), d


grid, d = make_grid()
cands = candidates_from_grid(grid, (1.0, 5.0))
ok('A 프론티어 후보가 있고 가까운 순', len(cands) >= 1 and all(cands[i].dist <= cands[i + 1].dist for i in range(len(cands) - 1)), [(c.x, c.y, c.size) for c in cands])
ok('A 후보는 자유 칸 위(벽·모름 아님)', all(d[int(c.y / 0.5), int(c.x / 0.5)] == 0 for c in cands))
ok('A 훑은 곳 1 m 안 후보 제외', len(candidates_from_grid(grid, (1.0, 5.0), visited=[(cands[0].src_x, cands[0].src_y)])) == len(cands) - 1 or len(cands) == 1)

core = DecisionCore('locobot_0')
obs = core.observation(10.0, (1.0, 5.0), grid, {'locobot_1/goal': (4.75, 2.0)}, {'locobot_1': ['pose', 'goal']}, set(), {'locobot_1/goal'}, role='explorer1', teammates=['locobot_1'])
ok('B 입력: 후보·need_goal·받은 정보·광고 목록·역할', obs.need_goal and len(obs.candidates) == len(cands) and obs.received['locobot_1/goal'] == (4.75, 2.0)
   and obs.available['locobot_1'] == ['pose', 'goal'] and obs.role == 'explorer1' and obs.subscribed == {'locobot_1/goal'} and obs.t == 0.0)
act = Action(choice=0)                               # 출력 적용 검사용 선택. 어느 후보든 된다
tgt, on, off, add, drop = core.apply(obs, Action(choice=act.choice, provide={'pose': True, 'goal': True}, subscribe={'locobot_1/goal', 'locobot_1/pose'}), set(), {'locobot_1/goal'})
ok('B 출력 적용: 목표·켤 항목·새 구독', tgt == (obs.candidates[act.choice].x, obs.candidates[act.choice].y) and on == ['pose', 'goal'] and off == [] and add == ['locobot_1/pose'] and drop == [])
ok('B 목표 보유 중 need_goal False', core.observation(13.0, (1.0, 5.0), grid, {}, {}, {'pose'}, set()).need_goal is False)
ok('B 결정 주기 3초', not core.due(14.0) and core.due(16.0))
ev = core.update_progress(20.0, (tgt[0] + 0.1, tgt[1]))
ok('B 도착 판정 → 훑은 곳 기록·목표 없음', ev == 'reached' and core.target is None and core.visited[-1] == tgt)
core.target = (9.0, 9.0); core.prog = (20.0, 5.0)
ok('B 45초 접근 없음 → 정체 포기', core.update_progress(70.0, (1.0, 1.0)) == 'stalled' and core.target is None)
try:
    core.apply(obs, Action(choice=99), set(), set()); ok('B 범위 밖 선택은 오류', False)
except ValueError:
    ok('B 범위 밖 선택은 오류', True)
ok('B keep: choice None 이면 목표 그대로', core.apply(obs, Action(choice=None), set(), set())[0] is None)

# C. 로더: 파일 지정
tmp = tempfile.mkdtemp(); pf = os.path.join(tmp, 'p.py')
open(pf, 'w').write('from jnp_rl_api import Policy, Action\nclass P(Policy):\n    def decide(self, obs):\n        return Action(choice=0 if obs.candidates else None, provide={"pose": True})\n')
p2 = load_policy(pf + ':P'); a2 = p2.decide(obs)
ok('C 로더 파일:클래스 → decide 동작', a2.choice == 0 and a2.provide == {'pose': True})
try:
    bad = os.path.join(tmp, 'bad.py'); open(bad, 'w').write('from jnp_rl_api import Policy\nclass Q(Policy):\n    api_version = "9.0"\n    def decide(self, obs): return None\n')
    load_policy(bad); ok('C api_version 불일치 거부', False)
except ValueError:
    ok('C api_version 불일치 거부', True)
ok('C RobotSpec 추정', RobotSpec.from_name('tb3_waffle_0').rtype == 'tb3' and RobotSpec.from_name('locobot_0').lidar_range == 16.0)

# D. [G3] 제작자 정의 항목·끝 보고·합친 지도 — 계약과 적용
import jnp_rl_registry as R
ok('D 제공 항목에 custom·done·merged_map', all(k in R.PROVIDES_ITEMS for k in ('custom', 'done', 'merged_map')) and R.PROVIDES_ITEMS['custom']['type'] == 'std_msgs/String')
xml_pv = R.provides_xml('/etri/a', ['custom', 'done', 'merged_map'])
ok('D 설명 v1.1 에 새 항목이 광고됨', 'name="custom"' in xml_pv and 'name="merged_map"' in xml_pv and 'nav_msgs/OccupancyGrid' in xml_pv)
core3 = DecisionCore('tb3_waffle_0')
obs3 = core3.observation(0.0, (1.0, 5.0), grid, {}, {}, set(), set())
act3 = Action(choice=None, provide={'custom': True, 'done': True}, custom_payload='{"frontiers": [[1, 2]]}', done=True, note='exhausted')
tgt3, on3, off3, add3, drop3 = core3.apply(obs3, act3, set(), set())
ok('D done·custom 은 목표를 바꾸지 않고 제공만 켠다', tgt3 is None and on3 == ['custom', 'done'] and act3.done and act3.custom_payload.startswith('{'))
ok('D merged_map 필드 기본 None', Action(choice=None).merged_map is None and Action(choice=None).done is False)

# E. [G3] 수색 모드 — 경유점 후보·도착 판정
cs = DecisionCore('locobot_1', mode='search'); cs.route = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]
os_ = cs.observation(0.0, (0.0, 0.0), None, {}, {}, set(), set())
ok('E 수색 후보 = 경유점 순서대로', [(c.x, c.y) for c in os_.candidates] == cs.route and os_.mode == 'search' and os_.route == cs.route)
a_ = Action(choice=0)                                # 첫 경유점으로 간다
cs.apply(os_, a_, set(), set()); ev_ = cs.update_progress(5.0, (1.1, 1.0))
os2 = cs.observation(6.0, (1.1, 1.0), None, {}, {}, set(), set())
ok('E 도착한 경유점은 후보에서 빠짐', ev_ == 'reached' and [(c.x, c.y) for c in os2.candidates] == [(2.0, 2.0), (3.0, 3.0)])
os3 = cs.observation(9.0, (1.1, 1.0), None, {}, {}, set(), set(), detections=[{'cls': 'person', 'x': 2.5, 'y': 1.0, 'dist': 1.4}])
ok('E 탐지가 입력에 들어온다', os3.detections == [{'cls': 'person', 'x': 2.5, 'y': 1.0, 'dist': 1.4}])
cs.route = []; os4 = cs.observation(12.0, (1.1, 1.0), None, {}, {}, set(), set())
ok('E 경유점 소진 → 후보 없음', os4.candidates == [])

# F. [G3-①] 정책 파일의 ROS 직접 접근 거부
from jnp_rl_loader import check_policy_source
ok('F 금지 모듈 탐지', sorted(set(check_policy_source('import rospy\nfrom tf2_ros import Buffer\nimport math\n'))) == ['rospy', 'tf2_ros'] and check_policy_source('import math\nfrom jnp_rl_api import Policy\n') == [])
badf = os.path.join(tmp, 'ros_policy.py'); open(badf, 'w').write('import rospy\nfrom jnp_rl_api import Policy, Action\nclass R(Policy):\n    def decide(self, obs): return Action(choice=None)\n')
try:
    load_policy(badf + ':R'); ok('F ROS 를 import 하는 정책 파일은 거부', False)
except ImportError:
    ok('F ROS 를 import 하는 정책 파일은 거부', True)

print('TOTAL test_rl_runtime: %d FAIL' % FAIL[0])
sys.exit(1 if FAIL[0] else 0)
