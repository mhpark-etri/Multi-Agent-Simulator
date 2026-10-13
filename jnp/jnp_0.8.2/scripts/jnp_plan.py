#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.8.2 2026-10-13]
"""jnp_plan.py — 기본 협업 태스크의 '작업 분할' 경로:
    plans/<task>.py (LLM-TDM 형식 계획) ─bind(payload)→ plan_to_tasktree (canonical TaskTree) ─어댑터→ jnp_task 객체 트리

계획 파일의 모듈 상수(ROBOTS·TARGETS·GOALS·ITEMS·FIRST/REST/PREV·HOST/EXPLORERS)는 GUI payload 에서 **실행 시 바인딩**한다
(계획 = 분할 구조, payload = 구체 값). 원자 node 의 실행 속성(goal 문자열·요구 능력·순차/병렬 종류·optional·상시 가상 서비스)은
스킬 카탈로그(config/skills_catalog_basic.json)에서 읽는다. 태스크별 어댑터는 노드 **이름**과 복합 node 의 **묶음**만 정하고
(plans/README.md '실행 변환 규칙'), 순서 제약은 바꾸지 않는다 — build() 가 반환하기 전에 다음을 검사한다:
  (1) canonical 원자 ↔ 실행 원자 1:1,  (2) 선행 쌍(순서 제약) 집합 동일,  (3) 태스크별 완전성(필수 스킬 수·로봇·호스트·중복).
검사에 걸리면 PlanBuildError — 그룹(jnp_group._plan_or_legacy)은 0.8.1 고정 빌더로 대체한다(~plan_strict=true 면 예외 전파).
만들어지는 트리는 0.8.1 고정 빌더와 이름·goal·요구 능력·선행·순서가 같다(test/test_plan_trees.py).

사용(그룹):   res = jnp_plan.build('Relay', payload, parse_multigoal=…, parse_avoidance=…, speed_fn=…, names=…, merge_host=…)
ROS 없이:     python3 jnp_plan.py Relay "tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.00,0.00"
              python3 jnp_plan.py MapExplore "robots=tb3_0|locobot_0" host=locobot_0
"""
import json
import math
import os
import re
import sys
import types

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from jnp_task import (SequentialCompositeTask, ParallelCompositeTask,          # noqa: E402
                      SequentialAtomicTask, ParallelAtomicTask)
import plan_to_tasktree as p2t                                               # noqa: E402

PLAN_FILES = {'Relay': 'relay.py', 'Mult-Goal': 'multigoal.py', 'Avoidance': 'avoidance.py',
              'MapExplore': 'map_explore.py', 'ObjectSearch': 'object_search.py'}
AGENT_NS = '/etri/'          # 0.8.1 고정 빌더와 같은 가상 task 의 agent 표시 네임스페이스
_CONTROL = re.compile(r'[\x00-\x1f\x7f]')


class PlanBuildError(RuntimeError):
    """계획을 실행 트리로 만들 수 없음(바인딩 값 거부·변환 실패·계약/완전성 검사 실패). 그룹은 고정 빌더로 대체."""


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
    """그룹 goal 문자열(예: 'Relay', 'Mult-Goal', …) → 계획 키."""
    for k in PLAN_FILES:
        if k in (goal or ''):
            return k
    raise PlanBuildError('계획이 없는 goal: %r' % goal)


def load_plan(key):
    path = os.path.join(plans_dir(), PLAN_FILES[key])
    with open(path, encoding='utf-8') as f:
        return path, f.read()


def _check_value(where, v):
    if not isinstance(v, str) or v == '':
        raise PlanBuildError('%s: 빈 값은 바인딩할 수 없음' % where)
    if _CONTROL.search(v):
        raise PlanBuildError('%s: 제어문자(줄바꿈 등)가 든 값 %r 은 지원하지 않음' % (where, v))


