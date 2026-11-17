#!/usr/bin/env python3
"""JnP 스케줄링/할당 모듈.

Allocator와 Scheduler를 인터페이스로 분리해 알고리즘 교체가 가능하다:
- 새 할당 알고리즘  : Allocator.select()만 구현 (예: 경매(bidding) 기반, 비용 최소화)
- 새 스케줄러 알고리즘: Scheduler.run()/notify_end()만 구현 (예: tier-batch, 우선순위 기반)

현재 구현:
- SimpleAllocator : agent 목록을 순회하다 처음 만나는 적합한(free + 능력 충족) agent 선택
- SimpleScheduler : task tree를 순회하며 시작 가능한 task에 start 신호를 보내고,
                    agent의 end 신호를 받으면 완료 표시 후 다시 순회 (start/end 이벤트 구동)

이 모듈은 ROS에 의존하지 않는다(순수 파이썬) — ROS 없이 단위 테스트 가능.
agent 객체에 요구되는 인터페이스: free, capability_set, setTask(t), start_task(scheduler),
그리고 end 시 scheduler.notify_end(agent, task, ok) 호출.
"""
import math
import queue
import re

from jnp_task import AtomicTask, SequentialCompositeTask


# ───────────────────────── [JnP-0.9.0 2026-10-18] 스킬 기반 역할 할당 ─────────────────────────
def short_name(name):
    return str(name or '').strip('/').split('/')[-1]


def natural_key(name):
    """이름의 자연 정렬 키: 'tb3_10' 이 'tb3_2' 뒤에 오도록 숫자 조각은 정수로 비교한다(문자열 비교 함정 회피)."""
    return tuple(int(t) if t.isdigit() else t for t in re.split(r'(\d+)', short_name(name)))


def can_execute(agent, skills_needed, caps_needed, skills_strict=False):
    """적격 검사(역할 또는 단위 task 하나에 대해). 반환 (ok, reason):
      busy   — 다른 미션 실행 중이면 불가
      skills — 광고 skills 가 있으면 요구 스킬 ⊆ 광고 스킬. None(미광고)은 호환 모드(skills_strict=False)에서 통과, strict 면 불가.
               빈 목록([] = '없음' 선언)은 요구 스킬이 있으면 불가.
      caps   — 요구 능력 ⊆ capability_set
    능력에서 스킬을 추정하지 않는다."""
    reason = {}
    if getattr(agent, 'busy', False):
        reason['busy'] = True
    sk = getattr(agent, 'skills', None)
    need = set(skills_needed or [])
    if sk is None:
        if skills_strict and need:
            reason['skills'] = 'unadvertised'
    elif not need <= set(sk):
        reason['skills'] = sorted(need - set(sk))
    caps = set(getattr(agent, 'capability_set', set()) or set())
    cneed = set(caps_needed or [])
    if not cneed <= caps:
        reason['caps'] = sorted(cneed - caps)
    return (not reason), reason


def eta_to(agent, point, positions, speed_fn):
    """로봇 위치(positions[짧은 이름] = (x, y))에서 point 까지 ETA(거리 ÷ 속도). 위치나 점을 모르면 0.0(불이익 없음)."""
    if not point:
        return 0.0
    pos = (positions or {}).get(short_name(getattr(agent, 'name', '')))
    if not pos:
        return 0.0
    sp = speed_fn(short_name(agent.name)) if speed_fn else 0.3
    return math.hypot(point[0] - pos[0], point[1] - pos[1]) / max(float(sp), 0.05)


