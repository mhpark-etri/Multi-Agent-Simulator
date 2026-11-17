#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.9.0 2026-10-18] 편성(모집) 통합 검사 — 검토 V-F1~V-F7 의 반례를 반전한 회귀검사.
# 실제 _recruit_and_plan / _plan_or_legacy / 빌더 / validator / 할당기 / dispatch 본문을 부르고, ROS 통신(접속·발행·대기)만 가짜로 바꾼다.
#   source <workspace>/devel/setup.bash && python3 test/test_recruit.py
import copy
import inspect
import json
import os
import sys
import threading
import types
from unittest.mock import patch

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import plan_to_tasktree as T                  # noqa: E402
import jnp_plan as P                          # noqa: E402
import jnp_scheduler as S                     # noqa: E402
import jnp_group as G                         # noqa: E402

F = [0]


def ok(what, cond, detail=''):
    print('%s %s %s' % ('PASS' if cond else 'FAIL', what, detail))
    if not cond:
        F[0] += 1


def cand(n, owner=None, sk=None, caps='lidar'):
    return G.Agent('/etri/' + n, 'Relay', caps or 'lidar', owner, skills=(sk if sk is not None else ['GoTo']))


class FakeGroup(types.SimpleNamespace):
    """실제 JnPGroup 대신: 명부 회차(rounds)·접속 실패(fail)·파라미터(params)를 주입. 종료는 terminate() 로 기록(프로세스 종료 없음)."""


def make_group(rounds, params=None, fail=lambda n: False):
    g = FakeGroup(member_list=[], _task_done=False, recruit_mode='skills', node_name='g', terminated=[], statuses=[], searched=[],
                  _killed=set(), agent_list=[], _reg_gen={}, _member_lock=threading.Lock())
    it = iter(rounds)
    last = {'r': None}

    def collect():
        try:
            last['r'] = next(it)
        except StopIteration:
            pass                      # 더 없으면 마지막 회차 반복
        out = [cand(n, g, sk, caps) for n, sk, caps in (last['r'] or [])]
        for a in out:
            a.gen = g._reg_gen.get(a.name, 0)         # 실제 collect_candidates 와 같이 설명 시점의 등록 세대를 담는다
        return out
    g.collect_candidates = collect
    g.robot_positions = lambda ns: {}
    g.register_candidate = types.MethodType(G.JnPGroup.register_candidate, g)
    g.publish_status = lambda state, root=None, note='': g.statuses.append((state, note))
    g.terminate = lambda note: g.terminated.append(note)
    g.search = lambda: g.searched.append(True)

    def connect(a, timeout=5.0):
        if fail(a.short):
            return False
        a.client = types.SimpleNamespace(send_goal=lambda *x, **k: None)
        return True
    pr = params or {}
    patches = [patch.multiple(G.rospy, logwarn=lambda *a, **k: None, loginfo=lambda *a, **k: None, sleep=lambda *a: (_ for _ in ()).throw(AssertionError('rospy.sleep 호출됨'))),
               patch.object(G.Agent, 'connect', connect), patch.object(G, '_param', lambda n, d: pr.get(n, d)),
               patch.object(P, 'publish', lambda *a: True), patch.object(P, 'publish_unassigned', lambda *a: True),
               patch.object(P, 'publish_fallback', lambda *a: True), patch('time.sleep', lambda *a: None)]
    return g, patches


def run(g, patches, fn):
    for p in patches:
        p.start()
    try:
        return fn()
    finally:
        for p in reversed(patches):
            p.stop()


# ── V-F1 접속 객체 유지·마지막 실패·벽시계 대기 ──
def vf1():
    print('== V-F1')
    g, ps = make_group([[('a', None, ''), ('b', None, '')], [('a', None, ''), ('c', None, '')]], {'~candidates': 'prefer-list'}, fail=lambda n: n == 'b')
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('V-F1a 재할당 뒤에도 a 의 접속 객체 유지, c 접속', [(m.short, m.client is not None) for m in g.member_list] == [('a', True), ('c', True)]
       and g._role_bind['leg1'].client is not None and g._role_bind['leg1'] is g.member_list[0])
    a = g._role_bind['leg1']
    a.setTask(P._exec_atomics(r['root'])[0])
    try:
        a.start_task(types.SimpleNamespace(notify_end=lambda *x: None))
        sent = True
    except AttributeError:
        sent = False
    ok('V-F1a start_task 가 send_goal 가능(client 보존)', sent)
    g, ps = make_group([[('a', None, '')], [('a', None, ''), ('b', None, '')]], {'~unassigned_policy': 'wait', '~candidates': 'prefer-list'})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('V-F1b wait 재수집 뒤 두 멤버 모두 접속 객체 보유', [(m.short, m.client is not None) for m in g.member_list] == [('a', True), ('b', True)]
       and r['recruit']['attempts'] == 2)
    g, ps = make_group([[('bad%d' % i, None, '')] for i in range(5)], {'~candidates': 'all'}, fail=lambda n: True)
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'bad0=1,0,0'))
    ok('V-F1c 네 번째 접속 실패도 배정 불가(성공 경로 아님): root None, 멤버 없음, 사유 connect_failed',
       r['root'] is None and r['unassigned'] == ['leg1'] and g.member_list == [] and r['recruit']['reasons']['leg1'].get('connect_failed') == 'bad3'
       and r['recruit']['attempts'] == 4)
    g, ps = make_group([[('a', None, '')]], {'~unassigned_policy': 'wait', '~recruit_timeout': 0.0})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('V-F1d wait 기한 0 → 즉시 배정 불가(벽시계 기한, rospy.sleep 미사용)', r['root'] is None and r['unassigned'] == ['leg2'])