def bind(code, consts):
    """모듈 상수 자리(NAME = …)를 실행 시 값으로 바꾼다. 값은 JSON 리터럴(= 파이썬 문자열/리스트/사전 리터럴)로 넣고,
    치환은 callable replacement 로 한다 — 정규식 replacement 의 이스케이프 재해석이 없어 백슬래시·따옴표가 그대로 보존된다.
    제어문자(실제 줄바꿈 등)가 든 값은 거부한다(조용히 다른 값으로 바꾸지 않는다). 코드는 실행하지 않는다(ast 기호 평가)."""
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


def convert(code, source):
    cat = p2t.load_catalog()
    try:
        r = p2t.convert_code(code, cat, source=source)
    except p2t.PlanIssue as e:
        raise PlanBuildError('계획 변환 실패(%s): %s' % (source, e))
    errs = []
    for key in ('canonical_validation', 'semantic_validation'):
        errs += (r.get(key) or {}).get('errors') or []
    if errs:
        raise PlanBuildError('canonical 검증 실패(%s): %s' % (source, errs))
    can = r['canonical']
    return {'canonical': can, 'warnings': r.get('warnings') or [], 'text': r.get('text', ''),
            'dump': p2t.dump_tree(can), 'catalog': cat}


def branches(doc):
    """canonical 루트 → 병렬 가지 목록(각 가지 = 원자 목록, 순서 보존).
    가지가 하나뿐이면 변환기가 루트를 sequential 로 접으므로 가지 1개로 되돌린다(실행 변환 규칙 R7)."""
    if doc['type'] == 'parallel':
        return [list(p2t.iter_atomics(sub)) for sub in doc.get('subtasks') or []]
    return [list(p2t.iter_atomics(doc))]


def _arg(node, key):
    return str((node.get('args') or {}).get(key, ''))


# ───────────────────────── 원자 node: 카탈로그가 실행 속성의 원천 (규칙 R1·R2) ─────────────────────────
def atomic_from(node, name, parent, catalog):
    skill = node['skill']
    info = (catalog.get('actions') or {}).get(skill)
    if info is None:
        raise PlanBuildError('카탈로그에 없는 스킬 %s' % skill)
    args = node.get('args') or {}
    try:
        goal = str(info['exec_goal']).format(**args)
    except (KeyError, IndexError) as e:
        raise PlanBuildError('%s: exec_goal 템플릿 인수 %s 가 없음' % (skill, e))
    cls = SequentialAtomicTask if info.get('node', 'sequential') == 'sequential' else ParallelAtomicTask
    t = cls(name=name, parent=parent, goal=goal)
    t.addRequirement(str(info['requirement']))
    for tag in node.get('required_skills') or []:          # R2: 추가 능력 태그(radar 등) → 요구 능력
        if tag != skill and tag not in t.requirement:
            t.addRequirement(tag)
    if info.get('optional'):
        t.optional = True
    if info.get('preassigned'):
        t.assign_status = True
        t.agent = types.SimpleNamespace(name=AGENT_NS + str(args.get('robot', '')))
    t._plan_id = node['id']
    return t


# ───────────────────────── 계약 검사: canonical ↔ 실행 트리 (1:1, 순서 제약 동일) ─────────────────────────
def _exec_atomics(t):
    if not hasattr(t, 'subtasks'):
        return [t]
    out = []
    for c in t.subtasks:
        out.extend(_exec_atomics(c))
    return out


def order_pairs_canonical(doc):
    """canonical 의 순서 제약: sequential 복합의 앞 자식 원자 → 뒤 자식 원자 쌍(id)."""
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
    """실행 트리의 순서 제약: SequentialCompositeTask 자식 순서 + 명시적 predecessors (canonical id 로 표현)."""
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
    """어댑터가 canonical 의 의미를 바꾸지 않았는지: 원자 1:1 + 순서 제약 집합 동일. 어긋나면 PlanBuildError."""
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


