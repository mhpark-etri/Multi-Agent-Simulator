#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.8.2 2026-10-14] JnP Monitor '미션 → 작업 분할 → 스킬 매칭' 패널의 순수 함수 검사(헤드리스, DialogJnpMonitor 인스턴스 없음).
#   source <workspace>/devel/setup.bash && QT_QPA_PLATFORM=offscreen python3 code/Multi-Agent-Simulator/test_dlgJnpMonitor_html.py
# M1 회차·그룹·해체 결합, M2 능력 정보 3상태·후보 문구, M3 이스케이프 (검수 보고서의 반례를 회귀검사로)
# R2-M1a 수신 handler 의 회차별 상태·해체 최종성·늦은 계획 결합, R2-M1c 합친 트리의 node 소유 그룹 (ROUND2 보고서 §6 반례 포함)
# R3-F1 run_id 없는 구버전 그룹의 회차 미식별 호환 모드, R3-F2 보관 상한에서 현재 계획 회차·종료 표식 보호 (ROUND3 §5 반례 포함)
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, 'jnp', 'jnp_0.8.2', 'scripts'), HERE]
import jnp_plan as P                                           # noqa: E402
from dlgJnpMonitor import build_plan_html, plan_row_for        # noqa: E402

F = 0


def ok(what, cond, detail=''):
    global F
    print('%s %s %s' % ('PASS' if cond else 'FAIL', what, detail))
    F += 0 if cond else 1


g = '/group_relay'
P.new_run_id(g)
rec = json.loads(json.dumps(P.plan_record(P.build_relay('tb3_0=99,99,0'), 'Relay', g), ensure_ascii=False))
rid = rec['run_id']
node = rec['subtasks'][0]['node']
s_run = {'group': g, 'run_id': rid, 'state': 'running', 'members': [{'name': '/etri/tb3_0', 'cap': ['lidar']}],
         'tree': {'name': 'relay', 'kind': 'seq', 'state': '', 'children': [{'name': node, 'kind': 'atomic', 'agent': '/etri/tb3_0', 'state': 'running'}]}}


def h(status, plans=None, caps=None, ko=True):
    return build_plan_html(plans or {g: rec}, {g: status} if status else {}, ko, caps)


# ── M1-a: 이전 회차의 완료 상태는 새 계획에 붙지 않는다 ──
old = copy.deepcopy(s_run); old['run_id'] = 'old-run'; old['state'] = 'success'; old['tree']['children'][0]['state'] = 'done'
x = h(old)
ok('M1-a 다른 회차 완료 상태 → 완료 표시 없음·회차 불일치 안내', '완료' not in x and '회차 불일치' in x and '상태 미확인' in x)
ok('M1-a 같은 회차 실행 상태는 결합', '실행 중' in h(s_run) and '✓ lidar⊆{lidar}' in h(s_run))
ok('M1-a 상태 없음 → 상태 미확인', '상태 미확인' in h(None) and '완료' not in h(None))
# ── M1-b: 해체·종료는 이력으로 표시되고 실행 중 표와 다르다 ──
dis = copy.deepcopy(s_run); dis['state'] = 'dissolved'
ok('M1-b dissolved HTML ≠ running HTML', h(dis) != h(s_run))
ok('M1-b 해체 표기: 종료됨·이력·후보 없음', '종료됨: 마지막 관측 이력' in h(dis) and '(이력)' in h(dis) and '능력 충족 후보' not in h(dis))
suc = copy.deepcopy(s_run); suc['state'] = 'success'; suc['tree']['children'][0]['state'] = 'done'
ok('M1-b success 도 이력 표기 + 완료', '종료됨' in h(suc) and '완료(이력)' in h(suc))
# ── M1-c: 노드 라벨 조회는 그룹·회차 한정, 모호하면 None ──
g2 = '/group_relay_2'
P.new_run_id(g2)
rec2 = json.loads(json.dumps(P.plan_record(P.build_relay('tb3_0=5,5,0'), 'Relay', g2), ensure_ascii=False))
s2 = {'group': g2, 'run_id': rec2['run_id'], 'state': 'running', 'members': [], 'tree': None}
plans = {g: rec, g2: rec2}; sts = {g: s_run, g2: s2}
ok('M1-c 그룹 한정 조회(G2 의 동명 node 는 G2 행)', plan_row_for(plans, sts, [g2], node)['args']['target'] == '5,5,0'
   and plan_row_for(plans, sts, [g], node)['args']['target'] == '99,99,0')
