#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.8.2 2026-10-13] / 개정 [JnP-0.9.0 2026-10-18] 역할(role) 기반 — 계획은 로봇을 지정하지 않는다
"""jnp_plan.py — 기본 협업 태스크의 '작업 분할' 경로 (0.9.0):

    plans/<task>.py (LLM-TDM 형식 계획, 로봇 미지정) ─bind(역할 이름·지점)→ plan_to_tasktree (canonical v2: 단위 task 에 role 칸)
      ─역할표(role_table)→ [그룹: 명부 수집 → 역할마다 로봇 할당(jnp_scheduler.assign_roles)]
      ─build(roles_bound)→ jnp_task 객체 트리 (노드 이름은 역할에 묶인 로봇 이름 — 그룹 후처리·Monitor 호환)

두 단계 API:
  prep = plan_roles(goal, payload, …)        # 계획 먼저: canonical·역할표·힌트·시작점 (로봇 없음)
  res  = build(goal, payload, roles_bound={역할: 로봇}, prep=prep, …)   # 역할→로봇 바인딩 뒤 실행 트리
roles_bound 를 주지 않으면 default_binding(힌트 순서) 으로 묶는다 — CLI·검사·0.8.2 비교용.

원자 node 의 실행 속성(goal 문자열·요구 능력·순차/병렬 종류·optional·상시 가상 서비스)은 스킬 카탈로그(config/skills_catalog_basic.json v0.3)에서
읽는다. 어댑터는 노드 **이름**과 복합 node 의 **묶음**만 정하고(plans/README.md '실행 변환 규칙'), 순서 제약은 바꾸지 않는다 — build() 가
반환하기 전에 (1) canonical 원자 ↔ 실행 원자 1:1, (2) 선행 쌍 집합 동일, (3) 태스크별 완전성을 검사한다. 걸리면 PlanBuildError.

사용(그룹):   prep = jnp_plan.plan_roles('Relay', payload, parse_multigoal=…, parse_avoidance=…, speed_fn=…, names=…)
              res  = jnp_plan.build('Relay', payload, roles_bound={'leg1': 'tb3_0', …}, prep=prep)
ROS 없이:     python3 jnp_plan.py Relay "tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.00,0.00"
              python3 jnp_plan.py MapExplore "robots=tb3_0|locobot_0" host=locobot_0
"""
import json
import math
import os
import re
import sys
import time
import types
import uuid

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from jnp_task import (SequentialCompositeTask, ParallelCompositeTask,          # noqa: E402
                      SequentialAtomicTask, ParallelAtomicTask)
import plan_to_tasktree as p2t                                               # noqa: E402

PLAN_FILES = {'Relay': 'relay.py', 'Mult-Goal': 'multigoal.py', 'Avoidance': 'avoidance.py',
              'MapExplore': 'map_explore.py', 'ObjectSearch': 'object_search.py'}
# [JnP-1.0 2026-11-07] 같은 goal 의 다른 계획(변형). 그룹이 파라미터로 고른다. 변형을 주지 않으면 위 기본 파일이다.
PLAN_VARIANTS = {'ObjectSearch': {'explore': 'object_search_explore.py'}}   # 지도 없는 수색: 순찰(Patrol) 대신 탐사(Explore) + 탐지
AGENT_NS = '/etri/'          # 0.8.1 고정 빌더와 같은 가상 task 의 agent 표시 네임스페이스
RECORD_SCHEMA = 'jnp-plan-record/2'   # [0.9.0] roles · assignments · recruit 추가
_CONTROL = re.compile(r'[\x00-\x1f\x7f]')


class PlanBuildError(RuntimeError):
    """계획을 실행 트리로 만들 수 없음(바인딩 값 거부·변환 실패·계약/완전성 검사 실패·역할 미바인딩). 그룹은 고정 빌더로 대체."""


# ───────────────────────── 계획 파일 읽기·바인딩·변환 ─────────────────────────
def plans_dir():
    cands = [os.path.join(os.path.dirname(HERE), 'plans')]          # 소스 트리 / devel 래퍼(__file__ = 소스 경로)
    try:
        import rospkg
        cands.append(os.path.join(rospkg.RosPack().get_path('jnp'), 'plans'))   # install 공간 share/jnp/plans
    except Exception:
        pass
    for d in cands:
        if os.path.isdir(d):
            return d
    raise PlanBuildError('plans/ 폴더를 찾을 수 없음: %s' % cands)


def goal_key(goal):
    """그룹 goal 라벨(미션 종류: 'Relay', 'Mult-Goal', …) → 계획 키."""
    for k in PLAN_FILES:
        if k in (goal or ''):
            return k
    raise PlanBuildError('계획이 없는 goal: %r' % goal)


def load_plan(key, variant=None):
    name = PLAN_FILES[key]
    if variant:
        try:
            name = PLAN_VARIANTS[key][variant]
        except KeyError:
            raise PlanBuildError('goal %s 에 계획 변형 %r 이 없음' % (key, variant))
    path = os.path.join(plans_dir(), name)
    with open(path, encoding='utf-8') as f:
        return path, f.read()


def _check_value(where, v):
    if not isinstance(v, str) or v == '':
        raise PlanBuildError('%s: 빈 값은 바인딩할 수 없음' % where)
    if _CONTROL.search(v):
        raise PlanBuildError('%s: 제어문자(줄바꿈 등)가 든 값 %r 은 지원하지 않음' % (where, v))


def bind(code, consts):
    """모듈 상수 자리(NAME = …)를 실행 시 값으로 바꾼다. 값은 JSON 리터럴로 넣고 치환은 callable replacement 로 한다
    (백슬래시·따옴표 보존). 제어문자가 든 값은 거부한다. 코드는 실행하지 않는다(ast 기호 평가)."""
    for name, values in consts.items():
        if isinstance(values, dict):
            out = {}
            for k, v in values.items():
                _check_value('%s 키' % name, k)
                if isinstance(v, (list, tuple)):
                    for x in v:
                        _check_value('%s[%s]' % (name, k), x)
                    out[k] = [str(x) for x in v]
                else:
                    _check_value('%s[%s]' % (name, k), v)
                    out[k] = str(v)
            lit = json.dumps(out, ensure_ascii=False)
        else:
            for v in values:
                _check_value(name, v)
            lit = json.dumps([str(v) for v in values], ensure_ascii=False)
        repl = '%s = %s' % (name, lit)
        code, n = re.subn(r'^%s\s*=.*$' % re.escape(name), lambda m: repl, code, count=1, flags=re.M)
        if n != 1:
            raise PlanBuildError('계획 파일에 모듈 상수 %s 자리가 없음' % name)
    return code


PLAN_SOURCES = ('example', 'llm-tdm', 'unknown')   # 작성자 선언(생성 사실을 검증하지 않음)