# ───────────────────────── goal 별 어댑터 (이름·묶음 규칙만; 0.8.1 고정 빌더와 같은 트리) ─────────────────────────
def build_relay(payload):
    """'name=x,y,z;…' → Sequential[relay1.<name>(nav:x,y,z) → relay2 …] (선행 사슬 포함, 규칙 R5).
    지원 범위: 로봇 이름 유일(중복이면 PlanBuildError → 고정 빌더). 형식 오류 조각은 0.8.1 과 같이 무시."""
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
    names = [n for n, _ in legs]
    if len(set(names)) != len(names):
        raise PlanBuildError('릴레이 계획은 로봇 이름이 유일해야 함(중복: %s) — 지원 범위 밖'
                             % sorted({n for n in names if names.count(n) > 1}))
    path, code = load_plan('Relay')
    bindings = {'ROBOTS': names, 'TARGETS': dict(legs)}
    conv = convert(bind(code, bindings), os.path.basename(path)) if legs else None
    root = SequentialCompositeTask(name="relay", parent=None, goal="Relay")
    atoms = list(p2t.iter_atomics(conv['canonical'])) if conv else []
    _expect('릴레이 계획의 단계', [(a['skill'], _arg(a, 'robot'), _arg(a, 'target')) for a in atoms],
            [('GoTo', n, xyz) for n, xyz in legs])
    prev = None
    for n, at in enumerate(atoms, 1):
        t = atomic_from(at, "relay%d.%s" % (n, _arg(at, 'robot')), root, conv['catalog'])
        if prev:
            t.addPredecessor(prev)
        root.add(t)
        prev = t
    if conv:
        check_contract(conv['canonical'], root)
    return {'root': root, 'meta': None, 'dicts': {}, 'plan': dict(conv or {}, file=path, bindings=bindings)}


def build_multigoal(payload, parse_fn):
    """'goals=G:x,y:count|…' → Parallel[ G[count] = Parallel[ G.itemk(trip:x,y@G) … ] … ]. parse_fn = jnp_group.parse_multigoal_payload.
    goal 가지는 payload 순서대로 모두 만든다(물품 0개면 빈 가지 — 0.8.1 과 같음, 규칙 R6)."""
    goals, _robots = parse_fn(payload)
    GOALS = list(goals)
    ITEMS = {g: ['%s.item%d' % (g, k) for k in range(1, goals[g][2] + 1)] for g in GOALS}
    GOAL_POS = {g: '%.2f,%.2f' % (goals[g][0], goals[g][1]) for g in GOALS}
    path, code = load_plan('Mult-Goal')
    bindings = {'GOALS': GOALS, 'ITEMS': ITEMS, 'GOAL_POS': GOAL_POS}
    conv = convert(bind(code, bindings), os.path.basename(path)) if any(ITEMS.values()) else None
    root = ParallelCompositeTask(name="multigoal")
    subs = {}
    for g in GOALS:
        subs[g] = ParallelCompositeTask(name="%s[%d]" % (g, goals[g][2]), parent=root)
        root.add(subs[g])
    atoms = [a for br in branches(conv['canonical']) for a in br] if conv else []
    _expect('다목적 이동 계획의 물품', [(a['skill'], _arg(a, 'item'), _arg(a, 'goal'), _arg(a, 'target')) for a in atoms],
            [('Trip', it, g, GOAL_POS[g]) for g in GOALS for it in ITEMS[g]])
    for at in atoms:
        g, item = _arg(at, 'goal'), _arg(at, 'item')
        t = atomic_from(at, item, subs[g], conv['catalog'])
        subs[g].add(t)
    if conv:
        check_contract(conv['canonical'], root)
    return {'root': root, 'meta': None, 'dicts': {}, 'plan': dict(conv or {}, file=path, bindings=bindings)}