# g2 는 트리가 없으므로 그려지는 동명 node 는 g 의 것 — 소유 그룹이 정해져 g 의 행; g2 트리에도 같은 node 가 있으면 모호 → None
ok('M1-c 두 그룹 중 트리가 한쪽에만 있으면 그 그룹의 행', plan_row_for(plans, sts, [g, g2], node)['args']['target'] == '99,99,0')
s2t = dict(s2, tree={'name': 'relay', 'kind': 'seq', 'children': [{'name': node, 'kind': 'atomic', 'agent': '', 'state': 'wait'}]})
ok('M1-c 두 그룹 트리에 모두 동명 node → 모호 → None', plan_row_for(plans, {g: s_run, g2: s2t}, [g, g2], node) is None)
sts_mis = {g: dict(s_run, run_id='other')}
ok('M1-c 회차 불일치면 None', plan_row_for(plans, sts_mis, [g], node) is None)
ok('M1-c 상태 없으면 None', plan_row_for(plans, {}, [g], node) is None)
# ── M2: 능력 정보 3상태 + 후보 문구 ──
rel = copy.deepcopy(s_run); rel['members'] = []
ok('M2 멤버 방출(정보 없음) → 검증 불가, ✗ 아님', '능력 정보 없음' in h(rel) and '✗' not in h(rel))
ok('M2 같은 회차 마지막 관측 cap 이 있으면 ✓(마지막 관측)', '✓ lidar⊆{lidar}' in h(rel, caps={(g, rid): {'/etri/tb3_0': ['lidar']}})
   and '같은 회차 마지막 관측' in h(rel, caps={(g, rid): {'/etri/tb3_0': ['lidar']}}))
ok('M2 다른 회차의 cap 이력은 쓰지 않음', '능력 정보 없음' in h(rel, caps={(g, 'old-run'): {'/etri/tb3_0': ['lidar']}}))
emp = copy.deepcopy(s_run); emp['members'] = [{'name': '/etri/tb3_0', 'cap': []}]
ok('M2 명시적 빈 능력 집합 → ✗ 불일치', '✗ lidar⊆{}' in h(emp))
una = copy.deepcopy(s_run); una['tree']['children'][0]['agent'] = ''; una['members'] = [{'name': '/etri/a', 'cap': ['lidar']}, {'name': '/etri/b', 'cap': ['camera']}]
ok('M2 미배정: "능력 충족 후보" 문구와 후보 a 만', '능력 충족 후보: a' in h(una) and ', b' not in h(una))
ok('M2 영어 문구', 'capability-compatible candidates: a' in h(una, ko=False) and 'cannot verify' in h(rel, ko=False))
ok('M2 표 밑 설명(유휴·affinity·ETA)', 'affinity' in h(s_run) and '실행 성공의 증빙이 아님' in h(s_run))
# ── M3: 매칭 셀 이스케이프 ──
mk = copy.deepcopy(s_run); mk['members'][0]['cap'].append('<b>CAP_MARK</b>')
x = h(mk)
ok('M3 매칭 셀·에이전트 셀 모두 리터럴', '<b>CAP_MARK</b>' not in x and x.count('&lt;b&gt;CAP_MARK&lt;/b&gt;') == 2)
mk2 = copy.deepcopy(rec); mk2['subtasks'][0]['requirement'] = ['lid<ar>&']
x2 = build_plan_html({g: mk2}, {g: s_run}, True)
ok('M3 요구 능력 쪽도 이스케이프, 판정(✗)은 보존', 'lid&lt;ar&gt;&amp;' in x2 and '<ar>' not in x2 and '✗' in x2)
# ── 입력 방어·기타 ──
ok('입력 방어: 상태가 객체가 아니면 무시', '상태 미확인' in build_plan_html({g: rec}, {g: []}, True))
ok('입력 방어: 계획이 객체가 아니면 빈 표', '<table>' in build_plan_html({g: []}, {}, True))
ok('CSS: 실행 중 class 일치', "class='running'" in h(s_run))
ok('가시성: 미션 16px 강조 블록', "class='mission'" in h(s_run) and 'font-size:16px' in h(s_run))
fb = P.fallback_record('Relay', 'PlanBuildError: x', g, P.build_relay('a=1,2,0')['root'])
ok('legacy: plan_source 빈 문자열·배지 없음·대체 표기', fb['plan_source'] == '' and 'EXAMPLE' not in build_plan_html({g: fb}, {}, True) and '고정 빌더로 대체' in build_plan_html({g: fb}, {}, True))
# ── R2-M1a: 수신 handler 를 데이터 객체에 적용(Dialog 없음) — 회차별 상태·해체 최종성·늦은 계획 결합 ──
from types import SimpleNamespace
from dlgJnpMonitor import DialogJnpMonitor as D