def plan_source(code):
    m = re.search(r"^#\s*Plan Source:\s*([A-Za-z0-9_\-]+)", code, flags=re.M)
    if not m:
        return 'unknown'
    v = m.group(1).lower()
    if v not in PLAN_SOURCES:
        print("[PLAN] warning: Plan Source %r 는 %s 밖의 값 — unknown 으로 기록" % (m.group(1), PLAN_SOURCES), flush=True)
        return 'unknown'
    return v


# 실행 회차 식별자 — 그룹 프로세스 하나 = 회차 하나.
_RUN = {'id': None}


def new_run_id(node_name='group'):
    _RUN['id'] = '%s@%d-%s' % ((node_name or 'group').strip('/'), int(time.time() * 1000), uuid.uuid4().hex[:6])
    return _RUN['id']


def current_run_id():
    return _RUN['id']


def convert(code, source):
    cat = p2t.load_catalog()
    try:
        r = p2t.convert_code(code, cat, source=source, strict_source=True)
    except p2t.PlanIssue as e:
        raise PlanBuildError('계획 변환 실패(%s): %s' % (source, e))
    errs = []
    for key in ('canonical_validation', 'semantic_validation'):
        errs += (r.get(key) or {}).get('errors') or []
    if errs:
        raise PlanBuildError('canonical 검증 실패(%s): %s' % (source, errs))
    can = r['canonical']
    return {'canonical': can, 'warnings': r.get('warnings') or [], 'text': r.get('text', ''),
            'dump': p2t.dump_tree(can), 'catalog': cat, 'plan_source': plan_source(code)}


def branches(doc):
    """canonical 루트 → 병렬 가지 목록(각 가지 = 원자 목록, 순서 보존). 가지가 하나뿐이면 루트가 sequential 로 접혀 있으므로 되돌린다(R7)."""
    if doc['type'] == 'parallel':
        return [list(p2t.iter_atomics(sub)) for sub in doc.get('subtasks') or []]
    return [list(p2t.iter_atomics(doc))]


def _arg(node, key):
    return str((node.get('args') or {}).get(key, ''))


def _xy(spec):
    """'x,y[,th]' → (x, y) 또는 None."""
    try:
        v = [float(t) for t in str(spec).split(',')[:2]]
        return (v[0], v[1]) if len(v) == 2 else None
    except (ValueError, TypeError):
        return None


# ───────────────────────── 역할표: canonical v2 → 역할마다 요구(스킬·능력) ─────────────────────────
def role_table(canonical, catalog):
    """역할표. 역할의 요구 = 그 역할의 **배정 대상** 단위 task 들의 스킬 합집합 + 요구 능력(카탈로그 requirement ∪ requirements) + 계획의
    ROLE_REQUIRES. 가상/상시 서비스 단계(WaitPass·Detect·SendMap·MergeMaps)는 스킬 요구를 만들지 않고 services 에만 적힌다.
    role 이 없는 단위 task(Trip) 는 풀(pool): 자격 있는 유휴 로봇 아무나.
    반환 (roles: [{name, skills, requirements, prefer, requires, tasks, services}] 선언 순, pool: {skills, requirements, tasks} 또는 None)."""
    acts = (catalog.get('actions') or {})
    decl = canonical.get('roles') or {}
    roles = []
    by = {}
    for r in canonical.get('role_order') or []:
        d = decl.get(r) or {}
        spec = {'name': r, 'skills': set(), 'requirements': set(d.get('requires') or []), 'prefer': list(d.get('prefer') or []),
                'requires': list(d.get('requires') or []), 'tasks': [], 'services': []}
        roles.append(spec)
        by[r] = spec
    pool = {'skills': set(), 'requirements': set(), 'tasks': [], 'services': []}
    for a in p2t.iter_atomics(canonical):
        info = acts.get(a['skill'])
        if info is None:
            raise PlanBuildError('카탈로그에 없는 스킬 %s' % a['skill'])
        r = a.get('role')
        if r is not None and r not in by:
            raise PlanBuildError('단위 task %s 의 역할 %r 가 역할표에 없음' % (a['id'], r))
        spec = by[r] if r is not None else pool
        if info.get('requirement') == 'virtual' or info.get('preassigned'):
            spec['services'].append(a['id'])
            continue
        spec['skills'].add(a['skill'])
        spec['requirements'].add(info.get('requirement'))
        spec['requirements'] |= set(a.get('requirements') or [])
        spec['tasks'].append(a['id'])
    return roles, (pool if pool['tasks'] else None)


# ───────────────────────── 1단계: 계획 먼저 (goal 별 prep) ─────────────────────────
def _prep(key, bindings, extra, hints=None, starts=None, prefer_names=None, skip_convert=False, variant=None):
    path, code = load_plan(key, variant)
    conv = None if skip_convert else convert(bind(code, bindings), os.path.basename(path))
    roles, pool = role_table(conv['canonical'], conv['catalog']) if conv else ([], None)
    d = {'key': key, 'file': path, 'code': code, 'bindings': bindings, 'conv': conv, 'variant': variant,
         'canonical': conv['canonical'] if conv else {}, 'catalog': conv['catalog'] if conv else p2t.load_catalog(),
         'roles': roles, 'pool': pool, 'hints': dict(hints or {}), 'starts': dict(starts or {}),
         'prefer_names': list(prefer_names or []), 'text': conv['text'] if conv else '',
         'warnings': list(conv['warnings']) if conv else [], 'dump': conv['dump'] if conv else '',
         'plan_source': plan_source(code)}
    d.update(extra)
    return d


def _parse_relay(payload):
    legs = []
    for seg in (payload or '').split(';'):
        seg = seg.strip()
        if not seg:
            continue
        name, eq, xyz = seg.partition('=')
        if not eq or not xyz.strip() or not name.strip():
            print("Group: 형식 오류 조각 무시: '%s' (기대: name=x,y,z)" % seg)
            continue
        legs.append((name.strip(), xyz.strip()))
    return legs


def prep_relay(payload):
    """'name=x,y,th;…' → 역할 leg1..N(payload 순서). 이름은 선호 로봇 힌트, 좌표는 다리의 목표(인계 지점).
    다리 i 의 시작점 = 다리 i-1 의 목표(ETA 계산용; leg1 은 없음). 지원 범위: 힌트 이름 유일(중복이면 PlanBuildError → 고정 빌더)."""
    legs = _parse_relay(payload)
    names = [n for n, _ in legs]
    if len(set(names)) != len(names):
        raise PlanBuildError('릴레이 계획은 로봇 이름이 유일해야 함(중복: %s) — 지원 범위 밖'
                             % sorted({n for n in names if names.count(n) > 1}))
    roles = ['leg%d' % (i + 1) for i in range(len(legs))]
    bindings = {'LEGS': roles, 'TARGETS': {r: xyz for r, (_, xyz) in zip(roles, legs)}}
    hints = {r: n for r, (n, _) in zip(roles, legs)}
    starts = {roles[i]: _xy(legs[i - 1][1]) for i in range(1, len(roles)) if _xy(legs[i - 1][1])}
    return _prep('Relay', bindings, {'legs': legs}, hints, starts, names, skip_convert=not legs)


