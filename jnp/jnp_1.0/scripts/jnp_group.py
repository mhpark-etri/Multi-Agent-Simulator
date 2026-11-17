#!/usr/bin/env python3
# [JnP-1.0 RL 2026-11-01] rosrun 은 devel 의 중계 스크립트(catkin_install_python)로 실행하므로 sys.path[0] 이 devel/lib/jnp 가 된다.
# 같은 폴더의 jnp_rl_* 모듈을 찾도록 이 파일의 실제 폴더를 import 경로에 올린다.
import os as _os
import sys as _sys
_SCRIPTS_DIR = _os.path.dirname(_os.path.realpath(__file__))
if _SCRIPTS_DIR not in _sys.path:
    _sys.path.insert(0, _SCRIPTS_DIR)

import rospy
from std_msgs.msg import String
import subprocess
from rosgraph import Master
import threading
import sys
import json
from std_srvs.srv import Trigger, TriggerResponse
from jnp.srv import DescriptionService, DescriptionServiceResponse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
# [JnP-0.8.2 2026-10-13] catkin devel/install 래퍼(devel/lib/jnp/<script>)에서 exec 되면 sys.path[0] 이 래퍼 폴더라
# 같은 이름의 래퍼 파일이 형제 모듈(jnp_agent 등)을 가린다 → 실제 scripts/ 폴더를 sys.path 맨 앞에 둔다(소스 직접 실행·install 공간에서도 무해).
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.realpath(__file__))
if _os.path.basename(_os.path.dirname(_here)) == 'lib':
    try:
        import rospkg as _rospkg
        _here = _os.path.join(_rospkg.RosPack().get_path('jnp'), 'scripts')
    except Exception:
        pass
if _here not in _sys.path:
    _sys.path.insert(0, _here)
from jnp_agent import JnPAgent
import actionlib
from actionlib_msgs.msg import GoalStatus
from jnp.msg import AgentActionAction, AgentActionGoal
# Task 모델은 jnp_task 모듈로 분리 (기존 클래스 정의 대체)
from jnp_task import Task, AtomicTask, SequentialCompositeTask, ParallelCompositeTask, \
    SequentialAtomicTask, ParallelAtomicTask
# 스케줄러/할당기 모듈 (교체 가능한 인터페이스 + Simple 구현)
from jnp_scheduler import (SimpleScheduler, SimpleAllocator, AffinityAllocator, RoleAllocator, assign_roles, pool_members, short_name,
                           eligible_agents)
# [JnP-0.8.2 2026-10-13] 작업 분할 경로: plans/<goal>.py(LLM-TDM 형식 계획) → plan_to_tasktree → Task 트리
import jnp_plan

class Agent:
    def __init__(self, name, goal, capability, main_instance, skills=None, busy=False, gen=0):
        self.name = name
        self.gen = gen            # [JnP-0.9.0 R3-F1] 설명을 받은 시점의 등록 세대(그룹의 _reg_gen) — kill/new 가 지나면 접속 객체는 무효
        self.short = str(name or '').strip('/').split('/')[-1]
        self.goal = goal
        self.capability = capability or ""     # baseline(부분 문자열 매칭)용
        # SimpleAllocator용 능력 집합: "lidar,camera" -> {'lidar','camera'}
        self.capability_set = {c.strip() for c in self.capability.split(',') if c.strip()}
        # [JnP-0.9.0 2026-10-18] 스킬 광고: None = 미광고(호환), [] = 없음 선언, [...] = 광고 목록. busy = 다른 미션 실행 중. role = 묶인 역할
        self.skills = list(skills) if skills is not None else None
        self.busy = bool(busy)
        self.role = None
        self.free = True
        self.execute_status = False
        self.task = None
        self.client = None    # start_task용 action client (인스턴스에 보관해야 콜백이 유지됨)
        self.main_instance = main_instance

    def setTask(self,task):
        self.task = task

    def connect(self, timeout=5.0):
        """action 서버 사전 접속(스케줄러 경로용). 성공 시 True — 죽은 agent를 멤버에서 배제."""
        self.client = actionlib.SimpleActionClient(self.name + '/AgentActionAction', AgentActionAction)
        return self.client.wait_for_server(rospy.Duration(timeout))

    def start_task(self, scheduler):
        """task start 신호(비동기, 즉시 리턴). end 신호는 scheduler.notify_end로 전달된다."""
        goal = AgentActionGoal()
        goal.command = f"execute:{self.task.name}:{self.task.goal}"
        t = self.task    # dispatch 시점의 task를 캡처
        self.client.send_goal(
            goal,
            done_cb=lambda state, result, t=t: scheduler.notify_end(
                self, t,
                state == GoalStatus.SUCCEEDED and result is not None
                and "completed" in result.result_message))

    def action(self):
        #None   
        print(f"Action ----{self.name}")
        client = actionlib.SimpleActionClient(self.name+'/AgentActionAction', AgentActionAction)
        client.wait_for_server()

        goal = AgentActionGoal()
        goal.command = "Execute some task"  # 서버에 보낼 명령

        client.send_goal(goal)
        client.wait_for_result()

        result = client.get_result()
        rospy.loginfo(f"Result: {result.result_message}")
        # if "completed" in result.result_message:
        #     self.free = True
        #     self.execute_status = False
        #     if isinstance(self.task, AtomicTask):
        #         self.task.agent=None
        #         self.task.assign_status=False
        #         if isinstance(self.task, SequentialAtomicTask):
        #             self.task.predecessors_complete = True
        #             for task1 in successors:
        #                 task1.predecessors_complete = True
        #     self.main_instance.task_allocation(self.main_instance.task_tree.root_task)
        #     self.main_instance.task_execution(self.main_instance.task_tree.root_task)


# Task/AtomicTask/SequentialCompositeTask/ParallelCompositeTask/
# SequentialAtomicTask/ParallelAtomicTask 클래스 정의는 jnp_task.py로 이동
# (상단 import 참조. addSucessor 오타, ParallelAtomicTask goal 미저장 등도 함께 수정됨)

def parse_description(description):
    """[JnP-0.9.0] 설명(description) XML → {'agent', 'goal', 'cap', 'skills'(None|list), 'busy'}; 에이전트가 아니거나 파싱 실패면 None.
    <skills> 요소 없음 = 미광고(None, 구버전 호환), 빈 요소 = 없음 선언([])."""
    try:
        root = ET.fromstring(description or '')
    except ET.ParseError:
        return None
    ag = root.find('agent')
    if ag is None:
        return None
    goal_el, cap_el, sk_el, busy_el = root.find('goal'), root.find('capability'), root.find('skills'), root.find('busy')
    skills = None
    if sk_el is not None:
        skills = [x.strip() for x in (sk_el.text or '').split(',') if x.strip()]
    from jnp_rl_registry import parse_provides, description_version   # [JnP-1.0 RL G1] <provides> 없음 = None(구판 설명)
    return {'agent': (ag.text or '').strip(), 'goal': goal_el.text if (goal_el is not None and goal_el.text) else '',
            'cap': cap_el.text if (cap_el is not None and cap_el.text) else '', 'skills': skills,
            'busy': bool(busy_el is not None and (busy_el.text or '').strip() in ('1', 'true', 'True')),
            'provides': parse_provides(root), 'desc_version': description_version(root)}


class TaskTree():
    def __init__(self):
        self.name = ""
        self.root_task = ParallelCompositeTask(name="root")
        child1=ParallelAtomicTask(name="child1", parent=self.root_task, goal="Mult-Goal")
        child1.addRequirement("lidar")
        self.root_task.add(child1)
        child2=SequentialCompositeTask(name="child2", parent=self.root_task, goal="Mult-Goal")
        self.root_task.add(child2)
        child3=SequentialAtomicTask(name="child3",parent=child2 , goal="Mult-Goal")
        child3.addRequirement("lidar")
        child3.addRequirement("camera")
        child4=SequentialAtomicTask(name="child4",parent=child2 , goal="Mult-Goal")
        child4.addRequirement("lidar")
        child4.addRequirement("camera")
        child4.addPredecessor(child3)
        child2.add(child3)
        child2.add(child4)
   

def parse_multigoal_payload(payload):
    """'goals=G1:x,y:개수|G2:x,y:개수;robots=이름:x,y|이름:x,y...' 파싱."""
    goals, robots = {}, {}
    for section in payload.split(';'):
        section = section.strip()
        if section.startswith('goals='):
            for g in section[len('goals='):].split('|'):
                parts = g.strip().split(':')
                if len(parts) >= 3:
                    x, y = parts[1].split(',')[:2]
                    goals[parts[0].strip()] = (float(x), float(y), int(parts[2]))
        elif section.startswith('robots='):
            for r in section[len('robots='):].split('|'):
                parts = r.strip().split(':')
                if not parts or not parts[0].strip():
                    continue
                if len(parts) >= 2 and ',' in parts[1]:
                    x, y = parts[1].split(',')[:2]
                    robots[parts[0].strip()] = (float(x), float(y))
                else:
                    robots[parts[0].strip()] = None    # 이름만 (좌표 미포함)
    return goals, robots


def build_multigoal_tree(payload):
    """0.8.1 다목적 이동(Mult-Goal): goal 마다 물품 N개 — 물품 1개 = 왕복 trip
    원자 task. 트리는 Parallel[ goal별 Parallel[item...] ] 로 고정 생성되고,
    할당기(MultiGoalAllocator)가 로봇 특성(시작위치-goal 거리)으로 배정한다.
    한 goal 의 물품이 소진되면 남는 로봇이 자동으로 다른 goal 물품에 재할당된다."""
    goals, _robots = parse_multigoal_payload(payload)
    root = ParallelCompositeTask(name="multigoal")
    for gname, (gx, gy, count) in goals.items():
        # goal 안도 Parallel — 멤버들이 동시에 왕복 출발 가능.
        # 목적지는 goal 자체이고, goal 점유 순서는 그룹의 진입 허가 서비스
        # (/goal_entry_<g>) 가 제어한다 — 대기점에서 순서를 기다림 (2026-08-08)
        sub = ParallelCompositeTask(name=f"{gname}[{count}]", parent=root)
        for k in range(1, count + 1):
            t = ParallelAtomicTask(name=f"{gname}.item{k}", parent=sub,
                                   goal=f"trip:{gx:.2f},{gy:.2f}@{gname}")
            t.addRequirement("lidar")
            sub.add(t)
        root.add(sub)
    return root


def _robot_speed(short):
    """로봇 속도 특성 (m/s) — ETA 계산용 (agent 쪽 _robot_speed 와 동일 기준)."""
    if 'locobot' in short:
        return 0.4
    if 'tb3' in short or 'burger' in short:
        return 0.2
    return 0.3


class MultiGoalAllocator:
    """다목적 이동 할당기: 물품(trip) task 를 로봇 특성으로 배정.
    특성 = ETA(시작위치-goal 거리 ÷ 속도, 빠른 로봇 우선). goal 소진 시 재할당은
    스케줄러가 남은 물품에 유휴 로봇을 계속 배정하는 것으로 자연히 일어난다."""

    def __init__(self, goal_pos, robot_homes):
        self.goals = goal_pos        # gname -> (x, y)
        self.homes = robot_homes     # 로봇 짧은이름 -> (x, y)

    skills_strict = False      # [V-F6] 적격 정책 — 그룹이 넣는다

    def select(self, task, agents):
        cands = eligible_agents(task, agents, self.skills_strict)     # [V-F6] free + 바쁨·스킬·능력 적격 집합 위에서 ETA 선택
        if not cands:
            return None
        gname = task.name.split('.')[0]
        gx, gy = self.goals.get(gname, (0.0, 0.0))

        def eta(a):
            short = a.name.strip('/').split('/')[-1]
            hx, hy = self.homes.get(short, (0.0, 0.0))
            return ((hx - gx) ** 2 + (hy - gy) ** 2) ** 0.5 / _robot_speed(short)
        return min(cands, key=eta)


def parse_avoidance_payload(payload):
    """'bt=cx,cy,r;routes=이름:sx,sy>tx,ty|...;robots=...' 파싱 (충돌회피 태스크)."""
    bt, routes = None, {}
    for sec in payload.split(';'):
        sec = sec.strip()
        if sec.startswith('bt='):
            v = sec[3:].split(',')
            bt = (float(v[0]), float(v[1]), float(v[2]))
        elif sec.startswith('routes='):
            for r in sec[len('routes='):].split('|'):
                name, _, rest = r.partition(':')
                se, _, ta = rest.partition('>')
                if not (name.strip() and ',' in se and ',' in ta):
                    continue
                sx, sy = [float(x) for x in se.split(',')[:2]]
                tx, ty = [float(x) for x in ta.split(',')[:2]]
                routes[name.strip()] = (sx, sy, tx, ty)
    return bt, routes


def _map_free_snap(x, y, ux, uy, grid=None, clear=0.45):
    """/map(있으면)에서 (x,y) 주변 clear(m) 원반이 free 인지 검사, 아니면
    (ux,uy) 방향으로 0.1m 씩(±15/30° 보조) 최대 2.5m 전진하며 free 로 스냅.
    ★ clear 는 로봇 반경+인플레이션(locobot 0.28+0.3≈0.58 의 실용 하한 0.45) —
    0.18 검사로는 벽에 붙은 goal 이 통과돼 플래너가 헤맴 (2026-08-09 실측).
    지도가 없으면 원좌표 반환 (무-검증 강등)."""
    import math
    if grid is None:
        return x, y
    info, data = grid
    n = max(1, int(clear / info.resolution))

    def free(px, py):
        gx = int((px - info.origin.position.x) / info.resolution)
        gy = int((py - info.origin.position.y) / info.resolution)
        if not (0 <= gx < info.width and 0 <= gy < info.height):
            return False
        # 표본 간격 ≤0.08m — 성기면 두께 0.15m 벽이 표본 사이로 새어 통과함
        stp = max(1, int(0.08 / info.resolution))
        for dx in range(-n, n + 1, stp):
            for dy in range(-n, n + 1, stp):
                if dx * dx + dy * dy > n * n:
                    continue
                ix, iy = gx + dx, gy + dy
                if 0 <= ix < info.width and 0 <= iy < info.height:
                    v = data[iy * info.width + ix]
                    if v > 50 or v < 0:
                        return False
        return True
    if free(x, y):
        return x, y
    for step in [i * 0.1 for i in range(1, 26)]:
        for ang in (0.0, 0.26, -0.26, 0.52, -0.52):
            ca, sa = math.cos(ang), math.sin(ang)
            rx, ry = ux * ca - uy * sa, ux * sa + uy * ca
            nx, ny = x + step * rx, y + step * ry
            if free(nx, ny):
                return nx, ny
    return x, y


def build_avoidance_tree(payload):
    """충돌회피 v3 (2026-08-09 지시: 병목 원은 디스플레이용 — 경유점 금지):
    로봇별 Sequential[ 통과대기(가상) → move(최종목표 한 번에) ] 의 병렬.
    '통과대기' 는 에이전트에 배정되지 않는 가상 task (requirement=virtual) —
    그룹의 위치 관찰자가 앞 로봇이 병목 구간을 '실제로 지나간 것'을 확인하면
    complete 처리해 다음 로봇의 move 가 열린다. 로봇은 자기 자리에서 대기하므로
    통로를 막지 않는다."""
    import math
    bt, routes = parse_avoidance_payload(payload)
    root = ParallelCompositeTask(name="avoidance")
    if not bt:
        return root
    cx, cy, r = bt

    def _eta(nm):
        sx, sy = routes[nm][0], routes[nm][1]
        return max(0.0, math.hypot(sx - cx, sy - cy) - r) / _robot_speed(nm)
    order = sorted(routes, key=_eta)
    moves, waits = {}, {}
    for k, name in enumerate(order):
        sx, sy, tx, ty = routes[name]
        branch = SequentialCompositeTask(name=f"cross.{name}", parent=root,
                                         goal='Avoidance')
        if k > 0:
            w = SequentialAtomicTask(name=f"wait_pass.{order[k-1]}",
                                     parent=branch, goal='virtual:wait')
            w.addRequirement("virtual")     # 어떤 에이전트도 못 받음 — 그룹이 완료 처리
            branch.add(w)
            waits[name] = w
        mv = SequentialAtomicTask(name=f"move.{name}", parent=branch,
                                  goal=f"nav:{tx:.2f},{ty:.2f}")
        mv.addRequirement("lidar")
        branch.add(mv)
        root.add(branch)
        moves[name] = mv
    root._bt_meta = {'order': order, 'moves': moves, 'waits': waits,
                     'center': (cx, cy), 'r': r,
                     'starts': {n: (routes[n][0], routes[n][1]) for n in routes},
                     'targets': {n: (routes[n][2], routes[n][3]) for n in routes}}
    return root


def build_relay_tree(payload):
    """0.8.1: 'name=x,y,z;name2=x,y,z' payload → 순차 릴레이 task tree.
    coalition이 종속되는 goal의 실체 — 협업 태스크 UI가 발행한 좌표로 만든다.
    (현 단계 agent execute()는 스텁 — 실주행 연결 시 'nav:' goal을 move_base로 해석 예정)"""
    root = SequentialCompositeTask(name="relay", parent=None, goal="Relay")
    prev = None
    n = 0
    for seg in payload.split(';'):
        seg = seg.strip()
        if not seg:
            continue
        name, eq, xyz = seg.partition('=')
        if not eq or not xyz.strip() or not name.strip():
            print(f"Group: 형식 오류 조각 무시: '{seg}' (기대: name=x,y,z)")
            continue
        n += 1
        t = SequentialAtomicTask(name=f"relay{n}.{name.strip()}", parent=root,
                                 goal=f"nav:{xyz.strip()}")
        t.addRequirement("lidar")
        if prev:
            t.addPredecessor(prev)
        root.add(t)
        prev = t
    return root


def build_object_search_tree(names):
    """분산탐색-물건찾기 고정 빌더(0.8.1 그룹 본문에서 분리, 2026-10-13): 로봇마다
    Parallel[ patrol.<n>(search, optional) , detect.<n>(service:yolov8, 가상·상시) ].
    반환 {'root','meta','dicts':{'etasks','dtasks','spars'}} — jnp_plan.build 와 같은 모양."""
    import types as _types0
    root = ParallelCompositeTask(name="object_search")
    _etasks, _dtasks, _spars = {}, {}, {}
    for _n in names:
        _par = ParallelCompositeTask(name=f"search.{_n}", parent=root)
        _t = ParallelAtomicTask(name=f"patrol.{_n}", parent=_par, goal='search')
        _t.addRequirement("lidar")
        _t.optional = True
        _par.add(_t)
        _d = ParallelAtomicTask(name=f"detect.{_n}", parent=_par, goal='service:yolov8')
        _d.addRequirement("virtual")
        _d.assign_status = True
        _d.agent = _types0.SimpleNamespace(name='/etri/' + _n)
        _par.add(_d)
        root.add(_par)
        _etasks[_n] = _t
        _dtasks[_n] = _d
        _spars[_n] = _par
    return {'root': root, 'meta': None, 'dicts': {'etasks': _etasks, 'dtasks': _dtasks, 'spars': _spars}}


