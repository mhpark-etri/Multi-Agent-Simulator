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


PLAN_SOURCES = ('example', 'llm-tdm', 'unknown')   # 작성자 선언(생성 사실을 검증하지 않음): example = 사람이 쓴 템플릿, llm-tdm = 모듈 출력


def plan_source(code):
    """계획 머리의 '# Plan Source: …' → 'example' | 'llm-tdm' | 'unknown'. 없거나 열거 밖의 값이면 'unknown'(경고)."""
    m = re.search(r"^#\s*Plan Source:\s*([A-Za-z0-9_\-]+)", code, flags=re.M)
    if not m:
        return 'unknown'
    v = m.group(1).lower()
    if v not in PLAN_SOURCES:
        print("[PLAN] warning: Plan Source %r 는 %s 밖의 값 — unknown 으로 기록" % (m.group(1), PLAN_SOURCES), flush=True)
        return 'unknown'
    return v


def _plan_meta(conv, path, code, bindings):
    """빌더 반환의 'plan' 항목. 변환을 건너뛴 빈 계획(물품 0개 등)에도 파일 출처(plan_source)는 남긴다."""
    d = dict(conv or {})
    d.update(file=path, bindings=bindings, plan_source=plan_source(code))
    return d


# 실행 회차 식별자 — 그룹 프로세스 하나 = 회차 하나. publish()/publish_fallback() 가 만들고 /jnp/plan 기록과
# 그룹의 /jnp/status(run_id) 양쪽에 실린다. JnP Monitor 는 같은 run_id 끼리만 계획과 상태를 결합한다.
_RUN = {'id': None}


def new_run_id(node_name='group'):
    _RUN['id'] = '%s@%d-%s' % ((node_name or 'group').strip('/'), int(time.time() * 1000), uuid.uuid4().hex[:6])
    return _RUN['id']


def current_run_id():
    return _RUN['id']


def convert(code, source):
    cat = p2t.load_catalog()
    try:
        # strict_source: 상수 변경문·상수 메서드 호출·카탈로그 밖 위치 인자·해석 불가 인자는 변환 전에 거부(PlanIssue)
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
    for tag in node.get('required_skills') or []:          # R2: 추가 능력 태그(radar 등) → 요구 능력
        if tag == skill or tag in t.requirement:
            continue
        if req == 'virtual' or info.get('preassigned'):
            raise PlanBuildError('%s: 가상/상시 서비스 단계에는 능력 태그 %r 를 붙일 수 없음(배정 대상이 아님)' % (skill, tag))
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
    """실행 트리의 순서 제약: SequentialCompositeTask 자식 순서(앞/뒤 하위 트리 원자의 모든 쌍) + 명시적 predecessors(직접 간선만).
    전이 폐쇄는 계산하지 않는다 — 어댑터가 만드는 트리(순차 복합 + 그와 중복인 선행 사슬) 범위에서만 동치 검사로 쓴다."""
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
    """canonical 과 실행 트리의 원자 ID 대응(1:1)과 순서 제약 집합을 검사한다. 어긋나면 PlanBuildError.
    원자의 실행 속성(goal·requirement·종류·optional·preassigned)은 atomic_from 이 카탈로그에서 채우고 test 의 동일성 검사가 확인하며,
    트리 참조 불변식과 소스 문법 적합성은 각각 test 의 불변식 검사·변환기(strict_source)가 맡는다 — 이 함수의 범위가 아니다."""
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
    return {'root': root, 'meta': None, 'dicts': {}, 'plan': _plan_meta(conv, path, code, bindings)}


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
    return {'root': root, 'meta': None, 'dicts': {}, 'plan': _plan_meta(conv, path, code, bindings)}