# ── V-F2 skip ──
def vf2():
    print('== V-F2')
    g, ps = make_group([[]], {'~unassigned_policy': 'skip', '~candidates': 'all'})
    r = run(g, ps, lambda: G._plan_or_legacy('ObjectSearch', '', lambda: G.build_object_search_tree(['a', 'b']), group=g, names=['a', 'b']))
    ok('V-F2a 두 역할 모두 skip → 실행할 계획 없음: 그룹 종료(terminate), legacy 로 가지 않음', r['root'] is None and g.terminated and not g.searched
       and r.get('source') == 'plan' and '편성 실패' in g.terminated[0])
    g, ps = make_group([[('a', ['Patrol'], 'lidar,camera')]], {'~unassigned_policy': 'skip', '~candidates': 'all'})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'ObjectSearch', '', names=['a', 'b']))
    keys = sorted(r['dicts']['etasks'])
    ok('V-F2b 한 역할만 skip: 피더 키는 실제 로봇뿐, 가짜 이름 없음, skipped 기록',
       keys == ['a'] and r['skipped'] == ['searcher2'] and '(none)' not in json.dumps(r['roles_bound'])
       and any(x['reason'].get('skipped') and x['role'] == 'searcher2' for x in r['assignments'])
       and [t.name for t in P._exec_atomics(r['root'])] == ['patrol.a', 'detect.a'])
    rec = P.plan_record(r, 'ObjectSearch', '/g')
    ok('V-F2b 기록(외부 rec): skipped·roles_all·assignments 에 원래 역할 보존, 트리엔 a 만', rec['skipped'] == ['searcher2'] and rec['roles_all'] == ['searcher1', 'searcher2']
       and [x['role'] for x in rec['assignments']] == ['searcher1', 'searcher2'] and 'patrol.a' in rec['tree'] and '(none)' not in rec['tree'])
    g, ps = make_group([[('a', ['Explore'], 'lidar,compute_arm')]], {'~unassigned_policy': 'skip', '~candidates': 'all'})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'MapExplore', '', names=['a', 'b']))
    ok('V-F2c 지도제작: host 는 a, explorer1 skip(SendMap 은 공유 서비스 아님)', r['roles_bound'] == {'host': 'a'} and r['skipped'] == ['explorer1']
       and sorted(r['dicts']['mtasks']) == ['a'] and r['dicts']['mtasks']['a'].name == 'merge_maps.a')
    g, ps = make_group([[]], {'~unassigned_policy': 'skip', '~candidates': 'all'})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'MapExplore', '', names=['a']))
    ok('V-F2c host 는 공유 서비스(MergeMaps) 때문에 skip 불가 → 배정 불가', r['root'] is None and r['unassigned'] == ['host']
       and '공유 서비스' in r['recruit']['skip_blocked']['host'])
    g, ps = make_group([[]], {'~unassigned_policy': 'skip', '~candidates': 'all'})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0'))
    ok('V-F2c 릴레이(GoTo 는 선택 태스크 아님) skip 불가', r['root'] is None and '선택 태스크가 아닌' in r['recruit']['skip_blocked']['leg1'])
    g, ps = make_group([[]], {'~unassigned_policy': 'skip', '~candidates': 'all'})
    r = run(g, ps, lambda: G._plan_or_legacy('MapExplore', '', lambda: G.build_map_explore_tree(['a'], 'a'), group=g, names=['a']))
    ok('V-F2d 정책 실패는 legacy 대체가 아니라 종료', g.terminated and not g.searched and r['root'] is None and '배정 불가' in g.terminated[0])


# ── V-F3 제거된 멤버 ──
def vf3():
    print('== V-F3')
    a = cand('a')
    r = P.build_relay('a=1,0,0')
    task = P._exec_atomics(r['root'])[0]
    ok('V-F3a RoleAllocator: 묶인 로봇이 현재 멤버가 아니면 None', S.RoleAllocator({'leg1': a}).select(task, []) is None
       and S.RoleAllocator({'leg1': a}).select(task, [a]) is a)
    sent = []
    a.start_task = lambda sched: sent.append(a.name)
    a.setTask = lambda t: None
    logs = []

    class _Blind(S.Allocator):
        def select(self, task, agents):
            return a
    n = S.SimpleScheduler(allocator=_Blind(), log=logs.append).dispatch(r['root'], [])
    ok('V-F3b dispatch 최종 방어: 할당기가 제거된 로봇을 골라도 발송 0', n == 0 and not sent and any('현재 멤버가 아님' in m for m in logs))
    ok('V-F3c AffinityAllocator 의 bind 도 현재 멤버 확인', S.AffinityAllocator(lambda t: 'k').select(task, [a]) is a
       and (lambda al: (al.select(task, [a]), al.select(task, []))[1])(S.AffinityAllocator(lambda t: 'k')) is None)


