#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.9.0 2026-10-18] 스킬 기반 역할 할당 검사 — ROS 마스터 불필요(rospy·jnp.msg 는 import 만 하므로 워크스페이스 source 필요):
#   source <workspace>/devel/setup.bash && python3 test/test_roles.py
# A. canonical v2: 역할 추출(role_param)·required_skills 1:1·requirements 분리·루트 roles/role_order/contract·역할 선언(ROLE_REQUIRES/ROLE_PREFER)·
#    역할 참조(WaitPass.prev)·검증 반례
# B. 역할표(role_table): 역할 요구 = 배정 대상 task 의 스킬·능력 합집합 + 선언 요구; 가상/상시 서비스는 services; 풀(Trip)
# C. 할당(assign_roles): 결정성, 힌트 우선, 스킬 3상태(None/[]/[...]), 능력, busy, 대체(명단 밖), 뒤 역할 힌트 보존, 자연 정렬 동률,
#    ETA(시작점·위치), prefer(소프트), list-only/all, 풀 멤버, 배정 불가 사유
# D. 실행 트리: 역할 바인딩 → 노드 이름(로봇), _role/_skill/_robot, RoleAllocator(역할 고정·풀·바쁨 대기), dispatch 최종 방어
# E. 에이전트 광고: advertised_skills 3상태·등록표 밖 이름·description_xml ↔ parse_description 왕복
# F. 기록 v2: plan_record 의 roles/assignments/recruit, unassigned_record
import json
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import plan_to_tasktree as p2t                   # noqa: E402
import jnp_plan as P                              # noqa: E402
import jnp_scheduler as S                         # noqa: E402
import jnp_agent as A                             # noqa: E402
import jnp_group as G                             # noqa: E402

KW = dict(parse_multigoal=G.parse_multigoal_payload, parse_avoidance=G.parse_avoidance_payload, speed_fn=G._robot_speed)
CAT = p2t.load_catalog()
F = [0]


def ok(what, cond, detail=''):
    print('%s %s %s' % ('PASS' if cond else 'FAIL', what, detail))
    if not cond:
        F[0] += 1


def err(what, fn, exc=P.PlanBuildError, must=None):
    try:
        fn()
    except exc as e:
        if must and must not in str(e):
            print('FAIL %s: 거부됐지만 사유가 다름: %s' % (what, e))
            F[0] += 1
            return
        print('PASS %s: 거부됨 (%s)' % (what, str(e)[:100]))
        return
    print('FAIL %s: 거부되지 않음' % what)
    F[0] += 1


class Cand:
    """후보 로봇 — jnp_group.Agent 와 같은 인터페이스(name, short, skills, capability_set, busy, free)."""

    def __init__(self, n, skills, caps, busy=False):
        self.name, self.short = '/etri/' + n, n
        self.skills = (list(skills) if skills is not None else None)
        self.capability_set = set(caps)
        self.busy, self.free = busy, True
        self.role = None

    def __repr__(self):
        return self.short


def bound_names(r):
    return {k: v.short for k, v in r['bound'].items()}