def build_avoidance(payload, parse_fn, speed_fn):
    """'bt=cx,cy,r;routes=name:sx,sy>tx,ty|…' → Parallel[ cross.<name> = Sequential[ wait_pass.<prev>(virtual) → move.<name>(nav:tx,ty) ] ]
    (ETA 순서는 실행 환경 정보라 여기서 계산해 FIRST/REST/PREV/TARGETS 로 바인딩; root._bt_meta 포함).
    parse_fn = jnp_group.parse_avoidance_payload, speed_fn = jnp_group._robot_speed."""
    bt, routes = parse_fn(payload)
    root = ParallelCompositeTask(name="avoidance")
    path, code = load_plan('Avoidance')
    if not bt:
        return {'root': root, 'meta': None, 'dicts': {}, 'plan': _plan_meta({'warnings': ['bt 없음 — 빈 트리']}, path, code, {})}
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
    return {'root': root, 'meta': root._bt_meta, 'dicts': {}, 'plan': _plan_meta(conv, path, code, bindings)}


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
            'plan': _plan_meta(conv, path, code, bindings)}


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
            'plan': _plan_meta(conv, path, code, bindings)}


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


PLAN_TOPIC = '/jnp/plan'      # latched std_msgs/String(JSON) — JnP Monitor 의 '미션 → 분할 → 스킬 매칭' 표시용
_PUB = {}


def subtask_rows(root, canonical=None, catalog=None):
    """실행 트리의 원자 task 하나 = 한 행. canonical 이 있으면 _plan_id 로 이어 스킬·인수·요구 스킬을 붙인다
    (어댑터가 붙인 _plan_id 가 canonical ↔ 실행 원자의 1:1 대응 — 이 함수는 그 대응을 검증하지 않는다; check_contract 가 한다).
    고정 빌더 트리(legacy)는 id/skill=None 으로 실행 속성만. **초기 트리**(실행 전) 기준의 기록이다:
      preassigned = 초기 트리에서 이미 agent 가 붙어 있는 상시 가상 서비스(Detect·SendMap·MergeMaps) 표시 — 실행 뒤 배정된 일반 task 에
                    같은 함수를 다시 쓰면 그것도 True 가 되므로 초기 호출에만 쓴다.
      after       = 명시적 predecessors 목록(Relay 의 선행 사슬)만. 순차 복합의 자식 순서는 여기 없고 canonical/실행 트리 구조가 담는다."""
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
            'required_skills': list(c.get('required_skills') or []),
            'signature': info.get('signature', ''),
            'node': t.name, 'kind': 'seq' if isinstance(t, SequentialAtomicTask) else 'par',
            'exec_goal': t.goal, 'requirement': list(t.requirement),
            'optional': bool(getattr(t, 'optional', False)),
            'preassigned': bool(getattr(t, 'assign_status', False) and ag is not None),
            'preassigned_agent': getattr(ag, 'name', '') if ag is not None else '',
            'after': [p.name for p in getattr(t, 'predecessors', []) or []],
        })
    return rows


def plan_record(res, goal, node_name='group'):
    """계획 경로의 기록(JSON 직렬화 가능): 미션(자연어 Task Description)·바인딩·canonical·실행 트리·행별 스킬 매칭."""
    plan = res.get('plan') or {}
    return {
        'schema': 'jnp-plan-record/1', 'run_id': current_run_id() or new_run_id(node_name),
        'source': 'plan', 'goal': goal, 'group': node_name, 'plan_file': plan.get('file', ''),
        'plan_name': os.path.basename(plan.get('file', '') or ''),
        'plan_source': plan.get('plan_source', 'unknown'),     # example = 사람이 쓴 템플릿(LLM-TDM 모듈 미사용)
        'task_description': plan.get('text', ''),
        'bindings': plan.get('bindings') or {},
        'canonical': plan.get('canonical') or {},
        'canonical_dump': plan.get('dump', ''),
        'warnings': list(plan.get('warnings') or []),
        'tree': tree_text(res['root']),
        'subtasks': subtask_rows(res['root'], plan.get('canonical'), plan.get('catalog')),
    }


