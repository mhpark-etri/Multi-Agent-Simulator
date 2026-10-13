#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.8.2 2026-10-13] 작업 분할 경로(plans/*.py → plan_to_tasktree → jnp_plan 어댑터 → Task 트리) 검사.
# ROS 마스터 불필요(rospy·jnp.msg 는 import 만 하므로 catkin 워크스페이스는 source 필요):
#   source <workspace>/devel/setup.bash && python3 test/test_plan_trees.py
# A. 동일성: 계획 경로 vs 0.8.1 고정 빌더 — 서명(이름·종류·goal·요구·선행·optional·상시표시·agent·자식 순서) 동일
# B. 불변식: 두 트리 모두 부모 참조·선행/후행 상호 참조·predessesors 별칭·complete=False·노드 중복 없음 (손상 트리는 걸러짐)
# C. 계약: canonical ↔ 실행 트리 원자 1:1, 순서 제약 집합 동일 (jnp_plan.check_contract 를 직접도 호출)
# D. 반례(검수 보고서 2026-10-13 1·2차): F1 바인딩 왕복/거부, F3 불완전 계획·추가 능력 태그·구조 변경·지원 범위 밖 입력의 거부,
#    R2-F1 상수 변경문·상수 메서드 호출·초과 위치 인자·해석 불가 인자의 거부
import copy
import json
import os
import sys
from unittest.mock import patch

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import jnp_plan as P                              # noqa: E402
import jnp_group as G                             # noqa: E402

KW = dict(parse_multigoal=G.parse_multigoal_payload, parse_avoidance=G.parse_avoidance_payload, speed_fn=G._robot_speed)
CASES = [
    # (goal, payload, kw for jnp_plan.build, legacy builder)
    ('Relay', 'tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.50,1.57;tb3_2=3.00,1.00,3.14', {}, lambda p: G.build_relay_tree(p)),
    ('Relay', 'tb3_0=1.00,0.00,0.00;bad;=1,2,3;tb3_1=2.00,0.50,1.57', {}, lambda p: G.build_relay_tree(p)),   # 형식 오류 조각 무시
    ('Relay', 'tb3_0=1.00,0.00,0.00', {}, lambda p: G.build_relay_tree(p)),                                   # 1 구간
    ('Mult-Goal', 'goals=A:1.0,2.0:2|B:-1.5,0.5:3;robots=tb3_0:0,0|tb3_1:0.5,0|tb3_2:1,0;opt=eta', {},
     lambda p: G.build_multigoal_tree(p)),
    ('Mult-Goal', 'goals=A:1.0,2.0:1;robots=tb3_0:0,0', {}, lambda p: G.build_multigoal_tree(p)),              # 물품 1개(가지 1개)
    ('Mult-Goal', 'goals=A:1,2:0;robots=tb3_0:0,0', {}, lambda p: G.build_multigoal_tree(p)),                  # 수량 0 → 빈 가지(0.8.1 과 같음)
    ('Mult-Goal', 'goals=A:1,2:0|B:3,4:1;robots=tb3_0:0,0', {}, lambda p: G.build_multigoal_tree(p)),          # 수량 0 + 1
    ('Avoidance', 'bt=2.0,0.0,0.6;routes=tb3_0:0.0,0.0>4.0,0.0|locobot_0:4.5,0.2>-0.5,0.1|tb3_1:0.5,0.3>4.2,0.4;mode=dynamic', {},
     lambda p: G.build_avoidance_tree(p)),
    ('Avoidance', 'bt=2.0,0.0,0.6;routes=tb3_0:0.0,0.0>4.0,0.0', {}, lambda p: G.build_avoidance_tree(p)),   # 로봇 1대
    ('MapExplore', 'robots=tb3_0|locobot_0|tb3_1', {'names': ['locobot_0', 'tb3_0', 'tb3_1'], 'merge_host': 'locobot_0'},
     lambda p: G.build_map_explore_tree(['locobot_0', 'tb3_0', 'tb3_1'], 'locobot_0')),
    ('MapExplore', 'robots=locobot_0', {'names': ['locobot_0'], 'merge_host': 'locobot_0'},
     lambda p: G.build_map_explore_tree(['locobot_0'], 'locobot_0')),
    ('ObjectSearch', 'robots=locobot_0|locobot_1;targets=sports_ball;count=2', {'names': ['locobot_0', 'locobot_1']},
     lambda p: G.build_object_search_tree(['locobot_0', 'locobot_1'])),
    ('ObjectSearch', 'robots=locobot_0', {'names': ['locobot_0']}, lambda p: G.build_object_search_tree(['locobot_0'])),
]