def assign_roles(roles, candidates, hints=None, starts=None, positions=None, speed_fn=None, prefer_names=None,
                 skills_strict=False, mode='prefer-list'):
    """역할표(선언 순)에 로봇을 결정적으로 묶는다(역할 1 ↔ 로봇 1, 한 로봇은 역할 하나).
    roles: [{name, skills, requirements, prefer}], candidates: skills/capability_set/busy/name 을 가진 객체들.
    hints: {역할: 선호 로봇}, starts: {역할: (x, y)} (ETA 기준점), positions: {로봇: (x, y)}, prefer_names: 요청자 명단(선호 집합).
    mode: prefer-list(명단 로봇 우선, 부족하면 명부 전체) | list-only(명단 밖 로봇 사용 안 함) | all(명단 무시).
    선택 키 = (힌트 로봇이면 0, 뒤 역할의 힌트 로봇이면 1(남겨 둠), 명단 로봇이면 0, 역할의 prefer 능력을 가지면 0, 시작점까지 ETA, 이름 자연 정렬) 의 최소.
    반환 {'bound': {역할: 후보}, 'unassigned': [역할], 'reasons': {역할: {...}}, 'rejected': {역할: {로봇: 사유}}}"""
    hints, starts, prefer_names = hints or {}, starts or {}, list(prefer_names or [])
    bound, unassigned, reasons, rejected = {}, [], {}, {}
    taken = set()
    for idx, role in enumerate(roles):
        rname = role['name']
        hint = hints.get(rname)
        later_hints = {hints.get(r['name']) for r in roles[idx + 1:] if hints.get(r['name'])}   # 뒤 역할의 힌트 로봇은 가급적 남겨 둔다
        rejected[rname] = {}
        elig = []
        for c in candidates:
            sn = short_name(c.name)
            if sn in taken:
                rejected[rname][sn] = {'taken': True}
                continue
            ok, why = can_execute(c, role.get('skills') or [], role.get('requirements') or [], skills_strict)
            if not ok:
                rejected[rname][sn] = why
                continue
            if mode == 'list-only' and sn not in prefer_names:
                rejected[rname][sn] = {'outside_list': True}     # [V-F4] 빈 명단이면 아무도 적격이 아니다(전체 명부로 확대하지 않음)
                continue
            elig.append(c)
        if not elig:
            unassigned.append(rname)
            reasons[rname] = {'hint': hint, 'eligible': 0, 'list_empty': (mode == 'list-only' and not prefer_names)}
            continue
        pref = set(role.get('prefer') or [])
        in_list = (lambda sn: 0 if (not prefer_names or mode == 'all' or sn in prefer_names) else 1)
        start = starts.get(rname)

        def pos_known(c):
            # [V-F11] 시작점이 있는데 위치를 모르는 후보는 ETA 0 으로 유리해지지 않게 — 위치를 아는 후보 뒤로
            return 0 if (not start or short_name(c.name) in (positions or {})) else 1

        def key(c):
            sn = short_name(c.name)
            return (0 if sn == hint else 1,
                    1 if (sn != hint and sn in later_hints) else 0,
                    in_list(sn),
                    0 if (pref and pref & set(getattr(c, 'capability_set', set()) or set())) else 1,
                    pos_known(c),
                    round(eta_to(c, start, positions, speed_fn), 3),
                    natural_key(sn))
        chosen = min(elig, key=key)
        sn = short_name(chosen.name)
        taken.add(sn)
        bound[rname] = chosen
        k = key(chosen)
        reasons[rname] = {'hint': hint, 'hinted': (sn == hint), 'prefer_hit': (k[3] == 0 and bool(pref)),
                          'pos_known': (k[4] == 0), 'eta': k[5],
                          'substituted': bool(prefer_names and mode != 'all' and sn not in prefer_names),
                          'eligible': len(elig), 'candidates': [short_name(c.name) for c in elig],
                          'skills_known': getattr(chosen, 'skills', None) is not None}
    return {'bound': bound, 'unassigned': unassigned, 'reasons': reasons, 'rejected': rejected}


def pool_members(pool, candidates, taken=(), prefer_names=None, skills_strict=False, mode='prefer-list'):
    """풀 task(역할 없음)의 멤버: 자격 있는 로봇 전부(명단 우선 규칙은 assign_roles 와 같음). 반환 (멤버 목록, 거부 사유)."""
    rejected = {}
    elig = []
    prefer_names = list(prefer_names or [])
    for c in candidates:
        sn = short_name(c.name)
        if sn in taken:
            rejected[sn] = {'taken': True}
            continue
        ok, why = can_execute(c, pool.get('skills') or [], pool.get('requirements') or [], skills_strict)
        if not ok:
            rejected[sn] = why
            continue
        if mode == 'list-only' and sn not in prefer_names:
            rejected[sn] = {'outside_list': True}     # [V-F4] 빈 명단 = 아무도 아님
            continue
        elig.append(c)
    if mode == 'prefer-list' and prefer_names:
        pre = [c for c in elig if short_name(c.name) in prefer_names]
        if pre:
            elig = pre
    return sorted(elig, key=lambda c: natural_key(c.name)), rejected