def build_avoidance(payload, parse_fn, speed_fn):
    """'bt=cx,cy,r;routes=name:sx,sy>tx,ty|…' → Parallel[ cross.<name> = Sequential[ wait_pass.<prev>(virtual) → move.<name>(nav:tx,ty) ] ]
    (ETA 순서는 실행 환경 정보라 여기서 계산해 FIRST/REST/PREV/TARGETS 로 바인딩; root._bt_meta 포함).
    parse_fn = jnp_group.parse_avoidance_payload, speed_fn = jnp_group._robot_speed."""
    bt, routes = parse_fn(payload)
    root = ParallelCompositeTask(name="avoidance")
    path, code = load_plan('Avoidance')
    if not bt:
        return {'root': root, 'meta': None, 'dicts': {}, 'plan': {'file': path, 'bindings': {}, 'warnings': ['bt 없음 — 빈 트리']}}
    cx, cy, r = bt

    def _eta(nm):
        sx, sy = routes[nm][0], routes[nm][1]
        return max(0.0, math.hypot(sx - cx, sy - cy) - r) / speed_fn(nm)
    order = sorted(routes, key=_eta)
    TARGETS = {nm: '%.2f,%.2f' % (routes[nm][2], routes[nm][3]) for nm in order}
    PREV = {nm: order[k - 1] for k, nm in enumerate(order) if k > 0}
    bindings = {'FIRST': order[:1], 'REST': order[1:], 'TARGETS': TARGETS, 'PREV': PREV}
    conv = convert(bind(code, bindings), os.path.basename(path)) if order else None
    moves, waits = {}, {}
    brs = branches(conv['canonical']) if conv else []
    _expect('충돌회피 계획의 가지(로봇, ETA 순)', [_arg(br[0], 'robot') if br else None for br in brs], order)
    for k, br in enumerate(brs):
        name = order[k]
        _expect('충돌회피 가지 %s 의 단계' % name, [(a['skill'], _arg(a, 'robot'), _arg(a, 'prev') if a['skill'] == 'WaitPass' else _arg(a, 'target')) for a in br],
                ([('WaitPass', name, PREV[name])] if k > 0 else []) + [('GoTo', name, TARGETS[name])])
        branch = SequentialCompositeTask(name="cross.%s" % name, parent=root, goal='Avoidance')
        for at in br:
            if at['skill'] == 'WaitPass':
                w = atomic_from(at, "wait_pass.%s" % _arg(at, 'prev'), branch, conv['catalog'])
                branch.add(w)
                waits[name] = w
            else:
                mv = atomic_from(at, "move.%s" % name, branch, conv['catalog'])
                branch.add(mv)
                moves[name] = mv
        root.add(branch)
    if conv:
        check_contract(conv['canonical'], root)
    root._bt_meta = {'order': order, 'moves': moves, 'waits': waits, 'center': (cx, cy), 'r': r,
                     'starts': {n: (routes[n][0], routes[n][1]) for n in routes},
                     'targets': {n: (routes[n][2], routes[n][3]) for n in routes}}
    return {'root': root, 'meta': root._bt_meta, 'dicts': {}, 'plan': dict(conv or {}, file=path, bindings=bindings)}


def _group_by_robot(brs, names, what):
    """병렬 가지들을 robot 인수로 묶는다(규칙 R3). 가지 하나에 로봇이 둘 섞이거나 names 밖 로봇이면 거부."""
    per = {n: [] for n in names}
    for br in brs:
        for at in br:
            rb = _arg(at, 'robot')
            if rb not in per:
                raise PlanBuildError('%s: 참여 로봇이 아닌 %r 의 단계 %s' % (what, rb, at['skill']))
            per[rb].append(at)
    return per