# ── A. canonical v2 ──
def run_canonical():
    print('== A canonical v2')
    r = P.build_relay('tb3_0=1,0,0;tb3_1=2,0,0;tb3_2=3,0,0')
    can = r['plan']['canonical']
    atoms = list(p2t.iter_atomics(can))
    ok('A contract v2 · role_order · roles', can['contract'] == 'jnp-canonical-tasktree/2' and can['role_order'] == ['leg1', 'leg2', 'leg3']
       and set(can['roles']) == {'leg1', 'leg2', 'leg3'})
    ok('A 단위 task: role 칸, args 에 robot 없음, required_skills 1:1, requirements []',
       all(a['role'] == 'leg%d' % (i + 1) and 'robot' not in a['args'] and a['required_skills'] == ['GoTo'] and a['requirements'] == [] for i, a in enumerate(atoms)))
    ok('A 로봇 이름이 canonical 어디에도 없다', 'tb3_' not in json.dumps(can))
    mg = P.build_multigoal('goals=A:1,2:2', G.parse_multigoal_payload)
    ma = list(p2t.iter_atomics(mg['plan']['canonical']))
    ok('A Trip(풀): role null · destination 인자 · roles 비어 있음', all(a['role'] is None and a['args']['destination'] == 'A' for a in ma)
       and mg['plan']['canonical']['roles'] == {} and mg['plan']['canonical']['role_order'] == [])
    me = P.build_map_explore(['locobot_0', 'tb3_0'], 'locobot_0')
    mc = me['plan']['canonical']
    ok('A ROLE_PREFER 선언 → roles.host.prefer', mc['roles']['host']['prefer'] == ['compute_x86'] and mc['roles']['explorer1'] == {'requires': [], 'prefer': []})
    ok('A optional 은 카탈로그에서(Explore)', all(a.get('optional') is True for a in p2t.iter_atomics(mc) if a['skill'] == 'Explore')
       and all('optional' not in a for a in p2t.iter_atomics(mc) if a['skill'] != 'Explore'))
    av = P.build_avoidance('bt=2,0,0.6;routes=R1:0,0>4,0|R2:0.5,0>4,0.5', G.parse_avoidance_payload, G._robot_speed)
    aa = list(p2t.iter_atomics(av['plan']['canonical']))
    ok('A WaitPass.prev 는 역할 참조(앞 경로 역할)', any(a['skill'] == 'WaitPass' and a['args']['prev'] in av['plan']['canonical']['roles'] for a in aa))
    # 검증 반례: 직접 만든 canonical
    bad = json.loads(json.dumps(can))
    bad['role_order'] = ['leg3', 'leg2', 'leg1']
    ok('A role_order 가 등장 순이 아니면 거부', p2t.validate_canonical(bad, CAT)['errors'])
    bad = json.loads(json.dumps(can))
    list(p2t.iter_atomics(bad))[0]['required_skills'] = ['GoTo', 'radar']
    ok('A required_skills 에 능력 태그를 섞으면 거부(v2)', p2t.validate_canonical(bad, CAT)['errors'])
    bad = json.loads(json.dumps(can))
    list(p2t.iter_atomics(bad))[0]['role'] = None
    ok('A role_param 스킬의 role null 은 거부', p2t.validate_canonical(bad, CAT)['errors'])
    bad = json.loads(json.dumps(can))
    bad['contract'] = 'jnp-canonical-tasktree/1'
    ok('A contract 불일치 거부', p2t.validate_canonical(bad, CAT)['errors'])
    bad = json.loads(json.dumps(av['plan']['canonical']))
    for a in p2t.iter_atomics(bad):
        if a['skill'] == 'WaitPass':
            a['args']['prev'] = 'ghost'
    ok('A 역할 참조(prev)가 역할표 밖이면 거부', p2t.validate_canonical(bad, CAT)['errors'])
    code = ('# Task Description: x\nROLE_REQUIRES = {"ghost": ["lidar"]}\nLEGS = ["leg1"]\nTARGETS = {"leg1": "1,2"}\n'
            'def f(leg, t):\n    GoTo(leg, t)\nfor leg in LEGS:\n    f(leg, TARGETS[leg])\n')
    err('A 선언된 역할이 단계에 없으면 거부', lambda: p2t.convert_code(code, CAT), exc=p2t.PlanIssue, must='선언된 역할')
    code2 = code.replace('"ghost"', '"leg1"')
    r2 = p2t.convert_code(code2, CAT)
    ok('A ROLE_REQUIRES 가 roles.requires 로', r2['canonical']['roles']['leg1']['requires'] == ['lidar'] and not r2['canonical_validation']['errors'])


