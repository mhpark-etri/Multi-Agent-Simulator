#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 신규 [JnP-0.8.1 2026-10-06] / [JnP-0.8.2 2026-10-13] jnp_bnt 에서 코어(jnp)로 이동 — 기본 협업 태스크도 같은 작업 분할 경로를 쓴다(jnp_plan.py).
"""plan_to_tasktree.py — LLM-TDM(SMART-LLM 의 분할 단계) 파이썬 계획 → canonical TaskTree JSON.

참조 번들(tasktree_from_stage1_20261006/pipeline/tasktree_pipeline.py)의 파이프라인
    AST → raw → normalize(id·required_skills·hold_group) → validate → canonical
을 Python 3.8(ROS Noetic) 에서 의존성 없이(ast, json) 돌도록 다시 썼다. 번들 파서가
못 다루던 구조는 '기호 평가(symbolic evaluation)'로 푼다 — 코드를 실행하지 않고
AST 위에서 값을 따라간다.
  - for 루프 전개(모듈 상수 리스트), 매개변수 바인딩(Thread args= / 직접 호출)
  - threads.append(t) / for t in threads: t.join() 장벽
  - 호출 결과 이름 추적: found = SearchObject(area) → SendLocation(found) 의 found 는
    그 수색의 대상(area)을 가리킨다
  - f-string 렌더링
  - if/else: 두 갈래가 같은 스킬이면 atomic 1개로 병합(실행기가 수색 결과로 보고
    내용을 정한다). 스킬이 다르면 둘 다 순차로 넣고 경고(조건부 실행).
원칙(번들 승계): LLM 없음, exec 없음, 스킬 이름 수정 없음(어휘 밖 호출은 경고만).
canonical JSON 스키마는 번들과 같다 — python3.9+ 가 있는 곳에서는 번들의
parse_canonical 로 교차검증할 수 있다.

사용:
  plan_to_tasktree.py PLAN.py [--catalog skills_catalog.json] [--out tree.json]
                              [--full] [--quiet]
파이썬:
  from plan_to_tasktree import convert_file
  r = convert_file("plan.py")      # r["canonical"], r["warnings"], r["text"], ...
"""
import argparse
import ast
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CATALOG = HERE.parent / "config" / "skills_catalog_basic.json"     # [JnP-0.8.2] 코어 기본 협업 태스크 스킬 어휘
# install 공간(lib/jnp/plan_to_tasktree.py)에서는 share/jnp/config 에 있다
CATALOG_CANDIDATES = [DEFAULT_CATALOG,
                      HERE.parent.parent / "share" / "jnp" / "config" / "skills_catalog_basic.json"]
# [ETRI-CD F9 2026-10-07] if/else 두 갈래가 같은 스킬일 때 병합을 허용하는 '보고' 스킬 — 실행기가 결과에
# 따라 보고 내용을 정한다. 그 밖의 스킬은 대상이 같을 때만 병합하고, 다르면 PlanIssue.
MERGE_REPORT_SKILLS = {"SendLocation"}
# [ETRI-CD R10 2026-10-07] required_skills 에 스킬 외에 붙을 수 있는 능력 태그(에이전트 ~jnp_capability 의 센서 항목).
# use_radar=True 는 'radar' 태그가 된다. strict 검증에서도 이 태그만 허용한다.
CAPABILITY_TAGS = {"radar", "lidar", "camera"}

RAW_NODE_KEYS = {"type", "subtasks", "skill", "args", "extra_skills"}   # extra_skills: [ETRI-CD R10] 능력 태그
CANON_ATOMIC_KEYS = {"id", "type", "skill", "args", "required_skills", "goal", "metadata"}
CANON_COMPOSITE_KEYS = {"id", "type", "subtasks", "goal"}
ROOT_META_KEYS = {"text", "floorplan", "robot_list", "source"}

HOLD_START = {"PickupObject"}
HOLD_RELEASE = {"PutObject", "ThrowObject", "DropHandObject"}
HOLD_KEEP = {"GoToObject", "SliceObject"}


class PlanIssue(ValueError):
    """트리로 옮길 수 없는 구조 — 조용히 뭉개지 않고 올린다(번들 ParseIssue 승계)."""


def load_catalog(path=None):
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    cands = list(CATALOG_CANDIDATES)
    try:                                              # [ETRI-CD F6 2026-10-07] rospkg 의 share 경로
        import rospkg
        cands.append(Path(rospkg.RosPack().get_path("jnp")) / "config" / "skills_catalog_basic.json")
    except Exception:
        pass
    for p in cands:
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    raise PlanIssue("skills_catalog.json 을 찾을 수 없음: %s" % ", ".join(str(p) for p in cands))


def task_description(code):
    m = re.search(r"^#\s*Task Description:\s*(.*)$", code, flags=re.M)
    return m.group(1).strip() if m else ""


# ─────────────────────────────────────────────────────────────────────
# 1. AST → raw (기호 평가)
# ─────────────────────────────────────────────────────────────────────
class _Ref(object):
    """앞선 스킬 호출의 결과를 담은 이름 (found = SearchObject(area))."""

    def __init__(self, skill, target):
        self.skill = skill
        self.target = target


class _Unknown(object):
    """값을 알 수 없는 이름 (어휘 밖 호출의 결과, 바인딩 안 된 매개변수)."""

    def __init__(self, what):
        self.what = what