# ── V-F4 빈 list-only ──
def vf4():
    print('== V-F4')
    out = cand('outsider', sk=['GoTo', 'Trip'])
    r = S.assign_roles([{'name': 'r', 'skills': ['GoTo']}], [out], mode='list-only', prefer_names=[])
    pm, rej = S.pool_members({'skills': ['Trip']}, [out], mode='list-only', prefer_names=[])
    ok('V-F4a 빈 명단 list-only: 역할·풀 모두 아무도 아님', r['unassigned'] == ['r'] and r['rejected']['r']['outsider'] == {'outside_list': True}
       and r['reasons']['r']['list_empty'] is True and pm == [] and rej['outsider'] == {'outside_list': True})
    g, ps = make_group([[('outsider', ['Trip'], 'lidar')]])
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Mult-Goal', 'goals=X:1,2:1;robots='))
    ok('V-F4b Mult-Goal 빈 robots= → 배정 불가(입력 오류), 명부 확대 없음', r['root'] is None and r['unassigned'] == ['(pool)'] and r['recruit']['list_empty'] is True
       and g.member_list == [])
    cs = [cand('a'), cand('b', sk=['Trip']), out]
    r = S.assign_roles([{'name': 'r1', 'skills': ['GoTo']}, {'name': 'r2', 'skills': ['GoTo']}], cs, mode='list-only', prefer_names=['a'])
    ok('V-F4c 한 명 명단: 그 로봇만, 둘째 역할 배정 불가(명단 밖 거부)', r['bound']['r1'].short == 'a' and r['unassigned'] == ['r2'] and r['rejected']['r2']['outsider'] == {'outside_list': True})
    r = S.assign_roles([{'name': 'r1', 'skills': ['GoTo']}, {'name': 'r2', 'skills': ['GoTo']}], cs, mode='list-only', prefer_names=['a', 'b'])
    ok('V-F4c 일부 부적격(b 는 GoTo 없음): r2 배정 불가', r['bound']['r1'].short == 'a' and r['unassigned'] == ['r2'] and r['rejected']['r2']['b'] == {'skills': ['GoTo']})
    r = S.assign_roles([{'name': 'r1', 'skills': ['Explore']}], cs, mode='list-only', prefer_names=['a', 'b'])
    ok('V-F4c 전원 부적격', r['unassigned'] == ['r1'] and set(r['rejected']['r1']) == {'a', 'b', 'outsider'})
    pm, rej = S.pool_members({'skills': ['Trip']}, cs, mode='list-only', prefer_names=['a', 'b'])
    ok('V-F4c 풀: 명단 안 적격(b)만', [x.short for x in pm] == ['b'] and rej['outsider'] == {'outside_list': True} and rej['a'] == {'skills': ['Trip']})


# ── V-F5 검증 빈틈 ──
def vf5():
    print('== V-F5')
    cat = T.load_catalog()
    base = P.build_map_explore(['a'], 'a')['plan']['canonical']
    doc = copy.deepcopy(base)
    next(a for a in T.iter_atomics(doc) if a['skill'] == 'Explore')['args'] = []
    ok('V-F5a args 가 객체가 아니면 오류', any('args must be an object' in e for e in T.validate_canonical(doc, cat)['errors']))
    doc = copy.deepcopy(base)
    next(a for a in T.iter_atomics(doc) if a['skill'] == 'Explore')['args'] = {'robot': 'physical_a'}
    ok('V-F5b args 에 숨은 역할 인자(robot) 거부', any('must not contain the role parameter' in e for e in T.validate_canonical(doc, cat)['errors']))
    doc = copy.deepcopy(base)
    doc['role_order'] = [{}]
    try:
        rep = T.validate_canonical(doc, cat)
        ok('V-F5c role_order 요소 형식 오류는 예외가 아니라 오류 목록', any('role_order must be a list of non-empty strings' in e for e in rep['errors']))
    except TypeError as e:
        ok('V-F5c role_order 요소 형식 오류는 예외가 아니라 오류 목록', False, str(e))
    doc = copy.deepcopy(base)
    doc['roles'] = [1]
    ok('V-F5c roles 형식 오류도 오류 목록', any('roles must be an object' in e for e in T.validate_canonical(doc, cat)['errors']))
    try:
        P.build_relay('a=1,0,0;b=2,0,0', roles_bound={'leg1': 'a', 'leg2': 'a'})
        dup = False
    except P.PlanBuildError as e:
        dup = '두 역할' in str(e)
    ok('V-F5d Relay 에서도 한 로봇 두 역할 바인딩 거부(R8 공통 경계)', dup)
    try:
        P.build_avoidance('bt=2,0,0.6;routes=R1:0,0>4,0|R2:0.5,0>4,0.5', G.parse_avoidance_payload, G._robot_speed, roles_bound={'R1': 'x', 'R2': 'x'})
        dup2 = False
    except P.PlanBuildError as e:
        dup2 = '두 역할' in str(e)
    ok('V-F5d Avoidance 도 거부', dup2)
    try:
        P.build_relay('a=1,0,0', roles_bound={'leg1': 'a', 'ghost': 'b'})
        extra = False
    except P.PlanBuildError as e:
        extra = '역할표에 없는' in str(e)
    ok('V-F5d 역할표 밖 키 거부', extra)
    doc = copy.deepcopy(base)
    next(a for a in T.iter_atomics(doc) if a['skill'] == 'Explore').pop('optional')
    ok('V-F5e optional 은 카탈로그와 같아야(Explore 에서 빼면 오류)', any('optional must follow the catalog' in e for e in T.validate_canonical(doc, cat)['errors']))
    ok('V-F5e 기본 계획의 canonical 은 여전히 오류 없음', not T.validate_canonical(base, cat)['errors']
       and not T.validate_canonical(P.build_relay('a=1,0,0;b=2,0,0')['plan']['canonical'], cat)['errors'])