def receiver():
    return SimpleNamespace(m_plans={}, m_statuses={}, m_dissolved=set(), m_caps={}, m_runs={}, m_run_seq=0,
                           MAX_RUNS_PER_GROUP=20, m_finished={}, MAX_FINISHED_PER_GROUP=200,
                           m_ko=True, m_status=None, _log=lambda *a: None,
                           _redraw=lambda: None, _redraw_plan=lambda: None,
                           _select_display_status=lambda grp, _o=None: None, _prune_runs=lambda grp: None)


def bind(o):
    o._select_display_status = lambda grp: D._select_display_status(o, grp)
    o._prune_runs = lambda grp: D._prune_runs(o, grp)
    o._protected_runs = lambda grp: D._protected_runs(o, grp)
    return o


def st(o, x): D._on_status_line(o, json.dumps(x))
def pl(o, x): D._on_plan_line(o, json.dumps(x))


sA = dict(group=g, run_id=rid, state='running', members=[{'name': '/etri/tb3_0', 'cap': ['lidar']}],
          tree=dict(name=node, kind='atomic', state='running', agent='/etri/tb3_0'))
# 시퀀스 1: status A:dissolved → status B:success → plan B  (A 의 해체가 B 를 막지 않고, 먼저 온 B 상태를 계획과 결합)
sA_done = dict(sA, state='success', tree=dict(sA['tree'], state='done'))
o = bind(receiver()); st(o, dict(sA, run_id='old', state='dissolved')); st(o, sA_done); pl(o, rec)
ok('R2-M1a ① 이전 회차 해체 뒤 새 회차 success → 늦은 계획과 결합', o.m_statuses.get(g, {}).get('state') == 'success' and o.m_statuses[g]['run_id'] == rid)
ok('R2-M1a ① 표에도 완료(이력)로 결합', '완료(이력)' in build_plan_html(o.m_plans, o.m_statuses, True, o.m_caps))
# 시퀀스 2: plan B → status B:running → 늦은 status A:dissolved → status B:success  (A 는 A 의 이력에만, B 는 계속 진행·완료)
o = bind(receiver()); pl(o, rec); st(o, sA); st(o, dict(sA, run_id='old', state='dissolved'))
ok('R2-M1a ② 늦은 이전 회차 해체가 현재 회차 상태를 덮지 않음', o.m_statuses[g]['run_id'] == rid and o.m_statuses[g]['state'] == 'running' and g not in o.m_dissolved)
st(o, dict(sA, state='success'))
ok('R2-M1a ② 현재 회차 success 가 차단되지 않음', o.m_statuses[g]['state'] == 'success')
ok('R2-M1a ② 이전 회차 해체는 회차 보관함에만', o.m_runs[(g, 'old')]['dissolved'] is True and o.m_runs[(g, rid)]['dissolved'] is False)
# 시퀀스 3: plan B → status B:dissolved → 잔여 status B:running  (같은 회차 해체는 최종)
o = bind(receiver()); pl(o, rec); st(o, dict(sA, state='dissolved')); st(o, sA)
ok('R2-M1a ③ 같은 회차 dissolved 뒤 running 은 되살아나지 않음', o.m_statuses[g]['state'] == 'dissolved' and g in o.m_dissolved)
st(o, dict(sA, state='success'))
ok('R2-M1a ③ 같은 회차 dissolved 뒤 success 도 무시', o.m_statuses[g]['state'] == 'dissolved')
# 정상 양방향 도착
o = bind(receiver()); pl(o, rec); st(o, sA); ok('R2-M1a 정상 plan→status 결합', o.m_statuses[g]['run_id'] == rid)
o = bind(receiver()); st(o, sA); pl(o, rec); ok('R2-M1a 정상 status→plan 결합', o.m_statuses[g]['run_id'] == rid)
# 거부된 잔여 상태는 cap 이력을 바꾸지 않음
o = bind(receiver()); pl(o, rec); st(o, dict(sA, state='dissolved'))
st(o, dict(sA, state='running', members=[{'name': '/etri/tb3_0', 'cap': ['lidar', 'bogus']}]))
ok('R2-M1a ④ 거부된 상태는 마지막 관측 cap 을 갱신하지 않음', o.m_caps[(g, rid)]['/etri/tb3_0'] == ['lidar'])
# 같은 회차의 트리 유지는 보관 상태에서, 다른 회차 트리는 붙지 않음
o = bind(receiver()); pl(o, rec); st(o, sA); st(o, dict(sA, state='running', tree=None))
ok('R2-M1a ⑤ 트리 없는 발행에 같은 회차 트리 유지', (o.m_statuses[g].get('tree') or {}).get('name') == node)
o = bind(receiver()); st(o, dict(sA, run_id='old')); st(o, dict(sA, tree=None))
ok('R2-M1a ⑤ 다른 회차의 트리는 붙지 않음', not o.m_statuses[g].get('tree'))
# 계획 없는 그룹(구버전): 가장 최근 수용 상태 표시
o = bind(receiver()); st(o, dict(sA, run_id='r1', state='running')); st(o, dict(sA, run_id='r2', state='forming'))
ok('R2-M1a ⑥ 계획 없는 그룹은 최근 수용 상태 표시', o.m_statuses[g]['run_id'] == 'r2')
# 보관 상한
o = bind(receiver())
for i in range(25):
    st(o, dict(sA, run_id='r%02d' % i))