class Converter(object):
    def __init__(self, catalog, max_depth=6, strict_conditionals=True):
        self.actions = catalog.get("actions") or {}
        self.max_depth = max_depth
        # [ETRI-CD R10 2026-10-07] True(운영·TF3 기본): 정적으로 판정할 수 없는 조건부 실행은 보고 병합 외에 거부.
        # False: fixture·변환 실험용 — 종전처럼 경고만 내고 양쪽/한쪽 갈래를 무조건 실행으로 넣는다.
        self.strict_conditionals = bool(strict_conditionals)
        self.warnings = []
        self.code = ""
        self.funcs = {}
        self.env = {}
        self.used_funcs = set()
        self.radar_marks = []       # [ETRI-CD F9 2026-10-07] use_radar=True 로 표시된 {skill, target}

    # ── 공용 ──
    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def _src(self, node):
        try:
            s = ast.get_source_segment(self.code, node)
            if s:
                return s.strip()
        except Exception:
            pass
        return type(node).__name__

    def literal(self, node):
        try:
            v = ast.literal_eval(node)
        except Exception:
            return None
        if isinstance(v, tuple):
            v = list(v)
        if isinstance(v, (str, int, float, list)):
            return v
        return None

    def resolve(self, node, env, where):
        """인자 노드 → 문자열 값. 해석 불가면 None(+경고)."""
        if isinstance(node, ast.Constant):
            return node.value if isinstance(node.value, str) else str(node.value)
        if isinstance(node, ast.Name):
            if node.id in env:
                v = env[node.id]
                if isinstance(v, _Ref):
                    return v.target
                if isinstance(v, _Unknown):
                    self.warn("%s: '%s' 는 %s 의 결과 — 값을 알 수 없음" % (where, node.id, v.what))
                    return None
                if isinstance(v, (str, int, float)):
                    return str(v)
                self.warn("%s: '%s' 는 문자열이 아님(%r) — 인자로 못 씀" % (where, node.id, type(v).__name__))
                return None
            self.warn("%s: 이름 '%s' 가 바인딩되지 않음" % (where, node.id))
            return None
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(str(v.value))
                elif isinstance(v, ast.FormattedValue):
                    inner = self.resolve(v.value, env, where)
                    parts.append(inner if inner is not None else "{?}")
            return "".join(parts)
        self.warn("%s: 인자 '%s' 는 리터럴이 아님" % (where, self._src(node)))
        return None

    def value_of(self, node, env, where):
        """바인딩용 값(문자열/리스트/_Ref/_Unknown 그대로)."""
        lit = self.literal(node)
        if lit is not None:
            return lit
        if isinstance(node, ast.Name) and node.id in env:
            return env[node.id]
        if isinstance(node, ast.JoinedStr):
            return self.resolve(node, env, where)
        return _Unknown(self._src(node))

    # ── 스킬 호출 → raw atomic ──
    def skill_atomic(self, call, env, where):
        name = call.func.id
        info = self.actions.get(name)
        if info is None:
            # [ETRI-CD F9 2026-10-07] 어휘 밖 스킬 호출은 실행 의미를 보존할 수 없다 — 조용히 버리지 않고 거부
            raise PlanIssue("%s: 어휘 밖 호출 %s() — 실행할 수 없는 단계(카탈로그에 없음)" % (where, name))
        keys = list(info.get("arg_keys") or ["object"])
        defaults = info.get("defaults") or {}
        args, use_radar = {}, False
        for i, a in enumerate(call.args):
            if i >= len(keys):
                self.warn("%s: %s() 위치 인자가 카탈로그(%s)보다 많음 — 초과분 무시"
                          % (where, name, ",".join(keys)))
                break
            args[keys[i]] = self.resolve(a, env, "%s:%s" % (where, name))
        for kw in call.keywords:
            if kw.arg in keys:
                args[kw.arg] = self.resolve(kw.value, env, "%s:%s" % (where, name))
            elif kw.arg == "use_radar":
                # [ETRI-CD F9 2026-10-07] LLM-TDM 의 radar 표시 — 버리지 않고 radar 요구 근거로 기록
                flag = self.literal(kw.value)
                if flag is None:
                    raise PlanIssue("%s: %s(use_radar=%s) 값을 해석할 수 없음"
                                    % (where, name, self._src(kw.value)))
                use_radar = bool(flag)
            else:
                raise PlanIssue("%s: %s() 키워드 인자 '%s' 는 카탈로그에 없음 — 의미를 보존할 수 없어 거부"
                                % (where, name, kw.arg))
        for k in keys:
            if args.get(k) in (None, ""):
                if k in defaults:
                    args[k] = str(defaults[k])
                else:
                    args[k] = "?"
                    self.warn("%s: %s() 인자 '%s' 가 리터럴이 아니거나 없음 → '?'"
                              % (where, name, k))
        node = {"type": "atomic", "skill": name, "args": args}
        if use_radar:
            self.radar_marks.append({"skill": name, "target": args.get(info.get("target_key", "object"))})
            node["extra_skills"] = ["radar"]       # [ETRI-CD R10] canonical required_skills 에 반영된다
        return node

    # ── 함수 본문 인라인 ──
    def bind_args(self, fn, call, env, where):
        params = [a.arg for a in fn.args.args]
        bound = {}
        for i, a in enumerate(call.args):
            if i < len(params):
                bound[params[i]] = self.value_of(a, env, where)
        for kw in call.keywords:
            if kw.arg in params:
                bound[kw.arg] = self.value_of(kw.value, env, where)
        return bound

    def inline(self, fname, bound, depth, where):
        if depth > self.max_depth:
            raise PlanIssue("%s: 함수 호출 깊이 %d 초과(재귀?)" % (where, self.max_depth))
        fn = self.funcs[fname]
        self.used_funcs.add(fname)
        env = dict(self.env)
        env.update(bound or {})
        for a in fn.args.args:
            if a.arg not in env:
                env[a.arg] = _Unknown("바인딩 안 된 매개변수 %s" % a.arg)
                self.warn("%s(): 매개변수 '%s' 가 바인딩되지 않음" % (fname, a.arg))
        return self.walk_body(fn.body, env, depth, "%s()" % fname)

    def walk_body(self, stmts, env, depth, where):
        steps = []
        for st in stmts:
            steps.extend(self.walk_stmt(st, env, depth, where))
        return steps

    def walk_stmt(self, st, env, depth, where):
        if isinstance(st, ast.Expr):
            if isinstance(st.value, ast.Call):
                return self.handle_call(st.value, env, depth, where)
            return []                                   # docstring 등
        if isinstance(st, ast.Assign) and len(st.targets) == 1 \
                and isinstance(st.targets[0], ast.Name):
            name = st.targets[0].id
            v = st.value
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Name):
                fid = v.func.id
                if fid in self.actions:
                    at = self.skill_atomic(v, env, where)
                    if at is None:
                        return []
                    info = self.actions[at["skill"]]
                    env[name] = _Ref(at["skill"], at["args"].get(info.get("target_key", "object")))
                    return [at]
                if fid in self.funcs:
                    env[name] = _Unknown("%s() 반환값" % fid)
                    return self.handle_call(v, env, depth, where)
                env[name] = _Unknown("어휘 밖 호출 %s()" % fid)
                self.warn("%s: 어휘 밖 호출 %s() 결과를 '%s' 에 대입 — 값 미상"
                          % (where, fid, name))
                return []
            lit = self.literal(v)
            if lit is not None:
                env[name] = lit
                return []
            if isinstance(v, ast.JoinedStr):
                env[name] = self.resolve(v, env, where)
                return []
            env[name] = _Unknown("식 %s" % self._src(v))
            self.warn("%s: 대입 '%s = %s' 해석 불가" % (where, name, self._src(v)))
            return []
        if isinstance(st, ast.If):
            return self.handle_if(st, env, depth, where)
        if isinstance(st, ast.For):
            return self.handle_for_inline(st, env, depth, where)
        if isinstance(st, (ast.Return, ast.Pass, ast.Import, ast.ImportFrom,
                           ast.Global, ast.Nonlocal, ast.Break, ast.Continue)):
            return []
        if isinstance(st, ast.While):
            # [ETRI-CD F9 2026-10-07] 반복 횟수를 알 수 없는 루프는 한 번 실행으로 바꿀 수 없다
            raise PlanIssue("%s: while 문은 실행 의미를 보존할 수 없음(반복 횟수 미상)" % where)
        if isinstance(st, (ast.With, ast.Try)):
            self.warn("%s: %s 문은 본문만 순차로 처리" % (where, type(st).__name__))
            return self.walk_body(getattr(st, "body", []), env, depth, where)
        self.warn("%s: 지원하지 않는 문 %s — 건너뜀" % (where, type(st).__name__))
        return []

    def handle_call(self, call, env, depth, where):
        if isinstance(call.func, ast.Name):
            fid = call.func.id
            if fid in self.actions:
                at = self.skill_atomic(call, env, where)
                return [at] if at else []
            if fid in self.funcs:
                bound = self.bind_args(self.funcs[fid], call, env, where)
                return self.inline(fid, bound, depth + 1, where)
            # [ETRI-CD F9 2026-10-07] 실행 단계로 쓰인 미등록 호출은 거부(값 조회용 대입은 경고만)
            raise PlanIssue("%s: 어휘 밖 호출 %s() — 실행할 수 없는 단계(카탈로그·정의된 함수에 없음)" % (where, fid))
        return []                                        # time.sleep() 등 속성 호출

    def _static_truth(self, node, env):
        """[ETRI-CD R10 2026-10-07] 조건식을 정적으로 판정: True/False 또는 None(판정 불가).
        상수, 리터럴에 바인딩된 이름, not <정적> 만 판정한다. 스킬 결과(_Ref)·미상 값은 None."""
        if isinstance(node, ast.Constant):
            return bool(node.value)
        if isinstance(node, ast.Name):
            if node.id in env:
                v = env[node.id]
                if isinstance(v, (str, int, float, list)):
                    return bool(v)
            return None
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            inner = self._static_truth(node.operand, env)
            return None if inner is None else (not inner)
        return None

    def handle_if(self, st, env, depth, where):
        cond = self._src(st.test)
        truth = self._static_truth(st.test, env)
        if truth is True:                              # [ETRI-CD R10] 정적 참: then 만, 조건 없음
            return self.walk_body(st.body, dict(env), depth, where)
        if truth is False:                             # 정적 거짓: else 만(없으면 아무것도)
            return self.walk_body(st.orelse, dict(env), depth, where)
        then_env, else_env = dict(env), dict(env)
        then_steps = self.walk_body(st.body, then_env, depth, where)
        else_steps = self.walk_body(st.orelse, else_env, depth, where)
        if then_steps and else_steps:
            same_single = (len(then_steps) == 1 and len(else_steps) == 1
                           and then_steps[0]["type"] == "atomic"
                           and else_steps[0]["type"] == "atomic"
                           and then_steps[0]["skill"] == else_steps[0]["skill"])
            if same_single:
                a, b = then_steps[0], else_steps[0]
                tkey = (self.actions.get(a["skill"]) or {}).get("target_key", "object")
                if a["skill"] not in MERGE_REPORT_SKILLS and a["args"].get(tkey) != b["args"].get(tkey):
                    # [ETRI-CD F9 2026-10-07] 대상이 다른 두 갈래를 하나로 합치면 실행 의미가 바뀐다
                    raise PlanIssue("%s: if (%s) 의 두 갈래가 같은 스킬 %s 이지만 대상이 다름(%r vs %r) — "
                                    "조건부 실행 의미를 보존할 수 없음"
                                    % (where, cond, a["skill"], a["args"].get(tkey), b["args"].get(tkey)))
                merged = self._merge_atomics(a, b)
                self.warn("%s: if (%s) 의 두 갈래가 같은 스킬 %s — atomic 1개로 병합"
                          "(실행기가 결과에 따라 보고 내용을 정함)"
                          % (where, cond, merged["skill"]))
                return [merged]
            if self.strict_conditionals:
                # [ETRI-CD R10] 판정 불가 조건의 서로 다른 갈래는 트리로 표현할 수 없다
                raise PlanIssue("%s: if (%s) 의 조건을 판정할 수 없고 두 갈래가 다른 단계(%s / %s) — "
                                "조건부 실행 의미를 보존할 수 없음(strict)"
                                % (where, cond, [s.get("skill") for s in then_steps],
                                   [s.get("skill") for s in else_steps]))
            self.warn("%s: if (%s) 의 두 갈래 스킬이 달라 둘 다 순차로 넣음(조건부 실행)"
                      % (where, cond))
            return then_steps + else_steps
        if then_steps or else_steps:
            steps = then_steps + else_steps
            only_report = all(s["type"] == "atomic" and s["skill"] in MERGE_REPORT_SKILLS for s in steps)
            if self.strict_conditionals and not only_report:
                # [ETRI-CD R10] 한쪽 갈래뿐이고 조건을 판정할 수 없으면 '무조건 실행'으로 바꿀 수 없다
                raise PlanIssue("%s: if (%s) 의 조건을 판정할 수 없는 조건부 단계 %d개(%s) — "
                                "무조건 실행으로 바꾸지 않음(strict)"
                                % (where, cond, len(steps), [s.get("skill") for s in steps]))
            self.warn("%s: if (%s) 조건부 단계 %d개를 무조건 실행으로 넣음%s"
                      % (where, cond, len(steps), "(보고 단계)" if only_report else ""))
            return steps
        return []

    @staticmethod
    def _merge_atomics(a, b):
        out = copy.deepcopy(a)
        for k in out["args"]:
            va, vb = a["args"].get(k), b["args"].get(k)
            if va in (None, "?") and vb not in (None, "?"):
                out["args"][k] = vb
        extra = list(a.get("extra_skills") or []) + [x for x in (b.get("extra_skills") or [])
                                                      if x not in (a.get("extra_skills") or [])]
        if extra:
            out["extra_skills"] = extra          # [ETRI-CD R10] 능력 태그는 합집합
        return out

    def iter_values(self, node, env):
        """for 문의 반복 대상 → 값 리스트, 못 풀면 None."""
        lit = self.literal(node)
        if isinstance(lit, list):
            return lit
        if isinstance(node, ast.Name) and isinstance(env.get(node.id), list):
            return env[node.id]
        return None

    def handle_for_inline(self, st, env, depth, where):
        if not isinstance(st.target, ast.Name):
            raise PlanIssue("%s: for 문의 변수가 단순 이름이 아님(%s)" % (where, self._src(st.target)))
        vals = self.iter_values(st.iter, env)
        if vals is None:
            raise PlanIssue("%s: for 문의 반복 대상 '%s' 을 해석할 수 없음" % (where, self._src(st.iter)))
        steps = []
        for v in vals:
            env2 = dict(env)
            env2[st.target.id] = v
            steps.extend(self.walk_body(st.body, env2, depth, where))
        return steps

    # ── 모듈 최상단: 스레드/블록 ──
    def thread_entry(self, node, env, where):
        """threading.Thread(target=f, args=(...), kwargs={...}) → (fname, bound) 또는 None."""
        if not isinstance(node, ast.Call):
            return None
        f = node.func
        is_thread = (isinstance(f, ast.Attribute) and f.attr == "Thread") or \
                    (isinstance(f, ast.Name) and f.id == "Thread")
        if not is_thread:
            return None
        fname, bound = None, {}
        for kw in node.keywords:
            if kw.arg == "target" and isinstance(kw.value, ast.Name):
                fname = kw.value.id
            elif kw.arg == "args" and isinstance(kw.value, (ast.Tuple, ast.List)):
                vals = [self.value_of(e, env, where) for e in kw.value.elts]
                if fname and fname in self.funcs:
                    params = [a.arg for a in self.funcs[fname].args.args]
                    for i, val in enumerate(vals):
                        if i < len(params):
                            bound[params[i]] = val
                else:
                    bound["__positional__"] = vals
            elif kw.arg == "kwargs" and isinstance(kw.value, ast.Dict):
                for k, v in zip(kw.value.keys, kw.value.values):
                    if isinstance(k, ast.Constant):
                        bound[str(k.value)] = self.value_of(v, env, where)
        if fname is None or fname not in self.funcs:
            self.warn("%s: Thread(target=%s) 의 대상 함수를 찾을 수 없음 — 무시" % (where, fname))
            return ("__missing__", {})
        pos = bound.pop("__positional__", None)
        if pos:
            params = [a.arg for a in self.funcs[fname].args.args]
            for i, val in enumerate(pos):
                if i < len(params):
                    bound[params[i]] = val
        return (fname, bound)

    def convert(self, code):
        self.code = code
        tree = ast.parse(code)
        self.funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        self.env = {}
        self.used_funcs = set()
        thread_vars = {}          # 변수 → (fname, bound)
        list_vars = {}            # 변수 → [thread entry]
        blocks = []               # [("PAR", [entry...]) | ("SEQ", [entry])]
        state = {"par": [], "barrier": False}

        def flush():
            if state["par"]:
                blocks.append(("PAR", state["par"]))
            state["par"], state["barrier"] = [], False

        def on_start(entry):
            if state["barrier"]:
                flush()
            state["par"].append(entry)

        def module_stmt(st, env, where):
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Import,
                               ast.ImportFrom, ast.ClassDef)):
                return
            if isinstance(st, ast.Assign) and len(st.targets) == 1 \
                    and isinstance(st.targets[0], ast.Name):
                name, v = st.targets[0].id, st.value
                entry = self.thread_entry(v, env, where)
                if entry is not None:
                    if entry[0] != "__missing__":
                        thread_vars[name] = entry
                    return
                if isinstance(v, ast.List) and not v.elts:
                    list_vars[name] = []      # threads = [] (스레드 목록 후보)
                    env[name] = []            # [ETRI-CD 2026-10-07] areas_to_search = [] 처럼 빈 리스트 상수로도 쓰인다
                    return
                lit = self.literal(v)
                if lit is not None:
                    env[name] = lit
                    return
                if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) \
                        and v.func.id in self.actions:
                    flush()
                    at = self.skill_atomic(v, env, where)
                    if at:
                        info = self.actions[at["skill"]]
                        env[name] = _Ref(at["skill"], at["args"].get(info.get("target_key", "object")))
                        blocks.append(("SEQ", [("__atomic__", at)]))
                        self.warn("%s: def 밖 스킬 직접 호출 %s() — 한 단계 순차 블록" % (where, at["skill"]))
                    return
                self.warn("%s: 대입 '%s' 해석 불가 — 무시" % (where, name))
                return
            if isinstance(st, ast.Expr):
                if not isinstance(st.value, ast.Call):
                    return
                call = st.value
                if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                    var, attr = call.func.value.id, call.func.attr
                    if attr == "start" and var in thread_vars:
                        on_start(thread_vars[var])
                    elif attr == "join" and var in thread_vars:
                        state["barrier"] = True
                    elif attr == "append" and var in list_vars and call.args \
                            and isinstance(call.args[0], ast.Name) \
                            and call.args[0].id in thread_vars:
                        list_vars[var].append(thread_vars[call.args[0].id])
                    return                                # 그 밖의 메서드 호출 무시
                if isinstance(call.func, ast.Name):
                    fid = call.func.id
                    if fid in self.funcs:
                        flush()
                        blocks.append(("SEQ", [(fid, self.bind_args(self.funcs[fid], call, env, where))]))
                    elif fid in self.actions:
                        flush()
                        at = self.skill_atomic(call, env, where)
                        if at:
                            blocks.append(("SEQ", [("__atomic__", at)]))
                            self.warn("%s: def 밖 스킬 직접 호출 %s() — 한 단계 순차 블록" % (where, fid))
                    else:
                        # [ETRI-CD F9 2026-10-07] 모듈 수준 미등록 호출도 거부
                        raise PlanIssue("%s: 어휘 밖 호출 %s() — 실행할 수 없는 단계" % (where, fid))
                return
            if isinstance(st, ast.For):
                module_for(st, env, where)
                return
            self.warn("%s: 지원하지 않는 문 %s — 건너뜀" % (where, type(st).__name__))

        def module_for(st, env, where):
            if not isinstance(st.target, ast.Name):
                raise PlanIssue("%s: for 문의 변수가 단순 이름이 아님" % where)
            var = st.target.id
            # for t in threads: t.join()  → 장벽 (스레드가 하나라도 append 된 목록일 때)
            if isinstance(st.iter, ast.Name) and list_vars.get(st.iter.id):
                joins = any(isinstance(b, ast.Expr) and isinstance(b.value, ast.Call)
                            and isinstance(b.value.func, ast.Attribute)
                            and b.value.func.attr == "join" for b in st.body)
                if joins:
                    state["barrier"] = True
                    return
            vals = self.iter_values(st.iter, env)
            if vals is None:
                raise PlanIssue("%s: for 문의 반복 대상 '%s' 을 해석할 수 없음"
                                % (where, self._src(st.iter)))
            for v in vals:
                env2 = dict(env)
                env2[var] = v
                for b in st.body:
                    module_stmt(b, env2, "%s[for %s=%r]" % (where, var, v))

        for st in tree.body:
            module_stmt(st, self.env, "module")
        flush()

        for name in self.funcs:
            if name not in self.used_funcs:
                # inline 되지 않은 함수 — 호출된 적 없거나 Thread 대상만 됐을 수 있음
                pass
        if not blocks:
            raise PlanIssue("실행되는 블록이 없다(스레드 start 나 함수 호출이 없음)")
        raw = self._blocks_to_raw(blocks)
        unused = [n for n in self.funcs if n not in self.used_funcs]
        for n in unused:
            self.warn("%s() 는 정의만 되고 호출되지 않았다" % n)
        return raw

    def _chain_of(self, entry):
        fname, bound = entry
        if fname == "__atomic__":
            return [bound]
        return self.inline(fname, bound, 1, "module")

    def _blocks_to_raw(self, blocks):
        nodes = []
        for kind, entries in blocks:
            if kind == "PAR":
                branches = []
                for e in entries:
                    steps = self._chain_of(e)
                    if steps:
                        branches.append({"type": "sequential", "subtasks": steps})
                if len(branches) == 1:
                    nodes.append(branches[0])
                elif branches:
                    nodes.append({"type": "parallel", "subtasks": branches})
            else:
                steps = []
                for e in entries:
                    steps.extend(self._chain_of(e))
                if steps:
                    nodes.append({"type": "sequential", "subtasks": steps})
        if not nodes:
            raise PlanIssue("스킬 호출이 하나도 없다(어휘 밖 호출만 있음?)")
        merged = []
        for n in nodes:
            if merged and n["type"] == "sequential" and merged[-1]["type"] == "sequential":
                merged[-1]["subtasks"].extend(n["subtasks"])
            else:
                merged.append(n)
        if len(merged) == 1:
            return merged[0]
        return {"type": "sequential", "subtasks": merged}