# ── V-F6 goal 호환 모드 ──
def vf6():
    print('== V-F6')
    a, b = cand('a', sk=['GoTo']), cand('b', sk=['Trip'])
    r = P.build_multigoal('goals=X:1,2:1', G.parse_multigoal_payload)
    item = P._exec_atomics(r['root'])[0]
    ok('V-F6a SimpleAllocator: 첫 후보 부적격이면 둘째 적격 후보', S.SimpleAllocator().select(item, [a, b]) is b)
    ok('V-F6a AffinityAllocator 도 적격 집합 위에서', S.AffinityAllocator(lambda t: None).select(item, [a, b]) is b)
    mg = G.MultiGoalAllocator({'X': (1.0, 2.0)}, {'a': (0.0, 0.0), 'b': (10.0, 10.0)})
    ok('V-F6a MultiGoalAllocator: 거리상 a 가 가까워도 Trip 미광고라 b', mg.select(item, [a, b]) is b)
    sent = []
    for c in (a, b):
        c.setTask = lambda t: None
        c.start_task = (lambda c: (lambda sched: sent.append(c.short)))(c)
    n = S.SimpleScheduler(allocator=S.SimpleAllocator(), log=lambda m: None).dispatch(r['root'], [a, b])
    ok('V-F6a dispatch: 적격 후보 b 에 발송', n == 1 and sent == ['b'])
    u = G.Agent('/etri/u', 'Relay', 'lidar', None, skills=None)     # 미광고(None)
    al = S.SimpleAllocator()
    al.skills_strict = True
    ok('V-F6b 할당기의 skills_strict: 미광고 로봇 제외', al.select(item, [u]) is None and S.SimpleAllocator().select(item, [u]) is u)
    mg.skills_strict = True
    ok('V-F6b MultiGoalAllocator 도 strict 정책', mg.select(item, [u]) is None)


# ── V-F7 기본 후보 범위 ──
def vf7():
    print('== V-F7')
    rounds = [[('a', None, ''), ('b', ['Trip'], ''), ('outsider', None, '')]]
    g, ps = make_group(rounds)
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('V-F7a 기본(list-only): 명단 밖 로봇으로 대체하지 않음 → leg2 배정 불가', r['root'] is None and r['unassigned'] == ['leg2']
       and r['recruit']['mode'] == 'list-only' and r['recruit']['rejected']['leg2']['outsider'] == {'outside_list': True})
    g, ps = make_group(rounds, {'~candidates': 'prefer-list'})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('V-F7a prefer-list 를 명시하면 대체', r['roles_bound'] == {'leg1': 'a', 'leg2': 'outsider'} and r['recruit']['mode'] == 'prefer-list')
    g, ps = make_group(rounds, {'~candidates': 'anything'})
    r = run(g, ps, lambda: G._plan_or_legacy('Relay', 'a=1,0,0', lambda: G.build_relay_tree('a=1,0,0'), group=g))
    ok('V-F7b 알 수 없는 ~candidates 값은 편성 실패(legacy 아님)', r['root'] is None and g.terminated and not g.searched)
    xml = G.parse_description('<data><agent>/etri/x</agent><goal>Relay</goal><capability>lidar</capability><skills>GoTo</skills><busy>1</busy></data>')
    ok('V-F7c busy 는 광고 값(실행 중)일 뿐 — 적격에서 제외', xml['busy'] is True and S.can_execute(cand('x', busy=None) if False else types.SimpleNamespace(busy=True, skills=['GoTo'], capability_set={'lidar'}, name='/etri/x'), ['GoTo'], ['lidar'])[1] == {'busy': True})