def build_map_explore_tree(names, merge_host):
    """지도제작 고정 빌더(0.8.1 그룹 본문에서 분리, 2026-10-13). 트리 구조(2026-08-11 지시):
      map_explore[P] → make_maps.<robot>[P] → { navigate.<robot>[S]→explore.<robot>, merge_maps|send_map.<robot> }
    병합 호스트(merge_host) 한 대만 merge_maps, 나머지는 send_map. 병목 처리는 '탐사 이전에 끝내야 하는
    선행 작업'이므로 navigate 순차 가지 안(explore 앞)에 삽입된다 — seqbr 가 그 삽입 지점.
    반환 {'root','meta','dicts':{'etasks','mtasks','branch','seqbr'}} — jnp_plan.build 와 같은 모양."""
    import types as _types9
    root = ParallelCompositeTask(name="map_explore")
    _etasks, _mtasks, _branch, _seqbr = {}, {}, {}, {}
    for _n in names:
        _br = ParallelCompositeTask(name=f"make_maps.{_n}", parent=root)
        _sq = SequentialCompositeTask(name=f"navigate.{_n}", parent=_br, goal='')
        _t = ParallelAtomicTask(name=f"explore.{_n}", parent=_sq, goal='explore')
        _t.addRequirement("lidar")
        _t.optional = True        # 한 로봇 실패가 미션을 죽이지 않게
        _sq.add(_t)
        _br.add(_sq)
        _seqbr[_n] = _sq
        _is_host = (_n == merge_host)
        _m = ParallelAtomicTask(
            name=(f"merge_maps.{_n}" if _is_host else f"send_map.{_n}"),
            parent=_br,
            goal=('service:map_merge' if _is_host else 'publish:map'))
        _m.addRequirement("virtual")   # 에이전트 배정 대상 아님
        _m.assign_status = True        # 상시 서비스 표시
        _m.agent = _types9.SimpleNamespace(name='/etri/' + _n)
        _br.add(_m)
        root.add(_br)
        _etasks[_n] = _t
        _mtasks[_n] = _m
        _branch[_n] = _br
    return {'root': root, 'meta': None, 'dicts': {'etasks': _etasks, 'mtasks': _mtasks, 'branch': _branch, 'seqbr': _seqbr}}


def _param(name, default):
    """rosparam 읽기 — 마스터 접속 실패 등은 기본값(계획 경로 선택이 ROS 오류로 죽지 않게)."""
    try:
        return rospy.get_param(name, default)
    except Exception:
        return default


class RecruitError(RuntimeError):
    """[JnP-0.9.0 V-F2] 편성 단계(역할 할당 이후)의 실패 — 계획 변환 실패(PlanBuildError → 0.8.1 고정 빌더 대체)와 달리 대체하지 않고 그룹을 끝낸다."""


def _recruit_and_plan(group, goal, payload, **kw):
    """[JnP-0.9.0 2026-10-18] 계획 우선 편성(B): 계획 변환(역할표) → 명부 수집 → 역할마다 적격 검사·선택(assign_roles) → 선택된 로봇 접속·멤버 등록
    → 역할→로봇 바인딩으로 실행 트리(jnp_plan.build).
    파라미터: ~candidates(list-only[기본]|prefer-list|all), ~skills_strict, ~unassigned_policy(fail|skip|wait), ~recruit_timeout(벽시계 초).
    Mult-Goal 은 분산 goal 선택이 편성을 끝냈으므로 항상 list-only.
    [V-F7] 기본 후보 범위는 payload 명단(list-only). 명단 밖 자동 대체(prefer-list/all)는 명시적으로 켠다 — busy 는 '광고 시점 실행 여부'일 뿐 예약이
    아니므로, 명단이 겹치는 미션을 동시에 돌리는 운영에서는 list-only 로도 중복 배정을 막지 못한다(plans/README.md 운영 조건).
    [V-F1] 재수집·재시도 중에도 같은 로봇의 접속 객체(client)는 하나로 유지하고 광고 값만 갱신한다. 마지막 회차의 접속 실패도 배정에서 뺀다.
    [V-F2] skip 은 역할을 계획에서 빼고(prep_without_roles) 다시 만든다 — 가짜 로봇 이름을 쓰지 않는다. 편성 뒤의 트리 생성 실패는 RecruitError.
    반환 res: root·meta·dicts·plan + assignments·skipped·recruit·roles_bound·robots. 배정 불가면 {'root': None, 'unassigned': […], …}."""
    node = rospy.get_name() if rospy.core.is_initialized() else 'group'
    key = jnp_plan.goal_key(goal)
    common = dict(parse_multigoal=parse_multigoal_payload, parse_avoidance=parse_avoidance_payload, speed_fn=_robot_speed)
    prep = jnp_plan.plan_roles(goal, payload, **dict(common, **kw))        # 변환 실패(PlanBuildError)는 호출자가 호환 모드로 처리
    try:
        return _recruit_body(group, goal, payload, prep, key, common, node, **kw)
    except RecruitError:
        raise
    except Exception as _e:
        # [R2-F3] 편성 단계(파라미터·명부·접속·할당·바인딩·트리)의 모든 오류는 RecruitError — 넓은 예외 포착으로 legacy 로 새지 않는다
        raise RecruitError('편성 중 오류(%s): %s' % (type(_e).__name__, _e))


def _profile_no_skip(prep, skipped):
    """[JnP-0.9.0 2026-10-19] 프로필이 skip_fn 을 주지 않았을 때: ~unassigned_policy=skip 은 설정 오류(RecruitError)."""
    raise jnp_plan.PlanBuildError('이 프로필은 skip 정책을 지원하지 않는다(역할 %s 을 뺀 계획을 만들 수 없음)' % (list(skipped),))


def recruit_with_prep(group, goal, payload, prep, build_fn, skip_fn=None, **kw):
    """[JnP-0.9.0 2026-10-19] 프로필용 공통 모집 진입점 — 검증된 준비 계획(prep: jnp_plan._prep 와 같은 키, 역할표 roles·pool·hints·starts·
    prefer_names 포함)과 실행 트리 빌더(build_fn(goal, payload, roles_bound=…, prep=…, **kw) → {'root','meta','dicts','plan'})를 받아
    _recruit_body 의 공통 수명 로직(명부 수집·세대·잠금·접속 재시도·정책·기록)을 그대로 쓴다. 기본 5종 경로(_recruit_and_plan)는 바뀌지 않는다.
    skip_fn(prep, skipped) 이 없으면 skip 정책은 RecruitError. 계획 변환은 호출자(프로필)가 이미 끝냈으므로 PlanBuildError 도 여기서는 RecruitError.
    도메인 이름을 쓰지 않는 공통 코드다 — 프로필(미션 종류·카탈로그·트리 빌더)은 호출자가 든다."""
    node = rospy.get_name() if rospy.core.is_initialized() else 'group'
    for k0 in ('roles', 'hints', 'starts', 'prefer_names'):
        if not isinstance(prep, dict) or k0 not in prep:
            raise RecruitError('프로필 prep 에 %r 가 없음' % k0)
    try:
        key = str(prep.get('key') or jnp_plan.goal_key(goal))
    except Exception as _e:
        raise RecruitError('프로필 prep.key 가 없고 goal %r 도 기본 미션 종류가 아님: %s' % (goal, _e))
    common = dict(parse_multigoal=parse_multigoal_payload, parse_avoidance=parse_avoidance_payload, speed_fn=_robot_speed)
    try:
        return _recruit_body(group, goal, payload, prep, key, common, node,
                             builder=build_fn, skipper=(skip_fn or _profile_no_skip), **kw)
    except RecruitError:
        raise
    except Exception as _e:
        raise RecruitError('편성 중 오류(%s): %s' % (type(_e).__name__, _e))


def _reg_gen(group, name):
    """[R3-F1] 노드의 등록 세대: kill: 처리와 명부에 없는 노드의 new: 처리마다 1 씩 오른다(중복 new: 는 제외). 세대가 다른 설명·접속 객체는 재사용하지 않는다."""
    return (getattr(group, '_reg_gen', None) or {}).get(name, 0)


def _member_lock(group):
    """[R3-F1] 제거 콜백과 편성 확정이 공유하는 잠금(검사용 그룹 객체에 없으면 무잠금)."""
    lk = getattr(group, '_member_lock', None)
    if lk is None:
        import contextlib
        return contextlib.nullcontext()
    return lk


def _recruit_params(key):
    """[R2-F3] 편성 파라미터를 읽고 검증한다. 잘못된 값은 RecruitError(설정 오류 → 그룹 종료, legacy 대체 아님).
    ~recruit_timeout: 숫자(초, 0 이상, 유한). 0 = 재수집 없음(첫 수집·할당만)."""
    import math as _m
    mode = str(_param('~candidates', 'list-only'))
    if key == 'Mult-Goal':
        mode = 'list-only'
    if mode not in ('list-only', 'prefer-list', 'all'):
        raise RecruitError('설정 오류: ~candidates 값 %r — list-only|prefer-list|all 만 허용' % mode)
    strict = bool(_param('~skills_strict', False))
    policy = str(_param('~unassigned_policy', 'fail'))
    if policy not in ('fail', 'skip', 'wait'):
        raise RecruitError('설정 오류: ~unassigned_policy 값 %r — fail|skip|wait 만 허용' % policy)
    raw = _param('~recruit_timeout', 20.0)
    try:
        timeout = float(raw)
    except (TypeError, ValueError):
        raise RecruitError('설정 오류: ~recruit_timeout 값 %r — 숫자(초, 0 이상)여야 함' % (raw,))
    if _m.isnan(timeout) or _m.isinf(timeout) or timeout < 0:
        raise RecruitError('설정 오류: ~recruit_timeout 값 %r — 0 이상의 유한한 초여야 함(NaN·무한대·음수 불가)' % (raw,))
    return mode, strict, policy, timeout


def _recruit_body(group, goal, payload, prep, key, common, node, builder=None, skipper=None, **kw):
    """_recruit_and_plan 의 본문(계획 변환 뒤). 시간 계약 [R2-F2, ROUND3 §4 문구]: ~recruit_timeout 은 **미배정 역할이 남았을 때 추가 대기·재수집을
    더 시작할지 판단하는 벽시계 예산**이다(첫 루프 진입 기준). 첫 수집·할당·접속과 접속 실패 재시도(최대 4회)는 이 시작 제한의 예외다. 미배정 상태에서
    예산 소진을 확인하면 일반 대기 뒤 재수집을 더 시작하지 않는다; 대기는 남은 예산보다 길지 않다. 이미 시작한 수집·접속은 예산을 넘겨 완료될 수 있고
    그 결과는 배정에 쓸 수 있다. 전체 종료 시간 상한은 보장하지 않는다(설명 서비스 응답 대기에는 상한이 없음 — 미지원 범위).
    기록: recollect_budget_s = 예산, elapsed_s = 수집·할당·접속 루프가 끝난 시점의 경과(뒤의 트리 생성·확정·발행 제외),
    budget_exhausted = 미배정이 남아 예산 때문에 더 재수집하지 않고 끝난 경우에만 True(성공 경로에서는 경과가 예산을 넘어도 없을 수 있다).
    [R2-F1] 모집 중 kill 통보를 받은 로봇(group._killed)은 후보·접속 캐시·바인딩에서 빼고 재할당한다. 편성 확정 직전에도 다시 확인한다.
    [JnP-0.9.0 2026-10-19] builder/skipper: 프로필(recruit_with_prep)이 주는 실행 트리 빌더(jnp_plan.build 와 같은 서명)와 skip 축소 함수
    (prep_without_roles 와 같은 서명). 기본값(None)이면 기본 5종 경로 그대로다."""
    import time as _t
    builder = builder or jnp_plan.build
    skipper = skipper or jnp_plan.prep_without_roles
    mode, strict, policy, timeout = _recruit_params(key)
    group._skills_strict = strict
    needs = [r['name'] for r in prep['roles']] + (['(pool)'] if prep.get('pool') else [])
    recruit = {'mode': mode, 'skills_strict': strict, 'policy': policy, 'attempts': 0, 'candidates': [], 'rejected': {}, 'pool_rejected': {},
               'hints': prep['hints'], 'prefer_names': prep['prefer_names'], 'excluded': [], 'recollect_budget_s': timeout,
               'elapsed_s': 0.0, 'killed': []}
    if mode == 'list-only' and not prep['prefer_names'] and needs:
        # [V-F4] 빈 명단 = 모집 대상 없음(입력 오류) — 전체 명부로 확대하지 않는다
        recruit['list_empty'] = True
        recruit['rejected'] = {r: {} for r in needs}
        return {'root': None, 'meta': None, 'dicts': {}, 'unassigned': needs, 'recruit': recruit, 'prep': prep, 'source': 'plan',
                'fallback_reason': None, 'published': jnp_plan.publish_unassigned(prep, goal, node, needs, recruit),
                'note': 'list-only 인데 payload 명단이 비어 있음(입력 오류)'}
    connected = {}                        # [V-F1] 짧은 이름 → 접속된 Agent 객체(client 보유). 재수집 때 광고 값만 갱신
    excluded, t0, attempt = set(), _t.monotonic(), 0
    deadline = t0 + timeout
    MAX_CONNECT_ROUNDS = 4
    cands, ar, pool, pool_rej, missing = [], {'bound': {}, 'unassigned': [], 'reasons': {}, 'rejected': {}}, [], {}, []
    killed = getattr(group, '_killed', None)
    if killed is None:
        killed = set()
    while True:
        attempt += 1
        group._recruiting = True
        for n0 in [n for n, a in connected.items() if a.name in killed or a.gen != _reg_gen(group, a.name)]:
            del connected[n0]             # [R2-F1/R3-F1] 제거됐거나 세대가 바뀐(kill→new) 로봇의 접속 캐시는 버린다 — 새 접속 없이는 복구 없음
        cands = []
        for c in group.collect_candidates():
            if c.short in excluded or c.name in killed:
                continue
            old = connected.get(c.short)
            if old is not None and old.gen != c.gen:
                del connected[c.short]
                old = None
            if old is not None:           # 접속 객체 유지(같은 세대), 광고 갱신
                old.skills, old.capability, old.capability_set, old.busy, old.goal = c.skills, c.capability, c.capability_set, c.busy, c.goal
                cands.append(old)
            else:
                cands.append(c)
        for n0 in getattr(group, '_collect_unstable', None) or []:
            recruit.setdefault('unstable', []).append(short_name(n0))     # [R4-F1] 설명 요청 중 재등록이 반복돼 이번 회차에서 뺀 로봇
        positions = group.robot_positions([c.short for c in cands]) if prep['starts'] else {}
        ar = assign_roles(prep['roles'], cands, hints=prep['hints'], starts=prep['starts'], positions=positions,
                          speed_fn=_robot_speed, prefer_names=prep['prefer_names'], skills_strict=strict, mode=mode)
        taken = {c.short for c in ar['bound'].values()}
        pool, pool_rej = (pool_members(prep['pool'], cands, taken, prep['prefer_names'], strict, mode)
                          if prep.get('pool') else ([], {}))
        failed, dead = [], []
        for c in list(ar['bound'].values()) + pool:
            if c.name in killed:                                   # [R2-F1] 접속 전후 어느 때든 kill 통보가 왔으면 제외
                dead.append(c)
                continue
            if c.short in connected:
                continue
            if group.register_candidate(c):
                connected[c.short] = c
            else:
                failed.append(c)
        dead += [c for c in list(ar['bound'].values()) + pool if c.name in killed and c not in dead]   # 접속 중 도착한 kill
        stale = [c for c in list(ar['bound'].values()) + pool
                 if c not in dead and c.gen != _reg_gen(group, c.name)]     # [R3-F1] 접속 중 kill→new 가 지나간 로봇: 이전 접속은 무효, 새로 받아 접속해야 한다
        if failed or dead or stale:
            excluded |= {c.short for c in failed + dead}
            for c in dead:
                connected.pop(c.short, None)
                recruit['killed'].append(c.short)
            for c in stale:
                connected.pop(c.short, None)
                recruit.setdefault('reregistered', []).append(c.short)
            group.member_list[:] = [a for a in group.member_list if a.short not in excluded and a not in stale]
            if attempt < MAX_CONNECT_ROUNDS:
                if stale and not (failed or dead):
                    print(f"[RECRUIT] 재등록(kill→new) 로봇 {sorted(c.short for c in stale)} — 새 설명·접속으로 재할당", flush=True)
                    continue
                print(f"[RECRUIT] 제외 — 접속 실패 {sorted(c.short for c in failed)}, 제거 통보 {sorted(c.short for c in dead)} — 재할당", flush=True)
                continue
            # [V-F1] 마지막 회차의 접속 실패·제거·재등록: 그 후보를 배정·풀에서 빼고 배정 불가로 돌린다(성공 경로로 가지 않는다)
            for r, a in list(ar['bound'].items()):
                if a.short in excluded or a in stale:
                    del ar['bound'][r]
                    ar['unassigned'].append(r)
                    ar['reasons'][r] = {'hint': prep['hints'].get(r), 'eligible': 0,
                                        ('killed' if a.name in killed else ('reregistered' if a in stale else 'connect_failed')): a.short}
            pool = [p for p in pool if p.short not in excluded and p not in stale]
        missing = list(ar['unassigned']) + (['(pool)'] if prep.get('pool') and not pool else [])
        if missing and policy == 'wait':
            remaining = deadline - _t.monotonic()
            if remaining > 0:
                nap = min(2.0, remaining)                          # [R2-F2] 대기는 남은 예산보다 길지 않다
                print(f"[SCHED] 배정 불가(재수집 예산 {remaining:.1f}s 남음): {missing} — {nap:.1f}s 뒤 명부 재수집", flush=True)
                group.publish_status('forming', None, note='배정 불가 대기: %s' % missing)
                _t.sleep(nap)                                      # 벽시계 — 시뮬 시계가 멈춰도 예산이 흐른다
                if _t.monotonic() < deadline:                      # 예산 안에서만 새 재수집을 시작한다(시작한 수집은 예산을 넘겨 끝나도 유효)
                    continue
            recruit['budget_exhausted'] = True
        break
    group._recruiting = False
    recruit.update({'attempts': attempt, 'elapsed_s': round(_t.monotonic() - t0, 3),
                    'candidates': [{'name': c.short, 'skills': c.skills, 'cap': sorted(c.capability_set), 'busy': c.busy} for c in cands],
                    'rejected': ar['rejected'], 'pool_rejected': pool_rej, 'excluded': sorted(excluded),
                    'reasons': {r: ar['reasons'].get(r, {}) for r in ar['reasons']}})
    skipped = []
    prep_exec = prep
    if missing:
        can_skip = policy == 'skip' and '(pool)' not in missing
        if can_skip:
            sk = jnp_plan.skippable_roles(prep)
            blockers = {r: (sk.get(r) if r in sk else '역할표에 없음') for r in missing if (r not in sk or sk.get(r))}
            if blockers:
                can_skip = False
                recruit['skip_blocked'] = blockers
        if not can_skip:
            group.member_list[:] = []
            return {'root': None, 'meta': None, 'dicts': {}, 'unassigned': missing, 'recruit': recruit, 'prep': prep, 'assign': ar,
                    'source': 'plan', 'fallback_reason': None, 'published': jnp_plan.publish_unassigned(prep, goal, node, missing, recruit)}
        skipped = list(missing)
        try:
            prep_exec = skipper(prep, skipped)     # [V-F2] 건너뛴 역할을 뺀 계획 — 가짜 로봇 없음 ([JnP-0.9.0 2026-10-19] 프로필이면 skip_fn)
        except jnp_plan.PlanBuildError as e:
            raise RecruitError('skip 정책으로 역할 %s 을 빼면 실행할 계획이 없음: %s' % (skipped, e))
        recruit['skipped'] = skipped
    roles_bound = {r: a.short for r, a in ar['bound'].items()}
    try:
        res = builder(goal, payload, roles_bound=roles_bound, prep=prep_exec, **dict(common, **kw))   # [JnP-0.9.0 2026-10-19] 프로필이면 build_fn
    except jnp_plan.PlanBuildError as e:
        raise RecruitError('편성 뒤 실행 트리 생성 실패(대체 없음): %s' % e)    # [V-F2] 정책 실패는 legacy 로 우회하지 않는다
    members = []
    for r, a in ar['bound'].items():
        a.role = r
        members.append(a)
    for p0 in pool:
        p0.role = p0.role or 'pool'
        if all(m.name != p0.name for m in members):
            members.append(p0)
    bad = [m.short for m in members if getattr(m, 'client', None) is None]
    if bad:
        raise RecruitError('접속 객체가 없는 멤버가 편성에 남음: %s' % bad)       # [V-F1] 불변식 — 모든 멤버는 접속된 객체
    with _member_lock(group):
        # [R3-F1] 확정은 제거 콜백과 같은 잠금 안에서: 잠금 전에 끝난 kill/new 는 여기서 보이고, 잠금 뒤에 온 kill 은 기존 제거 경로(멤버 목록 제자리 갱신)로 반영된다
        dead = [m.short for m in members if m.name in killed]
        if dead:
            raise RecruitError('편성 확정 직전에 제거 통보를 받은 로봇이 있음: %s — 편성 종료' % dead)   # [R2-F1] 되살리지 않는다
        stale = [m.short for m in members if m.gen != _reg_gen(group, m.name)]
        if stale:
            raise RecruitError('편성 확정 직전에 재등록(kill→new)된 로봇이 있음: %s — 이전 접속은 무효, 편성 종료' % stale)
        group.member_list[:] = members
        group._role_bind = {r: a for r, a in ar['bound'].items()}
        group._recruited = True
    res['assignments'] = ([{'role': r, 'robot': a.short, 'reason': ar['reasons'].get(r, {})} for r, a in ar['bound'].items()]
                          + [{'role': None, 'robot': p0.short, 'reason': {'pool': True}} for p0 in pool]
                          + [{'role': r, 'robot': '', 'reason': {'skipped': True}} for r in skipped])
    res['skipped'] = skipped
    res['recruit'] = recruit
    res['roles_bound'] = roles_bound
    res['robots'] = sorted({a.short for a in members})
    res['source'] = 'plan'
    res['fallback_reason'] = None
    res['plan']['roles_all'] = [r['name'] for r in prep['roles']]
    for row in res['assignments']:
        why = row['reason']
        tag = ('풀' if why.get('pool') else ('건너뜀' if why.get('skipped') else
               ('힌트' if why.get('hinted') else ('대체' if why.get('substituted') else '선택'))))
        print(f"[SCHED] 편성: {row['role'] or 'pool'} → {row['robot'] or '(없음)'} [{tag}] {why}", flush=True)
    res['published'] = jnp_plan.publish(res, goal, node)
    return res


