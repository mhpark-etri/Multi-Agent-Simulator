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
import queue

from jnp_task import AtomicTask, SequentialCompositeTask


class Allocator:
    """할당 알고리즘 인터페이스."""

    def select(self, task, agents):
        """task에 적합한 agent를 반환한다(없으면 None). 상태 변경은 하지 않는다."""
        raise NotImplementedError


class SimpleAllocator(Allocator):
    """단순 할당기: agent 목록을 순회하다 처음 만나는
    free 상태이면서 능력을 충족(requirement ⊆ capability)하는 agent를 반환."""

    def select(self, task, agents):
        for agent in agents:
            if agent.free and set(task.requirement) <= agent.capability_set:
                return agent
        return None


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
            return a if (a.free and set(task.requirement) <= a.capability_set) else None
        cands = [a for a in agents
                 if a.free and set(task.requirement) <= a.capability_set]
        if not cands:
            return None
        agent = self.prefer_fn(task, cands) if self.prefer_fn else cands[0]
        if key is not None:
            self.bind[key] = agent
        return agent


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
                 on_update=None, allow_idle=False):
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