ok('R2-M1a ⑦ 그룹당 회차 보관 상한(20)', len([k for k in o.m_runs if k[0] == g]) == 20 and (g, 'r00') not in o.m_runs and (g, 'r24') in o.m_runs)
# ── R2-M1c: 동명 node 두 그룹, 계획 부분 수신 ──
gA, gB = '/G1', '/G2'
P.new_run_id(gA); rA = json.loads(json.dumps(P.plan_record(P.build_relay('tb3_0=99,99,0'), 'Relay', gA)))
P.new_run_id(gB); rB = json.loads(json.dumps(P.plan_record(P.build_relay('tb3_0=5,5,0'), 'Relay', gB)))
nn = rA['subtasks'][0]['node']
sa = dict(group=gA, run_id=rA['run_id'], state='running', members=[], tree=dict(name='relay', kind='seq', children=[dict(name=nn, kind='atomic', agent='', state='wait', goal='nav:99,99,0')]))
sb = dict(group=gB, run_id=rB['run_id'], state='running', members=[], tree=dict(name='relay', kind='seq', children=[dict(name=nn, kind='atomic', agent='', state='wait', goal='nav:5,5,0')]))
both = {gA: sa, gB: sb}
ok('R2-M1c ① 양쪽 계획: 합친 트리에서 각자 자기 행(소유 그룹 단독 조회)', plan_row_for({gA: rA, gB: rB}, both, [gA], nn)['args']['target'] == '99,99,0'
   and plan_row_for({gA: rA, gB: rB}, both, [gB], nn)['args']['target'] == '5,5,0')
ok('R2-M1c ① 두 그룹을 함께 주면(소유 불명) None', plan_row_for({gA: rA, gB: rB}, both, [gA, gB], nn) is None)
ok('R2-M1c ② G1 계획만: G2 node 는 미확인, 합친 조회도 None', plan_row_for({gA: rA}, both, [gB], nn) is None and plan_row_for({gA: rA}, both, [gA, gB], nn) is None
   and plan_row_for({gA: rA}, both, [gA], nn)['args']['target'] == '99,99,0')