def _plan_or_legacy(goal, payload, legacy, group=None, **kw):
    """[JnP-0.8.2 2026-10-13] 기본 협업 태스크의 트리 생성 진입점.
    ~plan_mode(기본 true): plans/<goal>.py 계획을 payload 로 바인딩 → plan_to_tasktree(canonical TaskTree) → jnp_plan 어댑터
    (반환 전 계약·완전성 검사) → Task 트리. 계획·canonical·바인딩은 콘솔 [PLAN] 과 rosparam /jnp/plan/<group> 에 남긴다.
    계획 경로가 실패하면(계획 파일 없음·변환 실패·계약/완전성 검사 실패·그 밖의 예외) 사유를 남기고 0.8.1 고정 빌더(legacy)로
    대체한다 — 호환 모드. ~plan_strict=true(개발·CI)면 대체하지 않고 예외를 그대로 올린다.
    [JnP-0.9.0] group 을 주고 ~recruit_mode=skills(기본)면 _recruit_and_plan 으로 간다. 편성 단계의 실패(배정 불가·RecruitError)는
    대체가 아니라 그룹 종료다(_terminate). 호환 모드(legacy 대체)로 갈 때 멤버가 없으면 0.8.2 방식(goal 매칭 등록)으로 모으며,
    그 뒤 'new:' 등록 게이트와 정족수 대기는 recruit_mode 를 goal 로 바꿔 0.8.2 와 같게 한다.
    반환 {'root','meta','dicts','source'('plan'|'legacy'),'published','fallback_reason'}."""
    node = rospy.get_name() if rospy.core.is_initialized() else 'group'
    strict = bool(_param('~plan_strict', False))
    reason = None
    if _param('~plan_mode', True):
        try:
            if group is not None and str(_param('~recruit_mode', 'skills')) == 'skills':
                try:
                    res = _recruit_and_plan(group, goal, payload, **kw)
                except RecruitError as _re:
                    _terminate(group, goal, '편성 실패: %s' % _re)
                    return {'root': None, 'meta': None, 'dicts': {}, 'source': 'plan', 'fallback_reason': None, 'published': False,
                            'recruit_error': str(_re)}
                if res.get('unassigned'):
                    _fail_unassigned(group, goal, res)
                return res
            res = jnp_plan.build(goal, payload, parse_multigoal=parse_multigoal_payload,
                                 parse_avoidance=parse_avoidance_payload, speed_fn=_robot_speed, **kw)
            res['source'] = 'plan'
            res['fallback_reason'] = None
            res['published'] = jnp_plan.publish(res, goal, node)
            return res
        except Exception as _e:
            if strict:
                raise
            reason = '%s: %s' % (type(_e).__name__, _e)
            rospy.logwarn('[PLAN] 작업 분할 실패(%s) — 0.8.1 고정 빌더로 대체: %s', goal, reason)
            print(f'[PLAN] 작업 분할 실패({goal}) — 0.8.1 고정 빌더로 대체: {reason}', flush=True)
    else:
        reason = 'plan_mode=false'
    if group is not None and getattr(group, 'recruit_mode', 'skills') == 'skills':
        # 호환 모드: 이후 편성·등록·정족수는 0.8.2(goal 모드)와 같게 전환한다(부분 편성 잔여 멤버는 버린다)
        print('[RECRUIT] 호환 모드로 전환(recruit_mode=goal): goal 매칭으로 멤버 수집', flush=True)
        group.recruit_mode = 'goal'
        group.member_list[:] = []
        group._role_bind = None
        group._recruited = False
        group.search()
    res = legacy()
    if not isinstance(res, dict):
        res = {'root': res, 'meta': getattr(res, '_bt_meta', None), 'dicts': {}}
    res['source'] = 'legacy'
    res['fallback_reason'] = reason
    res['published'] = jnp_plan.publish_fallback(goal, reason, node, res['root'])
    return res


def _terminate(group, goal, note):
    """[JnP-0.9.0] 편성 실패로 그룹을 끝낸다: 상태 failed(note) 발행 → coalition 이면 해체, 아니면 종료.
    검사용 그룹 객체가 terminate(note) 를 가지면 그것을 부른다(프로세스를 끝내지 않음)."""
    print('[SCHED] ' + note, flush=True)
    group.publish_status('failed', None, note=note)
    term = getattr(group, 'terminate', None)
    if callable(term):
        term(note)
        return
    if str(_param('~group_type', 'team')) == 'coalition':
        group.dissolve('편성 실패', None)
    os._exit(1)


def _fail_unassigned(group, goal, res):
    """[JnP-0.9.0] 배정 불가(policy=fail / skip 불가 / wait 시간 초과 / 빈 명단): 사유를 남기고 그룹을 끝낸다."""
    miss = res.get('unassigned') or []
    rec = res.get('recruit') or {}
    rej = rec.get('rejected') or {}
    if rec.get('list_empty'):
        detail = 'list-only 인데 payload 명단이 비어 있음(입력 오류)'
    else:
        detail = '; '.join('%s: %s' % (r, ', '.join('%s=%s' % (k, v) for k, v in (rej.get(r) or {}).items()) or '후보 없음') for r in miss)
        if rec.get('skip_blocked'):
            detail += '; skip 불가: %s' % rec['skip_blocked']
    # [V-F8] 탐욕(선언 순) 배정에서 후보를 확보하지 못한 것 — 전체 배정 불가능의 증명은 아니다
    note = '배정 불가: 역할 %s 에 자격 로봇을 확보하지 못함(역할 선언 순 탐욕 배정; %s)' % (miss, detail)
    _terminate(group, goal, note)