def prep_multigoal(payload, parse_fn):
    """'goals=G:x,y:count|…;robots=…' → 풀 task(Trip). 멤버 명단(robots=)은 선호 로봇(분산 선택 결과)."""
    goals, robots = parse_fn(payload)
    GOALS = list(goals)
    ITEMS = {g: ['%s.item%d' % (g, k) for k in range(1, goals[g][2] + 1)] for g in GOALS}
    GOAL_POS = {g: '%.2f,%.2f' % (goals[g][0], goals[g][1]) for g in GOALS}
    bindings = {'GOALS': GOALS, 'ITEMS': ITEMS, 'GOAL_POS': GOAL_POS}
    return _prep('Mult-Goal', bindings, {'goals': goals, 'robots': robots}, {}, {}, list(robots),
                 skip_convert=not any(ITEMS.values()))


def prep_avoidance(payload, parse_fn, speed_fn):
    """'bt=cx,cy,r;routes=name:sx,sy>tx,ty|…' → 역할 = 경로 이름(ETA 순). 힌트 = 같은 이름의 로봇, 시작점 = 경로 시작점."""
    bt, routes = parse_fn(payload)
    if not bt:
        return _prep('Avoidance', {}, {'bt': None, 'routes': routes, 'order': []}, skip_convert=True)
    cx, cy, r = bt

    def _eta(nm):
        sx, sy = routes[nm][0], routes[nm][1]
        return max(0.0, math.hypot(sx - cx, sy - cy) - r) / speed_fn(nm)
    order = sorted(routes, key=_eta)
    TARGETS = {nm: '%.2f,%.2f' % (routes[nm][2], routes[nm][3]) for nm in order}
    PREV = {nm: order[k - 1] for k, nm in enumerate(order) if k > 0}
    bindings = {'FIRST': order[:1], 'REST': order[1:], 'TARGETS': TARGETS, 'PREV': PREV}
    hints = {nm: nm for nm in order}
    starts = {nm: (routes[nm][0], routes[nm][1]) for nm in order}
    return _prep('Avoidance', bindings, {'bt': bt, 'routes': routes, 'order': order}, hints, starts, list(order),
                 skip_convert=not order)


def prep_map_explore(names):
    """요청 로봇 수 k → 역할 host + explorer1..k-1. names 는 선호 로봇 명단(힌트 집합). 호스트는 ROLE_PREFER(compute_x86) 로 고른다."""
    names = list(names)
    k = len(names)
    explorers = ['explorer%d' % i for i in range(1, k)]
    bindings = {'HOST': ['host'] if k else [], 'EXPLORERS': explorers}
    return _prep('MapExplore', bindings, {'names': names}, {}, {}, names, skip_convert=not k)


def prep_object_search(names, variant=None):
    """variant=None: 알려진 지도의 구역 순찰(object_search.py). 'explore': 지도 없는 탐사형(object_search_explore.py) [2026-11-07]."""
    names = list(names)
    roles = ['searcher%d' % (i + 1) for i in range(len(names))]
    bindings = {'SEARCHERS': roles}
    return _prep('ObjectSearch', bindings, {'names': names}, {r: n for r, n in zip(roles, names)}, {}, names,
                 skip_convert=not names, variant=variant)


def plan_roles(goal, payload, **kw):
    """1단계: 계획을 변환해 canonical v2·역할표·힌트·시작점을 만든다. 로봇은 아직 없다.
    kw: parse_multigoal / parse_avoidance / speed_fn / names (그룹이 넘김)."""
    key = goal_key(goal)
    if key == 'Relay':
        return prep_relay(payload)
    if key == 'Mult-Goal':
        return prep_multigoal(payload, kw['parse_multigoal'])
    if key == 'Avoidance':
        return prep_avoidance(payload, kw['parse_avoidance'], kw['speed_fn'])
    if key == 'MapExplore':
        return prep_map_explore(kw['names'])
    return prep_object_search(kw['names'], variant=kw.get('variant'))


def default_binding(prep, **kw):
    """역할 → 로봇 기본 바인딩(힌트 순서): CLI·검사·0.8.2 고정 빌더와의 비교용. 그룹은 jnp_scheduler.assign_roles 결과를 쓴다.
    MapExplore: host ← kw['merge_host'](없으면 정렬 첫 이름), explorer 들 ← 나머지(정렬 순). ObjectSearch: searcher_i ← names_i(정렬 순)."""
    key = prep['key']
    if key in ('Relay', 'Avoidance', 'ObjectSearch'):
        return dict(prep['hints'])
    if key == 'MapExplore':
        names = sorted(prep['names'])
        if not names:
            return {}
        host = kw.get('merge_host') or names[0]
        if host not in names:
            raise PlanBuildError('지도제작: 병합 호스트 %r 가 참여 로봇 %s 에 없음' % (host, names))
        rest = [n for n in names if n != host]
        rb = {'host': host}
        for i, n in enumerate(rest, 1):
            rb['explorer%d' % i] = n
        return rb
    return {}


# ───────────────────────── 원자 node: 카탈로그가 실행 속성의 원천 (규칙 R1·R2) ─────────────────────────
def atomic_from(node, name, parent, catalog, robot=None):
    skill = node['skill']
    info = (catalog.get('actions') or {}).get(skill)
    if info is None:
        raise PlanBuildError('카탈로그에 없는 스킬 %s' % skill)
    args = dict(node.get('args') or {})
    rp = info.get('role_param')
    if rp:
        args[rp] = robot if robot is not None else str(node.get('role') or '')   # exec_goal 템플릿에 robot 자리가 쓰일 수 있음
    kind = info.get('node', 'sequential')
    if kind not in ('sequential', 'parallel'):
        raise PlanBuildError('카탈로그 %s.node 값 %r — sequential|parallel 만 허용' % (skill, kind))
    req = info.get('requirement')
    if not isinstance(req, str) or not req:
        raise PlanBuildError('카탈로그 %s.requirement 가 비어 있음' % skill)
    try:
        goal = str(info['exec_goal']).format(**args)
    except (KeyError, IndexError) as e:
        raise PlanBuildError('%s: exec_goal 템플릿 인수 %s 가 없음' % (skill, e))
    cls = SequentialAtomicTask if kind == 'sequential' else ParallelAtomicTask
    t = cls(name=name, parent=parent, goal=goal)
    t.addRequirement(req)
    for tag in node.get('requirements') or []:              # R2: 능력 태그(radar 등) → 요구 능력
        if tag in t.requirement:
            continue
        if req == 'virtual' or info.get('preassigned'):
            raise PlanBuildError('%s: 가상/상시 서비스 단계에는 능력 태그 %r 를 붙일 수 없음(배정 대상이 아님)' % (skill, tag))
        t.addRequirement(tag)
    if info.get('optional'):
        t.optional = True
    if info.get('preassigned'):
        t.assign_status = True
        t.agent = types.SimpleNamespace(name=AGENT_NS + str(robot if robot is not None else node.get('role') or ''))
    t._plan_id = node['id']
    t._skill = skill                      # [0.9.0] dispatch 최종 방어(can_execute)용
    t._role = node.get('role')            # [0.9.0] 역할(없으면 풀 task)
    t._robot = robot                      # [0.9.0] 역할에 묶인 로봇(짧은 이름)
    return t


