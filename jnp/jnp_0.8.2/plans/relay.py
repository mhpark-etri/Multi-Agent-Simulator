# Task Description: Relay — move an item across the field by handing it from robot to robot; each robot drives its leg to the next robot's hand-off point, the last robot to the final goal
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '릴레이' 의 작업 분할 계획(LLM-TDM 형식). 그룹이 GUI payload(name=x,y,th;…)로 LEGS 를 채운 뒤
# plan_to_tasktree 로 TaskTree 를 만든다(jnp_plan.py). 구조: 순차 — 앞 다리가 끝나야 다음 다리.

# GENERAL TASK DECOMPOSITION
# Decompose into one leg per robot. Legs are strictly sequential (the baton is handed over), so no parallelism.
# Subtask for each leg: the robot drives to its hand-off point (nav goal).

# CODE
LEGS = []   # "robot=x,y,th" per leg, in relay order (bound at run time from the GUI payload)

def relay_leg(leg):
    # 0: this robot drives to its hand-off point (the next robot's position, or the final goal for the last leg)
    GoTo(leg, leg)      # leg = 'robot=x,y,th' (robot 과 목표를 한 조각에 담음)

for leg in LEGS:        # sequential: leg i+1 starts only after leg i is complete
    relay_leg(leg)

# Task Relay is done