# ── A. 서명 ──
def sig(t):
    d = {'name': t.name, 'type': type(t).__name__, 'goal': getattr(t, 'goal', '')}
    if hasattr(t, 'subtasks'):
        d['children'] = [sig(c) for c in t.subtasks]
    else:
        d['req'] = list(t.requirement)
        d['after'] = [p.name for p in t.predecessors]
        d['optional'] = bool(getattr(t, 'optional', False))
        d['assign_status'] = bool(getattr(t, 'assign_status', False))
        d['agent'] = getattr(getattr(t, 'agent', None), 'name', None)
    return d


def meta_sig(m):
    if not m:
        return m
    return {'order': m['order'], 'center': m['center'], 'r': m['r'], 'starts': m['starts'], 'targets': m['targets'],
            'moves': {k: v.name for k, v in m['moves'].items()}, 'waits': {k: v.name for k, v in m['waits'].items()}}


def dicts_sig(d):
    return {k: {n: t.name for n, t in v.items()} for k, v in (d or {}).items()}


# ── B. 불변식(참조 구조) ──
def check_invariants(root, meta=None, dicts=None):
    """부모 참조는 실제 부모 객체, 선행/후행은 상호 참조, predessesors 는 predecessors 와 같은 리스트, complete=False,
    노드 객체 중복 없음, meta/dicts 의 노드는 트리 안의 객체. 어긋나면 AssertionError."""
    seen = set()
    nodes = []

    def rec(t, parent):
        assert id(t) not in seen, '노드 중복 참조: %s' % t.name
        seen.add(id(t))
        nodes.append(t)
        assert getattr(t, 'parent', None) is parent, '%s: parent 가 실제 부모가 아님' % t.name
        assert getattr(t, 'complete', False) is False, '%s: complete 가 True' % t.name
        if hasattr(t, 'subtasks'):
            for c in t.subtasks:
                rec(c, t)
        else:
            assert t.predessesors is t.predecessors, '%s: predessesors 별칭이 끊어짐' % t.name
            for p in t.predecessors:
                assert t in p.successors, '%s: 선행 %s 의 successors 에 없음' % (t.name, p.name)
            for s in t.successors:
                assert t in s.predecessors, '%s: 후행 %s 의 predecessors 에 없음' % (t.name, s.name)
    rec(root, None)
    for p in nodes:
        for s in getattr(p, 'successors', []) or []:
            assert id(s) in seen, '%s: successors 에 트리 밖 노드' % p.name
    if meta:
        for k in ('moves', 'waits'):
            for t in meta[k].values():
                assert id(t) in seen, '_bt_meta.%s 에 트리 밖 노드 %s' % (k, t.name)
    for k, v in (dicts or {}).items():
        for t in v.values():
            assert id(t) in seen, 'dicts.%s 에 트리 밖 노드 %s' % (k, t.name)


def build_plan(goal, payload, kw):
    return P.build(goal, payload, **dict(KW, **kw))


