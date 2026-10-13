#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.8.2 2026-10-14] JnP Monitor '미션 → 작업 분할 → 스킬 매칭' 패널의 순수 함수 검사(헤드리스, DialogJnpMonitor 인스턴스 없음).
#   source <workspace>/devel/setup.bash && QT_QPA_PLATFORM=offscreen python3 code/Multi-Agent-Simulator/test_dlgJnpMonitor_html.py
# M1 회차·그룹·해체 결합, M2 능력 정보 3상태·후보 문구, M3 이스케이프 (검수 보고서 CODEX_REVIEW_MONITOR_20261014 의 반례를 회귀검사로)
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
ok('M1-c 두 그룹을 합친 트리에서 동명 node 는 모호 → None', plan_row_for(plans, sts, [g, g2], node) is None)
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
print('TOTAL monitor html %d FAIL' % F)
sys.exit(1 if F else 0)