# ── B. 역할표 ──
def run_role_table():
    print('== B 역할표')
    me = P.prep_map_explore(['locobot_0', 'tb3_0', 'tb3_1'])
    byn = {r['name']: r for r in me['roles']}
    ok('B 역할 수 = 요청 로봇 수(host + explorer1·2)', [r['name'] for r in me['roles']] == ['host', 'explorer1', 'explorer2'])
    ok('B host: skills={Explore}, requirements={lidar}, prefer=[compute_x86], services=[MergeMaps id]',
       byn['host']['skills'] == {'Explore'} and byn['host']['requirements'] == {'lidar'} and byn['host']['prefer'] == ['compute_x86']
       and len(byn['host']['services']) == 1 and byn['host']['services'][0].startswith('t02_MergeMaps'))
    ok('B explorer1: SendMap 은 services, 스킬 요구 안 만듦', byn['explorer1']['skills'] == {'Explore'} and len(byn['explorer1']['services']) == 1)
    mg = P.prep_multigoal('goals=A:1,2:2|B:3,4:1', G.parse_multigoal_payload)
    ok('B Trip 풀: skills={Trip}, requirements={lidar}, tasks 3', mg['roles'] == [] and mg['pool']['skills'] == {'Trip'}
       and mg['pool']['requirements'] == {'lidar'} and len(mg['pool']['tasks']) == 3)
    code = ('# Task Description: x\nROLE_REQUIRES = {"leg1": ["camera"]}\nLEGS = ["leg1"]\nTARGETS = {"leg1": "1,2"}\n'
            'def f(leg, t):\n    GoTo(leg, t, use_radar=True)\nfor leg in LEGS:\n    f(leg, TARGETS[leg])\n')
    r = p2t.convert_code(code, CAT)
    roles, pool = P.role_table(r['canonical'], CAT)
    ok('B 역할 요구 = 카탈로그 requirement ∪ requirements(radar) ∪ 선언(camera)', roles[0]['requirements'] == {'lidar', 'radar', 'camera'} and pool is None)
    rl = P.prep_relay('tb3_0=1,0,0;tb3_1=2,0,0;tb3_2=3,0,0')
    ok('B 릴레이 힌트·시작점: leg2 힌트 tb3_1, 시작점 = leg1 목표', rl['hints'] == {'leg1': 'tb3_0', 'leg2': 'tb3_1', 'leg3': 'tb3_2'}
       and rl['starts'] == {'leg2': (1.0, 0.0), 'leg3': (2.0, 0.0)} and rl['prefer_names'] == ['tb3_0', 'tb3_1', 'tb3_2'])