# ───────────────────────── 계약 검사: canonical ↔ 실행 트리 ─────────────────────────
def _exec_atomics(t):
    if not hasattr(t, 'subtasks'):
        return [t]
    out = []
    for c in t.subtasks:
        out.extend(_exec_atomics(c))
    return out


def order_pairs_canonical(doc):
    pairs = set()

    def ids(n):
        return [a['id'] for a in p2t.iter_atomics(n)]

    def rec(n):
        if n['type'] == 'atomic':
            return
        ch = n.get('subtasks') or []
        if n['type'] == 'sequential':
            for i in range(len(ch)):
                for j in range(i + 1, len(ch)):
                    for a in ids(ch[i]):
                        for b in ids(ch[j]):
                            pairs.add((a, b))
        for c in ch:
            rec(c)
    rec(doc)
    return pairs


def order_pairs_exec(root):
    pairs = set()

    def pid(t):
        return getattr(t, '_plan_id', None)

    def rec(t):
        if not hasattr(t, 'subtasks'):
            for p in getattr(t, 'predecessors', []) or []:
                pairs.add((pid(p), pid(t)))
            return
        if isinstance(t, SequentialCompositeTask):
            ch = t.subtasks
            for i in range(len(ch)):
                for j in range(i + 1, len(ch)):
                    for a in _exec_atomics(ch[i]):
                        for b in _exec_atomics(ch[j]):
                            pairs.add((pid(a), pid(b)))
        for c in t.subtasks:
            rec(c)
    rec(root)
    return pairs


def check_contract(canonical, root):
    """canonical 과 실행 트리의 원자 ID 대응(1:1)과 순서 제약 집합을 검사한다. 어긋나면 PlanBuildError."""
    c_ids = [a['id'] for a in p2t.iter_atomics(canonical)]
    e_ids = [getattr(a, '_plan_id', None) for a in _exec_atomics(root)]
    if sorted(c_ids) != sorted(e_ids) or len(set(e_ids)) != len(e_ids):
        raise PlanBuildError('canonical 원자와 실행 원자가 1:1 이 아님: canonical=%s 실행=%s' % (c_ids, e_ids))
    pc, pe = order_pairs_canonical(canonical), order_pairs_exec(root)
    if pc != pe:
        raise PlanBuildError('순서 제약이 다름 — canonical 에만: %s, 실행 트리에만: %s'
                             % (sorted(pc - pe), sorted(pe - pc)))


def _expect(what, got, expect):
    if got != expect:
        raise PlanBuildError('%s: 기대 %s, 실제 %s' % (what, expect, got))


def _check_bound(prep, rb):
    """[R8] 역할 바인딩의 공통 경계: 모든 역할에 로봇(짧은 이름)이 묶였는지, 역할표 밖 키가 없는지, 한 로봇이 두 역할에 묶이지 않았는지.
    어긋나면 PlanBuildError — 트리를 만들 수 없다. (V-F5: Relay/Avoidance 에도 적용되도록 빌더별 검사에서 여기로 올림)"""
    if not isinstance(rb, dict):
        raise PlanBuildError('roles_bound 는 {역할: 로봇} 사전이어야 함')
    names = [r['name'] for r in prep['roles']]
    missing = [n for n in names if not rb.get(n)]
    if missing:
        raise PlanBuildError('역할에 로봇이 묶이지 않음: %s' % missing)
    extra = [k for k in rb if k not in names]
    if extra:
        raise PlanBuildError('역할표에 없는 역할이 바인딩됨: %s' % extra)
    for r, robot in rb.items():
        _check_value('역할 %s 의 로봇' % r, robot)
    seen = {}
    for r in names:
        if rb[r] in seen:
            raise PlanBuildError('한 로봇이 두 역할에 묶임: %s → %s, %s' % (rb[r], seen[rb[r]], r))
        seen[rb[r]] = r


def skippable_roles(prep):
    """[V-F2] skip 정책으로 건너뛸 수 있는 역할: 배정 대상 task 가 모두 optional 이고, 공유 서비스(shared_service)가 없고,
    다른 역할이 참조(role_refs, 예: WaitPass.prev)하지 않는 역할. 반환 {역할: 사유 또는 None(건너뛸 수 있음)}."""
    acts = (prep.get('catalog') or {}).get('actions') or {}
    can = prep.get('canonical') or {}
    referenced = set()
    for a in p2t.iter_atomics(can) if can else []:
        for ref in (acts.get(a['skill'], {}).get('role_refs') or []):
            referenced.add((a.get('args') or {}).get(ref))
    out = {}
    by_role = {}
    for a in p2t.iter_atomics(can) if can else []:
        by_role.setdefault(a.get('role'), []).append(a)
    for r in prep['roles']:
        atoms = by_role.get(r['name'], [])
        robot_tasks = [a for a in atoms if not (acts.get(a['skill'], {}).get('requirement') == 'virtual' or acts.get(a['skill'], {}).get('preassigned'))]
        why = None
        if not all(a.get('optional') for a in robot_tasks):
            why = '선택 태스크가 아닌 단계가 있음'
        elif any(acts.get(a['skill'], {}).get('shared_service') for a in atoms):
            why = '공유 서비스(%s)가 붙은 역할' % ','.join(a['skill'] for a in atoms if acts.get(a['skill'], {}).get('shared_service'))
        elif r['name'] in referenced:
            why = '다른 역할이 참조하는 역할'
        out[r['name']] = why
    return out


def prep_without_roles(prep, skipped):
    """[V-F2] 건너뛴 역할을 뺀 계획을 다시 만든다(바인딩 상수에서 그 역할 이름을 제거하고 재변환). 역할 이름은 그대로(번호를 다시 매기지 않음).
    남은 역할이 하나도 없으면 PlanBuildError."""
    skipped = set(skipped)
    binds = {}
    for k, v in (prep.get('bindings') or {}).items():
        if isinstance(v, dict):
            binds[k] = {kk: vv for kk, vv in v.items() if kk not in skipped}
        else:
            binds[k] = [x for x in v if x not in skipped]
    if not any(r['name'] not in skipped for r in prep['roles']):
        raise PlanBuildError('모든 역할을 건너뛰면 계획이 비어 실행할 수 없음: %s' % sorted(skipped))
    extra = {k: v for k, v in prep.items() if k not in ('key', 'file', 'code', 'bindings', 'conv', 'canonical', 'catalog', 'roles', 'pool',
                                                        'hints', 'starts', 'prefer_names', 'text', 'warnings', 'dump', 'plan_source')}
    new = _prep(prep['key'], binds, extra, {k: v for k, v in prep['hints'].items() if k not in skipped},
                {k: v for k, v in prep['starts'].items() if k not in skipped}, prep['prefer_names'])
    new['skipped'] = sorted(skipped)
    new['roles_all'] = prep['roles']
    return new