def run_equivalence():
    fails = 0
    for goal, payload, kw, legacy in CASES:
        res = build_plan(goal, payload, kw)
        leg = legacy(payload)
        if not isinstance(leg, dict):
            leg = {'root': leg, 'meta': getattr(leg, '_bt_meta', None), 'dicts': {}}
        ok = (sig(res['root']) == sig(leg['root']) and meta_sig(res['meta']) == meta_sig(leg['meta'])
              and dicts_sig(res['dicts']) == dicts_sig(leg['dicts']))
        try:
            check_invariants(res['root'], res['meta'], res['dicts'])
            check_invariants(leg['root'], leg['meta'], leg['dicts'])
            if res['plan'].get('canonical'):
                P.check_contract(res['plan']['canonical'], res['root'])
            inv = 'inv+contract ok'
        except Exception as e:
            ok, inv = False, 'INVARIANT/CONTRACT FAIL: %s' % e
        warn = res['plan'].get('warnings') or []
        print('%s %-12s %-62s warnings=%d  %s' % ('PASS' if ok else 'FAIL', goal, payload[:62], len(warn), inv))
        if not ok:
            fails += 1
            print(' plan  :', json.dumps(sig(res['root']), ensure_ascii=False))
            print(' legacy:', json.dumps(sig(leg['root']), ensure_ascii=False))
        for w in warn:
            print('   warning:', w)
    return fails, len(CASES)


# ── D. 반례 ──
def expect_error(what, fn, exc=P.PlanBuildError, must_contain=None):
    try:
        fn()
    except exc as e:
        if must_contain and must_contain not in str(e):
            print('FAIL %s: 거부됐지만 사유가 다름: %s' % (what, e))
            return 1
        print('PASS %s: 거부됨 (%s: %s)' % (what, exc.__name__, str(e)[:90]))
        return 0
    print('FAIL %s: 거부되지 않음' % what)
    return 1


def expect_ok(what, cond, detail=''):
    print('%s %s %s' % ('PASS' if cond else 'FAIL', what, detail))
    return 0 if cond else 1


def plan_variant(key, old, new):
    """계획 파일을 바꾸지 않고 메모리에서만 변형한 load_plan 패치."""
    path, code = P.load_plan(key)
    assert old in code, '%s 계획에 %r 가 없음' % (key, old)
    return patch.object(P, 'load_plan', return_value=(path, code.replace(old, new)))