# ─────────────────────────────────────────────────────────────────────
# 2. raw → canonical (번들 normalize/validate 이식, Python 3.8)
# ─────────────────────────────────────────────────────────────────────
def _issue_report():
    return {"errors": [], "warnings": [], "notes": []}


def validate_raw(raw, catalog):
    report = _issue_report()
    actions = catalog.get("actions") or {}

    def visit(node, path):
        if not isinstance(node, dict):
            report["errors"].append("%s: node must be an object" % path)
            return
        extra = set(node) - RAW_NODE_KEYS
        if extra:
            report["errors"].append("%s: forbidden/unknown fields %s" % (path, sorted(extra)))
        t = node.get("type")
        if t == "atomic":
            if "subtasks" in node:
                report["errors"].append("%s: atomic node cannot contain subtasks" % path)
            skill, args = node.get("skill"), node.get("args")
            if not isinstance(skill, str) or not skill:
                report["errors"].append("%s: non-empty skill is required" % path)
                return
            info = actions.get(skill)
            if info is None:
                report["errors"].append("%s: unknown skill %r" % (path, skill))
                return
            if not isinstance(args, dict):
                report["errors"].append("%s: args must be an object" % path)
                return
            required = set(info.get("arg_keys") or [])
            if set(args) != required:
                report["errors"].append("%s: %s args must be exactly %s; got %s"
                                        % (path, skill, sorted(required), sorted(args)))
            for k, v in args.items():
                if not isinstance(v, str) or not v:
                    report["errors"].append("%s.args.%s: non-empty string required" % (path, k))
            extra = node.get("extra_skills")
            if extra is not None:                                   # [ETRI-CD R10] 능력 태그만 허용
                if not isinstance(extra, list) or any(x not in CAPABILITY_TAGS for x in extra):
                    report["errors"].append("%s: extra_skills must be a list of capability tags %s; got %r"
                                            % (path, sorted(CAPABILITY_TAGS), extra))
            if not info.get("declared_by_any_robot", False):
                report["warnings"].append("%s: %s is declared by no current robot" % (path, skill))
            if not info.get("has_executor_wrapper", False):
                report["warnings"].append("%s: %s has no current executor wrapper" % (path, skill))
            return
        if t in ("sequential", "parallel"):
            for f in ("skill", "args"):
                if f in node:
                    report["errors"].append("%s: composite node cannot contain %s" % (path, f))
            ch = node.get("subtasks")
            if not isinstance(ch, list) or not ch:
                report["errors"].append("%s: non-empty subtasks array is required" % path)
                return
            for i, c in enumerate(ch):
                visit(c, "%s.subtasks[%d]" % (path, i))
            return
        report["errors"].append("%s: type must be atomic, sequential, or parallel" % path)

    visit(raw, "$")
    return report