class JnPGroup:

    def __init__(self, node_name='jnpgroup', topic_name='/jnp_agent_join_event', rate=1):
        # Node name 초기화
        self.node_name = node_name
        print("Group: =========================> {0}".format(node_name))
        # Publisher 객체 초기화
        self.publisher = rospy.Publisher(topic_name, String, queue_size=10)
        self.subcriber = rospy.Subscriber('/jnp_agent_join_event', String, self.discovery_callback)
        self.agent_list = [ ]
        self.member_list = [ ]
        self._killed = set()      # [JnP-0.9.0 R2-F1] kill 통보를 받은 노드(새 new: 통보가 오면 해제)
        self._reg_gen = {}        # [R3-F1] 노드별 등록 세대: kill: 처리와 '명부(agent_list)에 없는 노드'의 new: 처리마다 +1
                                  #   (이미 명부에 있는 노드의 중복 new: 는 세대를 올리지 않음 — 에이전트는 기동 때 new: 를 3번 보낸다). 세대가 바뀐 접속 객체는 재사용하지 않는다
        self._member_lock = threading.Lock()   # [R3-F1] 제거 콜백 ↔ 편성 확정의 공유 잠금
        self.flag_init_node = False
        self.goal = "Relay"

        # 전송 주기 설정
        #self.rate = rospy.Rate(rate)
        self.rate1=rate

    def setTaskTree(self,tasks):
        self.task_tree = tasks

    def start(self):
        #rospy.init_node(self.node_name, anonymous=True)
        # no
        print("Group start ===> 1")
        rospy.init_node(self.node_name)
        self.flag_init_node = True
        namespace = rospy.get_namespace()
        node_name = rospy.get_name() # namespace is include in node_name
        pure_node_name = node_name.replace(namespace, "", 1)
        #print("ns = {0} node_name = {1} pure name = {2}".format(namespace, node_name,pure_node_name))
        self.node_name = node_name
        #self.node_name = rospy.get_name()
        print("Group start ===> 2")
        # 0.8.1: JnP 모니터용 상태 발행 (한 줄 JSON) — init_node 이후 생성
        self.status_pub = rospy.Publisher('/jnp/status', String, queue_size=5)
        # ★ daemon 필수: 비데몬이면 input() 대기 스레드가 프로세스 종료를 막아
        #   실패 경로에서 좀비 그룹(서비스 응답하는 유령)이 되어 시스템 전체를 막는다
        thread = threading.Thread(target=self.input_thread, daemon=True)
        thread.start()
        print("Group start ===> 3")
        self.service = rospy.Service(self.node_name+'/description_service', DescriptionService, self.handle_description_request)
        self.rate = rospy.Rate(self.rate1)
        advertise_count=0
        print("Group start ===> 4")
        try:
            while not rospy.is_shutdown():
            #message = "Hello from Talker class! Time: %s" % rospy.get_time()
                if advertise_count > 2: #send 3 times
                    break
                message = f"new:{node_name}"
                #rospy.loginfo(message)
                print("Group: =====> Send Message[{0}]".format(message))
                self.publisher.publish(message)
                advertise_count = advertise_count + 1
                self.rate.sleep()
        except rospy.exceptions.ROSInterruptException:
            rospy.loginfo("Node shutting down.")

    def register_member(self, node, description):
        """description XML을 파싱해 goal이 맞고 action 서버가 살아있는 agent를 member로 등록.
        search()와 discovery_callback() 양쪽에서 호출된다.
        (기존 코드는 search()에서만 등록해서, discovery_callback이 먼저 발견한
        agent는 agent_list에만 들어가고 member가 영영 못 되는 구멍이 있었음)"""
        try:
            d = parse_description(description)
            if d is None:
                return                      # group 등 agent가 아닌 노드
            goal_text, cap_text = d['goal'], d['cap']
            print(f"Group Goal--->: {goal_text} : {self.goal}")
            # 'Any' 에이전트도 모집 대상 (handle_task_event 의 참여 판정과 대칭)
            if not (self.goal in goal_text or goal_text.strip() == 'Any'):
                return
            if any(a.name == node for a in self.member_list):
                return                      # 중복 등록 방지
            if getattr(self, '_task_done', False):
                print(f"Group: 등록 거부(임무 완료) — {node}", flush=True)
                return                      # 완료 그룹 유령 멤버 방지 (등록 시점 재검사)
            allowed = getattr(self, 'allowed_members', None)
            if allowed is not None and node.strip('/').split('/')[-1] not in allowed:
                return                      # 이 그룹의 로봇 명단이 아님 (goal별 그룹)
            jnp_agent = Agent(name=node, goal=goal_text, capability=cap_text, main_instance=self,
                              skills=d['skills'], busy=d['busy'])
            if jnp_agent.connect():         # action 서버 사전 접속(5s) — 죽은 agent 배제
                if getattr(self, '_task_done', False):
                    print(f"Group: 등록 거부(접속 중 임무 완료) — {node}", flush=True)
                    return                  # connect 동안 완료된 경우 — 최종 봉쇄
                self.member_list.append(jnp_agent)
                print(f"Group Member registered ---> {node} ({cap_text})")
            else:
                rospy.logwarn(f"{node}: action server not available; excluded")
        except (ET.ParseError, AttributeError, TypeError) as e:
            rospy.logerr(f"Error parsing XML: {e}")

    def discovery_callback(self, msg):
        rospy.loginfo("Received message: %s", msg.data)
        message= msg.data
        if message.startswith("dissolve:"):
            # 0.8.1: 수동 해제 명령 (Monitor 의 'Group 해제' 버튼 등)
            if message.split(":", 1)[1].strip() == self.node_name:
                print("Group: 해제 명령 수신", flush=True)
                self.dissolve('사용자 해제 명령')
            return
        if message.startswith("mgjoin:"):
            # 그룹 간 이적 영입: mgjoin:<goal라벨>:<agent노드>:<x,y> — 내 goal 이면 영입
            try:
                _, glabel, node, xy = message.split(':', 3)
                glabel, node = glabel.strip(), node.strip()
                if glabel not in getattr(self, '_goals', {}):
                    return                  # 다른 goal 그룹 대상
                if getattr(self, '_task_done', False):
                    # 완료된 그룹 — 영입 거부. 완료·최종방출 '직후'에 도착한
                    # 이적(mgjoin)이 등록되면 아무도 다시 방출하지 않아
                    # 유령 멤버로 남는다 (2026-08-08 실측: locobot_1 잔류)
                    print(f"Group: 이적 영입 거부(임무 완료) — {node}", flush=True)
                    return
                short = node.strip('/').split('/')[-1]
                if getattr(self, 'allowed_members', None) is not None:
                    self.allowed_members.add(short)
                if hasattr(self, '_mg_alloc') and hasattr(self._mg_alloc, 'homes') and ',' in xy:
                    hx, hy = [float(v) for v in xy.split(',')[:2]]
                    self._mg_alloc.homes[short] = (hx, hy)
                if node not in self.agent_list:
                    self.agent_list.append(node)
                desc = self.get_description(node)
                if desc:
                    self.register_member(node, desc)   # 중복 등록은 내부에서 차단
                if any(a.name == node for a in self.member_list):          # [V-F10] 실제 등록됐을 때만 영입 로그
                    print(f"Group: 이적 영입 {short} → {self.node_name}", flush=True)
                else:
                    print(f"Group: 이적 영입 거부 {short} (goal 불일치·접속 실패 또는 명단 밖)", flush=True)
                if hasattr(self, '_scheduler'):
                    self._scheduler.wake()  # 진행 중 스케줄러 즉시 재배정
            except (ValueError, IndexError) as e:
                rospy.logwarn('mgjoin 처리 실패: %s', e)
            return
        if message.startswith(("mgrelease:", "mgbid:", "mgassign:", "task:")):
            return                          # 에이전트용/이적 통보 — 그룹은 무시
        node_name = msg.data.split(":")[1]
        if message.startswith("kill:") and hasattr(self, '_killed'):
            with _member_lock(self):
                self._killed.add(node_name)        # [R2-F1] 제거 통보의 최종성 — 모집 중이면 편성이 이 집합을 보고 되살리지 않는다
                if hasattr(self, '_reg_gen'):
                    self._reg_gen[node_name] = self._reg_gen.get(node_name, 0) + 1   # [R3-F1] 세대 교체 — 이전 접속 객체 무효
                # 멤버에서도 제거(제자리 갱신) — 편성 확정 뒤에 온 kill 도 같은 경로로 반영된다
                self.member_list[:] = [a for a in self.member_list if a.name != node_name]
        if node_name not in self.agent_list:
            if node_name != self.node_name:
                if message.startswith("new:"):
                    print("--->{0}".format(node_name))
                    if hasattr(self, '_killed'):
                        with _member_lock(self):
                            self._killed.discard(node_name)   # 새 등록 통보 = 다시 후보가 될 수 있음
                            if hasattr(self, '_reg_gen'):
                                self._reg_gen[node_name] = self._reg_gen.get(node_name, 0) + 1   # [R3-F1] '제거 해제' ≠ '이전 접속 유효': 접속은 새로
                    description = self.get_description(node_name)
                    self.agent_list.append(node_name)
                    # [JnP-0.9.0] skills 편성(기본)에서는 멤버가 할당 결과로 정해진다 — 발견만으로 등록하지 않는다(goal 모드만 등록)
                    if description and getattr(self, 'recruit_mode', 'skills') == 'goal':
                        self.register_member(node_name, description)  # 발견 즉시 member 등록
        else:
            if message.startswith("kill:"):
                self.agent_list.remove(node_name)
                # member에서도 제거 (죽은 agent에 task가 가지 않도록)
                # ★ 제자리 갱신([:]) — 스케줄러가 들고 있는 리스트 객체와 동일해야 반영된다
                self.member_list[:] = [a for a in self.member_list if a.name != node_name]

    def handle_description_request(self, req):
    # 요청에서 XML 데이터 가져오기
        xml_data = req.input_xml
        rospy.loginfo("Received Description Request")
    # XML 데이터 처리 및 응답 설정 (이 예제에서는 단순한 문자열 응답만을 제공합니다)
        response = DescriptionServiceResponse()
        #response.output_response = "XML data processed successfully"
        response.output_xml = "<data><item>Sample XML content</item><group>"+self.node_name+"</group><goal>"+self.goal+"</goal></data>"
        return response

    # def get_description(self,node_name):
    #     rospy.wait_for_service(node_name+'/description_service')
    #     try:
    #         get_xml = rospy.ServiceProxy(node_name+'/description_service', DescriptionService)
    #         response = get_xml()
    #         #print("Get XML:{0}".format(response))
    #     #return response.output_xml
    #     except rospy.ServiceException as e:
    #         print("Service call failed: %s" % e)
    def get_description(self,node_name):
        # ★ 타임아웃 필수: join 토픽 퍼블리셔에는 description 서비스가 없는 일회성
        #   노드(GUI 의 rostopic pub 등)도 섞인다 — 무제한 대기면 그룹이 영원히 멈춘다
        try:
            rospy.wait_for_service(node_name+'/description_service', timeout=3.0)
        except rospy.ROSException:
            print("Group: description service timeout: %s" % node_name)
            return None
        try:
            get_xml = rospy.ServiceProxy(node_name+'/description_service', DescriptionService)
            response = get_xml()
            print("Get XML:{0}".format(response))
            return response.output_xml
        except rospy.ServiceException as e:
            print("Service call failed: %s" % e)
            return None

    def search(self):
        topic_name='/jnp_agent_join_event'
        master = Master('/rospy')
        # System state format: [publishers, subscribers, services]
        pub_list = master.getSystemState()[0]
        nodes = []
        print("Group Search Start 1")
        for topic, publishers in pub_list:
            print(f"Group Search Start 2: {topic} : {topic_name}")
            # [JnP-0.8.1 2026-10-06] 디버그 잔재 Path("/root/empty_file1.txt").touch() 제거 —
            # 비root NUC 에서 PermissionError 로 그룹이 죽는다
            if topic == topic_name:
                print(f"Group Search Start 2-1 : {publishers} : {self.node_name}")
                #because before init_node(which in start()), my node is not in publishers list.
                if self.flag_init_node:
                    print(f"Group Search Start 2-1-1 : {publishers}", flush=True)
                    if self.node_name in publishers:
                        print(f"Group Search Start 2-2 : {publishers}", flush=True)
                        publishers.remove(self.node_name)
                print(f"Group Search Start 2-3 : {publishers}",flush=True)
                nodes.extend(publishers) #publishers --> list , type of member of publishers --> string
                print("Group Search Start 3")
                for node in publishers:
                    description=self.get_description(node)
                    if not description:              # 서비스 실패(None) 방어
                        continue
                    if node not in self.agent_list:
                        self.agent_list.append(node)
                    self.register_member(node, description)   # 공용 등록 (중복은 내부에서 걸러짐)
                print("Group Search Start 4")
                set_A = set(self.agent_list)
                set_B = set(publishers)
                set_C = set(self.member_list)
                self.agent_list = list(set_B.intersection(set_A))
                self.member_list = list(set_C)
                print("-------------   Group Output -------")
                #print(f"Member={self.member_list}")
                print(", ".join(agent.name for agent in self.member_list))
                # [JnP-0.8.1 2026-10-06] 디버그 잔재 Path("/root/empty_file.txt").touch() 제거
        return nodes

    # ── [JnP-0.9.0 2026-10-18] 계획 우선 편성(B): 명부 수집 → 역할 할당 → 선택된 로봇만 멤버 ──
    def collect_candidates(self):
        """명부: join 토픽의 발행자(에이전트) 전부의 설명을 받아 후보 Agent(미접속) 목록으로. goal 필터 없음(스킬·능력으로 고른다)."""
        topic_name = '/jnp_agent_join_event'
        self._collect_unstable = []        # [JnP-0.9.0 2026-10-19 R5-N1] 이전 회차의 unstable 잔여를 비운다(master 실패로 조기 반환해도 남지 않게)
        try:
            pub_list = Master('/rospy').getSystemState()[0]
        except Exception as e:
            rospy.logwarn('명부 수집 실패(master): %s', e)
            return []
        out = []
        unstable = []
        for topic, publishers in pub_list:
            if topic != topic_name:
                continue
            for node in publishers:
                if node == self.node_name:
                    continue
                d, gen = None, None
                for _try in range(2):
                    # [R4-F1] 설명 요청 '전'의 등록 세대를 잡아 두고, 응답 뒤 세대가 그대로일 때만 그 응답을 그 세대의 설명으로 받는다.
                    # 요청 도중 kill→new 가 처리되면(세대 변경) 이전 응답은 버리고 한 번만 다시 요청한다(무제한 재수집 없음). 세대 조회는 잠금 없이 짧게.
                    g0 = _reg_gen(self, node)
                    desc = self.get_description(node)
                    parsed = parse_description(desc) if desc else None
                    if _reg_gen(self, node) == g0:
                        d, gen = parsed, g0
                        break
                    print('[RECRUIT] %s: 설명 요청 중 재등록(세대 %d→%d) — 이전 응답 폐기%s' % (
                        node, g0, _reg_gen(self, node), ', 다시 요청' if _try == 0 else ', 이번 회차 제외'), flush=True)
                if gen is None:
                    unstable.append(node)
                    continue
                if d is None:
                    continue
                if node not in self.agent_list:
                    self.agent_list.append(node)
                out.append(Agent(name=node, goal=d['goal'], capability=d['cap'], main_instance=self,
                                 skills=d['skills'], busy=d['busy'], gen=gen))
        self._collect_unstable = unstable
        out.sort(key=lambda a: a.short)
        print('[RECRUIT] 명부 %d대: %s' % (len(out), ', '.join(
            '%s(skills=%s cap=%s%s)' % (a.short, ','.join(a.skills) if a.skills is not None else '미광고',
                                        ','.join(sorted(a.capability_set)), ' busy' if a.busy else '') for a in out)), flush=True)
        return out

    def robot_positions(self, names, timeout=1.0):
        """ETA 계산용 현재 위치: /<robot>/odom 을 짧게 기다린다(없으면 생략 — 선택 키에서 불이익 없음)."""
        pos = {}
        try:
            from nav_msgs.msg import Odometry
        except Exception:
            return pos
        for n in names:
            try:
                od = rospy.wait_for_message('/%s/odom' % n, Odometry, timeout=timeout)
                pos[n] = (od.pose.pose.position.x, od.pose.pose.position.y)
            except Exception:
                pass
        return pos

    def register_candidate(self, agent):
        """할당된 후보를 멤버로: action 서버 접속(5 s) 확인. 실패하면 False(호출자가 제외하고 재할당).
        [V-F1] 같은 이름의 멤버가 이미 있어도 '이 객체'가 접속돼 있어야 True — 다른 객체면 접속한 뒤 교체한다."""
        if getattr(self, '_task_done', False):
            return False
        if getattr(agent, 'client', None) is None and not agent.connect():
            rospy.logwarn(f"{agent.name}: action server not available; excluded")
            return False
        if not any(a is agent for a in self.member_list):
            self.member_list[:] = [a for a in self.member_list if a.name != agent.name] + [agent]
            print(f"Group Member registered ---> {agent.name} (skills={agent.skills} cap={sorted(agent.capability_set)})", flush=True)
        return True

    def publish_status(self, state, root_task=None, note=''):
        """0.8.1: JnP 모니터용 상태 발행 — coalition/멤버/task tree 를 한 줄 JSON으로.
        state: forming | running | success | failed | dissolved"""
        def node(t):
            d = {'name': t.name, 'goal': getattr(t, 'goal', '') or ''}
            if isinstance(t, AtomicTask):
                ag = getattr(t, 'agent', None)
                d['kind'] = 'atomic'
                d['agent'] = getattr(ag, 'name', '') if ag else ''
                d['state'] = ('done' if t.complete
                              else ('running' if t.assign_status else 'wait'))
            else:
                d['kind'] = 'seq' if isinstance(t, SequentialCompositeTask) else 'par'
                d['state'] = 'done' if t.complete else ''
                d['children'] = [node(c) for c in t.subtasks]
            return d
        msg = {'group': self.node_name, 'goal': self.goal, 'state': state, 'note': note,
               'mission_id': getattr(self, '_mission_id', ''),   # [JnP-0.8.1 2026-10-07] 미션·라운드 식별
               'run_id': jnp_plan.current_run_id() or '',          # [JnP-0.8.2 2026-10-14] /jnp/plan 기록과 같은 회차 id (Monitor 결합 키)
               'members': [{'name': a.name, 'cap': sorted(a.capability_set),
                            'skills': (list(a.skills) if getattr(a, 'skills', None) is not None else None),   # [0.9.0] None=미광고
                            'role': getattr(a, 'role', None), 'busy': bool(getattr(a, 'busy', False))}
                           for a in self.member_list],
               'tree': node(root_task) if root_task is not None else None,
               'stamp': rospy.get_time()}
        try:
            self.status_pub.publish(json.dumps(msg, ensure_ascii=False))
        except Exception as e:
            rospy.logwarn('status publish failed: %s', e)

    def dissolve(self, reason='goal 도달', root_task=None):
        """0.8.1 coalition 해체: kill 발행(멤버 에이전트들의 group_list 청소) → 그룹 노드
        종료. 성공(goal 도달)뿐 아니라 실패 시에도 호출된다 — 안 하면 좀비 그룹이 되어
        이후 coalition 형성을 영구히 막는다. 에이전트는 살아남아 다음 task 를 기다린다.
        root_task 를 넘기면 해체 후에도 Monitor 에 최종 트리가 남는다."""
        self._dissolving = True     # team 유지-루프의 잔여 상태 발행 차단 (해체 후 success 역전 레이스)
        if root_task is None:
            root_task = getattr(self, '_last_root', None)
        self.publish_status('dissolved', root_task, note=f'{reason} — 그룹 해제')
        message = f"kill:{self.node_name}"
        for _ in range(2):              # 유실 대비 2회
            self.publisher.publish(message)
            rospy.sleep(0.7)
        print(f"Group: coalition dissolved ({reason})")
        sys.stdout.flush()
        # master 등록 해제(노드/서비스)까지 마친 뒤 종료 — 안 하면 rosnode list에
        # 유령 등록이 남아 다음 그룹 판별을 오염시킨다
        rospy.signal_shutdown('coalition dissolved (goal reached)')
        import time as _time
        # [JnP-0.8.1 2026-10-07] 고정 1 s 대기 대신 master 에서 이 노드의 등록이 실제로 사라졌는지 확인하고(최대 5 s)
        # 종료한다 — 부하가 높으면 1 s 안에 unregister 가 끝나지 않아 유령 등록이 남고, 미션 관리자의
        # 소멸 확인(재공지 조건)이 막힌다(드라이런에서 재현).
        _t0 = _time.time()
        while _time.time() - _t0 < 5.0:
            try:
                Master(self.node_name).lookupNode(self.node_name)
            except Exception:
                break                   # 등록 해제됨(또는 master 조회 불가 — 더 기다릴 이유가 없다)
            _time.sleep(0.2)
        os._exit(0)                     # input_thread(비데몬)에 막히지 않는 확정 종료

    def input_thread(self):
        while not rospy.is_shutdown():
        # 사용자 입력 대기
            try:                            # [JnP-0.8.1 2026-10-06] roslaunch(stdin 없음)에서 EOFError 스택 출력 방지
                user_input = input("Press 'q' to shut down the node1: ")
            except EOFError:
                return
        # 'q'가 입력되면 노드 종료
            if user_input == 'q':
                node_name = rospy.get_name()
                message = f"kill:{node_name}"
                rospy.loginfo(message)
                self.publisher.publish(message)
                rospy.signal_shutdown("User requested shutdown.")
                sys.exit(0)

#    def check_new():
    def task_allocation(self, root_task):
        #sub1=self.root_task.subtasks  #ParallelCompositeTask
        sub1=root_task.subtasks  
        for task in sub1:
            if isinstance(task, ParallelAtomicTask): #Atomic
                for agent in self.member_list:
                    print(f"agent={agent.name}")
                    for req1 in task.requirement:
                        print(f"task:{task.name} is trying to {agent.name} with {req1} for {agent.capability}")
                        if req1 in agent.capability:
                            if agent.free and not task.assign_status:
                                agent.free=False
                                task.assign_status=True
                                task.assign(agent)
                                print(f"task:{task.name} is assigned to {agent.name}")
            elif isinstance(task, SequentialAtomicTask): #Atomic
                if task.predecessors_complete or len(task.predessesors)==0:
                    for agent in self.member_list:
                        print(f"agent={agent.name}")
                        for req1 in task.requirement:
                            print(f"task:{task.name} is trying to {agent.name} with {req1} for {agent.capability}")
                            if req1 in agent.capability:
                                if agent.free and not task.assign_status:
                                    agent.free=False
                                    task.assign_status=True
                                    task.assign(agent)
                                    print(f"task:{task.name} is assigned to {agent.name}")
            else: # Composite
                print(f"-----> Allocate Again: {task.name}")
                self.task_allocation(task)

    def task_execution(self, root_task):   
        sub1=root_task.subtasks  
        for task in sub1:
            if isinstance(task, AtomicTask) and task.assign_status: #Atomic
                agent = task.agent
                if not agent.execute_status:
                    # send execute
                    agent.execute_status = True
                    agent.setTask(task)
                    agent.action()
                    print(f"Agent[{agent.name}] is executing...for {task.name}")
            elif not isinstance(task, AtomicTask):
                print(f"Paralle Task: {task.name}")
                self.task_execution(task)
            else:
                print(f" ----- No Class[{task.name}] ----")