def build_map_explore(names, merge_host):
    """로봇 이름(정렬됨)·병합 호스트 → Parallel[ make_maps.<n> = Parallel[ navigate.<n>=Sequential[explore.<n>], merge_maps|send_map.<n>(virtual, 상시) ] ].
    규칙 R3(로봇별 묶음)·R4(navigate 래퍼). dicts: etasks, mtasks, branch, seqbr(가지별 [S] navigate — 병목 양보/통과 삽입 지점)."""
    names = list(names)
    if names and merge_host not in names:
        raise PlanBuildError('지도제작: 병합 호스트 %r 가 참여 로봇 %s 에 없음' % (merge_host, names))
    bindings = {'HOST': [merge_host] if names else [], 'EXPLORERS': [n for n in names if n != merge_host]}
    path, code = load_plan('MapExplore')
    conv = convert(bind(code, bindings), os.path.basename(path)) if names else None
    root = ParallelCompositeTask(name="map_explore")
    etasks, mtasks, branch, seqbr = {}, {}, {}, {}
    per = _group_by_robot(branches(conv['canonical']) if conv else [], names, '지도제작 계획')
    for n in names:                      # 0.8.1 고정 빌더와 같은 순서(정렬된 이름)
        _expect('지도제작 계획 — 로봇 %s 의 단계' % n, sorted(a['skill'] for a in per[n]),
                sorted(['Explore', 'MergeMaps' if n == merge_host else 'SendMap']))
        _br = ParallelCompositeTask(name="make_maps.%s" % n, parent=root)
        _sq = SequentialCompositeTask(name="navigate.%s" % n, parent=_br, goal='')
        for at in per[n]:
            if at['skill'] == 'Explore':
                _t = atomic_from(at, "explore.%s" % n, _sq, conv['catalog'])
                _sq.add(_t)
                etasks[n] = _t
            else:
                _m = atomic_from(at, ("merge_maps.%s" if at['skill'] == 'MergeMaps' else "send_map.%s") % n, _br, conv['catalog'])
                mtasks[n] = _m
        _br.add(_sq)
        _br.add(mtasks[n])
        root.add(_br)
        seqbr[n] = _sq
        branch[n] = _br
    if conv:
        check_contract(conv['canonical'], root)
    return {'root': root, 'meta': None, 'dicts': {'etasks': etasks, 'mtasks': mtasks, 'branch': branch, 'seqbr': seqbr},
            'plan': dict(conv or {}, file=path, bindings=bindings)}


def build_object_search(names):
    """로봇 이름(정렬됨) → Parallel[ search.<n> = Parallel[ patrol.<n>(search, optional), detect.<n>(service:yolov8, virtual 상시) ] ].
    규칙 R3(로봇별 묶음). dicts: etasks, dtasks, spars."""
    names = list(names)
    bindings = {'ROBOTS': names}
    path, code = load_plan('ObjectSearch')
    conv = convert(bind(code, bindings), os.path.basename(path)) if names else None
    root = ParallelCompositeTask(name="object_search")
    etasks, dtasks, spars = {}, {}, {}
    per = _group_by_robot(branches(conv['canonical']) if conv else [], names, '물건찾기 계획')
    for n in names:
        _expect('물건찾기 계획 — 로봇 %s 의 단계' % n, sorted(a['skill'] for a in per[n]), ['Detect', 'Patrol'])
        _par = ParallelCompositeTask(name="search.%s" % n, parent=root)
        pat = [a for a in per[n] if a['skill'] == 'Patrol'][0]
        det = [a for a in per[n] if a['skill'] == 'Detect'][0]
        _t = atomic_from(pat, "patrol.%s" % n, _par, conv['catalog'])
        _par.add(_t)
        _d = atomic_from(det, "detect.%s" % n, _par, conv['catalog'])
        _par.add(_d)
        root.add(_par)
        etasks[n], dtasks[n], spars[n] = _t, _d, _par
    if conv:
        check_contract(conv['canonical'], root)
    return {'root': root, 'meta': None, 'dicts': {'etasks': etasks, 'dtasks': dtasks, 'spars': spars},
            'plan': dict(conv or {}, file=path, bindings=bindings)}