def _target(node, catalog):
    info = catalog["actions"][node["skill"]]
    return node["args"][info.get("target_key", "object")]


def _expected_hold_assignments(doc):
    """'손에 든 물건' 묶음(번들 A안 규칙) — 순차 흐름을 따라 Pickup~Put 구간을 같은
    hold_group 으로 묶는다. 중첩 sequential 은 투명, parallel 은 장벽."""
    assignments, counters = {}, {}

    def remember(node):
        if node["type"] == "atomic":
            assignments[node["id"]] = None
            return
        for c in node["subtasks"]:
            remember(c)

    remember(doc)

    def process_parallel(node):
        for c in node["subtasks"]:
            if c["type"] == "sequential":
                process_sequential(c)
            elif c["type"] == "parallel":
                process_parallel(c)

    def process_sequential(node):
        state = {"pending": [], "open": None}

        def new_group(label):
            counters[label] = counters.get(label, 0) + 1
            return "%s_h%d" % (label, counters[label])

        def atomic(item, label):
            skill = item["skill"]
            if skill in HOLD_START:
                glabel = state["pending"][0][1] if state["pending"] else label
                g = new_group(str(glabel))
                for p, _ in state["pending"]:
                    assignments[p["id"]] = g
                state["pending"] = []
                state["open"] = g
                assignments[item["id"]] = g
            elif state["open"] is not None:
                if skill in HOLD_KEEP:
                    assignments[item["id"]] = state["open"]
                elif skill in HOLD_RELEASE:
                    assignments[item["id"]] = state["open"]
                    state["open"] = None
            elif skill == "GoToObject":
                state["pending"].append((item, label))
            else:
                state["pending"] = []

        def consume(cur, label):
            for c in cur["subtasks"]:
                if c["type"] == "atomic":
                    atomic(c, label)
                elif c["type"] == "sequential":
                    consume(c, str(c["id"]))
                else:
                    state["pending"] = []
                    state["open"] = None
                    process_parallel(c)

        consume(node, str(node["id"]))

    if doc["type"] == "sequential":
        process_sequential(doc)
    elif doc["type"] == "parallel":
        process_parallel(doc)
    return assignments


