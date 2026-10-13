#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.8.2 2026-10-13] 작업 분할 경로(plans/*.py → plan_to_tasktree → Task 트리)가 0.8.1 고정 빌더와
# 같은 트리를 만드는지 검사. ROS 마스터 불필요(rospy·jnp.msg 는 import 만 하므로 catkin 워크스페이스는 source 필요).
#   source /root/catkin_ws_jnp082_test/devel/setup.bash && python3 test/test_plan_trees.py
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import jnp_plan                                   # noqa: E402
import jnp_group as G                             # noqa: E402

CASES = [
    # (goal, payload, kw for jnp_plan.build, legacy builder)
    ('Relay', 'tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.50,1.57;tb3_2=3.00,1.00,3.14', {},
     lambda p: G.build_relay_tree(p)),
    ('Relay', 'tb3_0=1.00,0.00,0.00;bad;=1,2,3;tb3_1=2.00,0.50,1.57', {},          # 형식 오류 조각 무시
     lambda p: G.build_relay_tree(p)),
    ('Relay', 'tb3_0=1.00,0.00,0.00', {}, lambda p: G.build_relay_tree(p)),          # 1 구간
    ('Mult-Goal', 'goals=A:1.0,2.0:2|B:-1.5,0.5:3;robots=tb3_0:0,0|tb3_1:0.5,0|tb3_2:1,0;opt=eta', {},
     lambda p: G.build_multigoal_tree(p)),
    ('Mult-Goal', 'goals=A:1.0,2.0:1;robots=tb3_0:0,0', {}, lambda p: G.build_multigoal_tree(p)),   # 물품 1개(가지 1개)
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


def sig(t):
    """Task 트리의 비교용 서명(이름·종류·goal·요구·선행·optional·상시표시·대리 agent·자식 순서)."""
    d = {'name': t.name, 'type': type(t).__name__, 'goal': getattr(t, 'goal', '')}
    if hasattr(t, 'subtasks'):
        d['children'] = [sig(c) for c in t.subtasks]
        d['parent'] = getattr(getattr(t, 'parent', None), 'name', None)
    else:
        d['req'] = list(t.requirement)
        d['after'] = [p.name for p in t.predecessors]
        d['optional'] = bool(getattr(t, 'optional', False))
        d['assign_status'] = bool(getattr(t, 'assign_status', False))
        d['agent'] = getattr(getattr(t, 'agent', None), 'name', None)
        d['parent'] = getattr(getattr(t, 'parent', None), 'name', None)
    return d


def meta_sig(m):
    if not m:
        return m
    return {'order': m['order'], 'center': m['center'], 'r': m['r'], 'starts': m['starts'], 'targets': m['targets'],
            'moves': {k: v.name for k, v in m['moves'].items()}, 'waits': {k: v.name for k, v in m['waits'].items()}}


def dicts_sig(d):
    return {k: {n: t.name for n, t in v.items()} for k, v in (d or {}).items()}


def main():
    fails = 0
    for goal, payload, kw, legacy in CASES:
        res = jnp_plan.build(goal, payload, parse_multigoal=G.parse_multigoal_payload,
                             parse_avoidance=G.parse_avoidance_payload, speed_fn=G._robot_speed, **kw)
        leg = legacy(payload)
        if not isinstance(leg, dict):
            leg = {'root': leg, 'meta': getattr(leg, '_bt_meta', None), 'dicts': {}}
        ok = (sig(res['root']) == sig(leg['root']) and meta_sig(res['meta']) == meta_sig(leg['meta'])
              and dicts_sig(res['dicts']) == dicts_sig(leg['dicts']))
        warn = res['plan'].get('warnings') or []
        print('%s %-12s %-60s warnings=%d' % ('PASS' if ok else 'FAIL', goal, payload[:60], len(warn)))
        if not ok:
            fails += 1
            import json
            print(' plan  :', json.dumps(sig(res['root']), ensure_ascii=False))
            print(' legacy:', json.dumps(sig(leg['root']), ensure_ascii=False))
            print(' meta  :', meta_sig(res['meta']), '|', meta_sig(leg['meta']))
            print(' dicts :', dicts_sig(res['dicts']), '|', dicts_sig(leg['dicts']))
        if warn:
            for w in warn:
                print('   warning:', w)
    print('TOTAL %d cases, %d FAIL' % (len(CASES), fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