def task_skills(task):
    """단위 task 가 요구하는 스킬 목록([skill] 또는 [] — 고정 빌더 트리처럼 _skill 이 없으면 스킬 검사 생략)."""
    sk = getattr(task, '_skill', None)
    return [sk] if sk else []


def eligible_agents(task, agents, skills_strict=False):
    """[JnP-0.9.0 V-F6] 모든 할당기가 공유하는 적격 후보 집합: free ∧ can_execute(바쁨·스킬·능력). 선호·거리 규칙은 이 집합 위에서 적용한다."""
    return [a for a in agents if a.free and can_execute(a, task_skills(task), task.requirement, skills_strict)[0]]


class Allocator:
    """할당 알고리즘 인터페이스."""
    skills_strict = False      # [V-F6] 적격 정책(스킬 3상태)은 그룹이 모든 할당기에 같은 값으로 넣는다

    def select(self, task, agents):
        """task에 적합한 agent를 반환한다(없으면 None). 상태 변경은 하지 않는다."""
        raise NotImplementedError


class SimpleAllocator(Allocator):
    """단순 할당기: 적격 후보(free + 바쁨·스킬·능력 충족) 중 처음 만나는 agent 를 반환."""

    def select(self, task, agents):
        elig = eligible_agents(task, agents, self.skills_strict)
        return elig[0] if elig else None


class AffinityAllocator(Allocator):
    """전담(affinity) 할당기: key_fn(task)가 같은 task 들은 같은 agent 에 고정.

    예(오더피킹): key = '주문id:능력' → 한 주문의 운반 task 전부가 같은 AMR —
    '주문마다 유휴 AMR 1대를 전담 배정'(원 실험 방식)을 재현한다.
    key 가 처음 등장하면 first-fit 으로 정한 뒤 기억하고, 전담 agent 가 바쁘면
    None 을 돌려 그 agent 가 빌 때까지 기다린다. key_fn 이 None 을 주는 task 는
    일반 first-fit."""

    def __init__(self, key_fn, prefer_fn=None):
        self.key_fn = key_fn
        self.prefer_fn = prefer_fn   # 새 key 바인딩 시 후보 중 선택(예: 최근접) — None=first-fit
        self.bind = {}               # key -> agent

    def select(self, task, agents):
        key = self.key_fn(task)
        if key is not None and key in self.bind:
            a = self.bind[key]
            return a if (a in agents and a.free and can_execute(a, task_skills(task), task.requirement, self.skills_strict)[0]) else None
        cands = eligible_agents(task, agents, self.skills_strict)
        if not cands:
            return None
        agent = self.prefer_fn(task, cands) if self.prefer_fn else cands[0]
        if key is not None:
            self.bind[key] = agent
        return agent


class RoleAllocator(Allocator):
    """[JnP-0.9.0] 역할 할당기: task._role 이 묶인 agent 로만 간다(역할 1 ↔ 로봇 1, 미션 동안 고정). 그 agent 가 바쁘면 None(대기).
    역할이 없는 풀 task 는 자격 있는(can_execute) 유휴 agent 중 pool_fn(task, cands) 가 고른 것(없으면 이름 자연 정렬 첫째)."""

    def __init__(self, bind, pool_fn=None, skills_strict=False):
        self.bind = dict(bind)          # 역할 → agent
        self.pool_fn = pool_fn
        self.skills_strict = skills_strict

    def select(self, task, agents):
        role = getattr(task, '_role', None)
        if role is not None:
            a = self.bind.get(role)
            if a is None or a not in agents:
                return None                 # [V-F3] 묶인 로봇이 현재 멤버가 아니면(kill/방출) 보내지 않는다 — 바인딩은 무효, 재할당 없음
            return a if (a.free and can_execute(a, task_skills(task), task.requirement, self.skills_strict)[0]) else None
        cands = eligible_agents(task, agents, self.skills_strict)
        if not cands:
            return None
        if self.pool_fn:
            return self.pool_fn(task, cands)
        return min(cands, key=lambda a: natural_key(a.name))