# ── 권고 반영분 ──
def recs():
    print('== 권고(V-F8·V-F10·V-F11)')
    pos = {'known': (0.0, 0.0)}
    cs = [cand('unknown'), cand('known')]
    r = S.assign_roles([{'name': 'r', 'skills': ['GoTo']}], cs, starts={'r': (5.0, 0.0)}, positions=pos, speed_fn=G._robot_speed)
    ok('V-F11 시작점이 있으면 위치를 아는 후보가 모르는 후보보다 앞', r['bound']['r'].short == 'known' and r['reasons']['r']['pos_known'] is True)
    r = S.assign_roles([{'name': 'r', 'skills': ['GoTo']}], cs, starts={}, positions=pos, speed_fn=G._robot_speed)
    ok('V-F11 시작점이 없으면 위치 유무는 키가 아님(자연 정렬)', r['bound']['r'].short == 'known')
    g, ps = make_group([[]], {'~candidates': 'all'})
    r = run(g, ps, lambda: G._plan_or_legacy('Relay', 'a=1,0,0', lambda: G.build_relay_tree('a=1,0,0'), group=g))
    ok('V-F8 배정 불가 문구: 탐욕 배정에서 확보 못함(증명 아님)', g.terminated and '탐욕' in g.terminated[0])
    g = FakeGroup(member_list=[], _task_done=False, goal='Mult-Goal', node_name='g', _goals={'X': (1, 1)}, agent_list=[], allowed_members=set(),
                  _mg_alloc=types.SimpleNamespace(homes={}), recruit_mode='skills')
    g.get_description = lambda n: '<data><agent>a</agent><goal>Relay</goal><capability>lidar</capability><skills>Trip</skills><busy>0</busy></data>'
    g.register_member = types.MethodType(G.JnPGroup.register_member, g)
    import io
    import contextlib
    buf = io.StringIO()
    with patch.object(G.rospy, 'loginfo', lambda *a: None), patch.object(G.Agent, 'connect', lambda a, timeout=5.0: True), contextlib.redirect_stdout(buf):
        G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='mgjoin:X:/etri/a:0,0'))
    ok('V-F10 mgjoin: 등록 안 되면 영입 성공 로그 없음(거부 로그)', g.member_list == [] and '이적 영입 거부' in buf.getvalue() and '이적 영입 a' not in buf.getvalue())