def run_counterexamples():
    import ast
    f = 0
    # F1 — 바인딩 왕복/거부 (bind 단독: 리터럴로 넣고 ast 로 읽어 같은 값이 나오는가)
    for value in ['a"b', "a'b", r'a\nb', r'a\1b', 'a\\b', 'a;b', 'a|b', '한글_로봇', 'tab\there']:
        code = P.bind('ROBOTS = []\nTARGETS = {}\n', {'ROBOTS': [value], 'TARGETS': {value: value}}) if '\t' not in value else None
        if code is None:
            f += expect_error('F1 bind 제어문자(탭) 거부 %r' % value,
                              lambda v=value: P.bind('ROBOTS = []\n', {'ROBOTS': [v]}), must_contain='제어문자')
            continue
        mod = ast.parse(code)
        got_list = ast.literal_eval(mod.body[0].value)[0]
        got_dict = ast.literal_eval(mod.body[1].value)
        f += expect_ok('F1 bind 왕복 %r' % value, got_list == value and got_dict == {value: value}, repr(got_list))
    for value in ['a\nb', 'a\rb', 'a\x00b', '']:
        f += expect_error('F1 bind 거부 %r' % value, lambda v=value: P.bind('ROBOTS = []\n', {'ROBOTS': [v]}))
    f += expect_error('F1 payload 안 제어문자 → build 거부', lambda: P.build_relay('tb3_0=1,2,0;tb3\n1=2,3,0'))
    # F3 — 불완전 계획(한 줄 제거)은 반환 전에 거부
    with plan_variant('ObjectSearch', '    Detect(robot)', '    pass'):
        f += expect_error('F3 ObjectSearch 계획에서 Detect 제거', lambda: P.build_object_search(['locobot_0']), must_contain='단계')
    with plan_variant('ObjectSearch', '    Patrol(robot)', '    pass'):
        f += expect_error('F3 ObjectSearch 계획에서 Patrol 제거', lambda: P.build_object_search(['locobot_0']), must_contain='단계')
    with plan_variant('MapExplore', '    Explore(robot)', '    pass'):
        f += expect_error('F3 MapExplore 계획에서 Explore 제거', lambda: P.build_map_explore(['locobot_0'], 'locobot_0'), must_contain='단계')
    with plan_variant('MapExplore', '    MergeMaps(robot)', '    SendMap(robot)'):
        f += expect_error('F3 MapExplore 호스트가 SendMap', lambda: P.build_map_explore(['locobot_0', 'tb3_0'], 'locobot_0'))
    with plan_variant('Relay', '    GoTo(robot, target)', '    GoTo(robot, target)\n    GoTo(robot, target)'):
        f += expect_error('F3 Relay 계획에 GoTo 중복', lambda: P.build_relay('tb3_0=1,2,0;tb3_1=2,3,0'))
    with plan_variant('Avoidance', '    WaitPass(robot, PREV[robot])\n', ''):
        f += expect_error('F3 Avoidance 계획에서 WaitPass 제거',
                          lambda: P.build_avoidance('bt=2,0,0.6;routes=tb3_0:0,0>4,0|tb3_1:0.5,0>4,0.5', G.parse_avoidance_payload, G._robot_speed))
    with plan_variant('Mult-Goal', '    Trip(item, goal, target)', '    pass'):
        f += expect_error('F3 Mult-Goal 계획에서 Trip 제거', lambda: P.build_multigoal('goals=A:1,2:2', G.parse_multigoal_payload))
    # F3 — 추가 능력 태그는 요구 능력으로 반영
    with plan_variant('Relay', 'GoTo(robot, target)', 'GoTo(robot, target, use_radar=True)'):
        r = P.build_relay('tb3_0=1,2,0')
        can = list(P.p2t.iter_atomics(r['plan']['canonical']))[0]
        f += expect_ok('F3 use_radar=True → requirement 에 radar', can['required_skills'] == ['GoTo', 'radar']
                       and r['root'].subtasks[0].requirement == ['lidar', 'radar'], str(r['root'].subtasks[0].requirement))
    # F2 — 계획의 순서 구조를 바꾸면 어댑터가 거부(계약 검사)
    seq_os = ('    t1 = threading.Thread(target=patrol_area, args=(robot,))\n    t1.start()\n    threads.append(t1)\n'
              '    t2 = threading.Thread(target=detect_objects, args=(robot,))\n    t2.start()\n    threads.append(t2)\n')
    with plan_variant('ObjectSearch', seq_os, '    patrol_area(robot)\n    detect_objects(robot)\n'):
        f += expect_error('F2 ObjectSearch 를 순차(Patrol→Detect)로 바꾼 계획', lambda: P.build_object_search(['locobot_0']), must_contain='순서 제약')
    par_relay = ('for robot in ROBOTS:        # sequential: leg i+1 starts only after leg i is complete\n'
                 '    relay_leg(robot, TARGETS[robot])\n')
    with plan_variant('Relay', par_relay,
                      'import threading\nthreads = []\nfor robot in ROBOTS:\n    t = threading.Thread(target=relay_leg, args=(robot, TARGETS[robot]))\n'
                      '    t.start()\n    threads.append(t)\nfor t in threads:\n    t.join()\n'):
        f += expect_error('F2 Relay 를 병렬로 바꾼 계획', lambda: P.build_relay('tb3_0=1,2,0;tb3_1=2,3,0'), must_contain='순서 제약')
    # 지원 범위 밖 입력·어휘 밖 스킬
    f += expect_error('지원 범위: Relay 로봇 이름 중복', lambda: P.build_relay('tb3_0=1,2,0;tb3_0=2,3,0'), must_contain='유일')
    f += expect_error('지원 범위: MapExplore 호스트가 참여 로봇 밖', lambda: P.build_map_explore(['tb3_0'], 'locobot_9'))
    with plan_variant('Relay', 'GoTo(robot, target)', 'Fly(robot, target)'):
        f += expect_error('어휘 밖 스킬 Fly', lambda: P.build_relay('tb3_0=1,2,0'))
    with plan_variant('Relay', 'GoTo(robot, target)', 'GoTo(robot, target, speed=2)'):
        f += expect_error('카탈로그에 없는 키워드 인자', lambda: P.build_relay('tb3_0=1,2,0'))
    # R2-F1 (2차 검수 2026-10-13) — 의미를 바꾸는 미지원 구문은 변환 전에 거부(상수는 바인딩 뒤 읽기 전용)
    site = '    relay_leg(robot, TARGETS[robot])'
    for what, old, new, key in [
        ('R2-F1 사전 첨자 대입 TARGETS[robot] = …', site, "    TARGETS[robot] = '99,99,0'\n" + site, '읽기 전용'),
        ('R2-F1 dict.update(…)', site, "    TARGETS.update({robot: '99,99,0'})\n" + site, '읽기 전용'),
        ('R2-F1 초과 위치 인자 GoTo(robot, target, \'radar\')', 'GoTo(robot, target)', "GoTo(robot, target, 'radar')", '초과분'),
        ('R2-F1 증감 대입 ROBOTS += […]', site, "    ROBOTS += ['x']\n" + site, '읽기 전용'),
        ('R2-F1 del TARGETS[robot]', site, "    del TARGETS[robot]\n" + site, '읽기 전용'),
        ('R2-F1 함수 안 TARGETS.pop(robot)', '    GoTo(robot, target)', "    TARGETS.pop(robot)\n    GoTo(robot, target)", '읽기 전용'),
        ('R2-F1 리스트 상수 ROBOTS.append(…)', site, "    ROBOTS.append('x')\n" + site, '읽기 전용'),
        ('R2-F1 해석 불가 인자(지역 첨자 대입)', '    GoTo(robot, target)', "    pos = TARGETS[robot]\n    GoTo(robot, pos)", '리터럴이 아니거나'),
    ]:
        with plan_variant('Relay', old, new):
            f += expect_error(what, lambda: P.build_relay('tb3_0=1,2,0'), must_contain=key)
    with plan_variant('Relay', 'GoTo(robot, target)', 'GoTo(robot, target)'):     # 변형 없음 — 기본 계획은 여전히 통과
        r = P.build_relay('tb3_0=1,2,0')
        f += expect_ok('R2-F1 기본 계획은 strict_source 에서도 통과', r['root'].subtasks[0].goal == 'nav:1,2,0' and not r['plan']['warnings'])
    # 가상/상시 서비스 단계의 능력 태그는 의미가 없어 거부; 카탈로그 값 오류도 거부
    with plan_variant('Avoidance', 'WaitPass(robot, PREV[robot])', 'WaitPass(robot, PREV[robot], use_radar=True)'):
        f += expect_error('가상 단계(WaitPass)에 radar 태그', lambda: P.build_avoidance('bt=2,0,0.6;routes=tb3_0:0,0>4,0|tb3_1:0.5,0>4,0.5',
                                                                              G.parse_avoidance_payload, G._robot_speed), must_contain='능력 태그')
    _cat = P.p2t.load_catalog()
    _bad = json.loads(json.dumps(_cat)); _bad['actions']['GoTo']['node'] = 'paralel'
    with patch.object(P.p2t, 'load_catalog', return_value=_bad):
        f += expect_error('카탈로그 node 오타(paralel)', lambda: P.build_relay('tb3_0=1,2,0'), must_contain='node')
    # 불변식 검사기가 손상 트리를 거르는가 (검수 보고서의 서명 우회 반례)
    a = G.build_relay_tree('tb3_0=1,2,0;tb3_1=2,3,0')
    b = G.build_relay_tree('tb3_0=1,2,0;tb3_1=2,3,0')
    b.subtasks[0].successors = []
    b.subtasks[1].parent = copy.copy(b)
    b.subtasks[1].predessesors = []
    b.subtasks[1].complete = True
    f += expect_ok('B 손상 트리는 서명으로는 같지만', sig(a) == sig(b))
    f += expect_error('B 손상 트리를 불변식 검사가 거름', lambda: check_invariants(b), exc=AssertionError)
    # 계약 검사 자체: 실행 트리에 선행을 하나 더 넣으면 걸린다
    r = P.build_relay('tb3_0=1,2,0;tb3_1=2,3,0;tb3_2=3,4,0')
    r['root'].subtasks[2].addPredecessor(r['root'].subtasks[0])     # 순차 복합과 중복인 제약 → 집합상 동일(통과해야 함)
    f += expect_ok('C 중복 제약(이미 순서상 함의)은 계약 위반 아님', P.check_contract(r['plan']['canonical'], r['root']) is None)
    r2 = P.build_object_search(['locobot_0'])
    r2['dicts']['dtasks']['locobot_0'].addPredecessor(r2['dicts']['etasks']['locobot_0'])
    f += expect_error('C 실행 트리에 canonical 에 없는 선행 추가', lambda: P.check_contract(r2['plan']['canonical'], r2['root']), must_contain='순서 제약')
    return f


