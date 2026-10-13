# Task Description: Collision Avoidance — every robot crosses a bottleneck to its own target without blocking the passage; robots pass one at a time in ETA order
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '충돌회피' 의 작업 분할 계획. 통과 순서(ETA = 시작점-병목 거리 ÷ 로봇 속도)는 실행 환경 정보라
# 계획 밖에서 계산한다(jnp_plan.build_avoidance 가 payload 의 bt·routes 와 그룹이 넘긴 속도 함수로 FIRST·REST·PREV·TARGETS 를 바인딩).
# 구조: 로봇별 병렬 가지; 첫 로봇은 바로 이동, 나머지는 앞 로봇의 통과를 기다린 뒤(가상 task, 그룹 관찰자가 완료 처리) 이동.

# GENERAL TASK DECOMPOSITION
# One branch per robot, all branches in parallel. The first robot (shortest ETA) drives straight to its target.
# Every later robot first waits until the robot before it has actually passed the bottleneck (a virtual step the group completes
# from position observation), then drives to its target. Robots wait where they are, so the passage is never blocked.

# CODE
import threading

FIRST = []      # [robot] — the robot that crosses first (bound at run time)
REST = []       # robots that cross after it, in crossing order (bound at run time)
TARGETS = {}    # robot -> "tx,ty" (bound at run time)
PREV = {}       # robot -> the robot that crosses just before it (bound at run time)

def cross_first(robot):
    # 0: drive to the target through the bottleneck
    GoTo(robot, TARGETS[robot])

def cross_after(robot):
    # 0: wait until the previous robot has passed the bottleneck (virtual: completed by the group's observer)
    WaitPass(robot, PREV[robot])
    # 1: then drive to the target
    GoTo(robot, TARGETS[robot])

threads = []
for robot in FIRST:
    t = threading.Thread(target=cross_first, args=(robot,))
    t.start()
    threads.append(t)
for robot in REST:
    t = threading.Thread(target=cross_after, args=(robot,))
    t.start()
    threads.append(t)
for t in threads:
    t.join()

# Task Collision Avoidance is done