def _plan_meta(prep, rb):
    return {'file': prep['file'], 'bindings': prep['bindings'], 'plan_source': prep['plan_source'],
            'canonical': prep['canonical'], 'catalog': prep['catalog'], 'text': prep['text'],
            'warnings': list(prep['warnings']), 'dump': prep['dump'], 'roles_bound': dict(rb),
            'roles': [{'name': r['name'], 'skills': sorted(r['skills']), 'requirements': sorted(r['requirements']),
                       'prefer': list(r['prefer']), 'tasks': list(r['tasks']), 'services': list(r['services'])} for r in prep['roles']],
            'pool': ({'skills': sorted(prep['pool']['skills']), 'requirements': sorted(prep['pool']['requirements']),
                      'tasks': list(prep['pool']['tasks'])} if prep.get('pool') else None)}


# ───────────────────────── 2단계: 역할→로봇 바인딩 뒤 실행 트리 (goal 별 어댑터) ─────────────────────────
def build_relay(payload, roles_bound=None, prep=None):
    """Sequential[relay1.<robot> → relay2.<robot> …] (선행 사슬 R5). robot = 역할 leg_i 에 묶인 로봇."""
    prep = prep or prep_relay(payload)
    rb = roles_bound if roles_bound is not None else default_binding(prep)
    _check_bound(prep, rb)
    conv = prep['conv']
    legs = prep['legs']
    root = SequentialCompositeTask(name="relay", parent=None, goal="Relay")
    atoms = list(p2t.iter_atomics(conv['canonical'])) if conv else []
    _expect('릴레이 계획의 단계', [(a['skill'], a.get('role'), _arg(a, 'target')) for a in atoms],
            [('GoTo', 'leg%d' % (i + 1), xyz) for i, (_, xyz) in enumerate(legs)])
    prev = None
    for n, at in enumerate(atoms, 1):
        robot = rb[at['role']]
        t = atomic_from(at, "relay%d.%s" % (n, robot), root, conv['catalog'], robot)
        if prev:
            t.addPredecessor(prev)
        root.add(t)
        prev = t
    if conv:
        check_contract(conv['canonical'], root)
    return {'root': root, 'meta': None, 'dicts': {}, 'plan': _plan_meta(prep, rb)}


def build_multigoal(payload, parse_fn, roles_bound=None, prep=None):
    """Parallel[ G[count] = Parallel[ G.itemk(trip:x,y@G) … ] … ] — 풀 task(역할 없음). 빈 goal 가지도 만든다(R6)."""
    prep = prep or prep_multigoal(payload, parse_fn)
    rb = roles_bound if roles_bound is not None else {}
    goals = prep['goals']
    GOALS, ITEMS, GOAL_POS = prep['bindings']['GOALS'], prep['bindings']['ITEMS'], prep['bindings']['GOAL_POS']
    conv = prep['conv']
    root = ParallelCompositeTask(name="multigoal")
    subs = {}
    for g in GOALS:
        subs[g] = ParallelCompositeTask(name="%s[%d]" % (g, goals[g][2]), parent=root)
        root.add(subs[g])
    atoms = [a for br in branches(conv['canonical']) for a in br] if conv else []
    _expect('다목적 이동 계획의 물품', [(a['skill'], a.get('role'), _arg(a, 'item'), _arg(a, 'destination'), _arg(a, 'target')) for a in atoms],
            [('Trip', None, it, g, GOAL_POS[g]) for g in GOALS for it in ITEMS[g]])
    for at in atoms:
        g, item = _arg(at, 'destination'), _arg(at, 'item')
        t = atomic_from(at, item, subs[g], conv['catalog'])
        subs[g].add(t)
    if conv:
        check_contract(conv['canonical'], root)
    return {'root': root, 'meta': None, 'dicts': {}, 'plan': _plan_meta(prep, rb)}


def build_avoidance(payload, parse_fn, speed_fn, roles_bound=None, prep=None):
    """Parallel[ cross.<robot> = Sequential[ wait_pass.<prev robot>(virtual) → move.<robot>(nav:tx,ty) ] ] (ETA 순, root._bt_meta 포함).
    역할 = 경로 이름; 노드 이름·_bt_meta 의 키는 역할에 묶인 로봇 이름(그룹 관찰자가 odom 을 그 이름으로 읽는다)."""
    prep = prep or prep_avoidance(payload, parse_fn, speed_fn)
    rb = roles_bound if roles_bound is not None else default_binding(prep)
    root = ParallelCompositeTask(name="avoidance")
    if not prep.get('bt'):
        return {'root': root, 'meta': None, 'dicts': {}, 'plan': dict(_plan_meta(prep, {}), warnings=['bt 없음 — 빈 트리'])}
    _check_bound(prep, rb)
    conv = prep['conv']
    order, routes = prep['order'], prep['routes']
    cx, cy, r = prep['bt']
    TARGETS, PREV = prep['bindings']['TARGETS'], prep['bindings']['PREV']
    moves, waits = {}, {}
    brs = branches(conv['canonical']) if conv else []
    _expect('충돌회피 계획의 가지(역할, ETA 순)', [br[0].get('role') if br else None for br in brs], order)
    for k, br in enumerate(brs):
        role = order[k]
        robot = rb[role]
        _expect('충돌회피 가지 %s 의 단계' % role,
                [(a['skill'], a.get('role'), _arg(a, 'prev') if a['skill'] == 'WaitPass' else _arg(a, 'target')) for a in br],
                ([('WaitPass', role, PREV[role])] if k > 0 else []) + [('GoTo', role, TARGETS[role])])
        branch = SequentialCompositeTask(name="cross.%s" % robot, parent=root, goal='Avoidance')
        for at in br:
            if at['skill'] == 'WaitPass':
                w = atomic_from(at, "wait_pass.%s" % rb[_arg(at, 'prev')], branch, conv['catalog'], robot)
                branch.add(w)
                waits[robot] = w
            else:
                mv = atomic_from(at, "move.%s" % robot, branch, conv['catalog'], robot)
                branch.add(mv)
                moves[robot] = mv
        root.add(branch)
    if conv:
        check_contract(conv['canonical'], root)
    robot_order = [rb[x] for x in order]
    root._bt_meta = {'order': robot_order, 'moves': moves, 'waits': waits, 'center': (cx, cy), 'r': r,
                     'starts': {rb[n]: (routes[n][0], routes[n][1]) for n in routes if n in rb},
                     'targets': {rb[n]: (routes[n][2], routes[n][3]) for n in routes if n in rb},
                     'roles': {rb[n]: n for n in order}}
    return {'root': root, 'meta': root._bt_meta, 'dicts': {}, 'plan': _plan_meta(prep, rb)}