def normalize(raw, catalog, root_meta=None):
    """raw → canonical. id·required_skills·hold_group 의 유일한 생성 주체(번들 승계)."""
    report = validate_raw(raw, catalog)
    if report["errors"]:
        raise PlanIssue("raw validation failed: " + "; ".join(report["errors"]))
    working = copy.deepcopy(raw)
    if working.get("type") == "atomic":
        working = {"type": "sequential", "subtasks": [working]}
    task_counter = [0]
    comp_counter = [0]

    def label_for(node, parent_label, index, is_root):
        if is_root:
            return "par" if node["type"] == "parallel" else "root"
        if parent_label == "par" and node["type"] == "sequential":
            return "sub%d" % (index + 1)
        if parent_label == "root" and node["type"] == "parallel":
            return "par"
        if parent_label == "root" and node["type"] == "sequential" and index > 0:
            return "after"
        comp_counter[0] += 1
        return "c%02d_%s" % (comp_counter[0], node["type"])

    def atomic_node(node):
        task_counter[0] += 1
        skill = node["skill"]
        target = _target(node, catalog)
        safe = re.sub(r"[^0-9A-Za-z_]+", "_", target).strip("_") or "x"
        return {
            "id": "t%02d_%s_%s" % (task_counter[0], skill, safe),
            "type": "atomic",
            "skill": skill,
            "args": copy.deepcopy(node["args"]),
            "required_skills": [skill] + [x for x in (node.get("extra_skills") or []) if x != skill],   # [ETRI-CD R10]
            "goal": "%s:%s" % (skill, target),
        }

    def visit(node, parent_label=None, index=0, is_root=False):
        if node["type"] == "atomic":
            return atomic_node(node)
        label = label_for(node, parent_label, index, is_root)
        out_children = []
        for ci, c in enumerate(node["subtasks"]):
            if c["type"] == "atomic":
                out_children.append(atomic_node(c))
            else:
                out_children.append(visit(c, label, ci, False))
        if node["type"] == "parallel":
            goal = "independent subtasks"
        elif all(c["type"] == "atomic" for c in node["subtasks"]):
            goal = " -> ".join(c["goal"] for c in out_children)
        else:
            goal = "sequential composite"
        return {"id": label, "type": node["type"], "goal": goal, "subtasks": out_children}

    canonical = visit(working, is_root=True)
    assignments = _expected_hold_assignments(canonical)

    def attach(node):
        if node["type"] == "atomic":
            g = assignments.get(node["id"])
            if g:
                node["metadata"] = {"hold_group": g}
            return
        for c in node["subtasks"]:
            attach(c)

    attach(canonical)
    for k, v in (root_meta or {}).items():
        if k in ROOT_META_KEYS:
            canonical[k] = copy.deepcopy(v)
    return canonical