ok('R2-M1c ③ G2 계획만: G1 node 는 미확인', plan_row_for({gB: rB}, both, [gA], nn) is None and plan_row_for({gB: rB}, both, [gB], nn)['args']['target'] == '5,5,0')
ok('R2-M1c ④ 한쪽 run 불일치 → None', plan_row_for({gA: rA, gB: rB}, {gA: dict(sa, run_id='x'), gB: sb}, [gA], nn) is None)
# 서로 다른 node 의 goal 별 coalition 합치기는 보존(각 node 는 자기 그룹에서 찾힘)
rB2 = json.loads(json.dumps(dict(rB, subtasks=[dict(rB['subtasks'][0], node='relay1.tb3_9')])))
sb2 = dict(sb, tree=dict(name='relay', kind='seq', children=[dict(name='relay1.tb3_9', kind='atomic', agent='', state='wait')]))
ok('R2-M1c ⑤ 서로 다른 node 는 합쳐도 각자 조회됨', plan_row_for({gA: rA, gB: rB2}, {gA: sa, gB: sb2}, [gA, gB], nn)['args']['target'] == '99,99,0'
   and plan_row_for({gA: rA, gB: rB2}, {gA: sa, gB: sb2}, [gA, gB], 'relay1.tb3_9')['args']['target'] == '5,5,0')
# 2차 보고서 §6 반례(기대값 반전)
o = bind(receiver()); st(o, dict(sA, run_id='old', state='dissolved')); st(o, dict(sA, state='success')); pl(o, rec)
ok('보고서 반례1 반전: 계획 뒤 상태 존재', g in o.m_statuses)
o = bind(receiver()); pl(o, rec); st(o, sA); st(o, dict(sA, run_id='old', state='dissolved')); st(o, dict(sA, state='success'))
ok('보고서 반례2 반전: 현재 회차가 old 에 덮이지 않음', o.m_statuses[g]['run_id'] != 'old')
o = bind(receiver()); pl(o, rec); st(o, dict(sA, state='dissolved')); st(o, sA)
ok('보고서 반례3 반전: dissolved 유지', o.m_statuses[g]['state'] != 'running')
s2x = dict(copy.deepcopy(sA), group='/group_relay_2', run_id='run2'); s2x['tree']['goal'] = 'nav:5,5,0'
ok('보고서 반례4 반전: 계획 없는 그룹의 동명 node 에 다른 그룹 행이 붙지 않음', plan_row_for({g: rec}, {g: sA, '/group_relay_2': s2x}, [g, '/group_relay_2'], node) is None)
# ── R3-F1: run_id 없는(구버전) 그룹은 회차 미식별 호환 모드 — 재시작이 영구 차단되지 않음 ──
for label, mk in (('생략', lambda x: {k: v for k, v in x.items() if k != 'run_id'}), ('빈 문자열', lambda x: dict(x, run_id=''))):
    o = bind(receiver()); lg = mk(sA)
    st(o, dict(lg, state='dissolved')); st(o, dict(lg, state='forming')); st(o, dict(lg, state='running'))
    ok('R3-F1 run_id %s: dissolved 뒤 forming/running 이 표시됨(재시작 허용)' % label, o.m_statuses[g]['state'] == 'running' and g not in o.m_dissolved)
    ok('R3-F1 run_id %s: 회차 미식별 표식·cap 이력 없음·종료 표식 없음' % label, o.m_statuses[g].get('_run_unknown') is True and (g, '') not in o.m_caps and not o.m_finished.get(g))
    st(o, dict(lg, state='running', tree=None))
    ok('R3-F1 run_id %s: 트리 유지도 적용하지 않음' % label, not o.m_statuses[g].get('tree'))
    o2 = bind(receiver()); pl(o2, rec); st(o2, dict(lg, state='running'))
    ok('R3-F1 run_id %s: 계획이 있는 그룹에서는 결합하지 않음(상태 미확인)' % label, g not in o2.m_statuses and '상태 미확인' in build_plan_html(o2.m_plans, o2.m_statuses, True, o2.m_caps))
    o3 = bind(receiver()); st(o3, dict(lg, state='running'))
    ok('R3-F1 run_id %s: 미식별 상태를 직접 넘기면 패널 머리말에 회차 미식별 안내·행은 상태 미확인' % label,
       '회차 미식별' in build_plan_html({g: rec}, o3.m_statuses, True) and '상태 미확인' in build_plan_html({g: rec}, o3.m_statuses, True)
       and 'without run_id' in build_plan_html({g: rec}, o3.m_statuses, False))