# ── ROUND2: R2-F1 모집 중 제거 통보, R2-F2 재수집 예산 계약, R2-F3 설정 오류의 종료 ──
def r2():
    print('== R2-F1')
    g, ps = make_group([[('a', None, ''), ('b', None, '')]])
    g.agent_list = ['/etri/a', '/etri/b']

    def connect(a, timeout=5.0):
        if a.short == 'b':      # b 접속 도중 a 의 kill 통보(실제 discovery_callback)
            G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))
        a.client = types.SimpleNamespace(send_goal=lambda *x, **k: None)
        return True
    ps.append(patch.object(G.Agent, 'connect', connect))
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    names = [m.short for m in g.member_list]
    ok('R2-F1a 모집 중 kill 된 a 는 최종 편성에 되살아나지 않음(list-only: leg1 → b, leg2 배정 불가)', 'a' not in names and r['root'] is None
       and r['unassigned'] == ['leg2'] and 'a' in r['recruit']['killed'] and '/etri/a' in g._killed and g.member_list == [])
    g, ps = make_group([[('a', None, ''), ('b', None, ''), ('c', None, '')]], {'~candidates': 'prefer-list'})
    g.agent_list = ['/etri/a', '/etri/b', '/etri/c']
    ps.append(patch.object(G.Agent, 'connect', connect))
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    names = [m.short for m in g.member_list]
    sent = []
    for m in g.member_list:
        m.setTask = lambda t: None
        m.start_task = (lambda m: (lambda sched: sent.append(m.short)))(m)
    n = S.SimpleScheduler(allocator=S.RoleAllocator(g._role_bind), log=lambda m: None).dispatch(r['root'], g.member_list)
    ok('R2-F1b 대체 허용(prefer-list)이면 나머지 후보로 재편성: a 없이 b·c, a 발송 0', r['root'] is not None and 'a' not in names and sorted(names) == ['b', 'c']
       and 'a' not in sent and n == 1 and r['recruit']['attempts'] == 2)
    g, ps = make_group([[('a', None, '')]])
    g.agent_list = ['/etri/a']
    G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))
    g.get_description = lambda n: None
    G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='new:/etri/a'))
    ok('R2-F1c new: 통보가 오면 제거 표식 해제(접속은 새로)', '/etri/a' not in g._killed)
    g, ps = make_group([[('a', None, '')]])
    g.agent_list = ['/etri/a']
    orig = G.JnPGroup.register_candidate

    def reg(self, agent):
        ok_ = orig(self, agent)
        G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))   # 접속 성공 직후 kill
        return ok_
    g.register_candidate = types.MethodType(reg, g)
    r = run(g, ps, lambda: G._plan_or_legacy('Relay', 'a=1,0,0', lambda: G.build_relay_tree('a=1,0,0'), group=g))
    ok('R2-F1d 접속 뒤 kill 도 편성에 넣지 않음 → 배정 불가 종료(legacy 아님)', r['root'] is None and g.terminated and not g.searched and g.member_list == [])

    print('== R2-F2')
    clock = [0.0]
    g, ps = make_group([[('a', None, '')], [('a', None, ''), ('b', None, '')]], {'~unassigned_policy': 'wait', '~recruit_timeout': 1.0})
    ps += [patch('time.monotonic', lambda: clock[0]), patch('time.sleep', lambda sec: clock.__setitem__(0, clock[0] + sec))]
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('R2-F2a 예산 1 s: 대기는 1 s(남은 만큼), 예산 뒤 재수집 없음 → 늦은 후보 b 미수용, 배정 불가', r['root'] is None and r['unassigned'] == ['leg2']
       and r['recruit']['attempts'] == 1 and clock[0] == 1.0 and r['recruit'].get('budget_exhausted') is True and r['recruit']['elapsed_s'] == 1.0)
    clock = [0.0]
    g, ps = make_group([[('a', None, '')], [('a', None, ''), ('b', None, '')]], {'~unassigned_policy': 'wait', '~recruit_timeout': 3.0})
    ps += [patch('time.monotonic', lambda: clock[0]), patch('time.sleep', lambda sec: clock.__setitem__(0, clock[0] + sec))]
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('R2-F2a 예산 3 s: 2 s 뒤 재수집해 b 편성(예산 안)', r['root'] is not None and r['recruit']['attempts'] == 2 and clock[0] == 2.0)
    clock = [0.0]
    g, ps = make_group([[('a', None, '')]], {'~unassigned_policy': 'wait', '~recruit_timeout': 1.0})
    old_c = g.collect_candidates

    def slow():
        clock[0] += 3.0
        return old_c()
    g.collect_candidates = slow
    ps += [patch('time.monotonic', lambda: clock[0])]
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0'))
    ok('R2-F2b 첫 수집이 예산보다 오래 걸려도 첫 할당은 유효(예산 = 재수집 예산, 전체 상한 아님; elapsed 기록)', r['root'] is not None
       and r['recruit']['elapsed_s'] == 3.0 and r['recruit']['recollect_budget_s'] == 1.0)
    clock = [0.0]
    g, ps = make_group([[('a', None, '')]], {'~unassigned_policy': 'wait', '~recruit_timeout': 1.0})
    g.collect_candidates = slow
    ps += [patch('time.monotonic', lambda: clock[0]), patch('time.sleep', lambda sec: clock.__setitem__(0, clock[0] + sec))]
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('R2-F2b 첫 수집이 예산을 넘긴 뒤 미배정이면 재수집 없이 배정 불가', r['root'] is None and r['recruit']['attempts'] == 1 and clock[0] == 3.0)
    g, ps = make_group([[('a', None, '')]], {'~unassigned_policy': 'wait', '~recruit_timeout': 0})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    ok('R2-F2c 예산 0 = 재수집 없음', r['root'] is None and r['recruit']['attempts'] == 1)

    print('== R2-F3')
    for val, label in (('oops', '문자열'), (-1.0, '음수'), (float('nan'), 'NaN'), (float('inf'), '무한대'), (None, 'None')):
        g, ps = make_group([[('a', None, '')]], {'~recruit_timeout': val})
        r = run(g, ps, lambda: G._plan_or_legacy('Relay', 'a=1,0,0', lambda: G.build_relay_tree('a=1,0,0'), group=g))
        ok('R2-F3a 잘못된 ~recruit_timeout(%s) → 설정 오류로 종료, legacy·search 없음' % label, r['root'] is None and g.terminated and not g.searched
           and '설정 오류' in g.terminated[0] and r.get('source') == 'plan')
    g, ps = make_group([[('a', None, '')]], {'~recruit_timeout': '0'})
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0'))
    ok('R2-F3a 문자열 "0" 은 허용(0 초)', r['root'] is not None and r['recruit']['recollect_budget_s'] == 0.0)
    g, ps = make_group([[('a', None, '')]])
    g.collect_candidates = lambda: (_ for _ in ()).throw(RuntimeError('명부 수집 중 예외'))
    r = run(g, ps, lambda: G._plan_or_legacy('Relay', 'a=1,0,0', lambda: G.build_relay_tree('a=1,0,0'), group=g))
    ok('R2-F3b 편성 중 예상 밖 예외도 종료(legacy 로 새지 않음)', r['root'] is None and g.terminated and not g.searched and 'RuntimeError' in g.terminated[0])
    g, ps = make_group([[('a', None, '')]])
    with patch.object(P, 'plan_roles', side_effect=P.PlanBuildError('변환 실패 모의')):
        r = run(g, ps, lambda: G._plan_or_legacy('Relay', 'a=1,0,0', lambda: G.build_relay_tree('a=1,0,0'), group=g))
    ok('R2-F3c 계획 변환 실패만 호환 모드(legacy, goal 전환)', r['source'] == 'legacy' and g.searched and not g.terminated and g.recruit_mode == 'goal')


# ── ROUND3: R3-F1 확정 경계의 kill, kill→new 뒤 이전 접속 재사용 ──
def _dispatch_count(g, r):
    sent = []
    for a in g.member_list:
        a.setTask = lambda t: None
        a.start_task = (lambda a: (lambda sched: sent.append(a.short)))(a)
    n = S.SimpleScheduler(allocator=S.RoleAllocator(g._role_bind), log=lambda m: None).dispatch(r['root'], g.member_list)
    return n, sent