def validate_canonical(doc, catalog, allow_extra_skills=False):
    """번들 규칙 검증. allow_extra_skills=True 면 required_skills 가 [skill] 보다
    넓어도(재계획이 radar 를 더한 경우) 허용한다 — BnT 확장."""
    report = _issue_report()
    seen = set()

    def visit(node, path, is_root=False):
        if not isinstance(node, dict):
            report["errors"].append("%s: node must be an object" % path)
            return
        t = node.get("type")
        allowed = CANON_ATOMIC_KEYS if t == "atomic" else CANON_COMPOSITE_KEYS
        if is_root:
            allowed = allowed | ROOT_META_KEYS
        extra = set(node) - allowed
        if extra:
            report["errors"].append("%s: forbidden/unknown fields %s" % (path, sorted(extra)))
        tid = node.get("id")
        if not isinstance(tid, str) or not tid:
            report["errors"].append("%s: non-empty id is required" % path)
        elif tid in seen:
            report["errors"].append("%s: duplicate id %r" % (path, tid))
        else:
            seen.add(tid)
        if t == "atomic":
            sub = validate_raw({k: node.get(k) for k in ("type", "skill", "args")}, catalog)
            report["errors"].extend("%s: %s" % (path, m) for m in sub["errors"])
            report["warnings"].extend("%s: %s" % (path, m) for m in sub["warnings"])
            rs = node.get("required_skills")
            if allow_extra_skills:
                if not isinstance(rs, list) or not rs or rs[0] != node.get("skill"):
                    report["errors"].append("%s: required_skills must start with skill" % path)
            elif not isinstance(rs, list) or not rs or rs[0] != node.get("skill") \
                    or any(x not in CAPABILITY_TAGS for x in rs[1:]):
                # [ETRI-CD R10] strict: [skill] 또는 [skill, <능력 태그>…] 만
                report["errors"].append("%s: required_skills must be [skill] plus capability tags %s"
                                        % (path, sorted(CAPABILITY_TAGS)))
            md = node.get("metadata")
            if md is not None:
                if not isinstance(md, dict) or set(md) != {"hold_group"}:
                    report["errors"].append("%s: metadata may contain only hold_group" % path)
                elif not isinstance(md["hold_group"], str) or not md["hold_group"]:
                    report["errors"].append("%s: hold_group must be a non-empty string" % path)
            return
        if t not in ("sequential", "parallel"):
            report["errors"].append("%s: invalid type %r" % (path, t))
            return
        ch = node.get("subtasks")
        if not isinstance(ch, list) or not ch:
            report["errors"].append("%s: non-empty subtasks array is required" % path)
            return
        for i, c in enumerate(ch):
            visit(c, "%s.subtasks[%d]" % (path, i))

    visit(doc, "$", True)
    if not report["errors"] and isinstance(doc, dict) and not allow_extra_skills:
        expected = _expected_hold_assignments(doc)

        def check(node, path):
            if node["type"] == "atomic":
                got = (node.get("metadata") or {}).get("hold_group")
                if got != expected.get(node["id"]):
                    report["errors"].append(
                        "%s: hold_group differs from recursive sequential-flow rule" % path)
                return
            for i, c in enumerate(node["subtasks"]):
                check(c, "%s.subtasks[%d]" % (path, i))

        check(doc, "$")
    return report