# ───────────────────────── 공통 진입점·표시·기록 ─────────────────────────
def build(goal, payload, **kw):
    """goal 문자열로 디스패치. kw: parse_multigoal / parse_avoidance / speed_fn / names / merge_host (그룹이 넘김).
    반환 {'root','meta','dicts','plan'} — 반환 전에 계약·완전성 검사를 마친 트리만 돌려준다."""
    key = goal_key(goal)
    if key == 'Relay':
        return build_relay(payload)
    if key == 'Mult-Goal':
        return build_multigoal(payload, kw['parse_multigoal'])
    if key == 'Avoidance':
        return build_avoidance(payload, kw['parse_avoidance'], kw['speed_fn'])
    if key == 'MapExplore':
        return build_map_explore(kw['names'], kw.get('merge_host'))
    return build_object_search(kw['names'])


def tree_text(root, indent=0):
    """Task 객체 트리의 사람용 덤프(검증·로그)."""
    lines = []
    kind = type(root).__name__
    extra = ''
    if not hasattr(root, 'subtasks'):
        extra = '  req=%s goal=%s' % (','.join(root.requirement), root.goal)
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


def _set_param(key, value):
    """rosparam 기록. ROS 밖/마스터 없음이면 False (실행 경로의 성공 여부와 분리해 보고한다)."""
    try:
        import rospy
        rospy.set_param(key, value)
        return True
    except Exception as e:
        print('[PLAN] rosparam %s 기록 실패: %s' % (key, e), flush=True)
        return False


def publish(res, goal, node_name='group'):
    """계획·canonical·바인딩·트리를 콘솔에 덤프하고 rosparam /jnp/plan/<group> 에 둔다(source=plan). 기록 성공 여부 반환."""
    plan = res.get('plan') or {}
    print('[PLAN] source=plan %s ← %s  bindings=%s' % (goal, os.path.basename(plan.get('file', '?')), plan.get('bindings')), flush=True)
    if plan.get('dump'):
        print('[PLAN] canonical TaskTree:\n' + plan['dump'], flush=True)
    for w in plan.get('warnings') or []:
        print('[PLAN] warning: %s' % w, flush=True)
    print('[PLAN] jnp TaskTree:\n' + tree_text(res['root']), flush=True)
    return _set_param(_param_key(node_name), {
        'source': 'plan', 'goal': goal, 'plan_file': plan.get('file', ''),
        'bindings': json.dumps(plan.get('bindings') or {}, ensure_ascii=False),
        'task_description': plan.get('text', ''),
        'canonical': json.dumps(plan.get('canonical') or {}, ensure_ascii=False),
        'warnings': list(plan.get('warnings') or []), 'tree': tree_text(res['root'])})


def publish_fallback(goal, reason, node_name='group', root=None):
    """고정 빌더로 간 사실을 같은 rosparam 에 남긴다(source=legacy) — 이전 계획 기록이 현재 것으로 오인되지 않게."""
    print('[PLAN] source=legacy %s — %s' % (goal, reason), flush=True)
    return _set_param(_param_key(node_name), {
        'source': 'legacy', 'goal': goal, 'reason': str(reason), 'plan_file': '', 'bindings': '{}',
        'task_description': '', 'canonical': '{}', 'warnings': [], 'tree': tree_text(root) if root is not None else ''})


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    g, pl = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else '')
    opts = dict(a.split('=', 1) for a in sys.argv[3:] if '=' in a)
    import jnp_group as G
    names = sorted([s.strip() for s in pl.replace('robots=', '').split(';')[0].split('|') if s.strip()]) \
        if g in ('MapExplore', 'ObjectSearch') else None
    # 주의: 이 CLI 는 변환 예제다. 지도제작의 병합 호스트는 실제 그룹이 멤버의 컴퓨팅 등급(_compute_rank)으로 고른다 —
    # 여기서는 host=<robot> 로 지정하고, 없으면 정렬 첫 이름을 쓴다.
    host = opts.get('host') or (names[0] if names else None)
    try:
        res = build(g, pl, parse_multigoal=G.parse_multigoal_payload, parse_avoidance=G.parse_avoidance_payload,
                    speed_fn=G._robot_speed, names=names, merge_host=host)
    except PlanBuildError as e:
        print('[PLAN] PlanBuildError: %s' % e)
        sys.exit(1)
    publish(res, g)