def _group_by_role(brs, roles, what):
    """병렬 가지들을 역할로 묶는다(규칙 R3). 가지 하나에 역할이 둘 섞이거나 역할표 밖이면 거부."""
    per = {n: [] for n in roles}
    for br in brs:
        for at in br:
            rl = at.get('role')
            if rl not in per:
                raise PlanBuildError('%s: 역할표에 없는 역할 %r 의 단계 %s' % (what, rl, at['skill']))
            per[rl].append(at)
    return per


def build_map_explore(names, merge_host=None, roles_bound=None, prep=None):
    """Parallel[ make_maps.<robot> = Parallel[ navigate.<robot>=Sequential[explore.<robot>], merge_maps|send_map.<robot>(virtual, 상시) ] ].
    규칙 R3(역할별 묶음)·R4(navigate 래퍼). dicts 의 키는 역할에 묶인 로봇 이름; 'host' 에 묶인 로봇이 병합 호스트."""
    prep = prep or prep_map_explore(names)
    rb = roles_bound if roles_bound is not None else default_binding(prep, merge_host=merge_host)
    conv = prep['conv']
    root = ParallelCompositeTask(name="map_explore")
    etasks, mtasks, branch, seqbr = {}, {}, {}, {}
    if not conv:
        return {'root': root, 'meta': None, 'dicts': {'etasks': etasks, 'mtasks': mtasks, 'branch': branch, 'seqbr': seqbr},
                'plan': _plan_meta(prep, rb)}
    _check_bound(prep, rb)
    role_names = [r['name'] for r in prep['roles']]
    per = _group_by_role(branches(conv['canonical']), role_names, '지도제작 계획')
    robots = {}
    for rl in role_names:
        robots[rl] = rb[rl]
        _expect('지도제작 계획 — 역할 %s 의 단계' % rl, sorted(a['skill'] for a in per[rl]),
                sorted(['Explore', 'MergeMaps' if rl == 'host' else 'SendMap']))
    if len(set(robots.values())) != len(robots):
        raise PlanBuildError('지도제작: 한 로봇이 두 역할에 묶임: %s' % robots)
    for rl in sorted(role_names, key=lambda x: robots[x]):          # 0.8.1 고정 빌더와 같은 순서(정렬된 로봇 이름)
        n = robots[rl]
        _br = ParallelCompositeTask(name="make_maps.%s" % n, parent=root)
        _sq = SequentialCompositeTask(name="navigate.%s" % n, parent=_br, goal='')
        for at in per[rl]:
            if at['skill'] == 'Explore':
                _t = atomic_from(at, "explore.%s" % n, _sq, conv['catalog'], n)
                _sq.add(_t)
                etasks[n] = _t
            else:
                _m = atomic_from(at, ("merge_maps.%s" if at['skill'] == 'MergeMaps' else "send_map.%s") % n, _br, conv['catalog'], n)
                mtasks[n] = _m
        _br.add(_sq)
        _br.add(mtasks[n])
        root.add(_br)
        seqbr[n] = _sq
        branch[n] = _br
    check_contract(conv['canonical'], root)
    return {'root': root, 'meta': None, 'dicts': {'etasks': etasks, 'mtasks': mtasks, 'branch': branch, 'seqbr': seqbr},
            'plan': _plan_meta(prep, rb)}


def build_object_search(names, roles_bound=None, prep=None):
    """Parallel[ search.<robot> = Parallel[ patrol.<robot>(search, optional), detect.<robot>(service:yolov8, virtual 상시) ] ] (R3).
    변형 'explore'(지도 없는 수색, 2026-11-07)는 순찰 대신 explore.<robot>(explore, optional) 이다. 그 밖의 묶음은 같다."""
    prep = prep or prep_object_search(names)
    rb = roles_bound if roles_bound is not None else default_binding(prep)
    conv = prep['conv']
    root = ParallelCompositeTask(name="object_search")
    etasks, dtasks, spars = {}, {}, {}
    if not conv:
        return {'root': root, 'meta': None, 'dicts': {'etasks': etasks, 'dtasks': dtasks, 'spars': spars}, 'plan': _plan_meta(prep, rb)}
    _check_bound(prep, rb)
    role_names = [r['name'] for r in prep['roles']]
    per = _group_by_role(branches(conv['canonical']), role_names, '물건찾기 계획')
    robots = {rl: rb[rl] for rl in role_names}
    if len(set(robots.values())) != len(robots):
        raise PlanBuildError('물건찾기: 한 로봇이 두 역할에 묶임: %s' % robots)
    for rl in sorted(role_names, key=lambda x: robots[x]):
        n = robots[rl]
        skills = sorted(a['skill'] for a in per[rl])
        if skills != ['Detect', 'Patrol']:          # 지도 없는 변형: 순찰 대신 탐사. 그 둘 밖의 조합은 거부
            _expect('물건찾기 계획 — 역할 %s 의 단계' % rl, skills, ['Detect', 'Explore'])
        _par = ParallelCompositeTask(name="search.%s" % n, parent=root)
        pat = [a for a in per[rl] if a['skill'] in ('Patrol', 'Explore')][0]
        det = [a for a in per[rl] if a['skill'] == 'Detect'][0]
        _t = atomic_from(pat, ("patrol.%s" if pat['skill'] == 'Patrol' else "explore.%s") % n, _par, conv['catalog'], n)
        _par.add(_t)
        _d = atomic_from(det, "detect.%s" % n, _par, conv['catalog'], n)
        _par.add(_d)
        root.add(_par)
        etasks[n], dtasks[n], spars[n] = _t, _d, _par
    check_contract(conv['canonical'], root)
    return {'root': root, 'meta': None, 'dicts': {'etasks': etasks, 'dtasks': dtasks, 'spars': spars}, 'plan': _plan_meta(prep, rb)}


