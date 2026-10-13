# Task Description: Collision Avoidance — every robot crosses a bottleneck to its own target without blocking the passage; robots pass one at a time in ETA order
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '충돌회피' 의 작업 분할 계획. 그룹이 payload(bt=…;routes=…)로 ETA 순서를 계산해 FIRST/REST 를 채운다.
# 구조: 로봇별 가지가 병렬 — 첫 로봇은 바로 이동, 뒤 로봇은 '앞 로봇 통과 대기(가상)' 뒤 이동. 대기 task 는 그룹의 위치 관찰자가 완료 처리한다.

# GENERAL TASK DECOMPOSITION
# One branch per robot, branches in parallel. The first robot in ETA order moves immediately.
# Every later robot first waits (virtual task, completed by the group's pass watcher when the previous robot has really passed), then moves to its target.

# CODE
FIRST = []   # ["robot:tx,ty"] — the first robot in crossing order (bound at run time)
REST = []    # ["robot:tx,ty:prev_robot"] — later robots with the robot they wait for (bound at run time)

def cross_first(route):
    # 0: drive to the target through the bottleneck
    GoTo(route, route)       # route = 'robot:tx,ty'

def cross_after(route):
    # 0: wait at the current position until the previous robot has passed the bottleneck (virtual, group-completed)
    WaitPass(route, route)   # route = 'robot:tx,ty:prev' — prev 로봇의 통과를 기다림
    # 1: then drive to the target
    GoTo(route, route)

import threading
threads = []
for route in FIRST:
    t = threading.Thread(target=cross_first, args=(route,))
    threads.append(t)
    t.start()
for route in REST:
    t = threading.Thread(target=cross_after, args=(route,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Task Collision Avoidance is done