def validate_semantics(doc):
    """Pickup/Put 물건 소지 흐름의 내부 모순만 거른다(번들 승계)."""
    report = _issue_report()

    def seq(node, state, path):
        for i, c in enumerate(node["subtasks"]):
            cp = "%s.subtasks[%d]" % (path, i)
            if c["type"] == "atomic":
                skill = c["skill"]
                obj = (c.get("args") or {}).get("object")
                held = state.get("held")
                if skill == "PickupObject":
                    if held is not None:
                        report["errors"].append("%s: PickupObject(%s) while already holding %s" % (cp, obj, held))
                    state["held"] = obj
                elif skill in HOLD_RELEASE:
                    if held is None:
                        report["errors"].append("%s: %s(%s) has no preceding pickup in this flow" % (cp, skill, obj))
                    elif obj != held:
                        report["errors"].append("%s: %s object %r differs from held %r" % (cp, skill, obj, held))
                    state["held"] = None
            elif c["type"] == "sequential":
                seq(c, state, cp)
            else:
                if state.get("held") is not None:
                    report["errors"].append("%s: parallel boundary while holding %r is ambiguous" % (cp, state["held"]))
                par(c, cp)
                state["held"] = None

    def par(node, path):
        for i, c in enumerate(node["subtasks"]):
            cp = "%s.subtasks[%d]" % (path, i)
            if c["type"] == "sequential":
                seq(c, {"held": None}, cp)
            elif c["type"] == "parallel":
                par(c, cp)
            elif c["skill"] in HOLD_RELEASE:
                report["errors"].append("%s: standalone %s has no preceding pickup" % (cp, c["skill"]))

    if doc["type"] == "sequential":
        seq(doc, {"held": None}, "$")
    elif doc["type"] == "parallel":
        par(doc, "$")
    elif doc.get("skill") in HOLD_RELEASE:
        report["errors"].append("$: standalone %s has no preceding pickup" % doc["skill"])
    return report