def fallback_record(goal, reason, node_name='group', root=None):
    return {
        'schema': 'jnp-plan-record/1', 'run_id': current_run_id() or new_run_id(node_name),
        'source': 'legacy', 'goal': goal, 'group': node_name, 'reason': str(reason), 'plan_file': '', 'plan_name': '',
        'plan_source': '',          # legacy 는 계획 파일이 없으므로 빈 문자열(EXAMPLE/LLM-TDM 배지 대상 아님)
        'task_description': '', 'bindings': {}, 'canonical': {}, 'canonical_dump': '', 'warnings': [],
        'tree': tree_text(root) if root is not None else '',
        'subtasks': subtask_rows(root) if root is not None else [],
    }


def _topic_publish(record):
    """latched 토픽 /jnp/plan 에 JSON 한 줄. ROS 밖/마스터 없음이면 False."""
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
    """rosparam 기록. ROS 밖/마스터 없음이면 False (실행 경로의 성공 여부와 분리해 보고한다)."""
    try:
        import rospy
        rospy.set_param(key, value)
        return True
    except Exception as e:
        print('[PLAN] rosparam %s 기록 실패: %s' % (key, e), flush=True)
        return False


def publish(res, goal, node_name='group'):
    """계획·canonical·바인딩·트리를 콘솔에 덤프하고 rosparam /jnp/plan/<group> 과 latched 토픽 /jnp/plan 에 둔다(source=plan).
    새 회차 id(run_id)를 만든다 — 그룹의 /jnp/status 도 같은 id 를 싣는다. 반환 = rosparam 기록 ∧ 토픽 publish 호출 성공
    (구독자 수신·화면 반영을 뜻하지 않음)."""
    new_run_id(node_name)
    plan = res.get('plan') or {}
    print('[PLAN] source=plan %s ← %s (plan source: %s)  bindings=%s' % (goal, os.path.basename(plan.get('file', '?')),
                                                                        plan.get('plan_source', 'unknown'), plan.get('bindings')), flush=True)
    if plan.get('text'):
        print('[PLAN] mission (%s): %s' % (plan.get('plan_source', 'unknown'), plan['text']), flush=True)
    if plan.get('dump'):
        print('[PLAN] canonical TaskTree:\n' + plan['dump'], flush=True)
    for w in plan.get('warnings') or []:
        print('[PLAN] warning: %s' % w, flush=True)
    print('[PLAN] jnp TaskTree:\n' + tree_text(res['root']), flush=True)
    rec = plan_record(res, goal, node_name)
    ok_param = _set_param(_param_key(node_name), {
        'source': 'plan', 'goal': goal, 'plan_file': plan.get('file', ''),
        'bindings': json.dumps(plan.get('bindings') or {}, ensure_ascii=False),
        'task_description': plan.get('text', ''), 'plan_source': rec['plan_source'], 'run_id': rec['run_id'],
        'canonical': json.dumps(plan.get('canonical') or {}, ensure_ascii=False),
        'warnings': list(plan.get('warnings') or []), 'tree': tree_text(res['root']),
        'subtasks': json.dumps(rec['subtasks'], ensure_ascii=False)})
    ok_topic = _topic_publish(rec)
    return bool(ok_param and ok_topic)


def publish_fallback(goal, reason, node_name='group', root=None):
    """고정 빌더로 간 사실을 같은 rosparam·토픽에 남긴다(source=legacy) — 이전 계획 기록이 현재 것으로 오인되지 않게. 새 run_id."""
    new_run_id(node_name)
    print('[PLAN] source=legacy %s — %s' % (goal, reason), flush=True)
    rec = fallback_record(goal, reason, node_name, root)
    ok_param = _set_param(_param_key(node_name), {
        'source': 'legacy', 'goal': goal, 'reason': str(reason), 'plan_file': '', 'bindings': '{}', 'run_id': rec['run_id'],
        'task_description': '', 'canonical': '{}', 'warnings': [], 'tree': tree_text(root) if root is not None else '',
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