# ── C. 할당 ──
def run_assign():
    print('== C 할당')
    roles = [{'name': 'leg%d' % i, 'skills': {'GoTo'}, 'requirements': {'lidar'}, 'prefer': []} for i in (1, 2, 3)]
    hints = {'leg1': 'tb3_0', 'leg2': 'tb3_1', 'leg3': 'tb3_2'}
    names = ['tb3_0', 'tb3_1', 'tb3_2']
    full = lambda: [Cand('tb3_0', ['GoTo', 'Trip'], ['lidar']), Cand('tb3_1', ['GoTo'], ['lidar']), Cand('tb3_2', ['GoTo'], ['lidar'])]
    r = S.assign_roles(roles, full(), hints=hints, prefer_names=names)
    ok('C 힌트 전원 적격 → 힌트대로', bound_names(r) == hints and not r['unassigned'] and all(r['reasons'][k]['hinted'] for k in hints))
    r2 = S.assign_roles(roles, list(reversed(full())), hints=hints, prefer_names=names)
    ok('C 결정성: 후보 순서가 바뀌어도 같은 결과', bound_names(r2) == bound_names(r))
    # 스킬 3상태
    c = full(); c[1].skills = ['Trip']
    c.append(Cand('tb3_3', ['GoTo'], ['lidar']))
    r = S.assign_roles(roles, c, hints=hints, prefer_names=names)
    ok('C 힌트 로봇이 GoTo 미광고 → 명단 밖 로봇으로 대체, 뒤 역할 힌트 보존', bound_names(r) == {'leg1': 'tb3_0', 'leg2': 'tb3_3', 'leg3': 'tb3_2'}
       and r['reasons']['leg2']['substituted'] is True and r['rejected']['leg2']['tb3_1'] == {'skills': ['GoTo']})
    c = full(); c[1].skills = None
    r = S.assign_roles(roles, c, hints=hints, prefer_names=names)
    ok('C 미광고(None) 는 호환 모드에서 적격', bound_names(r)['leg2'] == 'tb3_1' and r['reasons']['leg2']['skills_known'] is False)
    r = S.assign_roles(roles, c, hints=hints, prefer_names=names, skills_strict=True)
    ok('C 미광고는 strict 에서 부적격 → 적격 2대뿐이라 역할 하나 배정 불가', r['rejected']['leg2']['tb3_1'] == {'skills': 'unadvertised'} and r['unassigned'] == ['leg3']
       and bound_names(r) == {'leg1': 'tb3_0', 'leg2': 'tb3_2'})
    c = full(); c[1].skills = []
    r = S.assign_roles(roles, c, hints=hints, prefer_names=names)
    ok('C 없음 선언([]) 은 호환 모드에서도 부적격', r['rejected']['leg2']['tb3_1'] == {'skills': ['GoTo']} and r['unassigned'] == ['leg3'])
    c = full(); c[1].capability_set = {'camera'}
    r = S.assign_roles(roles, c, hints=hints, prefer_names=names)
    ok('C 능력 부족(lidar 없음) 부적격', r['rejected']['leg2']['tb3_1'] == {'caps': ['lidar']} and r['unassigned'] == ['leg3'])
    c = full(); c[1].busy = True
    r = S.assign_roles(roles, c, hints=hints, prefer_names=names)
    ok('C 바쁜 로봇 제외', r['rejected']['leg2']['tb3_1'] == {'busy': True} and r['unassigned'] == ['leg3'])
    # list-only / all
    c = full(); c[1].skills = ['Trip']; c.append(Cand('tb3_3', ['GoTo'], ['lidar']))
    r = S.assign_roles(roles, c, hints=hints, prefer_names=names, mode='list-only')
    ok('C list-only: 명단 밖 로봇을 쓰지 않아 역할 하나 배정 불가', r['unassigned'] == ['leg3'] and r['rejected']['leg3']['tb3_3'] == {'outside_list': True}
       and bound_names(r) == {'leg1': 'tb3_0', 'leg2': 'tb3_2'})
    r = S.assign_roles(roles, c, hints=hints, prefer_names=names, mode='all')
    ok('C all: 명단 무시, 대체 표시 없음', bound_names(r)['leg2'] == 'tb3_3' and r['reasons']['leg2']['substituted'] is False)
    # 자연 정렬·ETA·prefer
    c = [Cand('tb3_10', ['GoTo'], ['lidar']), Cand('tb3_2', ['GoTo'], ['lidar'])]
    r = S.assign_roles([roles[0]], c, hints={}, prefer_names=[])
    ok('C 동률은 자연 정렬(tb3_2 < tb3_10)', bound_names(r)['leg1'] == 'tb3_2')
    pos = {'tb3_10': (0.0, 0.0), 'tb3_2': (10.0, 0.0)}
    r = S.assign_roles([dict(roles[0], name='legX')], c, hints={}, starts={'legX': (0.0, 0.0)}, positions=pos, speed_fn=G._robot_speed, prefer_names=[])
    ok('C 시작점까지 ETA 가 짧은 로봇 우선', bound_names(r)['legX'] == 'tb3_10' and r['reasons']['legX']['eta'] == 0.0)
    host = [{'name': 'host', 'skills': {'Explore'}, 'requirements': {'lidar'}, 'prefer': ['compute_x86']}]
    c = [Cand('tb3_0', ['Explore'], ['lidar', 'compute_arm']), Cand('locobot_0', ['Explore'], ['lidar', 'compute_x86'])]
    r = S.assign_roles(host, c, hints={}, prefer_names=['tb3_0', 'locobot_0'])
    ok('C prefer(compute_x86) 는 소프트 선호 — locobot 선택', bound_names(r)['host'] == 'locobot_0' and r['reasons']['host']['prefer_hit'] is True)
    c = [Cand('tb3_0', ['Explore'], ['lidar', 'compute_arm'])]
    r = S.assign_roles(host, c, hints={}, prefer_names=['tb3_0'])
    ok('C prefer 를 가진 로봇이 없어도 배정은 된다', bound_names(r)['host'] == 'tb3_0' and r['reasons']['host']['prefer_hit'] is False)
    # 풀
    pool = {'skills': {'Trip'}, 'requirements': {'lidar'}}
    c = [Cand('tb3_0', ['GoTo', 'Trip'], ['lidar']), Cand('tb3_1', ['GoTo'], ['lidar']), Cand('tb3_2', None, ['lidar'])]
    m, rej = S.pool_members(pool, c, prefer_names=['tb3_0', 'tb3_1', 'tb3_2'])
    ok('C 풀 멤버 = 자격 있는 로봇 전부(Trip 광고 + 미광고 호환)', [x.short for x in m] == ['tb3_0', 'tb3_2'] and rej['tb3_1'] == {'skills': ['Trip']})
    m, rej = S.pool_members(pool, c, prefer_names=['tb3_0', 'tb3_1', 'tb3_2'], skills_strict=True)
    ok('C 풀 strict: 미광고 제외', [x.short for x in m] == ['tb3_0'])
    # can_execute 직접
    ok('C can_execute 사유 묶음', S.can_execute(Cand('x', ['GoTo'], ['lidar'], busy=True), ['Trip'], ['camera'])[1] == {'busy': True, 'skills': ['Trip'], 'caps': ['camera']})


