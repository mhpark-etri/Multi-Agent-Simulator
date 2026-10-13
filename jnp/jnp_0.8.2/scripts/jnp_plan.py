#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.8.2 2026-10-13]
"""jnp_plan.py — 기본 협업 태스크의 '작업 분할' 경로: plans/<goal>.py(LLM-TDM 형식 계획) → plan_to_tasktree(canonical TaskTree)
→ jnp_task 객체 트리. 그룹(jnp_group.py)이 goal 별 고정 빌더 대신 이 모듈로 트리를 만든다(~plan_mode, 기본 true).

계획 파일의 모듈 상수(LEGS·ITEMS·FIRST/REST·HOST/EXPLORERS·ROBOTS)는 GUI payload 에서 **실행 시 바인딩**한다(계획 = 분할 구조,
payload = 구체 값). 만들어지는 Task 객체 트리는 0.8.1 고정 빌더(build_relay_tree 등)와 노드 이름·goal 문자열·요구 능력·선행
관계·순서가 같아야 한다 — 그룹의 실행 시 후처리(병목 관찰자, 양보/통과 삽입, 지도 병합 호스트 등)가 그 이름으로 노드를 찾기
때문이다. 동일성은 test/test_plan_trees.py 가 검사한다.

사용(그룹):   res = jnp_plan.build('Relay', payload)      # res['root'], res['meta'], res['dicts'], res['plan']
ROS 없이:     python3 jnp_plan.py Relay "tb3_0=1.00,0.00,0.00;tb3_1=2.00,0.00,0.00"
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


class PlanBuildError(RuntimeError):
    pass


# ───────────────────────── 계획 파일 읽기·바인딩·변환 ─────────────────────────
def plans_dir():
    cands = [os.path.join(os.path.dirname(HERE), 'plans')]
    try:
        import rospkg
        cands.append(os.path.join(rospkg.RosPack().get_path('jnp'), 'plans'))
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


def bind(code, consts):
    """모듈 상수 자리(NAME = [...])를 실행 시 값으로 바꾼다 — 코드를 실행하지 않고 문자열만 치환."""
    for name, values in consts.items():
        lit = json.dumps([str(v) for v in values], ensure_ascii=False)
        code, n = re.subn(r'^%s\s*=.*$' % re.escape(name), '%s = %s' % (name, lit), code, count=1, flags=re.M)
        if n != 1:
            raise PlanBuildError('계획 파일에 모듈 상수 %s 자리가 없음' % name)
    return code


def convert(code, source):
    r = p2t.convert_code(code, p2t.load_catalog(), source=source)
    can = r['canonical']
    errs = (r.get('canonical_validation') or {}).get('errors') or []
    if errs:
        raise PlanBuildError('canonical validation: %s' % errs)
    return {'canonical': can, 'warnings': r.get('warnings') or [], 'text': r.get('text', ''), 'dump': p2t.dump_tree(can)}


def branches(doc):
    """canonical 루트 → 병렬 가지 목록(각 가지 = atomic 목록, 순서 보존). 가지가 하나면 변환기가 루트를 sequential 로 접으므로 되돌린다."""
    if doc['type'] == 'parallel':
        out = []
        for sub in doc.get('subtasks') or []:
            out.append(list(p2t.iter_atomics(sub)))
        return out
    return [list(p2t.iter_atomics(doc))]


def _arg(node, key):
    return str((node.get('args') or {}).get(key, ''))


# ───────────────────────── goal 별 빌더(0.8.1 고정 빌더와 같은 트리) ─────────────────────────
def build_relay(payload):
    """'name=x,y,z;…' → Sequential[relay1.<name>(nav:x,y,z) → relay2 …] (선행 사슬 포함)."""
    legs = []
    for seg in (payload or '').split(';'):
        seg = seg.strip()
        if not seg:
            continue
        name, eq, xyz = seg.partition('=')
        if not eq or not xyz.strip() or not name.strip():
            print("Group: 형식 오류 조각 무시: '%s' (기대: name=x,y,z)" % seg)
            continue
        legs.append('%s=%s' % (name.strip(), xyz.strip()))
    path, code = load_plan('Relay')
    conv = convert(bind(code, {'LEGS': legs}), os.path.basename(path)) if legs else None
    root = SequentialCompositeTask(name="relay", parent=None, goal="Relay")
    prev = None
    for n, at in enumerate(list(p2t.iter_atomics(conv['canonical'])) if conv else [], 1):
        if at['skill'] != 'GoTo':
            raise PlanBuildError('relay 계획에 GoTo 외 스킬: %s' % at['skill'])
        rname, _, xyz = _arg(at, 'target').partition('=')
        t = SequentialAtomicTask(name="relay%d.%s" % (n, rname), parent=root, goal="nav:%s" % xyz)
        t.addRequirement("lidar")
        if prev:
            t.addPredecessor(prev)
        root.add(t)
        prev = t
    return {'root': root, 'meta': None, 'dicts': {}, 'plan': dict(conv or {}, file=path, bindings={'LEGS': legs})}


def build_multigoal(payload, parse_fn):
    """'goals=G:x,y:count|…' → Parallel[ G[count] = Parallel[ G.itemk(trip:x,y@G) … ] … ]. parse_fn = jnp_group.parse_multigoal_payload."""
    goals, _robots = parse_fn(payload)
    items = []
    for gname, (gx, gy, count) in goals.items():
        for k in range(1, count + 1):
            items.append('%s:%.2f,%.2f:%d' % (gname, gx, gy, k))
    path, code = load_plan('Mult-Goal')
    conv = convert(bind(code, {'ITEMS': items}), os.path.basename(path)) if items else None
    root = ParallelCompositeTask(name="multigoal")
    subs = {}
    atoms = [a for br in branches(conv['canonical']) for a in br] if conv else []
    for at in atoms:
        if at['skill'] != 'Trip':
            raise PlanBuildError('multigoal 계획에 Trip 외 스킬: %s' % at['skill'])
        gname, xy, k = _arg(at, 'target').split(':')
        if gname not in subs:
            subs[gname] = ParallelCompositeTask(name="%s[%d]" % (gname, goals[gname][2]), parent=root)
            root.add(subs[gname])
        t = ParallelAtomicTask(name="%s.item%s" % (gname, k), parent=subs[gname], goal="trip:%s@%s" % (xy, gname))
        t.addRequirement("lidar")
        subs[gname].add(t)
    return {'root': root, 'meta': None, 'dicts': {}, 'plan': dict(conv or {}, file=path, bindings={'ITEMS': items})}


def build_avoidance(payload, parse_fn, speed_fn):
    """'bt=cx,cy,r;routes=name:sx,sy>tx,ty|…' → Parallel[ cross.<name> = Sequential[ wait_pass.<prev>(virtual) → move.<name>(nav:tx,ty) ] ]
    (ETA 순서, root._bt_meta 포함). parse_fn = jnp_group.parse_avoidance_payload, speed_fn = jnp_group._robot_speed."""
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
    first = ['%s:%.2f,%.2f' % (order[0], routes[order[0]][2], routes[order[0]][3])] if order else []
    rest = ['%s:%.2f,%.2f:%s' % (nm, routes[nm][2], routes[nm][3], order[k - 1]) for k, nm in enumerate(order) if k > 0]
    conv = convert(bind(code, {'FIRST': first, 'REST': rest}), os.path.basename(path)) if order else None
    moves, waits = {}, {}
    for br in (branches(conv['canonical']) if conv else []):
        name = None
        branch = None
        for at in br:
            fields = _arg(at, 'target' if at['skill'] == 'GoTo' else 'prev').split(':')
            name = fields[0]
            if branch is None:
                branch = SequentialCompositeTask(name="cross.%s" % name, parent=root, goal='Avoidance')
            if at['skill'] == 'WaitPass':
                w = SequentialAtomicTask(name="wait_pass.%s" % fields[2], parent=branch, goal='virtual:wait')
                w.addRequirement("virtual")
                branch.add(w)
                waits[name] = w
            elif at['skill'] == 'GoTo':
                mv = SequentialAtomicTask(name="move.%s" % name, parent=branch, goal="nav:%s" % fields[1])
                mv.addRequirement("lidar")
                branch.add(mv)
                moves[name] = mv
            else:
                raise PlanBuildError('avoidance 계획에 예상 밖 스킬: %s' % at['skill'])
        root.add(branch)
    root._bt_meta = {'order': order, 'moves': moves, 'waits': waits, 'center': (cx, cy), 'r': r,
                     'starts': {n: (routes[n][0], routes[n][1]) for n in routes},
                     'targets': {n: (routes[n][2], routes[n][3]) for n in routes}}
    return {'root': root, 'meta': root._bt_meta, 'dicts': {}, 'plan': dict(conv or {}, file=path, bindings={'FIRST': first, 'REST': rest})}


def build_map_explore(names, merge_host):
    """로봇 이름(정렬됨)·병합 호스트 → Parallel[ make_maps.<n> = Parallel[ navigate.<n>=Sequential[explore.<n>], merge_maps|send_map.<n>(virtual, 상시) ] ].
    dicts: etasks, mtasks, branch, seqbr(가지별 [S] navigate — 병목 양보/통과 삽입 지점)."""
    names = list(names)
    host = [merge_host] if merge_host in names else []
    explorers = [n for n in names if n != merge_host]
    path, code = load_plan('MapExplore')
    conv = convert(bind(code, {'HOST': host, 'EXPLORERS': explorers}), os.path.basename(path)) if names else None
    root = ParallelCompositeTask(name="map_explore")
    etasks, mtasks, branch, seqbr = {}, {}, {}, {}
    per = {}
    for br in (branches(conv['canonical']) if conv else []):
        n = _arg(br[0], 'robot')
        per[n] = br
    for n in names:                      # 0.8.1 고정 빌더와 같은 순서(정렬된 이름)
        br = per.get(n)
        if not br:
            raise PlanBuildError('map_explore 계획에 로봇 %s 의 가지가 없음' % n)
        _br = ParallelCompositeTask(name="make_maps.%s" % n, parent=root)
        _sq = SequentialCompositeTask(name="navigate.%s" % n, parent=_br, goal='')
        for at in br:
            if at['skill'] == 'Explore':
                _t = ParallelAtomicTask(name="explore.%s" % n, parent=_sq, goal='explore')
                _t.addRequirement("lidar")
                _t.optional = True
                _sq.add(_t)
                etasks[n] = _t
            elif at['skill'] in ('MergeMaps', 'SendMap'):
                _is_host = (at['skill'] == 'MergeMaps')
                _m = ParallelAtomicTask(name=("merge_maps.%s" if _is_host else "send_map.%s") % n, parent=_br,
                                        goal=('service:map_merge' if _is_host else 'publish:map'))
                _m.addRequirement("virtual")
                _m.assign_status = True
                _m.agent = types.SimpleNamespace(name=AGENT_NS + n)
                mtasks[n] = _m
            else:
                raise PlanBuildError('map_explore 계획에 예상 밖 스킬: %s' % at['skill'])
        _br.add(_sq)
        if n in mtasks:
            _br.add(mtasks[n])
        root.add(_br)
        seqbr[n] = _sq
        branch[n] = _br
    return {'root': root, 'meta': None, 'dicts': {'etasks': etasks, 'mtasks': mtasks, 'branch': branch, 'seqbr': seqbr},
            'plan': dict(conv or {}, file=path, bindings={'HOST': host, 'EXPLORERS': explorers})}


def build_object_search(names):
    """로봇 이름(정렬됨) → Parallel[ search.<n> = Parallel[ patrol.<n>(search, optional), detect.<n>(service:yolov8, virtual 상시) ] ].
    dicts: etasks, dtasks, spars."""
    names = list(names)
    path, code = load_plan('ObjectSearch')
    conv = convert(bind(code, {'ROBOTS': names}), os.path.basename(path)) if names else None
    root = ParallelCompositeTask(name="object_search")
    etasks, dtasks, spars = {}, {}, {}
    per = {}
    for br in (branches(conv['canonical']) if conv else []):
        per[_arg(br[0], 'robot')] = br
    for n in names:
        br = per.get(n)
        if not br:
            raise PlanBuildError('object_search 계획에 로봇 %s 의 가지가 없음' % n)
        _par = ParallelCompositeTask(name="search.%s" % n, parent=root)
        for at in br:
            if at['skill'] == 'Patrol':
                _t = ParallelAtomicTask(name="patrol.%s" % n, parent=_par, goal='search')
                _t.addRequirement("lidar")
                _t.optional = True
                _par.add(_t)
                etasks[n] = _t
            elif at['skill'] == 'Detect':
                _d = ParallelAtomicTask(name="detect.%s" % n, parent=_par, goal='service:yolov8')
                _d.addRequirement("virtual")
                _d.assign_status = True
                _d.agent = types.SimpleNamespace(name=AGENT_NS + n)
                _par.add(_d)
                dtasks[n] = _d
            else:
                raise PlanBuildError('object_search 계획에 예상 밖 스킬: %s' % at['skill'])
        root.add(_par)
        spars[n] = _par
    return {'root': root, 'meta': None, 'dicts': {'etasks': etasks, 'dtasks': dtasks, 'spars': spars},
            'plan': dict(conv or {}, file=path, bindings={'ROBOTS': names})}


# ───────────────────────── 공통 진입점·표시 ─────────────────────────
def build(goal, payload, **kw):
    """goal 문자열로 디스패치. kw: parse_multigoal / parse_avoidance / speed_fn / names / merge_host (그룹이 넘김)."""
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


def publish(res, goal, node_name='group'):
    """계획·canonical·바인딩을 rosparam /jnp/plan/<node> 에 두고 콘솔에 덤프(JnP Monitor·사용자 확인용). ROS 밖에서는 콘솔만."""
    plan = res.get('plan') or {}
    print('[PLAN] %s ← %s  bindings=%s' % (goal, os.path.basename(plan.get('file', '?')), plan.get('bindings')), flush=True)
    if plan.get('dump'):
        print('[PLAN] canonical TaskTree:\n' + plan['dump'], flush=True)
    for w in plan.get('warnings') or []:
        print('[PLAN] warning: %s' % w, flush=True)
    print('[PLAN] jnp TaskTree:\n' + tree_text(res['root']), flush=True)
    try:
        import rospy
        rospy.set_param('/jnp/plan/%s' % node_name.strip('/').replace('/', '_'),
                        {'goal': goal, 'plan_file': plan.get('file', ''), 'bindings': json.dumps(plan.get('bindings') or {}, ensure_ascii=False),
                         'task_description': plan.get('text', ''), 'canonical': json.dumps(plan.get('canonical') or {}, ensure_ascii=False),
                         'warnings': list(plan.get('warnings') or []), 'tree': tree_text(res['root'])})
    except Exception:
        pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    g, pl = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else '')
    import jnp_group as G
    names = sorted([s.strip() for s in pl.replace('robots=', '').split('|') if s.strip()]) if g in ('MapExplore', 'ObjectSearch') else None
    res = build(g, pl, parse_multigoal=G.parse_multigoal_payload, parse_avoidance=G.parse_avoidance_payload, speed_fn=G._robot_speed,
                names=names, merge_host=(names[0] if names else None))
    publish(res, g)