class Scheduler:
    """스케줄러 인터페이스."""

    def run(self, root_task, agents):
        """root_task 아래 전체가 완료될 때까지 스케줄. 성공 시 True."""
        raise NotImplementedError

    def notify_end(self, agent, task, ok):
        """agent가 task 종료(end 신호)를 알리는 수신구. 스레드 안전해야 한다."""
        raise NotImplementedError


class SimpleScheduler(Scheduler):
    """단순 스케줄러 — task tree 순회 + start/end 신호 기반.

    동작:
      1. task tree를 순회하며 '지금 시작 가능한' atomic task를 찾는다.
         - SequentialCompositeTask: 첫 번째 미완료 자식 서브트리만 내려감 (순서 보장)
         - ParallelCompositeTask  : 모든 자식 서브트리로 내려감
         - 중첩 composite         : 위 규칙이 재귀 적용되므로 깊이 무관
         - atomic task            : 미완료·미할당이고 모든 선행자가 완료면 시작 가능
      2. Allocator로 agent를 골라 start 신호를 보낸다 (agent.start_task, 비동기).
      3. agent의 end 신호(notify_end → 이벤트 큐)를 기다렸다가 완료 표시 후 1로 돌아간다.
      4. root 완료(= 모든 자식이 재귀적으로 완료)면 종료.

    end 신호(notify_end)는 actionlib 콜백 스레드에서 불리지만 큐에 넣기만 하고,
    모든 상태 변경은 run()을 실행하는 스케줄러 스레드에서만 하므로 락이 필요 없다.
    """

    def __init__(self, allocator=None, max_retry=3, end_timeout=120.0, log=print,
                 on_update=None, allow_idle=False, skills_strict=False):
        self.skills_strict = skills_strict   # [JnP-0.9.0] dispatch 최종 방어의 스킬 3상태 정책
        # allow_idle: 탐사처럼 task 가 실행 중에 '추가'되는 open-world 스케줄용 —
        # 시작 가능 task 가 일시적으로 없어도 실패하지 않고 wake 를 기다린다
        self.allocator = allocator if allocator is not None else SimpleAllocator()
        self.events = queue.Queue()   # end 신호 큐 (콜백 스레드 → 스케줄러 스레드)
        self.max_retry = max_retry    # task 실패 시 재시도 한도
        self.end_timeout = end_timeout  # end 신호 대기 시간 한도(초)
        self.log = log
        self.on_update = on_update    # 상태 변화 훅: on_update(root_task) — 시각화 등
        self.allow_idle = allow_idle

    def _update(self, root_task):
        if self.on_update is not None:
            try:
                self.on_update(root_task)
            except Exception:
                pass                  # 시각화 실패가 스케줄을 멈추면 안 됨

    # ---------- end 신호 수신 (agent가 호출; 콜백 스레드) ----------
    def notify_end(self, agent, task, ok):
        self.events.put((agent, task, ok))

    def wake(self):
        """멤버 변동(그룹 간 이적 영입 등) 알림 — run 루프를 깨워 즉시 재배정."""
        self.events.put((None, None, False))

    # ---------- task tree 순회 ----------
    def is_complete(self, task):
        """composite 완료 = 모든 자식이 (재귀적으로) 완료."""
        if isinstance(task, AtomicTask):
            return task.complete
        return all(self.is_complete(sub) for sub in task.subtasks)

    def find_startable(self, task, acc):
        """트리를 재귀 순회하며 지금 시작 가능한 atomic task를 acc에 모은다."""
        if isinstance(task, AtomicTask):
            if (not task.complete and not task.assign_status
                    and all(p.complete for p in task.predecessors)):
                acc.append(task)
        elif isinstance(task, SequentialCompositeTask):
            for sub in task.subtasks:        # 순서대로, 첫 미완료 자식까지만
                if not self.is_complete(sub):
                    self.find_startable(sub, acc)
                    break                    # 다음 형제는 이 서브트리 완료 후
        else:                                # ParallelCompositeTask 등
            for sub in task.subtasks:
                self.find_startable(sub, acc)
        return acc

    # ---------- start 신호 발송 ----------
    def dispatch(self, root_task, agents):
        """시작 가능한 task 각각에 agent를 할당하고 start 신호를 보낸다. 발송 수 반환."""
        started = 0
        for task in self.find_startable(root_task, []):
            agent = self.allocator.select(task, agents)
            if agent is None:
                continue                     # 지금은 배정할 agent 없음 — 다음 end 신호 후 재시도
            # [JnP-0.9.0] 최종 방어: 할당기가 무엇을 골랐든 현재 멤버이고 적격(스킬·능력·바쁨)이어야 start 를 보낸다
            if agent not in agents:
                self.log(f"[SCHED] 배정 불가: {task.name} -> {agent.name} 현재 멤버가 아님(제거됨) — 발송하지 않음")   # [V-F3]
                continue
            ok, why = can_execute(agent, task_skills(task), task.requirement, self.skills_strict)
            if not ok:
                self.log(f"[SCHED] 배정 불가: {task.name} -> {agent.name} 부적격 {why}")
                continue
            agent.free = False
            agent.execute_status = True
            task.assign_status = True
            task.assign(agent)
            agent.setTask(task)
            self.log(f"[SCHED] start: {task.name} -> {agent.name}")
            agent.start_task(self)           # 비동기 — end는 notify_end로 돌아온다
            started += 1
        return started

    # ---------- 메인 루프 ----------
    def run(self, root_task, agents):
        retry = {}
        inflight = self.dispatch(root_task, agents)
        self._update(root_task)
        while not self.is_complete(root_task):
            if inflight == 0 and not self.allow_idle:
                # 시작할 것도, 기다릴 것도 없음 = 능력/의존성 문제로 진행 불가
                self.log("[SCHED] 진행 불가: 시작 가능한 task에 배정할 agent가 없음")
                self._update(root_task)
                return False
            try:
                agent, task, ok = self.events.get(timeout=self.end_timeout)
            except queue.Empty:
                self.log(f"[SCHED] end 신호 대기 시간 초과({self.end_timeout}s)")
                self._update(root_task)
                return False
            if agent is None:            # wake 센티넬 — end 아님, 재배정만
                inflight += self.dispatch(root_task, agents)
                self._update(root_task)
                continue
            inflight = max(0, inflight - 1)
            agent.free = True                # agent 반납 → 재사용 가능
            agent.execute_status = False
            agent.task = None
            if ok:
                task.complete = True
                for s in task.successors:    # baseline 필드(predecessors_complete) 호환 갱신
                    s.predecessors_complete = all(p.complete for p in s.predecessors)
                self.log(f"[SCHED] end  : {task.name} <- {agent.name}")
            else:
                task.assign_status = False   # 롤백 → 재할당 대상으로 복귀
                task.agent = None
                retry[task] = retry.get(task, 0) + 1
                self.log(f"[SCHED] fail : {task.name} (재시도 {retry[task]}/{self.max_retry})")
                if retry[task] > self.max_retry:
                    if getattr(task, 'optional', False):
                        # 선택적 task(예: 선이동 최적화)는 포기하고 미션을 계속한다
                        self.log(f"[SCHED] skip : {task.name} (선택적 task — 한도 초과, 건너뜀)")
                        task.complete = True
                        for s in task.successors:
                            s.predecessors_complete = all(p.complete for p in s.predecessors)
                    else:
                        self._update(root_task)
                        return False
            inflight += self.dispatch(root_task, agents)
            self._update(root_task)
        self.log("[SCHED] 전체 task 완료")
        self._update(root_task)
        return True