# ── E. 그룹 연결부(_plan_or_legacy): 대체 정책·strict·기록 여부 (ROS 마스터 없음 → rosparam 기록은 False 로 보고돼야 한다) ──
def run_wrapper():
    import rospy
    f = 0
    pl = 'tb3_0=1,2,0;tb3_1=2,3,0'
    r = G._plan_or_legacy('Relay', pl, lambda: G.build_relay_tree(pl))
    f += expect_ok('E 계획 경로 선택 source=plan, 마스터 없음 → published=False',
                   r['source'] == 'plan' and r['published'] is False and r['fallback_reason'] is None, str((r['source'], r['published'])))
    dup = 'tb3_0=1,2,0;tb3_0=2,3,0'
    r = G._plan_or_legacy('Relay', dup, lambda: G.build_relay_tree(dup))
    f += expect_ok('E 지원 범위 밖(중복 이름) → source=legacy + 사유 기록',
                   r['source'] == 'legacy' and 'PlanBuildError' in (r['fallback_reason'] or '') and len(r['root'].subtasks) == 2,
                   str(r['fallback_reason'])[:80])
    with patch.object(rospy, 'get_param', side_effect=lambda k, d=None: {'~plan_mode': False}.get(k, d)):
        r = G._plan_or_legacy('Relay', pl, lambda: G.build_relay_tree(pl))
        f += expect_ok('E plan_mode=false → legacy, 사유 plan_mode=false', r['source'] == 'legacy' and r['fallback_reason'] == 'plan_mode=false')
    with patch.object(rospy, 'get_param', side_effect=lambda k, d=None: {'~plan_strict': True}.get(k, d)):
        f += expect_error('E plan_strict=true 면 대체하지 않고 예외 전파', lambda: G._plan_or_legacy('Relay', dup, lambda: G.build_relay_tree(dup)))
    with patch.object(P, 'build', side_effect=RuntimeError('뜻밖의 구현 오류')):
        r = G._plan_or_legacy('Relay', pl, lambda: G.build_relay_tree(pl))
        f += expect_ok('E 예상 밖 예외도 호환 모드에서는 legacy + 사유', r['source'] == 'legacy' and 'RuntimeError' in r['fallback_reason'])
        with patch.object(rospy, 'get_param', side_effect=lambda k, d=None: {'~plan_strict': True}.get(k, d)):
            f += expect_error('E 예상 밖 예외는 strict 에서 전파', lambda: G._plan_or_legacy('Relay', pl, lambda: G.build_relay_tree(pl)), exc=RuntimeError)
    with patch.object(rospy, 'get_param', side_effect=ConnectionRefusedError('no master')):
        r = G._plan_or_legacy('Relay', pl, lambda: G.build_relay_tree(pl))
        f += expect_ok('E get_param 실패는 기본값(plan_mode=true) 으로', r['source'] == 'plan')
    return f


def main():
    print('== A/B/C 동일성·불변식·계약')
    fa, n = run_equivalence()
    print('== D 반례')
    fd = run_counterexamples()
    print('== E 그룹 연결부')
    fe = run_wrapper()
    print('TOTAL equivalence %d cases %d FAIL; counterexamples %d FAIL; wrapper %d FAIL' % (n, fa, fd, fe))
    return 1 if (fa or fd or fe) else 0


if __name__ == '__main__':
    sys.exit(main())
