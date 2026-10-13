# Task Description: Relay — move an item across the field by handing it from robot to robot; each robot drives its leg to the next robot's hand-off point, the last robot to the final goal
# Plan Source: example — hand-written template in the LLM-TDM layout for this basic task; NOT produced by the LLM-TDM module
# (예시 계획: 기본 협업 태스크용으로 사람이 LLM-TDM 형식에 맞춰 직접 작성한 분할. LLM-TDM 모듈이 생성한 것이 아님)
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '릴레이' 의 작업 분할 계획(LLM-TDM 형식). 그룹이 GUI payload(name=x,y,th;…)로 ROBOTS·TARGETS 를
# 바인딩한 뒤 plan_to_tasktree 로 canonical TaskTree 를 만들고 jnp_plan 이 실행 트리로 바꾼다(plans/README.md 의 실행 변환 규칙).
# 구조: 순차 — 앞 다리가 끝나야 다음 다리. 지원 범위: 로봇 이름은 유일해야 한다(같은 로봇이 두 다리를 맡는 payload 는 거부 → 0.8.1 고정 빌더).

# GENERAL TASK DECOMPOSITION
# Decompose into one leg per robot. Legs are strictly sequential (the baton is handed over), so no parallelism.
# Subtask for each leg: the robot drives to its hand-off point (nav goal).

# CODE
ROBOTS = []     # relay order (bound at run time from the GUI payload)
TARGETS = {}    # robot -> "x,y,th" hand-off point (bound at run time)

def relay_leg(robot, target):
    # 0: this robot drives to its hand-off point (the next robot's position, or the final goal for the last leg)
    GoTo(robot, target)

for robot in ROBOTS:        # sequential: leg i+1 starts only after leg i is complete
    relay_leg(robot, TARGETS[robot])

# Task Relay is done
