#!/usr/bin/env python3
"""JnP Task 모델 모듈 (testgroup.py에서 분리).

기존 testgroup.py의 Task 클래스 대비 수정 사항:
- Task.complete 플래그 추가 (스케줄러의 완료 인지용)
- 선행자/후행자(predecessors/successors)를 AtomicTask 공통으로 승격
  → ParallelAtomicTask도 선행자를 가질 수 있음
- addPredecessor()가 양방향 등록 (predecessor.successors 자동 유지)
- 구 필드명 predessesors(오타)는 같은 리스트의 별칭으로 유지
  → 기존 task_allocation()이 무수정으로 동작 (baseline 호환)
- addSucessor()의 self.successor 오타 버그 제거 (addPredecessor가 대체)
- ParallelAtomicTask가 goal 인자를 저장하도록 수정 (기존엔 받고 버림)
"""


class Task:
    def __init__(self):
        self.name = ""
        self.goal = ""
        self.requirement = []
        self.complete = False  # 스케줄러가 end 신호 수신 시 True로 설정


class AtomicTask(Task):
    """실제 agent(robot)에 할당되는 leaf task."""

    def __init__(self):
        super().__init__()
        self.agent = None            # 할당된 agent
        self.assign_status = False
        self.predecessors = []       # 이 task보다 먼저 완료되어야 하는 task들
        self.successors = []         # 이 task 완료를 기다리는 task들
        self.predessesors = self.predecessors  # 구명칭 별칭(같은 리스트) — baseline 호환
        self.predecessors_complete = False

    def addRequirement(self, req):
        self.requirement.append(req)

    def assign(self, agent):
        self.agent = agent

    def addPredecessor(self, predecessor):
        """선행자 등록. 역방향(successors)도 함께 유지한다."""
        if predecessor not in self.predecessors:
            self.predecessors.append(predecessor)
            predecessor.successors.append(self)


class SequentialCompositeTask(Task):
    """자식들을 순서대로 실행하는 composite. subtasks 순서 = 실행 순서."""

    def __init__(self, name, parent, goal):
        super().__init__()
        self.name = name
        self.parent = parent
        self.subtasks = []  # 순서가 있음
        self.goal = goal

    def add(self, task):
        self.subtasks.append(task)


class ParallelCompositeTask(Task):
    """자식들을 동시에 실행할 수 있는 composite."""

    def __init__(self, name="", parent=None):
        super().__init__()
        self.name = name
        self.parent = parent
        self.subtasks = []  # 순서가 없음

    def add(self, task):
        self.subtasks.append(task)


class SequentialAtomicTask(AtomicTask):
    """선행자 관계(화살표)를 가질 수 있는 atomic task."""

    def __init__(self, name="", parent=None, goal=""):
        super().__init__()
        self.name = name
        self.parent = parent
        self.goal = goal


class ParallelAtomicTask(AtomicTask):
    """독립적으로 실행 가능한 atomic task (선행자 없으면 즉시 시작 가능)."""

    def __init__(self, name, parent, goal):
        super().__init__()
        self.name = name
        self.parent = parent
        self.goal = goal  # [수정] 기존 코드는 goal을 받고 저장하지 않았음