def r3():
    print('== R3-F1')
    # 3.1 확정 경계: 최종 검사가 끝나고 멤버 대입 줄에 멈춘 사이 별도 스레드가 실제 kill 콜백을 완료하려 한다(부록 반례 반전)
    g, ps = make_group([[('a', None, '')]])
    g.agent_list = ['/etri/a']
    lines, first = inspect.getsourcelines(G._recruit_body)
    target = next(first + i for i, ln in enumerate(lines) if ln.strip() == 'group.member_list[:] = members')
    hit, trigger, done = [], threading.Event(), threading.Event()
    seen = {}

    def worker():
        if trigger.wait(3.0):
            G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))
            done.set()

    def trace(frame, event, arg):
        if frame.f_code is G._recruit_body.__code__ and event == 'line' and frame.f_lineno == target and not hit:
            hit.append(target)
            trigger.set()
            seen['completed_before_commit'] = done.wait(0.5)       # 잠금 때문에 확정이 끝나기 전에는 완료되지 못해야 한다
        return trace

    def call():
        old = sys.gettrace()
        th = threading.Thread(target=worker)
        th.start()
        sys.settrace(trace)
        try:
            res = G._recruit_and_plan(g, 'Relay', 'a=1,0,0')
        finally:
            sys.settrace(old)
            trigger.set()
            th.join(3.0)
        return res
    r = run(g, ps, call)
    n, sent = _dispatch_count(g, r)
    ok('R3-F1a 확정 중 도착한 kill 은 확정 뒤 제거 경로로 반영: 콜백은 확정 전 완료 못함, 최종 멤버 없음, a 발송 0',
       hit and seen.get('completed_before_commit') is False and done.is_set() and '/etri/a' in g._killed and g.member_list == [] and n == 0 and sent == [])
    # 3.1 대조: 확정 검사 전에 완료된 kill 은 종료(기존 R2-F1d 와 같은 경로)
    g, ps = make_group([[('a', None, '')]])
    g.agent_list = ['/etri/a']
    orig_build = P.build

    def build_then_kill(*a, **kw):
        res = orig_build(*a, **kw)
        G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))
        return res
    ps.append(patch.object(P, 'build', build_then_kill))
    r = run(g, ps, lambda: G._plan_or_legacy('Relay', 'a=1,0,0', lambda: G.build_relay_tree('a=1,0,0'), group=g))
    ok('R3-F1a 대조: 확정 검사 전에 끝난 kill 은 편성 종료', r['root'] is None and g.terminated and '제거 통보' in g.terminated[0] and not g.searched)
    # 3.2 kill→new 가 한 접속 진행 중에 지나가면 이전 접속 객체를 쓰지 않는다
    g, ps = make_group([[('a', None, ''), ('b', None, '')]])
    g.agent_list = ['/etri/a', '/etri/b']
    g.get_description = lambda nm: '<data><agent>/etri/a</agent><goal>Relay</goal><capability>lidar</capability><skills>GoTo</skills></data>'
    calls, objs = [], []

    def connect(a, timeout=5.0):
        calls.append(a.short)
        objs.append(a)
        a.client = types.SimpleNamespace(send_goal=lambda *x, **k: None)
        if a.short == 'b' and calls.count('b') == 1:
            G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))
            G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='new:/etri/a'))
        return True
    ps.append(patch.object(G.Agent, 'connect', connect))
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0;b=2,0,0'))
    old_a = objs[0]
    n, sent = _dispatch_count(g, r)
    new_a = next((m for m in g.member_list if m.short == 'a'), None)
    ok('R3-F1b kill→new 뒤 a 는 새 설명·새 접속(세대 2)으로만 편성: 이전 객체 재사용 없음, connect 가 a 에 두 번',
       r['root'] is not None and calls.count('a') == 2 and new_a is not None and new_a is not old_a and new_a.gen == 2 and old_a.gen == 0
       and old_a not in g.member_list and 'a' in r['recruit'].get('reregistered', []) and r['recruit']['attempts'] == 2)
    ok('R3-F1b 발송은 새 객체로만(이전 객체 0)', n == 1 and sent == ['a'] and g._role_bind['leg1'] is new_a)
    # 3.2 재등록이 접속 회차 한도까지 반복되면 명시적 배정 불가
    g, ps = make_group([[('a', None, '')]])
    g.agent_list = ['/etri/a']
    g.get_description = lambda nm: '<data><agent>/etri/a</agent><goal>Relay</goal><capability>lidar</capability><skills>GoTo</skills></data>'

    def connect2(a, timeout=5.0):
        a.client = types.SimpleNamespace(send_goal=lambda *x, **k: None)
        G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))
        G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='new:/etri/a'))
        return True
    ps.append(patch.object(G.Agent, 'connect', connect2))
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0'))
    ok('R3-F1c 접속할 때마다 재등록되면 4회 뒤 배정 불가(reregistered 사유), 성공 경로 아님', r['root'] is None and r['unassigned'] == ['leg1']
       and r['recruit']['reasons']['leg1'].get('reregistered') == 'a' and r['recruit']['attempts'] == 4 and g.member_list == [])
    # 세대: new: 만 와도 이전 접속은 무효(제거 해제 ≠ 접속 유효)
    g, ps = make_group([[('a', None, '')]])
    g.agent_list = ['/etri/a']
    G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))
    g.get_description = lambda nm: None
    G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='new:/etri/a'))
    ok('R3-F1d 세대: kill 1 + new 1 → 2, 제거 표식은 해제', g._reg_gen['/etri/a'] == 2 and '/etri/a' not in g._killed)