# ─────────────────────────────────────────────────────────────────────
# 3. 진입점·도우미
# ─────────────────────────────────────────────────────────────────────
def convert_code(code, catalog=None, source=None, strict_conditionals=True):
    catalog = catalog or load_catalog()
    conv = Converter(catalog, strict_conditionals=strict_conditionals)
    raw = conv.convert(code)
    meta = {"text": task_description(code)}
    if source:
        meta["source"] = str(source)
    canonical = normalize(raw, catalog, meta)
    return {
        "text": meta["text"],
        "raw": raw,
        "canonical": canonical,
        "radar_marks": list(conv.radar_marks),        # [ETRI-CD F9 2026-10-07] use_radar=True 표시 대상
        "warnings": list(conv.warnings),
        "raw_validation": validate_raw(raw, catalog),
        "canonical_validation": validate_canonical(canonical, catalog),
        "semantic_validation": validate_semantics(canonical),
    }


def convert_file(path, catalog_path=None, strict_conditionals=True):
    code = Path(path).read_text(encoding="utf-8")
    return convert_code(code, load_catalog(catalog_path), source=Path(path).name,
                        strict_conditionals=strict_conditionals)


def iter_atomics(doc):
    if doc["type"] == "atomic":
        yield doc
        return
    for c in doc.get("subtasks") or []:
        for a in iter_atomics(c):
            yield a


def dump_tree(doc):
    """사람이 읽는 트리 덤프."""
    lines = []

    def rec(node, prefix, is_last, is_root):
        branch = "" if is_root else ("└─ " if is_last else "├─ ")
        if node["type"] == "atomic":
            lines.append("%s%s%s  [%s]  %s" % (
                prefix, branch, node["id"], ",".join(node.get("required_skills") or []),
                json.dumps(node.get("args") or {}, ensure_ascii=False)))
            return
        lines.append("%s%s%s (%s%s)" % (
            prefix, branch, node["id"], node["type"],
            (", " + node["goal"]) if node.get("goal") and node["type"] == "parallel" else ""))
        ch = node.get("subtasks") or []
        for i, c in enumerate(ch):
            ext = "" if is_root else ("   " if is_last else "│  ")
            rec(c, prefix + ext, i == len(ch) - 1, False)

    rec(doc, "", True, True)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="LLM-TDM 계획(.py) → canonical TaskTree JSON")
    ap.add_argument("plan")
    ap.add_argument("--catalog", default=None)
    ap.add_argument("--out", default=None, help="canonical JSON 저장 경로")
    ap.add_argument("--full", action="store_true", help="--out 에 raw/warnings/검증까지 저장")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--loose-conditionals", action="store_true",
                    help="[ETRI-CD R10] 판정 불가 조건부 단계를 거부하지 않고 경고와 함께 넣는다(변환 실험용, 운영 금지)")
    a = ap.parse_args(argv)
    try:
        r = convert_file(a.plan, a.catalog, strict_conditionals=not a.loose_conditionals)
    except (PlanIssue, SyntaxError) as e:
        print("변환 실패: %s" % e, file=sys.stderr)
        return 1
    if not a.quiet:
        print("# task: %s" % r["text"])
        print(dump_tree(r["canonical"]))
        n = sum(1 for _ in iter_atomics(r["canonical"]))
        print("# atomic %d개, warnings %d개" % (n, len(r["warnings"])))
        for w in r["warnings"]:
            print("  warning: %s" % w)
        for key in ("canonical_validation", "semantic_validation"):
            for e in r[key]["errors"]:
                print("  ERROR(%s): %s" % (key, e))
    if a.out:
        payload = r if a.full else r["canonical"]
        Path(a.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        if not a.quiet:
            print("# saved: %s" % a.out)
    bad = r["canonical_validation"]["errors"] or r["semantic_validation"]["errors"]
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
