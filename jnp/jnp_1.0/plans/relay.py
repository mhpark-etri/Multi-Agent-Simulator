# Task Description: Relay — move an item across the field by handing it from robot to robot; each robot drives its leg to the next robot's hand-off point, the last robot to the final goal
# Plan Source: example — hand-written template in the LLM-TDM layout for this basic task; NOT produced by the LLM-TDM module
# (예시 계획: 기본 협업 태스크용으로 사람이 LLM-TDM 형식에 맞춰 직접 작성한 분할. LLM-TDM 모듈이 생성한 것이 아님)
# [JnP-0.9.0 2026-10-18] 기본 협업 태스크 '릴레이' 의 작업 분할 계획(LLM-TDM 형식). 로봇을 지정하지 않는다 — 다리(leg)마다 역할(role)
# 하나이고, 그룹이 GUI payload(name=x,y,th;…)의 좌표로 LEGS·TARGETS 를 바인딩한다(이름은 선호 로봇 힌트). plan_to_tasktree 가 canonical v2
# (단위 task 의 role 칸 = 다리)를 만들고, 그룹이 역할마다 로봇을 할당한 뒤 jnp_plan 이 실행 트리로 바꾼다(plans/README.md).
# 구조: 순차 — 앞 다리가 끝나야 다음 다리.

# GENERAL TASK DECOMPOSITION
# Decompose into one leg per role (leg1, leg2, …; a robot is assigned to each role later). Legs are strictly sequential
# (the baton is handed over), so no parallelism. Subtask for each leg: its robot drives to the hand-off point (nav goal).

# CODE
LEGS = []       # leg roles in relay order, e.g. ["leg1", "leg2", "leg3"] (bound at run time)
TARGETS = {}    # leg -> "x,y,th" hand-off point (bound at run time)

def relay_leg(leg, target):
    # 0: the robot holding this leg drives to its hand-off point (the next leg's start, or the final goal for the last leg)
    GoTo(leg, target)

for leg in LEGS:            # sequential: leg i+1 starts only after leg i is complete
    relay_leg(leg, TARGETS[leg])

# Task Relay is done