if __name__ == '__main__':
    group1 = JnPGroup(node_name='group1')
    group1.start()
    # ---- 0.8.1: coalition은 task에 종속 — 리더 에이전트가 goal/payload를 param으로 전달 ----
    # str() 강제: rosrun 의 _param:=value 는 YAML 파싱되어 payload 형태에 따라
    # 숫자 등 비문자열이 될 수 있다 — 이후 split 에서 크래시(실측 리뷰 지적)
    group1.goal = str(rospy.get_param('~goal', group1.goal))     # 멤버 모집 기준 (goal 매칭)
    # goal별 그룹: payload robots= 명단이 있으면 그 로봇만 멤버로 받는다
    try:
        _g_pre, _r_pre = parse_multigoal_payload(str(rospy.get_param('~task_payload', '')))
        group1.allowed_members = set(_r_pre.keys()) if _r_pre else None
    except Exception:
        group1.allowed_members = None
    task_payload = str(rospy.get_param('~task_payload', ''))     # 'name=x,y,z;...' (없으면 샘플 트리)
    # 기본 team: 완료 후에도 그룹/트리 유지 — 해제는 Monitor 의 'Group 해제' 버튼(수동).
    # ~group_type:=coalition 이면 설계문서 원의미대로 goal 도달 시 자동 해체.
    group_type = str(rospy.get_param('~group_type', 'team'))
    use_sched = bool(rospy.get_param('~use_scheduler', True))    # 0.8.1 기본: 모듈화 스케줄러 경로
    print(f"Group: goal={group1.goal} type={group_type} payload='{task_payload}'")
    # [JnP-0.9.0] 편성 방식: skills(기본) = 계획 먼저 → 역할표로 명부에서 선택(_recruit_and_plan) / goal = 0.8.2 방식(goal 매칭 등록)
    recruit_mode = str(rospy.get_param('~recruit_mode', 'skills'))
    group1.recruit_mode = recruit_mode
    group1._skills_strict = bool(rospy.get_param('~skills_strict', False))   # [V-F6] 모든 편성·할당 경로에 같은 적격 정책
    if recruit_mode == 'skills':
        print("------------------------ GROUP RECRUIT (skills): 계획 먼저, 역할표로 명부에서 선택", flush=True)
    else:
        print("------------------------ GROUP SEARCH")
        nodes=group1.search()
        for node in nodes:
            print("Group: searched node:{0}".format(node))
        print("Group: ========")
    if task_payload:
        # (a) 방식: goal 별 트리 빌더 디스패치
        if 'Mult-Goal' in group1.goal:
            root_task = _plan_or_legacy(group1.goal, task_payload,
                                        lambda: build_multigoal_tree(task_payload), group=group1)['root']
            # 베이스(공동 출발지) 표시 — 로봇 시작위치 무게중심을 latch 발행
            # /task_base 발행 금지(2026-08-08): 그룹별 멤버 홈 무게중심을 발행하면
            # 다이얼로그의 슬롯-상수 발행을 그룹마다 덮어써 BASE 원이 실행마다
            # 이동했고(실측 -1.74,-0.65 / -2.75,-1.65), traffic_zones 의 base 존
            # 정의까지 오염시켰다. 발행 주체는 협업 다이얼로그 하나로 일원화.
        elif 'Avoidance' in group1.goal:
            root_task = _plan_or_legacy(group1.goal, task_payload,
                                        lambda: build_avoidance_tree(task_payload), group=group1)['root']
            _meta = getattr(root_task, '_bt_meta', None)
            if _meta:
                group1._bt_pub = rospy.Publisher('/bottleneck/status', String,
                                                 queue_size=2, latch=True)
                _crossed = []          # 병목을 '실제로 지나간' 로봇 (관찰 판정)
                _entered = set()

                def _bt_publish():
                    try:
                        order = _meta['order']
                        cur = next((n for n in order
                                    if _meta['moves'][n].assign_status
                                    and n not in _crossed), None)
                        group1._bt_pub.publish(json.dumps(
                            {'order': [n for n in order if n not in _crossed],
                             'current': cur, 'passed': list(_crossed),
                             'center': list(_meta['center']), 'r': _meta['r'],
                             'targets': {n: list(v) for n, v in
                                         _meta['targets'].items()}}))
                    except Exception as _e:
                        rospy.logwarn('bottleneck status 발행 실패: %s', _e)
                group1._bt_from_tree = lambda _r: _bt_publish()
                _bt_publish()
                print(f"[병목] 통과 순서(위치 관찰 판정): {_meta['order']}", flush=True)

                def _pass_watcher():
                    """앞 로봇의 '실제 통과'를 위치로 판정해 다음 대기 task 를 연다.
                    판정: 병목 원(디스플레이 기준)에 들어갔다가 나감, 또는 move 완료.
                    360 sim초 초과 시 안전 진행(logwarn)."""
                    import math as _m
                    from nav_msgs.msg import Odometry
                    cx0, cy0 = _meta['center']
                    rr = _meta['r']
                    t0 = {}
                    while not rospy.is_shutdown():
                        rospy.sleep(1.0)
                        try:
                            changed = False
                            for k, nm in enumerate(_meta['order']):
                                if nm in _crossed:
                                    continue
                                mv = _meta['moves'][nm]
                                if not (mv.assign_status or mv.complete):
                                    continue
                                t0.setdefault(nm, rospy.get_time())
                                try:
                                    od = rospy.wait_for_message(
                                        '/%s/odom' % nm, Odometry, timeout=1.5)
                                    px = od.pose.pose.position.x
                                    py = od.pose.pose.position.y
                                    d = _m.hypot(px - cx0, py - cy0)
                                    if d < rr:
                                        _entered.add(nm)
                                    inside = d < rr
                                except Exception:
                                    inside = True
                                passed = (mv.complete
                                          or (nm in _entered and not inside)
                                          or rospy.get_time() - t0[nm] > 360.0)
                                if passed:
                                    if rospy.get_time() - t0[nm] > 360.0                                             and not mv.complete:
                                        rospy.logwarn('[병목] %s 통과 판정 시간초과'
                                                      ' — 안전 진행', nm)
                                    _crossed.append(nm)
                                    # 다음 로봇의 대기 task 완료 처리 → 재배정
                                    if k + 1 < len(_meta['order']):
                                        nxt = _meta['order'][k + 1]
                                        w = _meta['waits'].get(nxt)
                                        if w is not None and not w.complete:
                                            w.complete = True
                                            for sc in w.successors:
                                                sc.predecessors_complete = all(
                                                    pp.complete
                                                    for pp in sc.predecessors)
                                    print(f"[병목] 통과 확인: {nm} — 다음 로봇 출발 허용",
                                          flush=True)
                                    changed = True
                            if changed:
                                _bt_publish()
                                if hasattr(group1, '_scheduler'):
                                    group1._scheduler.wake()
                            if len(_crossed) == len(_meta['order']):
                                return
                        except Exception as _e:
                            rospy.logwarn('[병목] 관찰자 오류(계속): %s', _e)
                threading.Thread(target=_pass_watcher, daemon=True).start()
        elif 'ObjectSearch' in group1.goal:
            # ── 분산탐색-물건찾기 (2026-08-10): 알려진 지도를 로봇 수만큼
            # 사전 분할(planning)하고 구역별 경유점 경로를 생성 — 로봇은 v3 지속
            # search task 로 자기 구역을 순회, YOLO 노드(/found_objects)가 발견을
            # 보고한다. 모든 대상 클래스 발견 또는 전 구역 순회 완료 시 SUCCESS.
            # 목표 채널은 지도제작 v3 과 동일(/explore_target, /explore_done) —
            # 에이전트 루프(병목 v4·잼 탈출 포함)를 그대로 재사용한다.
            from geometry_msgs.msg import PoseStamped as _PS
            from nav_msgs.msg import OccupancyGrid as _OG
            from std_msgs.msg import Bool as _Bool
            from std_msgs.msg import String as _Str2
            _g0, _r0 = parse_multigoal_payload(task_payload)
            _expl_names = sorted(_r0.keys()) if _r0 else ['locobot_0', 'locobot_1']
            # [JnP-0.8.2 2026-10-13] 트리 생성은 작업 분할 경로(plans/object_search.py) — 실패 시 고정 빌더
            # [JnP-1.0 2026-11-07] 지도 없는 수색(~search_known_map:=false): 계획 변형 'explore'(순찰 대신 탐사)를 고르고 구역 계산·경유점 발행을
            # 하지 않는다. 변형에서 고정 빌더(순찰 트리)로 대체하면 뜻이 달라지므로 계획 경로의 실패를 그대로 올린다(plan_strict).
            # ~search_done_topic 이 있으면(채점 환경 감시기의 유효 보고 판정, Bool) 그것을 '전 대상 발견' 끝 조건으로 쓴다.
            _known_map = bool(rospy.get_param('~search_known_map', True))
            _done_topic = str(rospy.get_param('~search_done_topic', '') or '')
            _plan_kw = {} if _known_map else {'variant': 'explore'}
            if not _known_map:
                rospy.set_param('~plan_strict', True)
            _res0 = _plan_or_legacy(group1.goal, task_payload,
                                    lambda: build_object_search_tree(_expl_names), names=_expl_names, group=group1, **_plan_kw)
            root_task = _res0['root']
            _expl_names = sorted(_res0['dicts']['etasks'].keys()) or _expl_names   # [0.9.0] 역할에 묶인 로봇 이름
            group1._last_root = root_task
            _targets = set()
            _count = 0
            for _sec in task_payload.split(';'):
                _sec = _sec.strip()
                if _sec.startswith('targets='):
                    # 클래스명 공백은 '_' 표기 (예: sports_ball → 'sports ball')
                    _targets = {t.strip().replace('_', ' ') for t in
                                _sec[len('targets='):].split(',') if t.strip()}
                elif _sec.startswith('count='):
                    try:
                        _count = int(_sec[len('count='):])
                    except ValueError:
                        pass
            _etasks = _res0['dicts']['etasks']
            _dtasks = _res0['dicts']['dtasks']
            _spars = _res0['dicts']['spars']
            _distributed = bool(rospy.get_param('~jnp_distributed', False))   # [RL G3] 분산 모드: 구역 계획만 한 번 주고 피더 없음
            _sf = {'grid': None, 'done': False, 'found': [], 'pos': {},
                   'routes': {}, 'idx': {n: 0 for n in _expl_names},
                   'wp_t': {}, 'rdone': set()}
            rospy.Subscriber('/map', _OG,
                             lambda m: _sf.__setitem__('grid', m), queue_size=1)
            rospy.Subscriber('/found_objects', _Str2,
                             lambda m: _sf.__setitem__(
                                 'found', json.loads(m.data)), queue_size=2)
            if _done_topic:
                rospy.Subscriber(_done_topic, _Bool, lambda m: _sf.__setitem__('ext_done', bool(m.data)), queue_size=2)
            # 병목 coalition 을 미션 트리 병렬 가지로 흡수 (2026-08-10 지시)
            import types as _types
            _conf_nodes = {}

            def _conf_cb(m):
                # 병목을 '로봇별 search 가지 안'에 표현 (2026-08-10 지시):
                # 양보 로봇 = yield 선행(patrol 은 wait 로 전이 — 순차 의미),
                # 우선 로봇 = pass 병렬(patrol 계속). 해소 시 완료+patrol 복원.
                try:
                    d = json.loads(m.data)
                except ValueError:
                    return
                key = d.get('group', '')
                ranks = d.get('ranks') or {}
                if ranks:
                    if key in _conf_nodes:
                        return
                    names9 = sorted(ranks, key=lambda k: ranks[k])
                    if len(names9) < 2:
                        return
                    high, low = names9[0], names9[1]
                    if high not in _spars or low not in _spars:
                        return
                    t1 = ParallelAtomicTask(name=f'pass.{low}',
                                            parent=_spars[high],
                                            goal='nav:cross')
                    t1.addRequirement('virtual')
                    t1.assign_status = True
                    t1.agent = _types0.SimpleNamespace(name='/etri/' + high)
                    _spars[high].add(t1)
                    t2 = ParallelAtomicTask(name=f'yield.{high}',
                                            parent=_spars[low],
                                            goal='virtual:hold')
                    t2.addRequirement('virtual')
                    t2.assign_status = True
                    t2.agent = _types0.SimpleNamespace(name='/etri/' + low)
                    _spars[low].add(t2)
                    # 양보 로봇 patrol 은 '선행(yield) 대기' — wait 표시
                    if not _etasks[low].complete:
                        _etasks[low].assign_status = False
                    _conf_nodes[key] = (t1, t2, low)
                    print(f'[물건찾기] 병목 편입: {high} pass ∥ {low} yield'
                          f' (patrol.{low} wait)', flush=True)
                else:
                    ent = _conf_nodes.get(key)
                    if ent is not None:
                        t1, t2, low = ent
                        for c in (t1, t2):
                            c.assign_status = False
                            c.complete = True
                        if not _etasks[low].complete:
                            _etasks[low].assign_status = True
                        print(f'[물건찾기] 병목 해소: {key} '
                              f'(patrol.{low} 재개)', flush=True)
            rospy.Subscriber('/conflict_display', _Str2, _conf_cb, queue_size=6)

            _tpub = {n: rospy.Publisher('/explore_target/%s' % n, _PS,
                                        queue_size=2, latch=True)
                     for n in _expl_names}
            _dpub = rospy.Publisher('/explore_done', _Bool, queue_size=2,
                                    latch=True)
            _dpub.publish(_Bool(False))
            _rdpub = {n: rospy.Publisher('/explore_done/%s' % n, _Bool,
                                         queue_size=2, latch=True)
                      for n in _expl_names}
            for _p9 in _rdpub.values():
                _p9.publish(_Bool(False))
            import tf2_ros as _tf2
            _tfbuf = _tf2.Buffer(rospy.Duration(10.0))
            _tflis = _tf2.TransformListener(_tfbuf)

            def _plan_regions():
                # 내부 구조(벽·방)를 존중하는 분할 (2026-08-10 지시):
                # 로봇 시작점 3곳을 시드로 자유공간 4-연결 그래프에서 균형
                # BFS 성장 → 벽을 넘지 않는 '연결된' 영역 3개. 방은 벽 기준
                # 실제 도달거리가 가까운 로봇에 자연 배정된다.
                import math as _m3
                from collections import deque as _dq
                g = _sf['grid']
                info = g.info
                res = info.resolution
                W, H = info.width, info.height
                C = max(1, int(0.10 / res))          # 0.1m 격자로 다운샘플
                cw, ch = W // C, H // C

                def _cell_free(cx, cy):
                    gx, gy = cx * C + C // 2, cy * C + C // 2
                    if not (0 <= gx < W and 0 <= gy < H):
                        return False
                    v = g.data[gy * W + gx]
                    return v != -1 and v < 50

                free = [[_cell_free(cx, cy) for cx in range(cw)]
                        for cy in range(ch)]

                def _to_cell(px, py):
                    return (int((px - info.origin.position.x) / res) // C,
                            int((py - info.origin.position.y) / res) // C)

                order = sorted(_expl_names,
                               key=lambda n: _sf['pos'].get(n, (0, 0))[0])
                label = [[-1] * cw for _ in range(ch)]
                fronts = []
                for li, n in enumerate(order):
                    px, py = _sf['pos'].get(n, (0.0, 0.0))
                    sx, sy = _to_cell(px, py)
                    # 시드가 벽/밖이면 근방 free 로 스냅
                    best = None
                    for rr in range(0, 12):
                        for dy in range(-rr, rr + 1):
                            for dx in range(-rr, rr + 1):
                                nx, ny = sx + dx, sy + dy
                                if (0 <= nx < cw and 0 <= ny < ch
                                        and free[ny][nx]
                                        and label[ny][nx] == -1):
                                    best = (nx, ny)
                                    break
                            if best:
                                break
                        if best:
                            break
                    if best is None:
                        fronts.append(_dq())
                        continue
                    label[best[1]][best[0]] = li
                    fronts.append(_dq([best]))
                sizes = [len(f) for f in fronts]
                # 균형 성장: 매 라운드 가장 작은 영역부터 한 겹 확장
                active = True
                while active:
                    active = False
                    for li in sorted(range(len(order)),
                                     key=lambda i: sizes[i]):
                        q = fronts[li]
                        nq = _dq()
                        while q:
                            cx, cy = q.popleft()
                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                                nx, ny = cx + dx, cy + dy
                                if (0 <= nx < cw and 0 <= ny < ch
                                        and free[ny][nx]
                                        and label[ny][nx] == -1):
                                    label[ny][nx] = li
                                    sizes[li] += 1
                                    nq.append((nx, ny))
                        fronts[li] = nq
                        if nq:
                            active = True
                _sf['region_cells'] = (label, cw, ch, C, res,
                                       info.origin.position.x,
                                       info.origin.position.y)

                def _free_disc(px, py, rr=0.55, stp=0.10):
                    xx = px - rr
                    while xx <= px + rr:
                        yy = py - rr
                        while yy <= py + rr:
                            if (xx - px) ** 2 + (yy - py) ** 2 <= rr * rr:
                                gx = int((xx - info.origin.position.x) / res)
                                gy = int((yy - info.origin.position.y) / res)
                                if not (0 <= gx < W and 0 <= gy < H):
                                    return False
                                v = g.data[gy * W + gx]
                                if v == -1 or v >= 50:
                                    return False
                            yy += stp
                        xx += stp
                    return True
                reg_pts = {li: [] for li in range(len(order))}
                nx9 = int(W * res / 1.2)
                ny9 = int(H * res / 1.2)
                for iy in range(ny9 + 1):
                    for ix in range(nx9 + 1):
                        px = info.origin.position.x + 0.6 + ix * 1.2
                        py = info.origin.position.y + 0.6 + iy * 1.2
                        if not _free_disc(px, py):
                            continue
                        cx, cy = _to_cell(px, py)
                        if not (0 <= cx < cw and 0 <= cy < ch):
                            continue
                        li = label[cy][cx]
                        if li < 0:
                            continue
                        reg_pts[li].append((px, py))
                # 지그재그 정렬은 '구역' 단위
                for li in reg_pts:
                    rows = {}
                    for p in reg_pts[li]:
                        rows.setdefault(round(p[1] / 1.2), []).append(p)
                    route = []
                    for rj, key9 in enumerate(sorted(rows)):
                        row = sorted(rows[key9], key=lambda p: p[0],
                                     reverse=(rj % 2 == 1))
                        route.extend(row)
                    reg_pts[li] = route
                # 구역 순환제 (2026-08-10 지시): 고정 배정이면 waffle(카메라가
                # 낮아 책상 위를 못 봄) 구역의 책상 물체는 영영 못 찾는다 —
                # 각 로봇이 자기 구역부터 시작해 모든 구역을 차례로 스캔.
                routes = {}
                segs = {}
                R = len(order)
                for li0, n in enumerate(order):
                    full = []
                    bounds = []
                    for k in range(R):
                        full.extend(reg_pts[(li0 + k) % R])
                        bounds.append(len(full))
                    routes[n] = full
                    segs[n] = bounds     # 구역 경계(누적 인덱스) — 표시·로그용
                _sf['segs'] = segs
                return routes

            from visualization_msgs.msg import Marker as _Mk
            from visualization_msgs.msg import MarkerArray as _MkA
            from geometry_msgs.msg import Point as _Pt
            _regpub = rospy.Publisher('/search_regions', _MkA,
                                      queue_size=2, latch=True)
            _RCOL = {'locobot_0': (0.0, 0.8, 0.0), 'locobot_1': (0.0, 0.45, 1.0),
                     'tb3_waffle_0': (1.0, 0.65, 0.0)}

            def _publish_regions():
                # 구조 존중(비정형) 영역 표시: 0.3m 타일 채움 + 라벨 (2026-08-10)
                arr = _MkA()
                mid = 0
                rc = _sf.get('region_cells')
                order = sorted(_expl_names,
                               key=lambda n: _sf['pos'].get(n, (0, 0))[0])
                if rc is not None:
                    label, cw, ch, C, res, ox9, oy9 = rc
                    for li, _n in enumerate(order):
                        cr, cg, cb = _RCOL.get(_n, (0.6, 0.6, 0.6))
                        tile = _Mk()
                        tile.header.frame_id = 'map'
                        tile.header.stamp = rospy.Time.now()
                        tile.ns = 'region_fill'
                        tile.id = mid; mid += 1
                        tile.type = _Mk.CUBE_LIST
                        tile.action = _Mk.ADD
                        tile.pose.orientation.w = 1.0
                        side = C * res
                        tile.scale.x = tile.scale.y = side * 0.9
                        tile.scale.z = 0.02
                        tile.color.r, tile.color.g, tile.color.b = cr, cg, cb
                        tile.color.a = 0.28
                        sx = sy = cnt = 0
                        for cy in range(ch):
                            for cx in range(cw):
                                if label[cy][cx] == li:
                                    p9 = _Pt()
                                    p9.x = ox9 + (cx + 0.5) * C * res
                                    p9.y = oy9 + (cy + 0.5) * C * res
                                    p9.z = 0.02
                                    tile.points.append(p9)
                                    sx += p9.x; sy += p9.y; cnt += 1
                        arr.markers.append(tile)
                        if cnt:
                            tx = _Mk()
                            tx.header.frame_id = 'map'
                            tx.header.stamp = rospy.Time.now()
                            tx.ns = 'region_label'
                            tx.id = mid; mid += 1
                            tx.type = _Mk.TEXT_VIEW_FACING
                            tx.action = _Mk.ADD
                            tx.pose.position.x = sx / cnt
                            tx.pose.position.y = sy / cnt
                            tx.pose.position.z = 0.5
                            tx.scale.z = 0.35
                            tx.color.r, tx.color.g, tx.color.b, tx.color.a = cr, cg, cb, 1.0
                            # 순환제: 구역 소유가 고정이 아니므로 중립 이름
                            tx.text = f"구역 {li + 1}"
                            arr.markers.append(tx)
                # planning 경유점 표시 (2026-08-10 지시): 구역 색 구슬 —
                # 남은 점 진하게 / 방문한 점 흐리게 / 현재 목표 크게,
                # 남은 순회 순서는 얇은 선. 피더가 점을 넘길 때마다 갱신.
                routes = _sf.get('routes') or {}
                for _n in order:
                    cr, cg, cb = _RCOL.get(_n, (0.6, 0.6, 0.6))
                    rt = routes.get(_n, [])
                    i9 = _sf.get('idx', {}).get(_n, 0)
                    # 순환제: 앞으로 갈 점은 '현재 구역 구간'까지만 표시
                    # (전 구역을 다 그리면 3색 점이 지도 전체에 겹침)
                    segb = _sf.get('segs', {}).get(_n, [len(rt)])
                    send9 = next((b for b in segb if b > i9), len(rt))
                    for ns9, seg, al, sc in (
                            ('wp_done', rt[:i9], 0.25, 0.09),
                            ('wp_todo', rt[i9 + 1:send9], 0.95, 0.13)):
                        mk = _Mk()
                        mk.header.frame_id = 'map'
                        mk.header.stamp = rospy.Time.now()
                        mk.ns = ns9
                        mk.id = mid; mid += 1
                        mk.action = _Mk.ADD if seg else _Mk.DELETE
                        mk.type = _Mk.SPHERE_LIST
                        mk.pose.orientation.w = 1.0
                        mk.scale.x = mk.scale.y = mk.scale.z = sc
                        mk.color.r, mk.color.g, mk.color.b, mk.color.a = \
                            cr, cg, cb, al
                        for px9, py9 in seg:
                            p9 = _Pt()
                            p9.x, p9.y, p9.z = px9, py9, 0.06
                            mk.points.append(p9)
                        arr.markers.append(mk)
                    cur = _Mk()
                    cur.header.frame_id = 'map'
                    cur.header.stamp = rospy.Time.now()
                    cur.ns = 'wp_current'
                    cur.id = mid; mid += 1
                    if i9 < len(rt):
                        cur.type = _Mk.SPHERE
                        cur.action = _Mk.ADD
                        cur.pose.position.x, cur.pose.position.y = rt[i9]
                        cur.pose.position.z = 0.10
                        cur.pose.orientation.w = 1.0
                        cur.scale.x = cur.scale.y = cur.scale.z = 0.25
                        cur.color.r, cur.color.g, cur.color.b, cur.color.a = \
                            cr, cg, cb, 1.0
                    else:
                        cur.action = _Mk.DELETE
                    arr.markers.append(cur)
                    ln = _Mk()
                    ln.header.frame_id = 'map'
                    ln.header.stamp = rospy.Time.now()
                    ln.ns = 'wp_route'
                    ln.id = mid; mid += 1
                    seg2 = rt[i9:send9]
                    if len(seg2) >= 2:
                        ln.type = _Mk.LINE_STRIP
                        ln.action = _Mk.ADD
                        ln.pose.orientation.w = 1.0
                        ln.scale.x = 0.03
                        ln.color.r, ln.color.g, ln.color.b, ln.color.a = \
                            cr, cg, cb, 0.55
                        for px9, py9 in seg2:
                            p9 = _Pt()
                            p9.x, p9.y, p9.z = px9, py9, 0.05
                            ln.points.append(p9)
                    else:
                        ln.action = _Mk.DELETE
                    arr.markers.append(ln)
                _regpub.publish(arr)

            def _feeder():
                import math as _m
                while not rospy.is_shutdown() and not _sf['done']:
                    try:
                        rospy.sleep(3.0)
                        nowt = rospy.get_time()
                        for _n in _expl_names:
                            try:
                                _tr = _tfbuf.lookup_transform(
                                    'map', '%s/base_footprint' % _n,
                                    rospy.Time(0))
                                _sf['pos'][_n] = (_tr.transform.translation.x,
                                                  _tr.transform.translation.y)
                            except Exception:
                                pass
                        if not _sf['routes']:
                            if _sf['grid'] is None or len(_sf['pos']) < 1:
                                continue
                            _sf['routes'] = _plan_regions()
                            for _n, rt in _sf['routes'].items():
                                print(f"[물건찾기] {_n} 구역 경유점 {len(rt)}개",
                                      flush=True)
                            _publish_regions()      # RViz 구역 표시 (2026-08-10)
                            continue
                        # 조기 성공: 대상 클래스 전부 발견 + (count 지정 시)
                        # 발견 개수 충족 (2026-08-10: 공 2개 등 동일 클래스 다수)
                        _fl = [f for f in _sf['found']
                               if f.get('cls') in _targets]
                        _fc = {f.get('cls') for f in _fl}
                        if (_targets and _targets <= _fc
                                and len(_fl) >= max(_count, len(_targets))):
                            _sf['done'] = True
                            for _t1, _t2, _lw in _conf_nodes.values():
                                for _cc in (_t1, _t2):
                                    _cc.assign_status = False
                                    _cc.complete = True
                            for _dd in _dtasks.values():
                                _dd.assign_status = False
                                _dd.complete = True
                            for _tt in _etasks.values():
                                if getattr(_tt, 'agent', None) is None:
                                    _tt.complete = True
                            _dpub.publish(_Bool(True))
                            print(f"[물건찾기] 전 대상 발견 {sorted(_fc)} — 종료",
                                  flush=True)
                            if hasattr(group1, '_scheduler'):
                                group1._scheduler.wake()
                            return
                        _present = [n for n in _expl_names
                                    if any(n in a.name
                                           for a in group1.member_list)]
                        for _n in _present:
                            if _n in _sf['rdone']:
                                continue
                            rp = _sf['pos'].get(_n)
                            rt = _sf['routes'].get(_n, [])
                            i9 = _sf['idx'][_n]
                            if i9 >= len(rt):
                                _sf['rdone'].add(_n)
                                _rdpub[_n].publish(_Bool(True))
                                _dtasks[_n].assign_status = False
                                _dtasks[_n].complete = True
                                print(f"[물건찾기] {_n} 구역 순회 완료", flush=True)
                                continue
                            wx, wy = rt[i9]
                            if _n not in _sf['wp_t']:
                                _sf['wp_t'][_n] = nowt
                                _msg = _PS()
                                _msg.header.frame_id = 'map'
                                _msg.header.stamp = rospy.Time.now()
                                _msg.pose.position.x = wx
                                _msg.pose.position.y = wy
                                _msg.pose.orientation.w = 1.0
                                _tpub[_n].publish(_msg)
                            reached = (rp is not None and
                                       _m.hypot(rp[0] - wx, rp[1] - wy) < 0.6)
                            if reached or nowt - _sf['wp_t'][_n] > 60.0:
                                _sf['idx'][_n] += 1
                                _sf['wp_t'].pop(_n, None)
                                segb = _sf.get('segs', {}).get(_n, [])
                                ri = next((k for k, b in enumerate(segb)
                                           if _sf['idx'][_n] < b), len(segb))
                                _etasks[_n].goal = (
                                    f"search[{ri + 1}/{max(1, len(segb))}구역]"
                                    f":{_sf['idx'][_n]}/{len(rt)}")
                                if _sf['idx'][_n] in segb[:-1]:
                                    print(f"[물건찾기] {_n} 구역 스캔 완료 → "
                                          f"다음 구역으로 순환", flush=True)
                                _publish_regions()   # 경유점 진행 갱신
                        if all(n in _sf['rdone'] for n in _expl_names):
                            _sf['done'] = True
                            for _t1, _t2, _lw in _conf_nodes.values():
                                for _cc in (_t1, _t2):
                                    _cc.assign_status = False
                                    _cc.complete = True
                            for _dd in _dtasks.values():
                                _dd.assign_status = False
                                _dd.complete = True
                            for _tt in _etasks.values():
                                if getattr(_tt, 'agent', None) is None:
                                    _tt.complete = True
                            _dpub.publish(_Bool(True))
                            print('[물건찾기] 전 구역 순회 완료 — 종료', flush=True)
                            if hasattr(group1, '_scheduler'):
                                group1._scheduler.wake()
                            return
                        group1.publish_status(
                            'running', root_task,
                            note='발견: ' + (', '.join(
                                f"{f['cls']}@({f['x']},{f['y']})"
                                for f in _sf['found']) or '아직 없음'))
                    except Exception as _fe:
                        rospy.logwarn('[물건찾기] 피더 오류(계속): %s', _fe)
            if _distributed:
                # [RL G3] 분산 수색: 구역 분할(JnP 배정의 일부)만 한 번 계산해 로봇별 경유점을 /search_route/<로봇> 으로 주고,
                # 그 뒤 순회는 각 로봇의 정책이 한다. 종료 = (a) 어느 로봇이 대상 발견을 보고(detections 제공 항목, 그룹이 구독 — 통신으로 셈)
                # (b) 모든 search 작업이 끝남(정책의 done). 미등록 로봇은 120초 뒤 완료 간주.
                def _dist_search():
                    import tf2_ros as _tf2d
                    from std_msgs.msg import String as _StrD
                    from jnp_rl_link import subscribe as _rl_sub
                    from jnp_rl_meter import CommLog as _RlLog
                    _bufd = _tf2d.Buffer(rospy.Duration(10.0)); _lisd = _tf2d.TransformListener(_bufd)
                    _rlog = _RlLog('group', str(rospy.get_param('~jnp_comm_log', '') or '/tmp/jnp_comm_group.jsonl'))
                    _rpubs = {n: rospy.Publisher('/search_route/%s' % n, _StrD, queue_size=1, latch=True) for n in _expl_names}
                    _subs = {}
                    _t0d = rospy.get_time()

                    def _on_report(n, m):
                        try:
                            for f in json.loads(m.data):
                                if isinstance(f, dict):
                                    f.setdefault('robot', n); _sf['found'].append(f)
                        except Exception:
                            pass
                    while not rospy.is_shutdown() and not _sf['done']:
                        try:
                            rospy.sleep(3.0)
                            nowt = rospy.get_time()
                            for _n in _expl_names:
                                try:
                                    _tr = _bufd.lookup_transform('map', '%s/base_footprint' % _n, rospy.Time(0))
                                    _sf['pos'][_n] = (_tr.transform.translation.x, _tr.transform.translation.y)
                                except Exception:
                                    pass
                                if _n not in _subs:
                                    try:
                                        _subs[_n] = _rl_sub('group', _n, 'detections', (lambda m, n=_n: _on_report(n, m)), _rlog)
                                    except Exception:
                                        pass
                            if not _sf['routes'] and _known_map:     # 지도 없는 수색은 구역·경유점이 없고 지도 준비를 기다리지 않는다
                                if _sf['grid'] is None or len(_sf['pos']) < 1:
                                    continue
                                _sf['routes'] = _plan_regions()
                                for _n, rt in _sf['routes'].items():
                                    _rpubs[_n].publish(_StrD(json.dumps([[float(x), float(y)] for x, y in rt])))
                                    print(f"[물건찾기] 분산 모드 — {_n} 구역 경유점 {len(rt)}개 전달", flush=True)
                                _publish_regions()
                                continue
                            _fl = [f for f in _sf['found'] if f.get('cls') in _targets]
                            _fc = {f.get('cls') for f in _fl}
                            if _done_topic:      # 외부 판정(사건 ID 를 검증한 유효 보고)만 '전 대상 발견'으로 본다. 그룹이 받은 보고 수는 쓰지 않는다
                                _found_all = bool(_sf.get('ext_done'))
                            else:
                                _found_all = bool(_targets and _targets <= _fc and len(_fl) >= max(_count, len(_targets)))
                            _pending = []
                            for _tn, _tt in _etasks.items():
                                if getattr(_tt, 'complete', False):
                                    continue
                                if getattr(_tt, 'agent', None) is None and nowt - _t0d > 120.0:
                                    _tt.complete = True; continue
                                _pending.append(_tn)
                            if _found_all or not _pending:
                                _sf['done'] = True
                                for _t1, _t2, _lw in _conf_nodes.values():
                                    for _cc in (_t1, _t2):
                                        _cc.assign_status = False; _cc.complete = True
                                for _dd in _dtasks.values():
                                    _dd.assign_status = False; _dd.complete = True
                                for _tt in _etasks.values():
                                    if getattr(_tt, 'agent', None) is None:
                                        _tt.complete = True
                                _dpub.publish(_Bool(True))
                                print('[물건찾기] 분산 모드 — %s' % (('외부 판정: 전 대상 발견 — 종료' if _done_topic else '전 대상 발견 보고 %s — 종료' % sorted(_fc)) if _found_all else '전 로봇 수색 완료 — 종료'), flush=True)
                                if hasattr(group1, '_scheduler'):
                                    group1._scheduler.wake()
                                return
                            group1.publish_status('running', root_task, note='발견 보고: ' + (', '.join(f"{f.get('cls')}@({f.get('x')},{f.get('y')})" for f in _sf['found']) or '아직 없음'))
                        except Exception as _fe:
                            rospy.logwarn('[물건찾기] 분산 감시 오류(계속): %s', _fe)
                threading.Thread(target=_dist_search, daemon=True).start()
            else:
                threading.Thread(target=_feeder, daemon=True).start()

            def _post_search_report():
                if _distributed:
                    print('[물건찾기] 분산 모드 — 보고: %s' % (_sf['found'] or '없음'), flush=True)
                    return
                try:
                    print('[물건찾기] 결과: ' + json.dumps(
                        _sf['found'], ensure_ascii=False), flush=True)
                except Exception:
                    pass
                try:
                    # 최종 결과 팝업 (2026-08-10 지시): 발견 스냅샷 뷰어
                    subprocess.Popen(
                        ['python3',
                         '/root/tesla/ros/navi/scripts/found_popup.py'])
                except Exception as _pe:
                    rospy.logwarn('팝업 기동 실패: %s', _pe)
            group1._post_success_hook = _post_search_report
        elif 'MapExplore' in group1.goal:
            # ── 분산 탐색 v3 (2026-08-09, 사용자 결정): 프런티어별 task 제거,
            # 로봇당 1개의 '지속 explore task'만 트리에 둔다. 피더는 로봇별 목표
            # 프런티어를 /explore_target/<robot>(latched) 로 갱신하고 에이전트의
            # explore 루프가 추종한다. 완료는 /explore_done(latched) 방송 →
            # 에이전트 루프 종료 → 스케줄러 end → SUCCESS. (프런티어 task 왕복의
            # 좀비-실행·used 영구제외 교착 구조 제거; v2 는 git 이력 참조)
            # 그룹만 교체 재기동할 때 스택 중복 기동(이름 뺏기→고아 노드) 방지:
            # _spawn_stack:=false 면 기존 스택 재사용 (2026-08-09)
            # [JnP-1.0 RL G3 2026-10-31] 분산 모드(~jnp_distributed:=true): RRT 스택·중앙 피더·상시 병합을 켜지 않는다.
            # 각 로봇의 정책(에이전트 ~jnp_policy)이 탐사와 완료를 정하고, 그룹은 편성·트리·상태·종료만 맡는다.
            # 기본값(false)은 지금까지와 같은 중앙 병합·중앙 배정 판(예제·기준).
            _distributed = bool(rospy.get_param('~jnp_distributed', False))
            if _distributed:
                print('[지도제작] 분산 모드 — RRT 스택·중앙 피더 없음(로봇별 정책이 탐사·완료를 정함)', flush=True)
                _stack = None
            elif not rospy.get_param('~spawn_stack', True):
                print('[지도제작] 기존 탐지 스택 재사용 (spawn_stack=false)', flush=True)
                _stack = None
            else:
                print('[지도제작] RRT 탐지 스택 기동 (목표 배정은 JnP 피더)', flush=True)
                # 탐사 스택 launch 는 이 패키지의 launch/ 에 있다(devel·install 공간 모두 패키지 경로로 찾는다)
                import rospkg as _rp
                _stack_launch = os.path.join(_rp.RosPack().get_path('jnp'), 'launch', 'exploration_stack.launch')
                _stack = subprocess.Popen(
                    ['bash', '-c',
                     'source /opt/ros/noetic/setup.bash; '
                     'source /root/interbotix_ws/devel/setup.bash; '
                     'source /root/catkin_ws_explo/devel/setup.bash; '
                     'roslaunch ' + _stack_launch])

            from geometry_msgs.msg import PoseArray as _PA
            from geometry_msgs.msg import PoseStamped as _PS
            from nav_msgs.msg import OccupancyGrid as _OG
            from std_msgs.msg import Bool as _Bool
            _g0, _r0 = parse_multigoal_payload(task_payload)
            _expl_names = sorted(_r0.keys()) if _r0 else ['locobot_0', 'locobot_1']
            # ── 트리 구조 (2026-08-11 지시): 지도제작은 '로봇마다' 수행하는 일이다.
            #   map_explore[P] → make_maps.<robot>[P] → { explore.<robot>,
            #                                             merge_maps/send_map.<robot> }
            #   ROS 실측: multirobot_map_merge 노드 1개가 각 로봇의 /<robot>/map 을
            #   받아 /map 을 낸다 → 병합 호스트는 '한 대'뿐이고 나머지는 자기 지도를
            #   보내는 역할.
            #   ★ 호스트는 '이름 순'이 아니라 '탑재 컴퓨팅 성능 순'으로 고른다
            #     (2026-08-11 지시): 병합은 무거운 연산이라 라즈베리파이(TB3)가
            #     아니라 x86 NUC급(LoCoBot)이 맡아야 한다. 근거는 에이전트가
            #     광고하는 capability(compute_x86/compute_arm), 광고가 없는
            #     구버전 에이전트는 기종 이름으로 대체 판정.
            import types as _types9

            def _compute_rank(nm):
                caps = set()
                for _a9 in getattr(group1, 'member_list', []) or []:
                    if nm in getattr(_a9, 'name', ''):
                        caps = set(getattr(_a9, 'capability_set', []) or [])
                        break
                if 'compute_x86' in caps:
                    return 3
                if 'compute_arm' in caps:
                    return 2
                return 3 if 'locobot' in nm else (2 if 'waffle' in nm else 1)

            _merge_host = (sorted(_expl_names,
                                  key=lambda n: (-_compute_rank(n), n))[0]
                           if _expl_names else None)
            if _merge_host:
                print(f"[지도제작] 지도 병합 호스트: {_merge_host} "
                      f"(컴퓨팅 등급 {_compute_rank(_merge_host)})", flush=True)
            # [JnP-0.8.2 2026-10-13] 트리 생성은 작업 분할 경로(plans/map_explore.py) — 실패 시 고정 빌더.
            # 병목 처리는 '탐사 이전에 끝내야 하는 선행 작업'이므로 navigate 순차 가지 안에 둔다
            # (2026-08-11 지시). 평시엔 explore 하나뿐이고, 양보가 걸리면 그 앞에 yield.<상대> 가
            # 삽입돼 explore 가 대기로 바뀐다. ★ 스케줄러는 순차 가지에서 '첫 미완료 자식'만 보고
            # 멈추므로, 앞에 선행이 생겨도 이미 실행 중인 explore 는 회수되지 않는다.
            _res9 = _plan_or_legacy(group1.goal, task_payload,
                                    lambda: build_map_explore_tree(_expl_names, _merge_host),
                                    names=_expl_names, merge_host=_merge_host, group=group1)
            root_task = _res9['root']
            _expl_names = sorted(_res9['dicts']['etasks'].keys()) or _expl_names        # [0.9.0] 역할에 묶인 로봇 이름
            _merge_host = (_res9.get('roles_bound') or {}).get('host', _merge_host)       # [0.9.0] host 역할의 로봇
            print(f"[지도제작] 지도 병합 호스트(역할 host): {_merge_host}", flush=True)
            try:   # [JnP-1.0 RL 2026-11-01, R4 F4] 역할 통지 — 로봇별 정책이 host 를 이름순 추측이 아니라 그룹 결정으로 안다
                _rpub = rospy.Publisher('/jnp/explore_roles', String, queue_size=1, latch=True)
                _rpub.publish(String(json.dumps({'host': _merge_host, 'explorers': list(_expl_names), 'goal': 'MapExplore'})))
                group1._roles_pub = _rpub
            except Exception as _re:
                print('[지도제작] 역할 통지 실패(계속): %s' % _re, flush=True)
            group1._last_root = root_task
            _etasks = _res9['dicts']['etasks']
            _mtasks = _res9['dicts']['mtasks']   # 지도 송신/병합 (가상 task — 표시용)
            _branch = _res9['dicts']['branch']
            _seqbr = _res9['dicts']['seqbr']     # 로봇별 [S] navigate 가지 (병목 선행 삽입 지점)

            # ── 병목(충돌) 처리를 트리에 접붙이기 (2026-08-11 지시) ──
            #   양보 로봇: navigate.<n> 안, explore 바로 앞에 yield.<상대> (순차)
            #   우선 로봇: make_maps.<n> 아래 pass.<상대> (병렬 — 계속 이동)
            #   같은 쌍이 반복되면 노드를 재사용해 트리가 무한히 자라지 않게 한다.
            _cnodes = {}          # (low, high) → (yield task, pass task)

            def _mx_conf_cb(m):
                try:
                    d = json.loads(m.data)
                except ValueError:
                    return
                ranks = d.get('ranks') or {}
                if ranks:
                    order9 = sorted(ranks, key=lambda k: ranks[k])
                    if len(order9) < 2:
                        return
                    high, low = order9[0], order9[1]
                    if high not in _branch or low not in _seqbr:
                        return
                    ent = _cnodes.get((low, high))
                    if ent is not None:               # 재발 — 노드 재사용
                        for c in ent:
                            c.complete = False
                            c.assign_status = True
                    else:
                        ty = ParallelAtomicTask(name=f'yield.{high}',
                                                parent=_seqbr[low],
                                                goal='virtual:hold')
                        ty.addRequirement('virtual')
                        ty.assign_status = True       # 배정 대상 아님(표시 전용)
                        ty.agent = _types9.SimpleNamespace(name='/etri/' + low)
                        _sq9 = _seqbr[low]
                        try:                          # explore 바로 앞에 삽입
                            _sq9.subtasks.insert(
                                _sq9.subtasks.index(_etasks[low]), ty)
                        except ValueError:
                            _sq9.add(ty)
                        tp = ParallelAtomicTask(name=f'pass.{low}',
                                                parent=_branch[high],
                                                goal='nav:cross')
                        tp.addRequirement('virtual')
                        tp.assign_status = True
                        tp.agent = _types9.SimpleNamespace(name='/etri/' + high)
                        _branch[high].add(tp)
                        _cnodes[(low, high)] = (ty, tp)
                    if not _etasks[low].complete:
                        _etasks[low].assign_status = False   # 'wait' 표시
                    print(f'[지도제작] 병목 편입: {high} pass ∥ {low} yield '
                          f'(explore.{low} 대기)', flush=True)
                else:
                    for (low, high), ent in list(_cnodes.items()):
                        if all(c.complete for c in ent):
                            continue
                        for c in ent:
                            c.assign_status = False
                            c.complete = True
                        if not _etasks[low].complete:
                            _etasks[low].assign_status = True
                        print(f'[지도제작] 병목 해소: {high}/{low} '
                              f'(explore.{low} 재개)', flush=True)
            rospy.Subscriber('/conflict_display', String, _mx_conf_cb,
                             queue_size=6)
            _fr = {'pts': [], 'known': 0, 'grid': None, 'fp_t': -1e9,
                   'hist': [], 'done': False, 'pos': {}, 'tgt': {},
                   'reach': {n: 0 for n in _expl_names}, 'bl': {}, 'prog': {},
                   'idle': {}, 'rdone': set(), 'visited': []}

            # ── 도착 기반 영구 제외 (2026-08-11 지시) ──
            # 벽 뒤 unknown 은 가시성 검사가 없는 정보이득 계산 때문에 점수가
            # 영영 안 떨어져 프런티어가 '불멸'이 된다(광선추적 실측: 가림 91~100%).
            # 로봇이 그 자리까지 실제로 갔다면 남은 미지는 관측 불가 영역이므로
            # 영구 제외한다. 완료 판정도 이 '살아있는' 목록으로 해야 미션이 끝난다.
            _VISIT_R = 0.7

            def _visited_near(x9, y9):
                return any((x9 - v[0]) ** 2 + (y9 - v[1]) ** 2 < _VISIT_R ** 2
                           for v in _fr['visited'])

            def _live_pts():
                return [f for f in _fr['pts'] if not _visited_near(f[0], f[1])]

            def _mark_visited(x9, y9):
                if not _visited_near(x9, y9):
                    _fr['visited'].append((x9, y9))
                    print(f"[지도제작] 방문 완료 지점 영구 제외 "
                          f"({x9:.2f},{y9:.2f}) — 누적 {len(_fr['visited'])}개",
                          flush=True)

            rospy.Subscriber('/frontiers_pose', _PA,
                             lambda m: (_fr.__setitem__(
                                 'pts', [(q.position.x, q.position.y)
                                         for q in m.poses]),
                                 _fr.__setitem__('fp_t', rospy.get_time())),
                             queue_size=2)
            rospy.Subscriber('/map', _OG,
                             lambda m: (_fr.__setitem__(
                                 'known', sum(1 for v in m.data if v != -1)),
                                 _fr.__setitem__('grid', (m.info, m.data))),
                             queue_size=1)
            _tpub = {n: rospy.Publisher('/explore_target/%s' % n, _PS,
                                        queue_size=2, latch=True)
                     for n in _expl_names}
            _dpub = rospy.Publisher('/explore_done', _Bool, queue_size=2,
                                    latch=True)
            _dpub.publish(_Bool(False))   # latched 초기값 (늦게 뜬 에이전트 대비)
            # 로봇별 개별 완료 채널 (2026-08-09 사용자 설계: 자기 몫 프런티어가
            # 소진된 로봇의 explore task 는 개별적으로 done)
            _rdpub = {n: rospy.Publisher('/explore_done/%s' % n, _Bool,
                                         queue_size=2, latch=True)
                      for n in _expl_names}
            for _p9 in _rdpub.values():
                _p9.publish(_Bool(False))
            # 로봇 위치는 TF(map→base_footprint) — odom 토픽은 스폰 기준 (0,0)
            import tf2_ros as _tf2
            _tfbuf = _tf2.Buffer(rospy.Duration(10.0))
            _tflis = _tf2.TransformListener(_tfbuf)

            def _near_free(fx, fy):
                """프런티어 '근방'(≤1.0m) 최근접 free(0.45m 원반) 지점.
                0.45 미만이면 도착 후 벽 inflation inscribed 링에 갇혀 다음
                plan 이 전부 실패 (2026-08-09 실측). 없으면 None."""
                import math as _m2
                g = _fr.get('grid')
                if g is None:
                    return fx, fy
                info, data = g

                def ok(px, py):
                    rr, stp = 0.45, 0.08
                    xx = px - rr
                    while xx <= px + rr:
                        yy = py - rr
                        while yy <= py + rr:
                            if (xx - px) ** 2 + (yy - py) ** 2 <= rr * rr:
                                gx = int((xx - info.origin.position.x) / info.resolution)
                                gy = int((yy - info.origin.position.y) / info.resolution)
                                if not (0 <= gx < info.width and 0 <= gy < info.height):
                                    return False
                                v = data[gy * info.width + gx]
                                if v == -1 or v >= 50:
                                    return False
                            yy += stp
                        xx += stp
                    return True
                if ok(fx, fy):
                    return fx, fy
                for r in (0.15, 0.30, 0.45, 0.60, 0.80, 1.00):
                    for k in range(12):
                        a = k * _m2.pi / 6.0
                        px, py = fx + r * _m2.cos(a), fy + r * _m2.sin(a)
                        if ok(px, py):
                            return px, py
                return None

            # [JnP-1.0 RL 2026-10-31] 리더 프록시의 결정 자리(중앙 피더). 원칙은 로봇마다 자기 정책(에이전트 쪽 ~jnp_policy)이지만,
            # 리더 프록시를 중앙에 두는 방식도 허용된다 — 프록시가 모든 로봇 정보를 받는 만큼 통신량이 늘 뿐이다.
            # ~jnp_policy(옛 ~lb_policy)가 비어 있으면 아래 코드는 아무것도 바꾸지 않는다(기본 휴리스틱 그대로).
            _lb_pol = None
            _lb_specs = {}
            try:
                _lb_spec = str(rospy.get_param('~jnp_policy', '') or rospy.get_param('~lb_policy', '') or '')
            except Exception:
                _lb_spec = ''
            if _lb_spec:
                try:
                    from jnp_rl_loader import load_policy as _lb_load
                    from jnp_rl_api import Observation as _LbObs, Candidate as _LbCand, RobotSpec as _LbSpec
                    _lb_pol = _lb_load(_lb_spec)
                    _lb_sp_param = rospy.get_param('~jnp_robot_specs', {}) or rospy.get_param('~lb_robot_specs', {}) or {}
                    _lb_specs = {n: _LbSpec.from_name(n, _lb_sp_param.get(n)) for n in _expl_names}
                    print('[지도제작][RL 프록시] 정책 로드: %s (api %s)' % (_lb_spec, getattr(_lb_pol, 'api_version', '?')), flush=True)
                except Exception as _le:
                    rospy.logerr('[지도제작][RL 프록시] 정책 로드 실패 — 기본 휴리스틱으로 진행: %s', _le)
                    _lb_pol = None

            def _feeder():
                import math as _m
                _t0 = rospy.get_time()
                while not rospy.is_shutdown() and not _fr['done']:
                    try:
                        # sleep 도 try 안: 클럭 점프 한 방에 스레드 사망 방지
                        rospy.sleep(3.0)
                        nowt = rospy.get_time()
                        for _n in _expl_names:
                            try:
                                _tr = _tfbuf.lookup_transform(
                                    'map', '%s/base_footprint' % _n, rospy.Time(0))
                                _fr['pos'][_n] = (_tr.transform.translation.x,
                                                  _tr.transform.translation.y)
                            except Exception:
                                pass
                        # 커버리지 플래토 → 종료 판정 (파이프라인 생존 가드 포함)
                        _fr['hist'].append((nowt, _fr['known']))
                        _fr['hist'] = [h for h in _fr['hist']
                                       if nowt - h[0] <= 60.0]
                        if (nowt - _t0 > 120.0 and len(_fr['hist']) >= 6
                                and _fr['known'] > 20000
                                and nowt - _fr.get('fp_t', -1e9) < 15.0):
                            g0 = _fr['hist'][0][1]
                            if ((_fr['known'] - g0) / max(g0, 1) < 0.01
                                    and not _live_pts()):
                                _fr['done'] = True
                                for _mt in _mtasks.values():   # 지도 송신/병합 종료
                                    _mt.assign_status = False
                                    _mt.complete = True
                                for _ent9 in _cnodes.values():  # 병목 가지 정리
                                    for _c9 in _ent9:           # (미완료면 미션이
                                        _c9.assign_status = False   # 안 끝난다)
                                        _c9.complete = True
                                # 미등록 로봇의 explore task 는 영원히 미배정 —
                                # 미션 완주를 막지 않게 강제 완료 (v3 리뷰 #1)
                                for _tn, _tt in _etasks.items():
                                    if getattr(_tt, 'agent', None) is None:
                                        _tt.complete = True
                                _dpub.publish(_Bool(True))
                                print('[지도제작] 커버리지 플래토 — 탐사 종료 방송',
                                      flush=True)
                                if hasattr(group1, '_scheduler'):
                                    group1._scheduler.wake()
                                return
                        _present = [n for n in _expl_names
                                    if any(n in a.name for a in group1.member_list)]
                        _fr['bl'] = {k: v for k, v in _fr['bl'].items()
                                     if v > nowt}
                        # ★ 전원 개별 완료(은퇴) → 미션 종료. 이 경로가 없으면
                        #   아무도 안 움직이는데 완료 판정은 '살아있는 프런티어
                        #   0개'를 기다려 영원히 안 끝난다 (리뷰 지적).
                        if _present and all(n in _fr['rdone'] for n in _present):
                            _fr['done'] = True
                            for _mt in _mtasks.values():
                                _mt.assign_status = False
                                _mt.complete = True
                            for _ent9 in _cnodes.values():
                                for _c9 in _ent9:
                                    _c9.assign_status = False
                                    _c9.complete = True
                            for _tn9, _tt9 in _etasks.items():
                                if getattr(_tt9, 'agent', None) is None:
                                    _tt9.complete = True
                            _dpub.publish(_Bool(True))
                            print('[지도제작] 전 로봇 몫 소진 — 탐사 종료 방송',
                                  flush=True)
                            if hasattr(group1, '_scheduler'):
                                group1._scheduler.wake()
                            return
                        for _n in _present:
                            if _n in _fr['rdone']:
                                continue          # 개별 완료된 로봇
                            rp = _fr['pos'].get(_n)
                            if rp is None:
                                continue
                            tgt = _fr['tgt'].get(_n)
                            if tgt is not None:
                                _fr['idle'].pop(_n, None)   # 목표 보유 중 — 유휴 아님
                                d = _m.hypot(rp[0] - tgt[0], rp[1] - tgt[1])
                                if d < 0.6:                     # 도달
                                    _fr['reach'][_n] += 1
                                    _etasks[_n].goal = (
                                        f"explore:{_fr['reach'][_n]}회 도달")
                                    # 지도 갱신 전 같은 프런티어 재선택 루프 방지
                                    _fr['bl'][(_n, round(tgt[0], 1),
                                               round(tgt[1], 1))] = nowt + 30.0
                                    _mark_visited(tgt[0], tgt[1])   # 영구 제외
                                    _src9 = _fr.get('src', {}).pop(_n, None)
                                    if _src9 is not None:
                                        _mark_visited(_src9[0], _src9[1])
                                    _fr['tgt'][_n] = tgt = None
                                    _fr['prog'].pop(_n, None)
                                else:
                                    _pt, _pd = _fr['prog'].get(_n, (nowt, d))
                                    if d < _pd - 0.3:
                                        _fr['prog'][_n] = (nowt, d)
                                    elif nowt - _pt > 45.0:
                                        # 45 sim초 접근 없음 — 잠정 제외 후 재선정
                                        _fr['bl'][(_n, round(tgt[0], 1),
                                                   round(tgt[1], 1))] = nowt + 120.0
                                        print(f"[지도제작] {_n} 목표 정체 — 제외·재선정",
                                              flush=True)
                                        _fr['tgt'][_n] = tgt = None
                                        _fr['prog'].pop(_n, None)
                            _live9 = _live_pts()
                            if tgt is None and _live9:
                                _others = [v for k, v in _fr['tgt'].items()
                                           if k != _n and v is not None]
                                _pick = None
                                _lb_live9 = _live9                      # [LB] 정책이 없으면 기본 선택 그대로
                                if _lb_pol is not None:
                                    _lb_live9 = []                      # [LB] 정책이 고른다(None 이면 이 라운드 유휴)
                                    _cands = []
                                    for _f in _live9:
                                        if any(k[0] == _n and _m.hypot(_f[0] - k[1], _f[1] - k[2]) < 0.5
                                               for k in _fr['bl']):
                                            continue
                                        _s = _near_free(_f[0], _f[1])
                                        if _s is None:
                                            continue
                                        _cands.append((_f, _s))
                                    _fr['lb_round'] = _fr.get('lb_round', 0) + 1
                                    try:
                                        _obs = _LbObs(t=nowt - _t0, round_index=_fr['lb_round'], robot=_n,
                                                      robot_spec=_lb_specs.get(_n), my_pos=(rp[0], rp[1]),
                                                      robots_pos=dict(_fr['pos']), others_targets=list(_others),
                                                      candidates=[_LbCand(x=_s[0], y=_s[1], src_x=_f[0], src_y=_f[1],
                                                                          dist=_m.hypot(_s[0] - rp[0], _s[1] - rp[1]))
                                                                  for _f, _s in _cands],
                                                      known_cells=_fr['known'], grid=_fr.get('grid'),
                                                      visited=list(_fr['visited']))
                                        _act = _lb_pol.decide(_obs)
                                        _ci = getattr(_act, 'choice', None)
                                        if _ci is not None:
                                            _ci = int(_ci)
                                            if 0 <= _ci < len(_cands):
                                                _f, _pick = _cands[_ci]
                                            else:
                                                raise ValueError('choice %r 가 후보 범위(0..%d) 밖' % (_ci, len(_cands) - 1))
                                    except Exception as _pe:
                                        rospy.logwarn('[지도제작][RL 프록시] 정책 오류 — 이 라운드 기본 선택: %s', _pe)
                                        _pick = None
                                        _lb_live9 = _live9
                                for _f in sorted(_lb_live9, key=lambda f: _m.hypot(
                                        f[0] - rp[0], f[1] - rp[1])):
                                    if any(k[0] == _n
                                           and _m.hypot(_f[0] - k[1],
                                                        _f[1] - k[2]) < 0.5
                                           for k in _fr['bl']):
                                        continue
                                    _s = _near_free(_f[0], _f[1])
                                    if _s is None:
                                        continue
                                    # 간격 0.8→2.0m (2026-08-09: 프런티어가 한
                                    # 구역에 몰리면 전원이 같은 곳으로 뭉침)
                                    if any(_m.hypot(_s[0] - o[0], _s[1] - o[1]) < 2.0
                                           for o in _others):
                                        continue
                                    _pick = _s
                                    break
                                if _pick is None:
                                    # 이 로봇 몫 후보 없음 — 60 sim초 지속 시 개별 완료
                                    _t9 = _fr['idle'].setdefault(_n, nowt)
                                    if (nowt - _t9 > 60.0
                                            and nowt - _fr.get('fp_t', -1e9) < 15.0):
                                        _fr['rdone'].add(_n)
                                        _rdpub[_n].publish(_Bool(True))
                                        print(f"[지도제작] {_n} 몫 프런티어 소진 — "
                                              "개별 완료", flush=True)
                                else:
                                    _fr['idle'].pop(_n, None)
                                if _pick is not None:
                                    # 스냅 전 원본 프런티어를 함께 기억 —
                                    # 도착 시 그 지점을 영구 제외해야 한다
                                    # (_near_free 가 최대 1.0m 옮기므로 스냅
                                    #  지점만 제외하면 원본이 살아남는다)
                                    _fr.setdefault('src', {})[_n] = (_f[0], _f[1])
                                    _fr['tgt'][_n] = _pick
                                    _fr['prog'][_n] = (nowt, _m.hypot(
                                        rp[0] - _pick[0], rp[1] - _pick[1]))
                                    _msg = _PS()
                                    _msg.header.frame_id = 'map'
                                    _msg.header.stamp = rospy.Time.now()
                                    _msg.pose.position.x = _pick[0]
                                    _msg.pose.position.y = _pick[1]
                                    _msg.pose.orientation.w = 1.0
                                    _tpub[_n].publish(_msg)
                                    print(f"[지도제작] {_n} 목표 갱신 → "
                                          f"({_pick[0]:.2f},{_pick[1]:.2f})",
                                          flush=True)
                        # 도달 카운트 등 트리 표시 주기 갱신 (스케줄러 이벤트 없이도)
                        group1.publish_status('running', root_task)
                    except Exception as _fe:
                        rospy.logwarn('[지도제작] 피더 오류(계속): %s', _fe)
            if _distributed:
                # [RL G3] 분산 모드의 종료: 로봇마다 자기 정책이 '끝' 을 정해 explore 액션이 끝나면 스케줄러가 그 task 를 완료로
                # 표시한다. 여기서는 그것만 지켜보다가 전원 완료 때 가상 task(지도 송신/병합)·병목 가지를 닫고 스케줄러를 깨운다.
                # 등록되지 않은 로봇의 explore task 는 120초 뒤 완료로 간주(기존 피더의 플래토 처리와 같음).
                _res_box = {}      # [R5 F7] host 의 결과물 제출 알림(/jnp/explore_result, latched JSON) — 자기 보고
                _recv_box = []     # [R7 F4] 채점 모니터의 수신 확인(/lb/result_received, latched JSON) — trusted 확인

                def _res_cb(_m):
                    try:
                        _res_box.update(json.loads(_m.data))
                    except Exception:
                        pass

                def _recv_cb(_m):
                    try:
                        _recv_box.append(json.loads(_m.data))
                    except Exception:
                        pass
                try:
                    group1._res_sub = rospy.Subscriber('/jnp/explore_result', String, _res_cb, queue_size=1)
                    group1._recv_sub = rospy.Subscriber('/lb/result_received', String, _recv_cb, queue_size=10)
                except Exception as _rse:
                    print('[지도제작] 결과 알림 구독 실패(계속): %s' % _rse, flush=True)

                def _dist_watch():
                    _t0d = rospy.get_time()
                    while not rospy.is_shutdown():
                        try:
                            rospy.sleep(3.0)
                        except Exception:
                            break
                        _now = rospy.get_time()
                        _pending = []
                        for _tn, _tt in _etasks.items():
                            if getattr(_tt, 'complete', False):
                                continue
                            if getattr(_tt, 'agent', None) is None:
                                if _now - _t0d > 120.0:
                                    _tt.complete = True
                                    _tt.lb_result = 'unassigned_timeout'        # 미배정 로봇의 explore: 성공이 아니라 시간 초과로 닫음(표시)
                                    print('[지도제작] %s 는 120 s 동안 미배정 — 시간 초과로 닫음(성공 아님)' % _tn, flush=True)
                                    continue
                            _pending.append(_tn)
                        if _pending:
                            continue
                        # [R5 F7] 결과물 제출 확인: host 가 병합 지도를 냈다는 알림이 있어야 병합·송신 가상 task 를 완료로 본다(최대 15 s 대기)
                        _w0 = rospy.get_time()
                        while not _res_box and rospy.get_time() - _w0 < 15.0 and not rospy.is_shutdown():
                            try:
                                rospy.sleep(1.0)
                            except Exception:
                                break
                        _fr['done'] = True
                        _self = bool(_res_box) and (_res_box.get('robot') == _merge_host)
                        try:
                            _ep_run = rospy.get_param('/lb/episode/run_id', None)      # [R8 F3] 회차 ID — 확인 메시지와 자기 보고가 같은 회차·같은 결과물이어야 한다
                        except Exception:
                            _ep_run = None

                        def _confirmed():
                            # [R9 F2] 확인은 run_id·digest 가 **둘 다 있고 같을 때만** 인정한다 — 누락이면 바이트·시각 같은 대체 근거로 돌아가지 않는다
                            out9 = []
                            for r in _recv_box:
                                if not r.get('valid') or str(r.get('sender', '')) != str(_merge_host):
                                    continue
                                if not (_ep_run and r.get('run_id') == _ep_run):
                                    continue
                                if not (_self and _res_box.get('run_id') == _ep_run):      # [R10 F2] 자기 보고의 run_id 도 현재 회차와 정확히 같아야 한다
                                    continue
                                if not (_res_box.get('digest') and r.get('digest') and r.get('digest') == _res_box.get('digest')):
                                    continue
                                out9.append(r)
                            return out9
                        _conf = _confirmed()
                        if _self and not _conf:                          # 자기 보고만 있으면 trusted 확인을 잠깐 더 기다린다
                            _w1 = rospy.get_time()
                            while not _confirmed() and rospy.get_time() - _w1 < 10.0 and not rospy.is_shutdown():
                                try:
                                    rospy.sleep(1.0)
                                except Exception:
                                    break
                            _conf = _confirmed()
                        _ok = bool(_conf)                                # [R7 F4] 병합 task 완료 = trusted 모니터가 host 의 유효 결과물을 받았다는 확인
                        _partial = bool(_res_box.get('partial')) if _self else False
                        for _mt in _mtasks.values():
                            _mt.assign_status = False
                            _mt.complete = bool(_ok)
                            _mt.lb_run_id = _ep_run
                            _mt.lb_digest = (_conf[0].get('digest') if _ok else None)
                            _mt.lb_result = (('submitted_partial' if _partial else 'submitted') + '_confirmed') if _ok else (
                                'submitted_unconfirmed' if _self else ('no_submission' if not _res_box else 'submitted_by_non_host:%s' % _res_box.get('robot')))
                        for _ent9 in _cnodes.values():
                            for _c9 in _ent9:
                                _c9.assign_status = False
                                _c9.complete = True
                        _dpub.publish(_Bool(True))
                        print('[지도제작] 분산 모드 — 로봇 전원이 탐사 완료를 보고 → 미션 종료 (결과물: %s)' % (
                            ('제출·수신 확인' + (' (부분)' if _partial else '')) if _ok else
                            ('host 자기 보고만 있고 채점 모니터 수신 확인 없음 — 미확정(병합 task 미완료)' if _self else
                             ('없음 — 병합·송신 task 미완료' if not _res_box else 'host 가 아닌 %s 가 제출 — 미완료' % _res_box.get('robot')))), flush=True)
                        if hasattr(group1, '_scheduler'):
                            group1._scheduler.wake()
                        return
                threading.Thread(target=_dist_watch, daemon=True).start()
            else:
                threading.Thread(target=_feeder, daemon=True).start()

            def _post_explore_save():
                if _distributed:
                    print('[지도제작] 분산 모드 — 병합 지도는 제작자 몫(host 로봇의 merged_map 제공 항목). 중앙 저장 생략', flush=True)
                    return
                try:
                    # map_saver 는 상위 폴더를 만들지 않는다. 런타임 산출물 폴더라
                    # 저장소에 없으므로 새로 설치한 환경에서는 여기서 만들어 준다.
                    os.makedirs('/root/tesla/ros/navi/maps/jnp_explored', exist_ok=True)
                    subprocess.run(
                        ['bash', '-c',
                         'source /opt/ros/noetic/setup.bash; timeout 30 rosrun '
                         'map_server map_saver -f /root/tesla/ros/navi/maps/'
                         'jnp_explored/map map:=/map'], timeout=40)
                    print('[지도제작] 완성 지도 저장: maps/jnp_explored/', flush=True)
                except Exception as _e:
                    rospy.logwarn('지도 저장 실패: %s', _e)
            group1._post_success_hook = _post_explore_save
        else:
            root_task = _plan_or_legacy(group1.goal, task_payload,
                                        lambda: build_relay_tree(task_payload), group=group1)['root']
        if not root_task.subtasks:
            print("Group: payload 전체가 형식 오류 — coalition 성립 불가", flush=True)
            group1.publish_status('failed', None, note='payload 형식 오류')
            group1.dissolve() if group_type == 'coalition' else os._exit(1)
        # 기대 멤버 수 = 참여 로봇 수 (payload 형식이 태스크별로 다름)
        if 'Mult-Goal' in group1.goal:
            _g2, _r2 = parse_multigoal_payload(task_payload)
            expected_members = max(1, len(_r2))
        else:
            robot_names = {s.split('=')[0].strip() for s in task_payload.split(';')
                           if '=' in s and s.split('=')[0].strip()}
            expected_members = max(1, len(robot_names))
    else:
        tasks = TaskTree()
        group1.setTaskTree(tasks)
        root_task = tasks.root_task
        expected_members = 1

    if use_sched:
        # ---- 신규 경로: 모듈화된 스케줄러/할당기 ----
        # 다른 알고리즘으로 바꾸려면 SimpleScheduler/SimpleAllocator 대신
        # Scheduler/Allocator 인터페이스를 구현한 클래스를 넣으면 된다.
        # 멤버 대기: search() 직후 늦게 발견되는 에이전트 여유 (최대 20s, 최소 1명이면 진행)
        if getattr(group1, '_recruited', False):
            expected_members = len(group1.member_list)      # [0.9.0] 멤버 = 역할 할당 결과 — 더 기다리지 않는다
        group1.publish_status('forming', root_task, note='멤버 수집 중' if not getattr(group1, '_recruited', False) else '편성 완료')
        _t_end = rospy.get_time() + 20.0
        while (len(group1.member_list) < expected_members and rospy.get_time() < _t_end
               and not rospy.is_shutdown()):
            rospy.sleep(0.5)
            group1.publish_status('forming', root_task, note='멤버 수집 중')
        if not group1.member_list:
            print("[SCHED] member 없음 — coalition 성립 불가, 종료", flush=True)
            group1.publish_status('failed', root_task, note='member 없음 — coalition 성립 불가')
            # coalition 이면 kill 발행까지 해서 유령 소속을 남기지 않는다
            group1.dissolve() if group_type == 'coalition' else os._exit(1)
        print(f"[SCHED] members = {[a.name for a in group1.member_list]}")
        # 릴레이(payload) 트리는 다리 이름의 로봇에 전담 배정: 'relay1.robot_a' → robot_a.
        # 지정 로봇이 없으면 first-fit 폴백 (AffinityAllocator + prefer_fn)
        if task_payload and 'Mult-Goal' in group1.goal:
            _goals, _homes = parse_multigoal_payload(task_payload)
            # ── goal 진입 순서 제어: 한 번에 1대만 goal 점유 (병목/충돌 방지) ──
            from std_srvs.srv import Trigger, TriggerResponse
            # busy + since(sim s): 보유자 사망 시 timeout 자동 반납 (리뷰 #3)
            group1._entry_busy = {g: {'busy': False, 'since': 0.0}
                                  for g in _goals}
            group1._entry_lock = threading.Lock()
            _ENTRY_TIMEOUT = 240.0      # goal 점유(진입→반납)는 짧다 — 240 sim초면 사망 판정

            def _mk_acquire(gname):
                def _srv(_req):
                    with group1._entry_lock:
                        e = group1._entry_busy[gname]
                        now = rospy.get_time()
                        if e['busy'] and now - e['since'] > _ENTRY_TIMEOUT:
                            rospy.logwarn('goal_entry %s: 보유 시간초과 — 자동 반납',
                                          gname)
                            e['busy'] = False
                        if not e['busy']:
                            e['busy'] = True
                            e['since'] = now
                            return TriggerResponse(success=True, message='granted')
                    return TriggerResponse(success=False, message='busy')
                return _srv

            def _mk_release(gname):
                def _srv(_req):
                    with group1._entry_lock:
                        group1._entry_busy[gname]['busy'] = False
                    return TriggerResponse(success=True, message='released')
                return _srv
            for _g in _goals:
                rospy.Service('/goal_entry_%s/acquire' % _g, Trigger, _mk_acquire(_g))
                rospy.Service('/goal_entry_%s/release' % _g, Trigger, _mk_release(_g))

            # ── 남은 물품 수 발행: 왕복(복귀) 완료된 item 수 기준 ──
            group1._items_pub = rospy.Publisher('/goal_items', String,
                                                queue_size=4, latch=True)

            def _publish_items(root):
                try:
                    for sub in root.subtasks:
                        gname = sub.name.split('[')[0]
                        if gname not in _goals:
                            continue
                        total = len(sub.subtasks)
                        done = sum(1 for t in sub.subtasks if t.complete)
                        gx, gy, _c = _goals[gname]
                        group1._items_pub.publish(
                            f"{gname}:{total - done}:{gx:.2f},{gy:.2f}")
                except Exception as _e:
                    rospy.logwarn('goal_items 발행 실패: %s', _e)
            group1._publish_items = _publish_items
            # 시작 직후 초기 개수 발행 — goal 판/물품 표시가 즉시 나타나게
            for _g, (_gx, _gy, _c) in _goals.items():
                group1._items_pub.publish(f"{_g}:{_c}:{_gx:.2f},{_gy:.2f}")
            # latch 는 '마지막 1건'만 유지 — 늦게 구독한 노드(교통관제 등)를 위해
            # 주기 재발행 (수신측은 멱등 — 리뷰 #5/#7/#14)
            def _repub_items(_ev):
                try:
                    if getattr(group1, '_last_root', None) is not None:
                        _publish_items(group1._last_root)
                    else:
                        for _g2, (_gx2, _gy2, _c2) in _goals.items():
                            group1._items_pub.publish(
                                f"{_g2}:{_c2}:{_gx2:.2f},{_gy2:.2f}")
                except Exception:
                    pass
            group1._items_timer = rospy.Timer(rospy.Duration(5.0), _repub_items)
            group1._goals = _goals          # mgjoin 대상 판정용

            def _count_unassigned(t):
                if isinstance(t, AtomicTask):
                    return 0 if (t.complete or t.assign_status) else 1
                return sum(_count_unassigned(u) for u in t.subtasks)

            def _release_surplus(root):
                """유휴 멤버 + 내 트리에 미배정 물품 없음 → 방출(mgrelease).
                방출된 에이전트는 탈퇴와 동시에 물품 남은 goal 그룹에 가입한다.
                ★ 예외를 반드시 로그로 — 스케줄러 on_update 의 except-pass 에 묻히면
                마지막 멤버가 명단에 남는 불일치가 생긴다 (2026-08-08 실측)."""
                try:
                    if _count_unassigned(root) > 0:
                        return
                    for a in list(group1.member_list):
                        if not a.free:
                            continue
                        short = a.name.strip('/').split('/')[-1]
                        group1.member_list[:] = [x for x in group1.member_list
                                                 if x is not a]
                        if getattr(group1, 'allowed_members', None) is not None:
                            group1.allowed_members.discard(short)
                        group1.publisher.publish(
                            f"mgrelease:{a.name}:{rospy.get_name()}"
                            f":{','.join(sorted(_goals))}")
                        print(f"[이적] 유휴 방출: {short} (미배정 물품 없음)", flush=True)
                except Exception as _e:
                    rospy.logwarn('[이적] 방출 실패: %s', _e)
            group1._release_surplus = _release_surplus
            _homes_xy = {k: v for k, v in _homes.items() if v is not None}
            if _homes_xy:
                # 좌표가 오면 특성(거리) 할당기
                allocator = MultiGoalAllocator({g: (v[0], v[1]) for g, v in _goals.items()},
                                               _homes_xy)
            else:
                # goal별 그룹(이름 명단만): 멤버 아무나 유휴 순 — 동시 왕복
                allocator = SimpleAllocator()
        elif task_payload:
            def _leg_robot(t):
                parts = t.name.split('.', 1)
                return parts[1] if len(parts) > 1 else None

            def _prefer_named(t, cands):
                want = _leg_robot(t)
                if want:
                    for a in cands:
                        if want in a.name:
                            return a
                    return None      # 지정 로봇 미등록 — 엉뚱한 로봇 배정 금지 (리뷰 #6/#11)
                return cands[0]
            allocator = AffinityAllocator(_leg_robot, prefer_fn=_prefer_named)
        else:
            allocator = SimpleAllocator()
        allocator.skills_strict = getattr(group1, '_skills_strict', False)   # [V-F6] goal 모드의 기존 할당기도 같은 적격 정책
        if getattr(group1, '_role_bind', None) is not None:
            # [JnP-0.9.0] 역할 할당기: 역할 task 는 묶인 로봇으로만(미션 동안 고정), 풀 task 는 기존 할당기 규칙(ETA 등) + 적격 검사
            _pool_alloc = allocator
            allocator = RoleAllocator(group1._role_bind, pool_fn=lambda t, cands: _pool_alloc.select(t, cands),
                                      skills_strict=getattr(group1, '_skills_strict', False))
            group1._mg_alloc_inner = _pool_alloc
        def _on_update(r):
            # 순서 중요(2026-08-08 레이스): ⑴ 남은 물품 수를 먼저 발행해
            # 이적 에이전트가 최신 값을 보게 하고, ⑵ 방출, ⑶ 명단 반영된 status.
            if hasattr(group1, '_publish_items'):
                group1._publish_items(r)
            if hasattr(group1, '_release_surplus'):
                group1._release_surplus(r)
            if hasattr(group1, '_bt_from_tree'):
                group1._bt_from_tree(r)      # 충돌회피: 병목 표시 상태(트리 파생)
            group1.publish_status('running', r)
        scheduler = SimpleScheduler(allocator=allocator,
                                    allow_idle=('MapExplore' in group1.goal),
                                    log=lambda m: print(m, flush=True),
                                    end_timeout=3600.0,  # ★벽시계 초 — 저 RTF(0.2)에서
                                    # 에이전트의 sim초 대기(병목 600 sim초=벽 ~50분)를
                                    # 견디도록 상향 (리뷰 #5: 벽/심 불일치)
                                    on_update=_on_update,
                                    skills_strict=getattr(group1, '_skills_strict', False))
        group1._scheduler = scheduler       # mgjoin 영입 시 즉시 재배정용
        group1._mg_alloc = getattr(group1, '_mg_alloc_inner', allocator)   # 이적 로봇 홈 좌표 갱신용(풀 할당기)
        group1._last_root = root_task           # 해제 시 최종 트리 발행용
        # ── 정족수 대기: payload 명단 전원이 등록될 때까지 (벽시계 최대 15초) ──
        # 첫 배정 때 늦게 등록된 멤버(특히 리더 자신)가 빠져 일감을 못 받는 문제 방지.
        # 등록은 네트워크(벽시계) 과정이라 sim-time rospy.sleep 대신 wall time 사용.
        _allowed = getattr(group1, 'allowed_members', None)
        if _allowed and getattr(group1, 'recruit_mode', 'skills') != 'skills':   # [0.9.0] skills 편성은 멤버가 이미 확정
            import time as _time
            _t0 = _time.monotonic()
            while _time.monotonic() - _t0 < 15.0:
                _have = {a.name.strip('/').split('/')[-1] for a in group1.member_list}
                if _have >= set(_allowed):
                    break
                _time.sleep(0.5)
            _have = {a.name.strip('/').split('/')[-1] for a in group1.member_list}
            _miss = set(_allowed) - _have
            print(f"[SCHED] 멤버 정족수 {len(_have)}/{len(_allowed)}"
                  + (f" (미등록: {sorted(_miss)} — 없이 진행)" if _miss else " — 전원 등록"),
                  flush=True)
        # 위치공유(mutual_obstacles) 노드에 그룹 구성 알림 (시맨틱: 멤버 간 위치 교환)
        try:
            _sg = rospy.Publisher('/mutual_obstacles/set_group', String,
                                  queue_size=2, latch=True)
            _names = ','.join(sorted(
                a.name.strip('/').split('/')[-1] for a in group1.member_list))
            _sg.publish(f"{rospy.get_name()}:{_names}")
        except Exception as _e:
            rospy.logwarn('set_group 발행 실패: %s', _e)
        ok = scheduler.run(root_task, group1.member_list)
        print(f"[SCHED] result = {'SUCCESS' if ok else 'FAILED'}", flush=True)
        group1._task_done = True                 # 이후 mgjoin 영입 거부
        if ok and hasattr(group1, '_post_success_hook'):
            try:
                group1._post_success_hook()      # 예: 지도제작 — 완성 지도 저장
            except Exception as _he:
                rospy.logwarn('성공 후 훅 실패: %s', _he)
        if ok and hasattr(group1, '_release_surplus'):
            group1._release_surplus(root_task)   # 최종 방출 보증 — 명단 비움
        group1.publish_status('success' if ok else 'failed', root_task,
                              note='전체 task 완료' if ok else '실행 실패')
        if group_type == 'coalition':
            # ★ 성공이든 실패든 해체 — 실패 시 살아남으면 서비스가 계속 응답하는
            #   좀비 그룹이 되어 이후 모든 coalition 형성을 영구히 막는다(리뷰 확정)
            group1.dissolve('goal 도달' if ok else '실행 실패', root_task)
        else:
            # team: 그룹/트리 유지 — 'Group 해제' 명령(dissolve:)이 올 때까지 생존.
            # 5초마다 상태를 재발행해 늦게 연 Monitor 도 트리를 볼 수 있게 한다
            print("Group: team 유지 — 해제 명령 대기", flush=True)
            while not rospy.is_shutdown():
                rospy.sleep(5.0)
                if getattr(group1, '_dissolving', False):
                    break               # 해체 진행 중 — 상태 재발행 금지
                group1.publish_status('success' if ok else 'failed', root_task,
                                      note='완료 — 그룹 유지 중 (해제 버튼 대기)')
    else:
        # ---- 기존 baseline 경로 (로직 무변경 — 트리 변수만 root_task 로 통일) ----
        group1.task_allocation(root_task)
        print("Initial Allocation Complete: ========")
        for task in root_task.subtasks:
            if isinstance(task, AtomicTask):
                print(f"task name={task.name} status={task.assign_status}")
            else:
                print(f"task name={task.name} Composite")
                for task2 in task.subtasks:
                    if isinstance(task2, AtomicTask):
                        print(f"task name={task2.name} status={task2.assign_status}")
                    else:
                        print(f"task name={task2.name} Composite")

        group1.task_execution(root_task)
    