# ───────────────────────── 공통 진입점·표시·기록 ─────────────────────────
def build(goal, payload, roles_bound=None, prep=None, **kw):
    """goal 라벨(미션 종류)로 디스패치. roles_bound = {역할: 로봇 짧은 이름}(그룹의 할당 결과; None 이면 기본 바인딩).
    prep = plan_roles() 결과(없으면 여기서 만든다). kw: parse_multigoal / parse_avoidance / speed_fn / names / merge_host.
    반환 {'root','meta','dicts','plan'} — 계약·완전성 검사를 마친 트리만 돌려준다."""
    key = goal_key(goal)
    if prep is None:
        prep = plan_roles(goal, payload, **kw)
    if key == 'Relay':
        return build_relay(payload, roles_bound, prep)
    if key == 'Mult-Goal':
        return build_multigoal(payload, kw.get('parse_multigoal'), roles_bound, prep)
    if key == 'Avoidance':
        return build_avoidance(payload, kw.get('parse_avoidance'), kw.get('speed_fn'), roles_bound, prep)
    if key == 'MapExplore':
        return build_map_explore(kw.get('names'), kw.get('merge_host'), roles_bound, prep)
    return build_object_search(kw.get('names'), roles_bound, prep)


def tree_text(root, indent=0):
    lines = []
    kind = type(root).__name__
    extra = ''
    if not hasattr(root, 'subtasks'):
        extra = '  req=%s goal=%s' % (','.join(root.requirement), root.goal)
        if getattr(root, '_role', None):
            extra += ' role=%s' % root._role
        if getattr(root, 'predecessors', None):
            extra += ' after=%s' % ','.join(p.name for p in root.predecessors)
        if getattr(root, 'optional', False):
            extra += ' optional'
        if getattr(root, 'assign_status', False) and getattr(root, 'agent', None) is not None:
            extra += ' preassigned=%s' % getattr(root.agent, 'name', '')
    lines.append('%s%s(%s)%s' % ('  ' * indent, root.name, kind, extra))
    for s in getattr(root, 'subtasks', []) or []:
        lines.append(tree_text(s, indent + 1))
    return '\n'.join(lines)


def _param_key(node_name):
    return '/jnp/plan/%s' % (node_name or 'group').strip('/').replace('/', '_')


PLAN_TOPIC = '/jnp/plan'      # latched std_msgs/String(JSON) — JnP Monitor 의 '미션 → 분할 → 스킬 매칭' 표시용
_PUB = {}


def subtask_rows(root, canonical=None, catalog=None):
    """실행 트리의 원자 task 하나 = 한 행(초기 트리 기준). canonical 이 있으면 _plan_id 로 이어 스킬·인자·역할·요구를 붙인다."""
    by_id = {a['id']: a for a in p2t.iter_atomics(canonical)} if canonical else {}
    acts = (catalog or {}).get('actions') or {}
    rows = []
    for t in _exec_atomics(root):
        pid = getattr(t, '_plan_id', None)
        c = by_id.get(pid) or {}
        ag = getattr(t, 'agent', None)
        info = acts.get(c.get('skill'), {}) if c else {}
        rows.append({
            'id': pid, 'skill': c.get('skill'), 'args': c.get('args') or {},
            'role': c.get('role') if c else getattr(t, '_role', None),
            'robot': getattr(t, '_robot', None) or '',
            'required_skills': list(c.get('required_skills') or []),
            'requirements': list(c.get('requirements') or []),
            'signature': info.get('signature', ''),
            'node': t.name, 'kind': 'seq' if isinstance(t, SequentialAtomicTask) else 'par',
            'exec_goal': t.goal, 'requirement': list(t.requirement),
            'optional': bool(getattr(t, 'optional', False)),
            'preassigned': bool(getattr(t, 'assign_status', False) and ag is not None),
            'preassigned_agent': getattr(ag, 'name', '') if ag is not None else '',
            'after': [p.name for p in getattr(t, 'predecessors', []) or []],
        })
    return rows


def assignment_rows(res):
    """역할 → 로봇 바인딩 행. 그룹이 res['assignments'](사유 포함)를 넣었으면 그대로, 없으면 roles_bound 에서 만든다."""
    if res.get('assignments'):
        return list(res['assignments'])
    plan = res.get('plan') or {}
    return [{'role': r, 'robot': b, 'reason': {}} for r, b in (plan.get('roles_bound') or {}).items()]


def plan_record(res, goal, node_name='group'):
    """계획 경로의 기록(JSON 직렬화 가능): 미션·바인딩·canonical v2·역할표·할당·실행 트리·행별 스킬 매칭."""
    plan = res.get('plan') or {}
    can = plan.get('canonical') or {}
    return {
        'schema': RECORD_SCHEMA, 'run_id': current_run_id() or new_run_id(node_name),
        'contract': can.get('contract', ''),
        'source': 'plan', 'goal': goal, 'group': node_name, 'plan_file': plan.get('file', ''),
        'plan_name': os.path.basename(plan.get('file', '') or ''),
        'plan_source': plan.get('plan_source', 'unknown'),
        'task_description': plan.get('text', ''),
        'bindings': plan.get('bindings') or {},
        'canonical': can,
        'canonical_dump': plan.get('dump', ''),
        'roles': list(plan.get('roles') or []),
        'roles_all': list(plan.get('roles_all') or [r['name'] for r in (plan.get('roles') or [])]),   # [R2 §5] 건너뛰기 전 원래 역할 이름 전부
        'pool': plan.get('pool'),
        'assignments': assignment_rows(res),
        'skipped': list(res.get('skipped') or []),          # [V-F2] 건너뛴 역할(로봇 없음) — 실행 성공이 아니라 '수행하지 않음'
        'recruit': res.get('recruit') or {},
        'warnings': list(plan.get('warnings') or []),
        'tree': tree_text(res['root']),
        'subtasks': subtask_rows(res['root'], can, plan.get('catalog')),
    }


def fallback_record(goal, reason, node_name='group', root=None):
    return {
        'schema': RECORD_SCHEMA, 'run_id': current_run_id() or new_run_id(node_name), 'contract': '',
        'source': 'legacy', 'goal': goal, 'group': node_name, 'reason': str(reason), 'plan_file': '', 'plan_name': '',
        'plan_source': '', 'task_description': '', 'bindings': {}, 'canonical': {}, 'canonical_dump': '',
        'roles': [], 'pool': None, 'assignments': [], 'recruit': {}, 'warnings': [],
        'tree': tree_text(root) if root is not None else '',
        'subtasks': subtask_rows(root) if root is not None else [],
    }


def _topic_publish(record):
    try:
        import rospy
        from std_msgs.msg import String
        pub = _PUB.get(PLAN_TOPIC)
        if pub is None:
            pub = rospy.Publisher(PLAN_TOPIC, String, queue_size=1, latch=True)
            _PUB[PLAN_TOPIC] = pub
        pub.publish(String(data=json.dumps(record, ensure_ascii=False)))
        return True
    except Exception as e:
        print('[PLAN] 토픽 %s 발행 실패: %s' % (PLAN_TOPIC, e), flush=True)
        return False


def _set_param(key, value):
    try:
        import rospy
        rospy.set_param(key, value)
        return True
    except Exception as e:
        print('[PLAN] rosparam %s 기록 실패: %s' % (key, e), flush=True)
        return False