# ── D. 실행 트리·RoleAllocator ──
def run_tree_alloc():
    print('== D 실행 트리·역할 할당기')
    prep = P.prep_relay('tb3_0=1,0,0;tb3_1=2,0,0;tb3_2=3,0,0')
    res = P.build('Relay', '', roles_bound={'leg1': 'tb3_0', 'leg2': 'tb3_3', 'leg3': 'tb3_2'}, prep=prep)
    names = [t.name for t in res['root'].subtasks]
    ok('D 역할 바인딩이 노드 이름(로봇)에 반영', names == ['relay1.tb3_0', 'relay2.tb3_3', 'relay3.tb3_2'])
    t2 = res['root'].subtasks[1]
    ok('D 원자 task 에 _role/_skill/_robot', t2._role == 'leg2' and t2._skill == 'GoTo' and t2._robot == 'tb3_3' and t2.goal == 'nav:2,0,0')
    err('D 역할이 묶이지 않으면 트리 생성 거부', lambda: P.build('Relay', '', roles_bound={'leg1': 'tb3_0'}, prep=prep), must='묶이지 않음')
    err('D 지도제작: 한 로봇이 두 역할', lambda: P.build_map_explore(['a', 'b'], roles_bound={'host': 'a', 'explorer1': 'a'}), must='두 역할')
    me = P.build_map_explore(['locobot_0', 'tb3_0'], roles_bound={'host': 'tb3_0', 'explorer1': 'locobot_0'})
    ok('D 지도제작: host 에 묶인 로봇이 merge_maps', 'merge_maps.tb3_0' in [t.name for t in me['dicts']['mtasks'].values()]
       and me['dicts']['mtasks']['tb3_0'].agent.name == '/etri/tb3_0')
    av = P.build_avoidance('bt=2,0,0.6;routes=R1:0,0>4,0|R2:0.5,0>4,0.5', G.parse_avoidance_payload, G._robot_speed,
                           roles_bound={'R1': 'tb3_9', 'R2': 'tb3_8'})
    ok('D 충돌회피: ETA 순(R2 먼저), _bt_meta 의 order/moves/waits 는 로봇 이름, wait_pass.<앞 로봇>', av['meta']['order'] == ['tb3_8', 'tb3_9']
       and 'wait_pass.tb3_8' in [t.name for t in av['meta']['waits'].values()] and av['meta']['roles'] == {'tb3_9': 'R1', 'tb3_8': 'R2'})
    # RoleAllocator
    a0, a3, a2 = Cand('tb3_0', ['GoTo'], ['lidar']), Cand('tb3_3', ['GoTo'], ['lidar']), Cand('tb3_2', ['GoTo'], ['lidar'])
    alloc = S.RoleAllocator({'leg1': a0, 'leg2': a3, 'leg3': a2})
    ok('D 역할 task 는 묶인 로봇으로만', alloc.select(res['root'].subtasks[1], [a0, a2, a3]) is a3)
    a3.free = False
    ok('D 묶인 로봇이 바쁘면 None(대기, 다른 로봇 금지)', alloc.select(res['root'].subtasks[1], [a0, a2, a3]) is None)
    a3.free = True
    a3.skills = ['Trip']
    ok('D 묶인 로봇이 스킬을 잃으면 None', alloc.select(res['root'].subtasks[1], [a0, a2, a3]) is None)
    mg = P.build_multigoal('goals=A:1,2:2', G.parse_multigoal_payload)
    item = mg['root'].subtasks[0].subtasks[0]
    pool_alloc = S.RoleAllocator({}, pool_fn=lambda t, cands: cands[-1])
    ok('D 풀 task: 자격 있는 유휴 로봇 중 pool_fn 선택', pool_alloc.select(item, [Cand('tb3_1', ['GoTo'], ['lidar']), Cand('tb3_0', ['Trip'], ['lidar'])]).short == 'tb3_0')
    # dispatch 최종 방어
    logs = []

    class _Blind(S.Allocator):            # 적격을 보지 않는 할당기 — 최종 방어만 검사
        def select(self, task, agents):
            return agents[0] if agents else None
    sch = S.SimpleScheduler(allocator=_Blind(), log=logs.append)
    bad = Cand('tb3_0', ['Trip'], ['lidar'])
    bad.execute_status = False
    bad.setTask = lambda t: None
    bad.start_task = lambda s: None
    started = sch.dispatch(res['root'], [bad])
    ok('D dispatch 최종 방어: 할당기가 골라도 스킬 부적격이면 start 안 함', started == 0 and any('배정 불가' in m for m in logs), logs[:1])
    good = Cand('tb3_1', ['GoTo'], ['lidar'])
    ok('D SimpleAllocator 는 부적격 첫 후보를 건너뛰고 적격 후보를 고른다(V-F6)', S.SimpleAllocator().select(res['root'].subtasks[0], [bad, good]) is good)