o = bind(receiver()); pl(o, rec); st(o, dict(sA, state='dissolved')); st(o, sA)
ok('R3-F1 비어 있지 않은 run_id 의 해체 최종성은 유지', o.m_statuses[g]['state'] == 'dissolved')
# ── R3-F2: 보관 상한이 현재 계획 회차의 상태·해체 표식을 지우지 않음 ──
o = bind(receiver()); pl(o, rec); st(o, dict(sA, state='dissolved'))
for i in range(20):
    st(o, dict(sA, run_id='other-%d' % i))
ok('R3-F2 현재 계획 회차는 정리에서 보호됨', (g, rid) in o.m_runs and o.m_statuses.get(g, {}).get('state') == 'dissolved')
ok('R3-F2 상세 보관 상한 유지(보호 1 + 나머지 19 = 20)', len([k for k in o.m_runs if k[0] == g]) == 20)
st(o, dict(sA, members=[dict(name='/etri/tb3_0', cap=['bogus'])]))
ok('R3-F2 늦은 A:running 은 거부(해체 최종성 유지)·cap 미반영', o.m_statuses[g]['state'] == 'dissolved' and o.m_caps[(g, rid)]['/etri/tb3_0'] == ['lidar'])
# 상세가 정리된(비보호) 종료 회차의 늦은 상태도 종료 표식 창 안에서는 거부
o = bind(receiver()); st(o, dict(sA, run_id='fin-1', state='dissolved'))
for i in range(25):
    st(o, dict(sA, run_id='x-%d' % i))
ok('R3-F2 정리된 종료 회차의 표식은 별도 창에 남음', (g, 'fin-1') not in o.m_runs and 'fin-1' in o.m_finished[g])
st(o, dict(sA, run_id='fin-1', state='running'))
ok('R3-F2 정리된 종료 회차의 늦은 running 도 거부', (g, 'fin-1') not in o.m_runs)
# 계획이 다른 회차로 바뀌면 보호 대상도 바뀜
o = bind(receiver()); pl(o, rec); st(o, sA)
rec_b = dict(rec, run_id='B-run'); pl(o, rec_b); st(o, dict(sA, run_id='B-run'))
for i in range(20):
    st(o, dict(sA, run_id='o-%d' % i))
ok('R3-F2 계획 교체 뒤 새 회차가 보호되고 옛 회차는 정리 가능', (g, 'B-run') in o.m_runs and (g, rid) not in o.m_runs)
# 종료 표식 창 상한
o = bind(receiver())
for i in range(205):
    st(o, dict(sA, run_id='d-%d' % i, state='dissolved'))
ok('R3-F2 종료 표식 창 상한(200)', len(o.m_finished[g]) == 200 and 'd-0' not in o.m_finished[g] and 'd-204' in o.m_finished[g])
# ROUND3 §5 재현 코드(기대값 반전)
o = bind(receiver()); legacy = {k: v for k, v in sA.items() if k != 'run_id'}
st(o, dict(legacy, state='dissolved')); st(o, dict(legacy, state='forming')); st(o, dict(legacy, state='running'))
ok('ROUND3 반례 R3-F1 반전', o.m_statuses[g]['state'] != 'dissolved')
o = bind(receiver()); pl(o, rec); st(o, dict(sA, state='dissolved'))
for i in range(20):
    st(o, dict(sA, run_id='other-' + str(i)))
st(o, dict(sA, members=[dict(name='/etri/tb3_0', cap=['bogus'])]))
ok('ROUND3 반례 R3-F2 반전', (g, rid) in o.m_runs and g in o.m_statuses and o.m_statuses[g]['state'] != 'running' and o.m_caps[(g, rid)]['/etri/tb3_0'] != ['bogus'])
print('TOTAL monitor html %d FAIL' % F)
sys.exit(1 if F else 0)