def publish(res, goal, node_name='group'):
    """계획·canonical·역할·할당·트리를 콘솔에 덤프하고 rosparam /jnp/plan/<group> 과 latched 토픽 /jnp/plan 에 둔다(source=plan).
    새 회차 id(run_id)를 만든다. 반환 = rosparam 기록 ∧ 토픽 publish 호출 성공."""
    new_run_id(node_name)
    plan = res.get('plan') or {}
    print('[PLAN] source=plan %s ← %s (plan source: %s)  bindings=%s' % (goal, os.path.basename(plan.get('file', '?')),
                                                                        plan.get('plan_source', 'unknown'), plan.get('bindings')), flush=True)
    if plan.get('text'):
        print('[PLAN] mission (%s): %s' % (plan.get('plan_source', 'unknown'), plan['text']), flush=True)
    if plan.get('dump'):
        print('[PLAN] canonical TaskTree (%s):\n%s' % ((plan.get('canonical') or {}).get('contract', ''), plan['dump']), flush=True)
    for r in plan.get('roles') or []:
        print('[PLAN] role %s: skills=%s requirements=%s prefer=%s → %s' % (
            r['name'], ','.join(r['skills']) or '-', ','.join(r['requirements']) or '-', ','.join(r['prefer']) or '-',
            (plan.get('roles_bound') or {}).get(r['name'], '(미배정)')), flush=True)
    if plan.get('pool'):
        print('[PLAN] pool: skills=%s requirements=%s tasks=%d' % (','.join(plan['pool']['skills']), ','.join(plan['pool']['requirements']),
                                                                 len(plan['pool']['tasks'])), flush=True)
    for w in plan.get('warnings') or []:
        print('[PLAN] warning: %s' % w, flush=True)
    print('[PLAN] jnp TaskTree:\n' + tree_text(res['root']), flush=True)
    rec = plan_record(res, goal, node_name)
    ok_param = _set_param(_param_key(node_name), {
        'source': 'plan', 'goal': goal, 'plan_file': plan.get('file', ''), 'schema': RECORD_SCHEMA, 'contract': rec['contract'],
        'bindings': json.dumps(plan.get('bindings') or {}, ensure_ascii=False),
        'task_description': plan.get('text', ''), 'plan_source': rec['plan_source'], 'run_id': rec['run_id'],
        'canonical': json.dumps(plan.get('canonical') or {}, ensure_ascii=False),
        'roles': json.dumps(rec['roles'], ensure_ascii=False), 'assignments': json.dumps(rec['assignments'], ensure_ascii=False),
        'recruit': json.dumps(rec['recruit'], ensure_ascii=False),
        'warnings': list(plan.get('warnings') or []), 'tree': tree_text(res['root']),
        'subtasks': json.dumps(rec['subtasks'], ensure_ascii=False)})
    ok_topic = _topic_publish(rec)
    return bool(ok_param and ok_topic)


def unassigned_record(prep, goal, node_name, unassigned, recruit):
    """[0.9.0] 배정 불가(역할에 자격 로봇 없음)의 기록 — 트리는 없고 역할표·모집 결과만 남긴다(source=plan, unassigned 비어 있지 않음)."""
    return {
        'schema': RECORD_SCHEMA, 'run_id': current_run_id() or new_run_id(node_name),
        'contract': (prep.get('canonical') or {}).get('contract', ''),
        'source': 'plan', 'goal': goal, 'group': node_name, 'plan_file': prep.get('file', ''),
        'plan_name': os.path.basename(prep.get('file', '') or ''), 'plan_source': prep.get('plan_source', 'unknown'),
        'task_description': prep.get('text', ''), 'bindings': prep.get('bindings') or {},
        'canonical': prep.get('canonical') or {}, 'canonical_dump': prep.get('dump', ''),
        'roles': _plan_meta(prep, {})['roles'], 'pool': _plan_meta(prep, {})['pool'],
        'assignments': [], 'unassigned': list(unassigned), 'recruit': recruit or {},
        'warnings': list(prep.get('warnings') or []), 'tree': '', 'subtasks': [],
    }


def publish_unassigned(prep, goal, node_name, unassigned, recruit):
    """배정 불가를 rosparam /jnp/plan/<group> 과 latched 토픽 /jnp/plan 에 남긴다(새 run_id). 반환 = 기록 ∧ 발행 호출 성공."""
    new_run_id(node_name)
    rec = unassigned_record(prep, goal, node_name, unassigned, recruit)
    print('[PLAN] source=plan %s — 배정 불가: %s' % (goal, unassigned), flush=True)
    ok_param = _set_param(_param_key(node_name), {
        'source': 'plan', 'goal': goal, 'plan_file': rec['plan_file'], 'schema': RECORD_SCHEMA, 'contract': rec['contract'],
        'bindings': json.dumps(rec['bindings'], ensure_ascii=False), 'task_description': rec['task_description'],
        'plan_source': rec['plan_source'], 'run_id': rec['run_id'], 'canonical': json.dumps(rec['canonical'], ensure_ascii=False),
        'roles': json.dumps(rec['roles'], ensure_ascii=False), 'assignments': '[]', 'unassigned': list(unassigned),
        'recruit': json.dumps(rec['recruit'], ensure_ascii=False), 'warnings': rec['warnings'], 'tree': '', 'subtasks': '[]'})
    ok_topic = _topic_publish(rec)
    return bool(ok_param and ok_topic)


def publish_fallback(goal, reason, node_name='group', root=None):
    new_run_id(node_name)
    print('[PLAN] source=legacy %s — %s' % (goal, reason), flush=True)
    rec = fallback_record(goal, reason, node_name, root)
    ok_param = _set_param(_param_key(node_name), {
        'source': 'legacy', 'goal': goal, 'reason': str(reason), 'plan_file': '', 'schema': RECORD_SCHEMA, 'contract': '',
        'bindings': '{}', 'run_id': rec['run_id'], 'task_description': '', 'canonical': '{}', 'roles': '[]', 'assignments': '[]',
        'recruit': '{}', 'warnings': [], 'tree': tree_text(root) if root is not None else '',
        'subtasks': json.dumps(rec['subtasks'], ensure_ascii=False)})
    ok_topic = _topic_publish(rec)
    return bool(ok_param and ok_topic)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    g, pl = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else '')
    opts = dict(a.split('=', 1) for a in sys.argv[3:] if '=' in a)
    import jnp_group as G
    names = sorted([s.strip() for s in pl.replace('robots=', '').split(';')[0].split('|') if s.strip()]) \
        if g in ('MapExplore', 'ObjectSearch') else None
    host = opts.get('host') or (names[0] if names else None)
    try:
        res = build(g, pl, parse_multigoal=G.parse_multigoal_payload, parse_avoidance=G.parse_avoidance_payload,
                    speed_fn=G._robot_speed, names=names, merge_host=host)
    except PlanBuildError as e:
        print('[PLAN] PlanBuildError: %s' % e)
        sys.exit(1)
    publish(res, g)