# ── ROUND4: R4-F1 설명 요청 도중 재등록(실제 collect_candidates), R4-N1 wait 에서 반복 재등록 ──
def _xml(skill, busy='false'):
    return ('<data><agent>/etri/a</agent><goal>Relay</goal><capability>lidar</capability><skills>%s</skills><busy>%s</busy></data>' % (skill, busy))


def r4():
    print('== R4-F1')
    master = types.SimpleNamespace(getSystemState=lambda: ([('/jnp_agent_join_event', ['/etri/a'])], [], []))

    def setup(race, always=False):
        g, ps = make_group([[]])
        g.agent_list = ['/etri/a']
        g.collect_candidates = types.MethodType(G.JnPGroup.collect_candidates, g)     # 실제 수집 본문
        calls = []                     # 수집(collect) 쪽에서 온 설명 요청만 센다(new: 콜백 안의 요청은 제외)
        state = {'in_cb': False}

        def description(node):
            if state['in_cb']:
                return _xml('Trip', 'true')                                                    # new: 콜백이 읽는 새 설명
            calls.append(node)
            if race and (len(calls) == 1 or always):
                state['in_cb'] = True
                G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))    # 응답이 오기 전에 kill→new 처리
                G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='new:/etri/a'))
                state['in_cb'] = False
                return _xml('GoTo')                                                            # 이전 요청의 응답 = 옛 세대의 설명
            return _xml('Trip', 'true') if race else _xml('GoTo')                               # 새 설명: GoTo 없음·busy
        g.get_description = description
        ps.append(patch.object(G, 'Master', lambda *a: master))
        return g, ps, calls

    g, ps, calls = setup(False)
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0'))
    n, sent = _dispatch_count(g, r)
    ok('R4-F1 정상 대조: 세대 안정 → 설명 1회, 편성·발송 1', r['root'] is not None and len(calls) == 1 and n == 1 and g.member_list[0].gen == 0)
    g, ps, calls = setup(True)
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0'))
    ok('R4-F1 경계 반례 반전: 요청 중 kill→new → 이전 응답 폐기·재요청, 새 설명(Trip·busy)으로 부적격 → 편성 0', r['root'] is None and len(calls) == 2
       and g._reg_gen['/etri/a'] == 2 and g.member_list == [] and r['unassigned'] == ['leg1'] and r['recruit']['rejected']['leg1']['a'] == {'busy': True, 'skills': ['GoTo']})
    g, ps, calls = setup(True, always=True)
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0'))
    ok('R4-F1 두 번 연속 재등록이면 이번 회차에서 제외(unstable 기록), 무제한 재요청 없음', r['root'] is None and len(calls) == 2 and 'a' in r['recruit'].get('unstable', [])
       and g.member_list == [])
    print('== R4-N1')
    g, ps = make_group([[('a', None, '')]], {'~unassigned_policy': 'wait', '~recruit_timeout': 5.0})
    g.agent_list = ['/etri/a']
    g.get_description = lambda n: _xml('GoTo')      # new: 콜백이 읽는 설명
    clock = [0.0]

    def connect(a, timeout=5.0):
        a.client = types.SimpleNamespace(send_goal=lambda *x, **k: None)
        G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='kill:/etri/a'))
        G.JnPGroup.discovery_callback(g, types.SimpleNamespace(data='new:/etri/a'))
        return True
    ps += [patch.object(G.Agent, 'connect', connect), patch('time.monotonic', lambda: clock[0]), patch('time.sleep', lambda n: clock.__setitem__(0, clock[0] + n))]
    r = run(g, ps, lambda: G._recruit_and_plan(g, 'Relay', 'a=1,0,0'))
    ok('R4-N1 wait: 즉시 재시도 4번 뒤 남은 미배정은 예산 안에서 추가 수집(attempts 6) → 예산 소진 뒤 배정 불가(부적격 객체는 성공 경로에 없음)',
       r['root'] is None and r['recruit']['attempts'] == 6 and r['recruit'].get('budget_exhausted') is True and r['recruit']['reasons']['leg1'].get('reregistered') == 'a'
       and g.member_list == [])


def main():
    vf1()
    vf2()
    vf3()
    vf4()
    vf5()
    vf6()
    vf7()
    recs()
    r2()
    r3()
    r4()
    print('TOTAL test_recruit: %d FAIL' % F[0])
    return 1 if F[0] else 0


if __name__ == '__main__':
    sys.exit(main())