# ── E. 광고 ──
def run_advert():
    print('== E 광고')
    ok('E advertised_skills 3상태', A.advertised_skills('') == (['Explore', 'GoTo', 'Patrol', 'Trip'], 'registry') and A.advertised_skills('none') == ([], 'param')
       and A.advertised_skills('unadvertised') == (None, 'param') and A.advertised_skills('Trip, GoTo') == (['GoTo', 'Trip'], 'param'))
    ok('E 등록표 밖 이름은 버림', A.advertised_skills('Fly,GoTo') == (['GoTo'], 'param'))
    for skills, busy in ((['GoTo', 'Trip'], False), ([], True), (None, False)):
        xml = A.description_xml('/etri/tb3_0', 'Relay', 'lidar,camera', skills, 'registry', busy)
        d = G.parse_description(xml)
        ok('E description_xml ↔ parse_description 왕복 skills=%r busy=%r' % (skills, busy),
           d['agent'] == '/etri/tb3_0' and d['cap'] == 'lidar,camera' and d['skills'] == skills and d['busy'] is busy)
    ok('E 구버전 XML(skills 없음) → None, busy False', G.parse_description('<data><agent>/etri/x</agent><goal>Relay</goal><capability>lidar</capability></data>')['skills'] is None)
    ok('E 에이전트가 아닌 XML → None', G.parse_description('<data><group>/g</group></data>') is None and G.parse_description('<<bad') is None)


# ── F. 기록 ──
def run_record():
    print('== F 기록 v2')
    prep = P.prep_relay('tb3_0=1,0,0;tb3_1=2,0,0')
    res = P.build('Relay', '', roles_bound={'leg1': 'tb3_0', 'leg2': 'tb3_3'}, prep=prep)
    res['assignments'] = [{'role': 'leg1', 'robot': 'tb3_0', 'reason': {'hinted': True}}, {'role': 'leg2', 'robot': 'tb3_3', 'reason': {'substituted': True}}]
    res['recruit'] = {'mode': 'prefer-list', 'candidates': []}
    rec = P.plan_record(res, 'Relay', '/group_relay')
    js = json.dumps(rec, ensure_ascii=False)
    ok('F schema v2 · contract · roles · assignments · recruit', rec['schema'] == 'jnp-plan-record/2' and rec['contract'] == 'jnp-canonical-tasktree/2'
       and [r['name'] for r in rec['roles']] == ['leg1', 'leg2'] and rec['assignments'][1]['robot'] == 'tb3_3' and rec['recruit']['mode'] == 'prefer-list' and len(js) > 100)
    ok('F subtasks 행에 role·robot·requirements', rec['subtasks'][1]['role'] == 'leg2' and rec['subtasks'][1]['robot'] == 'tb3_3' and rec['subtasks'][1]['requirements'] == [])
    rec2 = P.plan_record(P.build('Relay', '', prep=prep), 'Relay', '/g')
    ok('F assignments 가 없으면 roles_bound 로', [a['robot'] for a in rec2['assignments']] == ['tb3_0', 'tb3_1'])
    ur = P.unassigned_record(prep, 'Relay', '/g', ['leg2'], {'mode': 'prefer-list', 'rejected': {'leg2': {'tb3_1': {'skills': ['GoTo']}}}})
    ok('F unassigned_record: 트리 없음, 역할표·사유 보존, JSON', ur['unassigned'] == ['leg2'] and ur['tree'] == '' and ur['roles'][1]['name'] == 'leg2'
       and json.dumps(ur) and ur['recruit']['rejected']['leg2']['tb3_1'] == {'skills': ['GoTo']})


def main():
    run_canonical()
    run_role_table()
    run_assign()
    run_tree_alloc()
    run_advert()
    run_record()
    print('TOTAL test_roles: %d FAIL' % F[0])
    return 1 if F[0] else 0


if __name__ == '__main__':
    sys.exit(main())
